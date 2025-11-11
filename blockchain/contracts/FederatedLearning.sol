// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {RewardToken} from "./RewardToken.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
/**
 * @title FederatedLearning (联邦学习)
 * @dev 用于协调联邦学习流程的主合约。
 */
// 继承自 Ownable 合约，意味着 FederatedLearning 合约本身也具有所有权管理功能
contract FederatedLearning is Ownable {
    // --- 状态变量 (State Variables) ---
    // 这些变量像合约的“记忆”，它们的值被永久存储在区块链上。

    RewardToken public rewardToken; // 指向我们部署的 RewardToken 合约的实例
    uint256 public currentRound;    // 记录当前是第几轮训练
    string public globalModelCID;   // 存储当前全局模型的 IPFS 内容标识符 (CID)
    uint256 public updatesNeeded;   // 每轮需要多少个客户端更新才能触发聚合

    // --- 数据结构 (Data Structures) ---
    // 自定义的数据类型，用于更好地组织和管理复杂数据。

    // 代表一个已注册的客户端的状态
    struct Client {
        bool isRegistered;       // 标记该客户端是否已注册
        uint256 lastSubmittedRound; // 记录该客户端最后一次提交更新是在第几轮
    }

    // 代表一次客户端提交的模型更新
    struct ModelUpdate {
        address clientAddress; // 提交更新的客户端地址
        string modelCID;       // 该更新对应的模型文件的 IPFS CID
    }

    // --- 映射 (Mappings) ---
    // 类似于 Python 中的字典或 Java 中的 HashMap，用于存储键值对。

    // 存储所有已注册的客户端信息。
    // mapping(address => Client) 表示从一个地址可以查询到一个 Client 结构体。
    mapping(address => Client) public clients;

    // 存储每一轮所有客户端提交的更新。
    // mapping(uint256 => ModelUpdate[]) 表示从一个轮次编号可以查询到该轮次所有模型更新组成的数组。
    mapping(uint256 => ModelUpdate[]) public roundUpdates;

    // --- 事件 (Events) ---
    // 用于向区块链外部的应用程序（如我们的Python脚本）广播合约内部发生的重要事情。
    // 外部应用可以监听这些事件并作出反应。`indexed` 关键字可以更快地按该参数搜索事件。

    event ClientRegistered(address indexed clientAddress);
    event UpdateSubmitted(uint256 indexed round, address indexed clientAddress, string modelCID);
    event RoundFinalized(uint256 indexed round, string newGlobalModelCID);

    // --- 构造函数 (Constructor) ---
    // 在合约部署时仅执行一次的特殊函数，用于初始化合约的初始状态。
    constructor(
        address _rewardTokenAddress, // 奖励代币合约的地址
        string memory _initialModelCID, // 初始全局模型的 IPFS CID
        uint256 _updatesNeeded,      // 每轮需要的更新数量
        address initialOwner         // 本合约的初始所有者地址
    ) Ownable(initialOwner) { // 调用 Ownable 的构造函数来设置所有者
        rewardToken = RewardToken(_rewardTokenAddress);
        globalModelCID = _initialModelCID;
        updatesNeeded = _updatesNeeded;
        currentRound = 1; // 联邦学习从第一轮开始
    }

    /**
     * @dev 将调用此函数的客户端注册到联邦学习系统中。
     * 前提条件：调用者之前不能已经注册过。
     */
    function registerClient() public {
        // `require` 是一个检查语句。如果条件为 false，交易将立即停止并回滚，同时返回错误信息。
        // `msg.sender` 是一个全局变量，代表当前调用此函数的账户地址。
        require(!clients[msg.sender].isRegistered, "Client already registered.");

        // 在 clients 映射中，以调用者地址为键，存入一个新的 Client 结构体
        clients[msg.sender] = Client({
            isRegistered: true,
            lastSubmittedRound: 0 // 初始时，我们认为它在第0轮提交过，这样它就可以在第1轮提交
        });

        // 触发 ClientRegistered 事件，向外界广播有新客户端注册成功
        emit ClientRegistered(msg.sender);
    }

    /**
     * @dev 为当前轮次提交一个模型更新。
     * @param _modelCID 客户端本地训练后生成的模型更新的 IPFS CID。
     * 前提条件：
     * 1. 调用者必须是一个已注册的客户端。
     * 2. 该客户端在本轮中尚未提交过更新。
     */
    function submitUpdate(string memory _modelCID) public {
        require(clients[msg.sender].isRegistered, "Client not registered.");
        require(clients[msg.sender].lastSubmittedRound < currentRound, "Update already submitted for this round.");

        // 更新客户端状态，记录它已经在本轮提交过了
        clients[msg.sender].lastSubmittedRound = currentRound;

        // 将本次更新信息（一个 ModelUpdate 结构体）添加到当前轮次的更新数组中
        roundUpdates[currentRound].push(ModelUpdate({
            clientAddress: msg.sender,
            modelCID: _modelCID
        }));

        // 触发 UpdateSubmitted 事件，广播这次提交的详细信息
        emit UpdateSubmitted(currentRound, msg.sender, _modelCID);
    }

    /**
     * @dev 结束当前轮次，进行聚合、发奖，并开启下一轮。
     * @param _newGlobalModelCID 聚合者在链下计算出的新全局模型的 IPFS CID。
     * 前提条件：
     * 1. 只有本合约的所有者（我们指定的聚合者）才能调用此函数。
     * 2. 当前轮次收到的更新数量必须达到或超过 `updatesNeeded` 的要求。
     */
    function finalizeRound(string memory _newGlobalModelCID) public onlyOwner {
        // `storage` 关键字表示 `updates` 是一个指向区块链存储中原始数据的指针，而不是内存中的副本。
        // 对它的修改会直接改变区块链的状态。
        ModelUpdate[] storage updates = roundUpdates[currentRound];

        require(updates.length >= updatesNeeded, "Not enough updates to finalize the round.");

        // --- 奖励分发 ---
        // 在真实的论文项目中，这是可以重点创新的部分，例如根据模型质量、数据量等设计复杂的贡献度评估算法。
        uint256 totalReward = 100 * 1e18; // 简单设定每轮总奖励为 100 个代币。`1e18` 是因为代币通常有18位小数。
        uint256 rewardPerClient = totalReward / updates.length; // 简单地将总奖励平分给所有参与者。

        // 遍历本轮的所有更新，为每个做出贡献的客户端铸造并发送奖励代币
        for (uint i = 0; i < updates.length; i++) {
            rewardToken.mint(updates[i].clientAddress, rewardPerClient);
        }

        // --- 更新全局状态 ---
        globalModelCID = _newGlobalModelCID; // 更新全局模型
        currentRound++; // 轮次加一，开启下一轮

        // （可选但推荐）删除上一轮的更新数据，可以释放存储空间，节省后续交易的 Gas 费用。
        delete roundUpdates[currentRound - 1];

        // 触发 RoundFinalized 事件，广播本轮已结束，并提供新的全局模型 CID
        emit RoundFinalized(currentRound - 1, _newGlobalModelCID);
    }

        /**
     * @dev 获取指定轮次收到的模型更新数量。
     * @param _round 要查询的轮次编号。
     * @return uint256 该轮次的更新数量。
     */
    function getRoundUpdatesCount(uint256 _round) public view returns (uint256) {
        return roundUpdates[_round].length;
    }
}