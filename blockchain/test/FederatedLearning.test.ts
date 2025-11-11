// 导入测试需要用到的库
import { expect } from "chai"; // "chai" 是一个断言库，用来写 "期望 a 等于 b" 这样的语句
import { ethers } from "hardhat"; // "ethers" 是一个与以太坊交互的库
import { FederatedLearning, RewardToken } from "../typechain-types"; // 这是 Hardhat 编译后自动生成的合约类型定义
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

// `describe` 用来组织一组相关的测试，我们为 `FederatedLearning` 合约创建一个测试套件
describe("FederatedLearning Contract Tests", function () {
  // 在这里定义一些变量，它们会在多个测试用例中被重复使用
  let federatedLearning: FederatedLearning;
  let rewardToken: RewardToken;
  let owner: HardhatEthersSigner; // 合约的所有者（聚合者）
  let client1: HardhatEthersSigner; // 模拟第一个客户端
  let client2: HardhatEthersSigner; // 模拟第二个客户端

  // 定义一些在部署合约时需要用到的常量
  const initialModelCID = "initial_model_cid_v1";
  const updatesNeeded = 2;

  // `beforeEach` 是一个钩子函数，它会在每一个 `it(...)` 测试用例运行之前执行
  // 作用是确保每个测试都在一个干净、独立的环境中运行
  beforeEach(async function () {
    // 从 Hardhat 的本地测试网络中获取可用的账户列表
    [owner, client1, client2] = await ethers.getSigners();

    // 部署 RewardToken 合约
    const RewardTokenFactory = await ethers.getContractFactory("RewardToken");
    rewardToken = await RewardTokenFactory.deploy(owner.address);
    await rewardToken.waitForDeployment();
    const rewardTokenAddress = await rewardToken.getAddress();

    // 部署 FederatedLearning 主合约，并传入必要的参数
    const FederatedLearningFactory = await ethers.getContractFactory("FederatedLearning");
    federatedLearning = await FederatedLearningFactory.deploy(
      rewardTokenAddress,
      initialModelCID,
      updatesNeeded,
      owner.address
    );
    await federatedLearning.waitForDeployment();
  });

  // --- 第一个测试分组：测试注册功能 ---
  describe("Client Registration", function () {
    
    // `it` 定义了一个具体的测试用例，描述了它要测试的行为
    it("Should allow a new client to register successfully", async function () {
      // 模拟 client1 调用 registerClient 函数
      // .connect(client1) 的意思是“接下来的调用将由 client1 发起”
      await federatedLearning.connect(client1).registerClient();

      // 断言：检查 client1 的注册状态是否变为了 true
      const clientInfo = await federatedLearning.clients(client1.address);
      expect(clientInfo.isRegistered).to.equal(true);
    });

    it("Should emit a ClientRegistered event upon successful registration", async function () {
      // 断言：期望在执行 registerClient 函数时，会触发一个名为 "ClientRegistered" 的事件
      // 并且该事件的参数应该是 client1 的地址
      await expect(federatedLearning.connect(client1).registerClient())
        .to.emit(federatedLearning, "ClientRegistered")
        .withArgs(client1.address);
    });

    it("Should prevent a client from registering twice", async function () {
      // 先让 client1 成功注册一次
      await federatedLearning.connect(client1).registerClient();

      // 断言：期望当 client1 尝试第二次调用 registerClient 时，交易会失败
      // 并且返回的错误信息应该与我们合约中 `require` 语句定义的一致
      await expect(federatedLearning.connect(client1).registerClient())
        .to.be.revertedWith("Client already registered.");
    });
  });

    // --- 第二个测试分组：测试模型更新提交功能 ---
  describe("Model Update Submission", function () {
    const modelCID = "client1_model_update_cid";

    // 在这个分组的每个测试用例开始前，我们先确保 client1 已经注册
    beforeEach(async function () {
      await federatedLearning.connect(client1).registerClient();
    });

     it("Should allow a registered client to submit an update", async function () {
      // ... (the expect(...).to.emit(...) part remains the same) ...
      await expect(federatedLearning.connect(client1).submitUpdate(modelCID))
        .to.emit(federatedLearning, "UpdateSubmitted")
        .withArgs(1, client1.address, modelCID);

      // 检查合约状态是否正确更新
      const clientInfo = await federatedLearning.clients(client1.address);
      expect(clientInfo.lastSubmittedRound).to.equal(1);

      // **修正部分：**
      // 1. 使用新的辅助函数检查更新数量
      const count = await federatedLearning.getRoundUpdatesCount(1);
      expect(count).to.equal(1);

      // 2. 使用正确的 getter 方式获取第0个元素并检查其内容
      const firstUpdate = await federatedLearning.roundUpdates(1, 0);
      expect(firstUpdate.clientAddress).to.equal(client1.address);
      expect(firstUpdate.modelCID).to.equal(modelCID);
    });

    it("Should prevent an unregistered client from submitting an update", async function () {
      // 断言：期望一个未注册的 client2 提交更新时，交易会失败
      await expect(federatedLearning.connect(client2).submitUpdate(modelCID))
        .to.be.revertedWith("Client not registered.");
    });

    it("Should prevent a client from submitting an update twice in the same round", async function () {
      // client1 先成功提交一次
      await federatedLearning.connect(client1).submitUpdate(modelCID);

      // 断言：期望当 client1 尝试第二次提交时，交易会失败
      await expect(federatedLearning.connect(client1).submitUpdate("another_cid"))
        .to.be.revertedWith("Update already submitted for this round.");
    });
  });

  // --- 第三个测试分组：测试回合结束功能 ---
  describe("Round Finalization", function () {
    const newGlobalModelCID = "new_global_model_cid_round_1";

    // 在这个分组的每个测试用例开始前，我们先模拟一个完整的、已准备好结束的回合
    // 即：client1 和 client2 都已注册并提交了更新
    beforeEach(async function () {
      await federatedLearning.connect(client1).registerClient();
      await federatedLearning.connect(client2).registerClient();
      await federatedLearning.connect(client1).submitUpdate("client1_update");
      await federatedLearning.connect(client2).submitUpdate("client2_update");

      // 为了能给 client 发放奖励，我们需要先让 FederatedLearning 合约成为 RewardToken 的“所有者”
      // 这样它才有权限调用 mint 函数
      await rewardToken.transferOwnership(await federatedLearning.getAddress());
    });

    it("Should allow the owner to finalize the round and distribute rewards", async function () {
      // 检查 client1 和 client2 在收到奖励前的余额
      const client1BalanceBefore = await rewardToken.balanceOf(client1.address);
      const client2BalanceBefore = await rewardToken.balanceOf(client2.address);
      expect(client1BalanceBefore).to.equal(0);
      expect(client2BalanceBefore).to.equal(0);

      // 由 owner 调用 finalizeRound
      await expect(federatedLearning.connect(owner).finalizeRound(newGlobalModelCID))
        .to.emit(federatedLearning, "RoundFinalized")
        .withArgs(1, newGlobalModelCID);

      // 检查合约状态是否更新
      expect(await federatedLearning.globalModelCID()).to.equal(newGlobalModelCID);
      expect(await federatedLearning.currentRound()).to.equal(2);

      // 检查奖励是否已正确分发
      const client1BalanceAfter = await rewardToken.balanceOf(client1.address);
      const client2BalanceAfter = await rewardToken.balanceOf(client2.address);
      
      // 您的合约中设定每轮总奖励为 100，平分给 2 个客户端，每人 50
      // ethers.parseUnits("50", 18) 用来处理代币的18位小数
      const expectedReward = ethers.parseUnits("50", 18); 
      expect(client1BalanceAfter).to.equal(expectedReward);
      expect(client2BalanceAfter).to.equal(expectedReward);
    });

    it("Should prevent a non-owner from finalizing the round", async function () {
      // 断言：期望当 client1 (非所有者) 尝试调用时，交易会失败
      // 注意：错误信息来自 OpenZeppelin 的 Ownable 合约
      await expect(federatedLearning.connect(client1).finalizeRound(newGlobalModelCID))
        .to.be.revertedWithCustomError(federatedLearning, "OwnableUnauthorizedAccount")
        .withArgs(client1.address);
    });

    it("Should prevent finalizing the round if not enough updates are submitted", async function () {
      // 部署一个新合约，这次设定需要 3 个更新
      const FLFactory = await ethers.getContractFactory("FederatedLearning");
      const fl2 = await FLFactory.deploy(
        await rewardToken.getAddress(),
        initialModelCID,
        3, // 需要 3 个更新
        owner.address
      );
      await fl2.waitForDeployment();

      // 让 client1 和 client2 在这个新合约中注册并提交 (总共只有 2 个更新)
      await fl2.connect(client1).registerClient();
      await fl2.connect(client2).registerClient();
      await fl2.connect(client1).submitUpdate("c1_update");
      await fl2.connect(client2).submitUpdate("c2_update");

      // 断言：期望当 owner 尝试结束回合时，交易会失败，因为更新数量不足
      await expect(fl2.connect(owner).finalizeRound(newGlobalModelCID))
        .to.be.revertedWith("Not enough updates to finalize the round.");
    });
  });
});