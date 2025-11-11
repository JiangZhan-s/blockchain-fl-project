#!/bin/bash

# 设置颜色变量
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}正在查找并停止 Hardhat 节点进程...${NC}"

# 查找正在运行的 Hardhat 节点进程
# pgrep -f "hardhat node" 会查找命令行中包含 "hardhat node" 的进程
# -f 选项表示匹配完整的进程命令行，而不仅仅是进程名
PID=$(pgrep -f "hardhat node")

# 检查是否找到了进程
if [ -z "$PID" ]; then
  echo "没有找到正在运行的 Hardhat 节点。"
else
  # 如果找到了，就杀死该进程
  echo "找到 Hardhat 节点进程 (PID: $PID)，正在停止..."
  kill $PID
  echo "✅ Hardhat 节点已停止。"
fi