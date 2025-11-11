import os
import re

# --- 项目根目录 ---

# --- 项目根目录 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_dotenv():
    """
    从项目根目录的 .env 文件加载环境变量。
    """
    env_path = os.path.join(PROJECT_ROOT, ".env")
    variables = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    variables[key] = value
        print(f"从 {env_path} 加载配置成功。")
        return variables
    except FileNotFoundError:
        print(f"错误：找不到配置文件: {env_path}")
        return None

# 加载 .env 文件
env_vars = load_dotenv()
if env_vars is None:
    raise FileNotFoundError("未能找到 .env 文件。请确保已成功运行 start_local_node.sh 脚本。")

# os.path.abspath(__file__) -> 获取 config.py 的绝对路径
# os.path.dirname(...) -> 获取 client 目录的路径
# os.path.dirname(...) -> 获取项目根目录的路径

# --- 区块链配置 ---
RPC_URL = "http://127.0.0.1:8545"

# 合约地址 - 每次部署后都需要从 deploy.log 文件更新
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3" 

# ABI 文件路径 - 现在是绝对路径，不会再出错
ABI_PATH = os.path.join(PROJECT_ROOT, "blockchain", "artifacts", "contracts", "FederatedLearning.sol", "FederatedLearning.json")

# --- 合约地址 ---
# 自动从 .env 文件获取
CONTRACT_ADDRESS = env_vars.get("CONTRACT_ADDRESS")
if CONTRACT_ADDRESS is None:
    raise ValueError("未能在 .env 文件中找到 CONTRACT_ADDRESS。")
print(f"读取到合约地址: {CONTRACT_ADDRESS}")


# ================== 账户设置 ==================
# 警告：这些私钥仅用于本地开发测试！绝不要在主网上使用！

# 我们指定 Hardhat 账户列表中的第一个账户作为聚合者
# 地址: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
AGGREGATOR_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

# 我们用第二个和第三个账户来模拟两个联邦学习客户端
# 客户端 1 地址: 0x70997970C51812dc3A010C7d01b50e0d17dc79C8
CLIENT1_PRIVATE_KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

# 客户端 2 地址: 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC
CLIENT2_PRIVATE_KEY = "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"

# ================== IPFS 设置 ==================
# 如果您的 IPFS 守护进程运行在不同的地址，请修改这里
# IPFS_API_URL = "/ip4/127.0.0.1/tcp/5001"