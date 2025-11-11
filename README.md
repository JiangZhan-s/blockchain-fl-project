# ⛓️ 区块链赋能的联邦学习平台 🚀

这是一个将区块链技术与联邦学习（Federated Learning, FL）相结合的完整原型项目。它利用智能合约作为去中心化的协调器，管理和激励客户端参与联邦学习任务，并通过一个功能强大的Web仪表盘对整个过程进行实时监控。

## ✨ 功能亮点

- **端到端联邦学习**：实现了包含客户端本地训练、服务器端模型聚合（FedAvg）的完整联邦学习流程。
- **区块链协调**：使用 Solidity 智能合约管理联邦学习轮次、客户端注册、模型更新提交和奖励分发，确保了过程的透明和可追溯性。
- **自动化实验服务器**：提供一个“一键启动”的 `server.py` 脚本，能够全自动地清理环境、部署合约、调度多轮客户端训练和模型聚合。
- **全功能实时仪表盘**：基于 Streamlit 构建的动态 Web UI，能够：
    - 实时监控联邦学习的总体状态、当前步骤和详细日志。
    - 实时展示链上状态，包括区块高度、当前轮次和更新进度。
    - 实现类似“区块浏览器”的功能，解码并展示与合约相关的每一笔交易历史。
    - 动态绘制模型准确率随轮次变化的曲线图。
    - 在实验结束后，依然能够展示最终状态的“历史快照”。

## 🛠️ 技术栈

- **区块链**:
    - **智能合约**: Solidity `^0.8.28`
    - **开发环境**: Hardhat
    - **核心库**: Ethers.js, OpenZeppelin Contracts
- **联邦学习与后端**:
    - **语言**: Python 3.8+
    - **机器学习框架**: PyTorch
    - **Web3 交互**: web3.py
- **前端仪表盘**:
    - **框架**: Streamlit
    - **数据处理**: Pandas
    - **可视化**: Matplotlib

## 📂 项目结构

```
blockchain-fl-project/
│
├── blockchain/                # 智能合约与区块链脚本
│   ├── contracts/            # Solidity 智能合约
│   │   ├── FederatedLearning.sol
│   │   └── RewardToken.sol
│   ├── scripts/              # 部署脚本
│   │   └── deploy.ts
│   ├── test/                 # 合约测试
│   │   └── FederatedLearning.test.ts
│   ├── hardhat.config.ts     # Hardhat 配置文件
│   ├── start_local_node.sh   # 一键启动本地节点的脚本
│   └── stop_local_node.sh    # 停止本地节点的脚本
│
├── client/                   # 联邦学习客户端
│   ├── client.py             # 客户端主程序
│   ├── config.py             # 客户端配置文件（私钥、地址等）
│   ├── data_loader.py        # 数据加载与划分
│   ├── models.py             # PyTorch 模型定义
│   └── trainer.py            # 训练器类
│
├── aggregator/               # 联邦学习聚合器
│   └── aggregator.py         # 聚合、评估、记录与更新图表
│
├── utils/                    # 通用工具脚本
│   └── plotter.py            # 绘图脚本
│
├── data/                     # （自动生成）存放 CIFAR-10 数据集
├── logs/                     # （自动生成）存放历史准确率 history.csv
├── plots/                    # （自动生成）存放准确率图表
├── saved_models/             # （自动生成）存放全局模型和客户端模型
│
├── server.py                 # 自动化实验服务器（一键启动）
├── dashboard.py              # Streamlit 实时监控仪表盘
│
├── .env                      # （自动生成）存放最新的合约地址
├── status.json               # （自动生成）存放服务器实时状态
└── final_blockchain_state.json # （自动生成）存放实验结束时的区块链快照
```

## 🚀 如何运行

### 1. 环境准备

- **Node.js 与 npm**: 用于运行 Hardhat 区块链环境。
- **Python**: 用于运行联邦学习客户端、聚合器和服务器。
- **依赖安装**:
    - 安装 Node.js 依赖:
      ```bash
      cd blockchain
      npm install
      cd ..
      ```
    - 安装 Python 依赖:
      ```bash
      pip install -r requirements.txt 
      # requirements.txt 可能需要手动创建，主要包括:
      # pip install web3 torch torchvision pandas matplotlib streamlit
      ```

### 2. 启动实验与监控

本项目提供了高度自动化的运行方式，你只需要打开两个终端。

- **终端 1：启动自动化服务器**
  在项目根目录运行：
  ```bash
  python server.py
  ```
  该命令会自动完成所有工作：清理环境、启动区块链、部署合约、按顺序执行多轮训练和聚合，并在结束后关闭节点。

- **终端 2：启动监控仪表盘**
  在项目根目录运行：
  ```bash
  streamlit run dashboard.py
  ```
  运行后，终端会提供一个 URL (通常是 `http://localhost:8501`)。在浏览器中打开此地址，即可实时监控整个实验过程。

---
现在，这份 `README.md` 已经非常完整和专业了。它不仅能帮助别人理解你的项目，也是对我们共同努力成果的最好总结！# ⛓️ 区块链赋能的联邦学习平台 🚀

这是一个将区块链技术与联邦学习（Federated Learning, FL）相结合的完整原型项目。它利用智能合约作为去中心化的协调器，管理和激励客户端参与联邦学习任务，并通过一个功能强大的Web仪表盘对整个过程进行实时监控。

## ✨ 功能亮点

- **端到端联邦学习**：实现了包含客户端本地训练、服务器端模型聚合（FedAvg）的完整联邦学习流程。
- **区块链协调**：使用 Solidity 智能合约管理联邦学习轮次、客户端注册、模型更新提交和奖励分发，确保了过程的透明和可追溯性。
- **自动化实验服务器**：提供一个“一键启动”的 `server.py` 脚本，能够全自动地清理环境、部署合约、调度多轮客户端训练和模型聚合。
- **全功能实时仪表盘**：基于 Streamlit 构建的动态 Web UI，能够：
    - 实时监控联邦学习的总体状态、当前步骤和详细日志。
    - 实时展示链上状态，包括区块高度、当前轮次和更新进度。
    - 实现类似“区块浏览器”的功能，解码并展示与合约相关的每一笔交易历史。
    - 动态绘制模型准确率随轮次变化的曲线图。
    - 在实验结束后，依然能够展示最终状态的“历史快照”。

## 🛠️ 技术栈

- **区块链**:
    - **智能合约**: Solidity `^0.8.28`
    - **开发环境**: Hardhat
    - **核心库**: Ethers.js, OpenZeppelin Contracts
- **联邦学习与后端**:
    - **语言**: Python 3.8+
    - **机器学习框架**: PyTorch
    - **Web3 交互**: web3.py
- **前端仪表盘**:
    - **框架**: Streamlit
    - **数据处理**: Pandas
    - **可视化**: Matplotlib

## 📂 项目结构

```
blockchain-fl-project/
│
├── blockchain/                # 智能合约与区块链脚本
│   ├── contracts/            # Solidity 智能合约
│   │   ├── FederatedLearning.sol
│   │   └── RewardToken.sol
│   ├── scripts/              # 部署脚本
│   │   └── deploy.ts
│   ├── test/                 # 合约测试
│   │   └── FederatedLearning.test.ts
│   ├── hardhat.config.ts     # Hardhat 配置文件
│   ├── start_local_node.sh   # 一键启动本地节点的脚本
│   └── stop_local_node.sh    # 停止本地节点的脚本
│
├── client/                   # 联邦学习客户端
│   ├── client.py             # 客户端主程序
│   ├── config.py             # 客户端配置文件（私钥、地址等）
│   ├── data_loader.py        # 数据加载与划分
│   ├── models.py             # PyTorch 模型定义
│   └── trainer.py            # 训练器类
│
├── aggregator/               # 联邦学习聚合器
│   └── aggregator.py         # 聚合、评估、记录与更新图表
│
├── utils/                    # 通用工具脚本
│   └── plotter.py            # 绘图脚本
│
├── data/                     # （自动生成）存放 CIFAR-10 数据集
├── logs/                     # （自动生成）存放历史准确率 history.csv
├── plots/                    # （自动生成）存放准确率图表
├── saved_models/             # （自动生成）存放全局模型和客户端模型
│
├── server.py                 # 自动化实验服务器（一键启动）
├── dashboard.py              # Streamlit 实时监控仪表盘
│
├── .env                      # （自动生成）存放最新的合约地址
├── status.json               # （自动生成）存放服务器实时状态
└── final_blockchain_state.json # （自动生成）存放实验结束时的区块链快照
```

## 🚀 如何运行

### 1. 环境准备

- **Node.js 与 npm**: 用于运行 Hardhat 区块链环境。
- **Python**: 用于运行联邦学习客户端、聚合器和服务器。
- **依赖安装**:
    - 安装 Node.js 依赖:
      ```bash
      cd blockchain
      npm install
      cd ..
      ```
    - 安装 Python 依赖:
      ```bash
      pip install -r requirements.txt 
      # requirements.txt 可能需要手动创建，主要包括:
      # pip install web3 torch torchvision pandas matplotlib streamlit
      ```

### 2. 启动实验与监控

本项目提供了高度自动化的运行方式，你只需要打开两个终端。

- **终端 1：启动自动化服务器**
  在项目根目录运行：
  ```bash
  python server.py
  ```
  该命令会自动完成所有工作：清理环境、启动区块链、部署合约、按顺序执行多轮训练和聚合，并在结束后关闭节点。

- **终端 2：启动监控仪表盘**
  在项目根目录运行：
  ```bash
  streamlit run dashboard.py
  ```
  运行后，终端会提供一个 URL (通常是 `http://localhost:8501`)。在浏览器中打开此地址，即可实时监控整个实验过程。

---
现在，这份 `README.md` 已经非常完整和专业了。它不仅能帮助别人理解你的项目，也是对我们共同努力成果的最好总结！