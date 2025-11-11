import json
import os
import time
from web3 import Web3

# --- 解决代理问题 ---
if 'http_proxy' in os.environ:
    del os.environ['http_proxy']
if 'https_proxy' in os.environ:
    del os.environ['https_proxy']
# --------------------

# 从 client 目录的 config.py 中导入配置
# 我们需要告诉 Python 在哪里找到 config 模块
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client')))
from config import (
    RPC_URL,
    CONTRACT_ADDRESS,
    ABI_PATH,
    AGGREGATOR_PRIVATE_KEY, # 聚合者使用自己的私钥
)

class Aggregator:
    """
    模拟聚合者，负责结束回合、聚合模型和分发奖励。
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

    def finalize_current_round(self):
        """
        尝试结束当前轮次。
        """
        current_round = self.contract.functions.currentRound().call()
        print(f"\n[聚合者] 正在检查第 {current_round} 轮的状态...")

        # 检查本轮收到的更新数量
        updates_count = self.contract.functions.getRoundUpdatesCount(current_round).call()
        updates_needed = self.contract.functions.updatesNeeded().call()
        print(f"  - 本轮已收到 {updates_count} 个更新，需要 {updates_needed} 个。")

        if updates_count < updates_needed:
            print("  - 更新数量不足，无法结束本轮。聚合者将等待更多更新。")
            return

        print("  - 更新数量已满足要求，开始执行聚合流程...")

        # 1. 模拟下载所有模型更新
        print(f"  - 正在获取第 {current_round} 轮的所有更新 CID...")
        update_cids = []
        for i in range(updates_count):
            update = self.contract.functions.roundUpdates(current_round, i).call()
            update_cids.append(update[1]) # update[1] 是 modelCID
        print(f"  - 成功获取 CIDs: {update_cids}")

        # 2. 模拟聚合过程
        print("  - 正在执行聚合算法 (例如 FedAvg)...")
        time.sleep(2)
        
        # 3. 模拟生成新的全局模型并上传
        new_global_model_cid = f"aggregated_global_model_for_round_{current_round}"
        print(f"  - 聚合完成，生成新的全局模型 CID: {new_global_model_cid}")

        # 4. 调用合约的 finalizeRound 函数
        print("  - 正在向区块链提交新模型，以结束本轮...")
        try:
            func_call = self.contract.functions.finalizeRound(new_global_model_cid)
            receipt = self._send_transaction(func_call)
            print(f"✅ 第 {current_round} 轮成功结束！交易哈希: {receipt.transactionHash.hex()}")
            new_round = self.contract.functions.currentRound().call()
            print(f"🎉 新的一轮 ({new_round}) 已经开始！")
        except Exception as e:
            print(f"❌ 结束回合失败: {e}")


if __name__ == "__main__":
    # 使用 config.py 中定义的聚合者的私钥
    aggregator = Aggregator(private_key=AGGREGATOR_PRIVATE_KEY)
    
    # 尝试结束当前回合
    aggregator.finalize_current_round()