import os
import json
import time
from web3 import Web3

# --- 解决代理问题 ---
# 检查是否存在 http_proxy 或 https_proxy 环境变量
# 如果存在，暂时将它们移除，以确保能连接到本地的 Hardhat 节点
# 这是一个常见的解决方法，因为代理可能会干扰对 127.0.0.1 的本地连接
if 'http_proxy' in os.environ:
    del os.environ['http_proxy']
if 'https_proxy' in os.environ:
    del os.environ['https_proxy']
if 'HTTP_PROXY' in os.environ:
    del os.environ['HTTP_PROXY']
if 'HTTPS_PROXY' in os.environ:
    del os.environ['HTTPS_PROXY']
if 'ALL_PROXY' in os.environ:
    del os.environ['ALL_PROXY']

# 从 config.py 中导入我们所有的配置信息
from config import (
    RPC_URL,
    CONTRACT_ADDRESS,
    ABI_PATH,
    CLIENT1_PRIVATE_KEY, # 我们将用这个脚本模拟客户端1
    CLIENT2_PRIVATE_KEY, # 我们将用这个脚本模拟客户端2
)

class FederatedLearningClient:
    """
    模拟一个联邦学习客户端，负责与区块链进行交互。
    """

    def __init__(self, private_key: str):
        """
        初始化客户端。
        - 连接到以太坊节点。
        - 加载账户和智能合约。
        """
        # 1. 连接到区块链节点
        # web3是一个用于与以太坊区块链交互的Python库
        # httpprovider用于通过HTTP协议连接到以太坊节点
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not self.w3.isConnected():
            raise ConnectionError(f"无法连接到 RPC URL: {RPC_URL}")

        # 2. 加载执行操作的账户，这里的private_key是客户端的私钥，来源于config.py
        self.account = self.w3.eth.account.from_key(private_key)
        print(f"客户端初始化成功，地址: {self.account.address}")

        # 3. 加载智能合约，即根据合约地址和ABI文件加载合约实例
        self.contract = self._load_contract()
        print(f"成功加载合约，地址: {self.contract.address}")

    def _load_contract(self):
        """一个内部辅助函数，用于加载合约的 ABI 和地址。"""
        with open(ABI_PATH, 'r') as f:
            abi = json.load(f)["abi"]
        return self.w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

    def _send_transaction(self, func_call):
        """一个通用的内部函数，用于构建、签名和发送交易。"""
        # 构建交易
        tx = func_call.build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 2000000, # Gas limit，可以根据需要调整
            'gasPrice': self.w3.eth.gas_price,
        })
        # 签名交易
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)
        # 发送交易
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        # 等待交易被打包确认
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt

    def register(self):
        """调用智能合约的 registerClient 函数进行注册。"""
        print("\n[步骤 1/3] 正在尝试注册客户端...")
        try:
            # 先检查是否已经注册
            client_info = self.contract.functions.clients(self.account.address).call()
            if client_info[0]: # client_info[0] 对应 Client 结构体中的 isRegistered
                print("客户端已经注册过了。")
                return

            # 调用合约的 registerClient 函数
            func_call = self.contract.functions.registerClient()
            receipt = self._send_transaction(func_call)
            print(f"✅ 注册成功！交易哈希: {receipt.transactionHash.hex()}")
        except Exception as e:
            print(f"❌ 注册失败: {e}")

    def run_training_round(self):
        """
        执行一个完整的训练回合：获取模型 -> 本地训练 -> 提交更新。
        """
        # 获取当前轮次
        current_round = self.contract.functions.currentRound().call()
        print(f"\n[步骤 2/3] 开始第 {current_round} 轮训练...")

        # 检查是否需要提交更新
        client_info = self.contract.functions.clients(self.account.address).call()
        if client_info[1] >= current_round: # client_info[1] 对应 lastSubmittedRound
            print(f"您已经在第 {current_round} 轮提交过更新了，跳过。")
            return

        # 1. 从合约获取全局模型 CID
        global_model_cid = self.contract.functions.globalModelCID().call()
        print(f"  - 成功获取全局模型 CID: {global_model_cid}")
        # (在真实场景中，这里会从 IPFS 下载模型)

        # 2. 模拟本地训练
        print("  - 正在进行本地训练...")
        time.sleep(2) # 模拟训练耗时
        # (在真实场景中，这里会加载数据并训练模型)
        
        # 3. 模拟生成模型更新并上传到 IPFS
        # 我们用客户端地址和当前轮次来伪造一个独一无二的 CID
        local_update_cid = f"fake_cid_from_{self.account.address}_at_round_{current_round}"
        print(f"  - 本地训练完成，生成模型更新 CID: {local_update_cid}")
        # (在真实场景中，这里会保存模型并上传到 IPFS)

        # 4. 调用合约的 submitUpdate 函数提交更新
        print("  - 正在向区块链提交模型更新...")
        try:
            func_call = self.contract.functions.submitUpdate(local_update_cid)
            receipt = self._send_transaction(func_call)
            print(f"✅ 第 {current_round} 轮更新提交成功！交易哈希: {receipt.transactionHash.hex()}")
        except Exception as e:
            print(f"❌ 更新提交失败: {e}")


if __name__ == "__main__":
    # 使用 config.py 中定义的客户端1的私钥来初始化客户端
    fl_client = FederatedLearningClient(private_key=CLIENT2_PRIVATE_KEY)

    # 执行注册流程
    fl_client.register()

    # 执行一轮训练
    fl_client.run_training_round()