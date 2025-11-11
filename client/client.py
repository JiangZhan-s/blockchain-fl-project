import os
import json
import torch
from web3 import Web3
import sys

# --- 解决代理问题 ---
if 'http_proxy' in os.environ:
    del os.environ['http_proxy']
if 'https_proxy' in os.environ:
    del os.environ['https_proxy']
# --------------------

# 动态添加 client 目录到 sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from config import (
    RPC_URL,
    CONTRACT_ADDRESS,
    ABI_PATH,
    CLIENT1_PRIVATE_KEY,
    CLIENT2_PRIVATE_KEY
)
from models import ComplexCNN
from data_loader import load_cifar10
from trainer import Trainer

# --- 全局参数 ---
TOTAL_CLIENTS = 2
# 全局模型将从这个固定的绝对路径加载
GLOBAL_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'saved_models', 'global_model.pth'))


class FederatedLearningClient:
    def __init__(self, private_key: str, client_id: int):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not self.w3.isConnected():
            raise ConnectionError(f"无法连接到 RPC URL: {RPC_URL}")

        self.account = self.w3.eth.account.from_key(private_key)
        self.client_id = client_id
        self.contract = self._load_contract()
        
        print(f"客户端 {client_id} 初始化成功，地址: {self.account.address}")
        print(f"成功加载合约，地址: {self.contract.address}")

    def _load_contract(self):
        with open(ABI_PATH, 'r') as f:
            abi = json.load(f)["abi"]
        return self.w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

    def _send_transaction(self, func_call):
        tx = func_call.build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price,
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt

    def register(self):
        print(f"\n[客户端 {self.client_id} | 步骤 1/3] 正在尝试注册...")
        try:
            client_info = self.contract.functions.clients(self.account.address).call()
            if client_info[0]: # client_info[0] is 'isRegistered'
                print("  - 客户端已经注册过了。")
                return
            func_call = self.contract.functions.registerClient()
            receipt = self._send_transaction(func_call)
            print(f"  - ✅ 注册成功！交易哈希: {receipt.transactionHash.hex()}")
        except Exception as e:
            print(f"  - ❌ 注册失败: {e}")

    def run_training_round(self):
        current_round = self.contract.functions.currentRound().call()
        print(f"\n[客户端 {self.client_id} | 步骤 2/3] 开始第 {current_round} 轮训练...")

        client_info = self.contract.functions.clients(self.account.address).call()
        if client_info[1] >= current_round: # client_info[1] is 'lastUpdateRound'
            print(f"  - 您已经在第 {current_round} 轮提交过更新了，跳过。")
            return

        # 1. 加载全局模型
        print(f"  - 正在加载全局模型: {GLOBAL_MODEL_PATH}")
        model = ComplexCNN()
        if os.path.exists(GLOBAL_MODEL_PATH):
            model.load_state_dict(torch.load(GLOBAL_MODEL_PATH))
            print("  - 成功加载全局模型权重。")
        else:
            print("  - 未找到全局模型文件，将使用随机初始化的模型。")

        # 2. 加载本客户端的本地数据 (现在返回 Dataset)
        train_dataset = load_cifar10(client_id=self.client_id, num_clients=TOTAL_CLIENTS)

        # 3. 进行真实训练
        # --- 这是修改的地方 ---
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"  - 使用设备: {device}")
        
        # 创建 Trainer 时传入所有必需参数
        trainer = Trainer(model, train_dataset, test_dataset=train_dataset, device=device)
        trainer.train(epochs=1)
        # --- 修改结束 ---

        # 4. 保存模型更新到本地文件
        saved_models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'saved_models'))
        os.makedirs(saved_models_dir, exist_ok=True)
        local_update_path = os.path.join(saved_models_dir, f"client_{self.client_id}_update_round_{current_round}.pth")
        torch.save(model.state_dict(), local_update_path)
        print(f"  - 模型更新已保存到: {local_update_path}")

        # 5. 向区块链提交模型更新的 *绝对路径*
        print("  - 正在向区块链提交模型文件路径...")
        try:
            func_call = self.contract.functions.submitUpdate(local_update_path)
            receipt = self._send_transaction(func_call)
            print(f"  - ✅ 第 {current_round} 轮更新提交成功！交易哈希: {receipt.transactionHash.hex()}")
        except Exception as e:
            print(f"  - ❌ 更新提交失败: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ['0', '1']:
        print("用法: python client.py [client_id]")
        print("  client_id: 0 或 1")
        sys.exit(1)

    client_id = int(sys.argv[1])
    private_key = CLIENT1_PRIVATE_KEY if client_id == 0 else CLIENT2_PRIVATE_KEY

    # 初始化并运行客户端
    fl_client = FederatedLearningClient(private_key=private_key, client_id=client_id)
    fl_client.register()
    fl_client.run_training_round()