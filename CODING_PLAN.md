# Blockchain-FL 项目编码计划

本文档为您提供了一个清晰的、分阶段的编码路线图，以指导您使用 Hardhat 和 Python 完成整个项目。按照这个顺序，您可以循序渐进地构建和测试每个组件。

---

### 阶段一：搭建并测试区块链核心 (Solidity & Hardhat)

**目标：** 创建、测试并部署一个功能完备的智能合约，作为联邦学习的“去中心化协调员”。

1.  **环境初始化 (Setup)**
    *   **动作：** 在 `blockchain` 目录下打开终端，运行 `npm install`。
    *   **目的：** 安装 Hardhat、Ethers.js、Waffle 等所有必需的 Node.js 依赖。

2.  **实现 `RewardToken.sol`**
    *   **文件：** `blockchain/contracts/RewardToken.sol`
    *   **动作：** 当前代码已基本可用。您需要引入 OpenZeppelin 库来使其更健壮。
        *   在 `blockchain` 目录下运行 `npm install @openzeppelin/contracts`。
        *   确认合约代码使用了 `import "@openzeppelin/contracts/token/ERC20/ERC20.sol";`。
    *   **目的：** 创建一个标准的 ERC20 代币，用于奖励联邦学习的参与者。

3.  **实现 `FederatedLearning.sol` (核心)**
    *   **文件：** `blockchain/contracts/FederatedLearning.sol`
    *   **动作：** 这是最重要的部分。您需要逐步添加以下功能：
        *   **状态变量定义：** 定义管理员、当前回合数、全局模型 IPFS 哈希、奖励代币地址等。
        *   **数据结构 (Structs)：** 创建用于存储参与者信息和模型更新的数据结构。
        *   **事件 (Events)：** 定义关键事件，如 `ClientRegistered`、`UpdateSubmitted`、`RoundFinalized`，方便链下应用监听。
        *   **`registerClient()` 函数：** 允许新客户端加入。
        *   **`submitUpdate()` 函数：** 接收客户端提交的模型更新的 IPFS 哈希。
        *   **`finalizeRound()` 函数：** 由聚合者调用，用于聚合模型、分发奖励，并开启下一轮。
        *   **Getter 函数：** 提供一些公共视图函数，让客户端可以查询当前状态（如最新模型哈希）。
    *   **目的：** 实现联邦学习流程的完整链上协调逻辑。

4.  **编写合约测试 (`fl_test.js`)**
    *   **文件：** `blockchain/test/fl_test.js`
    *   **动作：** 使用 Waffle 和 Ethers.js 编写单元测试，模拟以下场景：
        *   测试客户端能否成功注册。
        *   测试客户端能否成功提交更新。
        *   测试聚合者能否成功结束回合。
        *   测试奖励是否被正确分配。
        *   测试失败场景（例如，非注册用户提交更新）。
    *   **目的：** 确保您的合约在各种情况下都能按预期工作，这是高质量科研和开发的基础。

5.  **部署合约 (`deploy.js`)**
    *   **文件：** `blockchain/scripts/deploy.js`
    *   **动作：** 完善部署脚本，确保它能同时部署 `FederatedLearning` 和 `RewardToken` 合约，并将后者的地址传递给前者。
    *   **目的：** 创建一个可重复执行的部署流程。

6.  **本地部署与验证**
    *   **动作：**
        1.  运行 `npx hardhat node` 启动一个本地测试网络。
        2.  打开一个新终端，运行 `npx hardhat run scripts/deploy.js --network localhost` 将合约部署到该网络。
        3.  记录下部署后的合约地址。
    *   **目的：** 成功在本地运行您的区块链后端。

---

### 阶段二：开发链下组件 (Python)

**目标：** 开发能够与您的智能合约交互的 Python 客户端和聚合器。

1.  **环境初始化 (Setup)**
    *   **动作：** 在 `client` 目录下打开终端，运行 `pip install -r requirements.txt`。
    *   **目的：** 安装 Web3.py, torch, ipfshttpclient 等 Python 依赖。

2.  **配置 `config.py`**
    *   **文件：** `client/config.py`
    *   **动作：** 将阶段一中部署得到的 `FederatedLearning` 合约地址填入 `CONTRACT_ADDRESS`。同时，从 Hardhat Node 启动时显示的账户列表中，挑选几个私钥填入 `ACCOUNT_PRIVATE_KEY`（用于模拟不同客户端）和 `AGGREGATOR_PRIVATE_KEY`。
    *   **目的：** 连接 Python 应用和区块链。

3.  **完善 `client.py`**
    *   **文件：** `client/client.py`
    *   **动作：** 基于现有模板，实现完整的客户端逻辑：
        *   从合约获取最新全局模型。
        *   在本地进行模型训练。
        *   将训练好的模型更新上传到 IPFS。
        *   调用合约的 `submitUpdate` 函数，将 IPFS 哈希上链。
    *   **目的：** 创建一个能参与联邦学习的独立客户端。

4.  **完善 `aggregator.py`**
    *   **文件：** `aggregator/aggregator.py`
    *   **动作：** 实现完整的聚合器逻辑：
        *   从合约获取本轮所有的模型更新哈希。
        *   从 IPFS 下载所有更新。
        *   执行聚合算法（如 FedAvg）。
        *   将聚合后的新全局模型上传到 IPFS。
        *   调用合约的 `finalizeRound` 函数，结束本轮并分发奖励。
    *   **目的：** 创建一个能驱动联邦学习流程前进的聚合器。

---

### 阶段三：端到端集成测试

**目标：** 确保整个系统能够顺畅地运行一个完整的联邦学习回合。

1.  **启动所有服务**
    *   启动 Hardhat 本地节点。
    *   启动一个本地 IPFS 守护进程 (`ipfs daemon`)。

2.  **执行完整流程**
    *   部署您的智能合约。
    *   运行一个或多个 `client.py` 实例，让它们注册并提交更新。
    *   运行 `aggregator.py` 来完成回合的聚合和最终化。

3.  **调试与迭代**
    *   观察终端输出，检查每个步骤是否成功（IPFS 上传、交易确认等）。
    *   使用 Hardhat 的 `console.log` 和 Python 的 `print` 语句进行调试。
    *   根据测试结果，返回阶段一或阶段二修改代码，然后重复本阶段。

---

遵循这个路线图，您将能够有条不紊地完成项目。
