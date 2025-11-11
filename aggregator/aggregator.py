import json
import os
import time
import torch
from collections import OrderedDict
from web3 import Web3

# --- 解决代理问题 ---
if 'http_proxy' in os.environ:
    del os.environ['http_proxy']
if 'https_proxy' in os.environ:
    del os.environ['https_proxy']
# --------------------

# 告诉 Python 在哪里找到 config 和 models 模块
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client')))
from config import (
    RPC_URL,
    CONTRACT_ADDRESS,
    ABI_PATH,
    AGGREGATOR_PRIVATE_KEY,
)
# 从 client 目录导入模型定义，以便加载权重
from models import ComplexCNN 

# --- 全局参数 ---
# 新的全局模型将保存在这个路径
GLOBAL_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'saved_models', 'global_model.pth'))


class Aggregator:
    """
    聚合者，负责结束回合、通过本地文件聚合模型和分发奖励。
    """

    def __init__(self, private_key: str):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not self.w3.isConnected():
            raise ConnectionError(f"无法连接到 RPC URL: {RPC_URL}")

        self.account = self.w3.eth.account.from_key(private_key)
        self.contract = self._load_contract()
        print(f"聚合者初始化成功，地址: {self.account.address}")
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

    def _federated_averaging(self, model_paths: list):
        """
        执行联邦平均算法。
        :param model_paths: 包含所有客户端模型更新文件路径的列表。
        :return: 聚合后的模型 state_dict。
        """
        if not model_paths:
            return None

        print("  - 开始联邦平均...")
        
        # 加载所有模型的状态字典
        all_state_dicts = [torch.load(path) for path in model_paths]
        
        # 初始化一个空的 state_dict 用于累加
        avg_state_dict = OrderedDict()
        
        print(f"  - 正在聚合 {len(all_state_dicts)} 个模型...")
        # 累加所有模型的权重
        for key in all_state_dicts[0].keys():
            # 将所有客户端在这一层的权重张量相加
            avg_state_dict[key] = sum(state_dict[key] for state_dict in all_state_dicts)
        
        # 计算平均值
        for key in avg_state_dict.keys():
            avg_state_dict[key] = avg_state_dict[key] / len(all_state_dicts)
            
        print("  - 联邦平均完成。")
        return avg_state_dict


    def finalize_current_round(self):
        """
        尝试结束当前轮次。
        """
        current_round = self.contract.functions.currentRound().call()
        print(f"\n[聚合者] 正在检查第 {current_round} 轮的状态...")

        updates_count = self.contract.functions.getRoundUpdatesCount(current_round).call()
        updates_needed = self.contract.functions.updatesNeeded().call()
        print(f"  - 本轮已收到 {updates_count} 个更新，需要 {updates_needed} 个。")

        if updates_count < updates_needed:
            print("  - 更新数量不足，无法结束本轮。")
            return

        print("  - 更新数量已满足要求，开始执行聚合流程...")

        # 1. 从区块链获取所有模型更新的文件路径
        print(f"  - 正在获取第 {current_round} 轮的所有模型文件路径...")
        model_update_paths = []
        for i in range(updates_count):
            update = self.contract.functions.roundUpdates(current_round, i).call()
            model_update_paths.append(update[1]) # update[1] 是 modelCID，现在是文件路径
        print(f"  - 成功获取文件路径: {model_update_paths}")

        # 2. 执行真正的聚合算法
        new_global_weights = self._federated_averaging(model_update_paths)

        # 3. 保存新的全局模型
        os.makedirs(os.path.dirname(GLOBAL_MODEL_PATH), exist_ok=True)
        torch.save(new_global_weights, GLOBAL_MODEL_PATH)
        print(f"  - 聚合完成，新的全局模型已保存到: {GLOBAL_MODEL_PATH}")

        # 4. 调用合约的 finalizeRound 函数，传入新全局模型的路径
        print("  - 正在向区块链提交新模型路径，以结束本轮...")
        try:
            # 提交的是新全局模型的绝对路径
            func_call = self.contract.functions.finalizeRound(GLOBAL_MODEL_PATH)
            receipt = self._send_transaction(func_call)
            print(f"  - ✅ 第 {current_round} 轮成功结束！交易哈希: {receipt.transactionHash.hex()}")
            new_round = self.contract.functions.currentRound().call()
            print(f"🎉 新的一轮 ({new_round}) 已经开始！")
        except Exception as e:
            print(f"  - ❌ 结束回合失败: {e}")


if __name__ == "__main__":
    aggregator = Aggregator(private_key=AGGREGATOR_PRIVATE_KEY)
    aggregator.finalize_current_round()