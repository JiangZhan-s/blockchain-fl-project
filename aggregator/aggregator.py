import json
import os
import time
import torch
import csv
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
# 从 client 目录导入模型定义和新的测试数据加载器
from models import ComplexCNN 
from data_loader import load_cifar10_test

# --- 全局参数 ---
# 新的全局模型将保存在这个路径
GLOBAL_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'saved_models', 'global_model.pth'))
# 评估历史将保存在这个路径
HISTORY_LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'history.csv'))


class Aggregator:
    """
    聚合者，负责结束回合、聚合模型、评估新模型并记录准确率。
    """

    def __init__(self, private_key: str):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not self.w3.isConnected():
            raise ConnectionError(f"无法连接到 RPC URL: {RPC_URL}")

        self.account = self.w3.eth.account.from_key(private_key)
        self.contract = self._load_contract()
        # 初始化测试数据加载器
        self.test_loader = load_cifar10_test()
        # 初始化设备（CPU或GPU）
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"聚合者初始化成功，地址: {self.account.address}")
        print(f"成功加载合约，地址: {self.contract.address}")
        print(f"使用设备进行评估: {self.device}")

    def _load_contract(self):
        """加载合约 ABI 并返回合约实例。"""
        with open(ABI_PATH, 'r') as f:
            abi = json.load(f)["abi"]
        return self.w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

    def _send_transaction(self, func_call):
        """构建、签名并发送交易。"""
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
        all_state_dicts = [torch.load(path, map_location=self.device) for path in model_paths]
        avg_state_dict = OrderedDict()
        
        print(f"  - 正在聚合 {len(all_state_dicts)} 个模型...")
        for key in all_state_dicts[0].keys():
            avg_state_dict[key] = sum(state_dict[key] for state_dict in all_state_dicts) / len(all_state_dicts)
            
        print("  - 联邦平均完成。")
        return avg_state_dict

    def _evaluate_model(self, model_weights):
        """
        在测试集上评估给定模型的准确率。
        :param model_weights: 要评估的模型的 state_dict。
        :return: 准确率（百分比）。
        """
        model = ComplexCNN().to(self.device)
        model.load_state_dict(model_weights)
        model.eval()  # 设置为评估模式
        
        correct = 0
        total = 0
        with torch.no_grad(): # 在评估时不需要计算梯度
            for images, labels in self.test_loader:
                images, labels = images.to(self.device), labels.to(self.device)
                outputs = model(images)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        accuracy = 100 * correct / total
        print(f"  - 📈 模型评估完成，准确率: {accuracy:.2f}%")
        return accuracy

    def _log_history(self, round_number, accuracy):
        """
        将轮次和准确率记录到 CSV 文件中。
        """
        # 确保日志目录存在
        os.makedirs(os.path.dirname(HISTORY_LOG_PATH), exist_ok=True)
        
        # 检查文件是否存在，如果不存在则先写入表头
        file_exists = os.path.isfile(HISTORY_LOG_PATH)
        
        with open(HISTORY_LOG_PATH, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Round', 'Accuracy']) # 写入表头
            writer.writerow([round_number, accuracy])
        print(f"  - 📝 已将第 {round_number} 轮的准确率记录到 {HISTORY_LOG_PATH}")

    def finalize_current_round(self):
        """
        尝试结束当前轮次，并执行聚合、评估和记录。
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

        # 1. 获取模型文件路径
        model_update_paths = []
        for i in range(updates_count):
            update = self.contract.functions.roundUpdates(current_round, i).call()
            model_update_paths.append(update[1])
        print(f"  - 成功获取文件路径: {model_update_paths}")

        # 2. 执行联邦平均
        new_global_weights = self._federated_averaging(model_update_paths)

        # 3. 评估新全局模型的准确率
        accuracy = self._evaluate_model(new_global_weights)

        # 4. 记录本轮的准确率
        self._log_history(current_round, accuracy)

        # 5. 保存新的全局模型
        os.makedirs(os.path.dirname(GLOBAL_MODEL_PATH), exist_ok=True)
        torch.save(new_global_weights, GLOBAL_MODEL_PATH)
        print(f"  - 聚合完成，新的全局模型已保存到: {GLOBAL_MODEL_PATH}")

        # 6. 调用合约结束本轮
        print("  - 正在向区块链提交新模型路径，以结束本轮...")
        try:
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