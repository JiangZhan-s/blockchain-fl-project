#!/bin/bash

# 设置颜色变量，让输出更好看
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 获取脚本所在的目录
BASEDIR=$(dirname "$0")
echo "脚本位于: $BASEDIR"

# 进入 blockchain 目录
cd "$BASEDIR"
echo "当前目录: $(pwd)"

# 步骤 1: 启动 Hardhat 节点，并在后台运行
# 我们将节点的输出重定向到 node.log 文件，方便排查问题
echo -e "\n${GREEN}[步骤 1/2] 正在后台启动 Hardhat 节点...${NC}"
npx hardhat node > node.log 2>&1 &

# 获取后台运行的 Hardhat 节点的进程 ID (PID)
NODE_PID=$!
echo "Hardhat 节点已启动，进程 ID: $NODE_PID"
echo "节点的输出日志将保存在 node.log 文件中。"

# 等待几秒钟，确保节点完全启动并准备好接受连接
echo "等待 5 秒，确保节点稳定..."
sleep 5

# 步骤 2: 部署智能合约到本地节点
echo -e "\n${GREEN}[步骤 2/2] 正在部署智能合约...${NC}"
# 我们将部署脚本的输出也保存到 deploy.log，同时在屏幕上显示
npx hardhat run scripts/deploy.ts --network localhost | tee deploy.log

echo -e "\n${GREEN}✅ 本地开发环境已准备就绪！${NC}"
echo "  - Hardhat 节点正在后台运行 (PID: $NODE_PID)。"
echo "  - 合约已部署，部署详情请查看 deploy.log。"
echo "  - 您现在可以运行 Python 客户端和聚合者了。"
echo -e "\n${GREEN}如需停止节点，请运行: kill $NODE_PID${NC}"