# ================== 区块链设置 ==================
# Hardhat 本地节点的 RPC URL
RPC_URL = "http://127.0.0.1:8545"

# 刚刚部署的 FederatedLearning 合约地址
CONTRACT_ADDRESS = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"

# 合约的 ABI (Application Binary Interface) 文件路径
# ABI 告诉 web3.py 库我们的合约有哪些函数可以调用
# 这个json文件可以在部署合约后从 artifacts 文件夹中找到
ABI_PATH = "../blockchain/artifacts/contracts/FederatedLearning.sol/FederatedLearning.json"


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
IPFS_API_URL = "/ip4/127.0.0.1/tcp/5001"