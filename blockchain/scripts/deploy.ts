import { ethers } from "hardhat";
import fs from "fs";
import path from "path";

async function main() {
  // 1. 获取部署者账户
  // `ethers.getSigners()` 会返回您在上面看到的账户列表中的第一个账户
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);

  // 2. 部署 RewardToken 合约
  // `deployer.address` 作为初始所有者
  // 获取合约工厂，即用于部署合约的抽象
  const rewardTokenFactory = await ethers.getContractFactory("RewardToken");
  // 使用合约工厂部署合约实例，即创建合约
  const rewardToken = await rewardTokenFactory.deploy(deployer.address);
  // 等待合约部署完成
  await rewardToken.waitForDeployment();
  // 获取部署后的合约地址，即 RewardToken 合约地址
  const rewardTokenAddress = await rewardToken.getAddress();
  // 输出部署成功信息
  console.log(`✅ RewardToken deployed to: ${rewardTokenAddress}`);

  // 3. 部署 FederatedLearning 主合约
  const initialModelCID = "Qm_Initial_Model_CID_Placeholder"; // 初始模型的IPFS哈希占位符
  const updatesNeeded = 2; // 每轮需要2个更新
  // 获取 FederatedLearning 合约工厂，即用于部署合约的抽象
  const federatedLearningFactory = await ethers.getContractFactory("FederatedLearning");
  // 使用合约工厂部署 FederatedLearning 合约实例，即创建合约
  const federatedLearning = await federatedLearningFactory.deploy(
    rewardTokenAddress,
    initialModelCID,
    updatesNeeded,
    deployer.address // 部署者是主合约的初始所有者（聚合者）
  );
  await federatedLearning.waitForDeployment();
  const federatedLearningAddress = await federatedLearning.getAddress();
  console.log(`✅ FederatedLearning deployed to: ${federatedLearningAddress}`);

  // 4. 将 RewardToken 的所有权转移给 FederatedLearning 合约，这是为了让主合约能够管理奖励发放
  console.log("\n🔄 Transferring ownership of RewardToken to FederatedLearning contract...");
  const tx = await rewardToken.transferOwnership(federatedLearningAddress);
  await tx.wait(); // 等待交易被打包确认
  console.log(`✅ Ownership of RewardToken transferred to ${federatedLearningAddress}`);

  // --- 新增：将地址写入 .env 文件 ---
  const envContent = `CONTRACT_ADDRESS=${federatedLearningAddress}\n`;
  // 将 .env 文件创建在项目根目录
  const envPath = path.join(__dirname, "..", "..", ".env"); 
  fs.writeFileSync(envPath, envContent);
  console.log(`Contract address saved to ${envPath}`);

}

// 我们推荐使用 async/await 语法来处理异步操作
// 这样可以更清晰地表达代码的执行顺序
// 调用 main 函数，并捕获可能出现的错误
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});