// SPDX-License-Identifier: MIT
// 指定 Solidity 编译器版本，^0.8.28 表示使用 0.8.28 或更高但不超过 0.9.0 的版本
pragma solidity ^0.8.28;

// ...
// 从openzeppelin合约库导入ERC20和Ownable合约，即标准的ERC20代币实现和所有权管理功能
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
// ...

/**
 * @title RewardToken (奖励代币)
 * @dev 一个由所有者控制铸造的 ERC20 代币。
 * 这个代币将用于奖励联邦学习的参与者。
 */
// 定义 RewardToken 合约，它同时继承了 ERC20 和 Ownable 的所有功能
contract RewardToken is ERC20, Ownable {
    /**
     * @dev 合约的构造函数，在部署时仅执行一次。
     * @param initialOwner 将被设置为合约的初始所有者地址。
     */
    constructor(
        address initialOwner
    // 调用父合约 ERC20 的构造函数，设置代币的全名和简称
    // 调用父合约 Ownable 的构造函数，设置合约的初始所有者
    ) ERC20("RewardToken", "RWT") Ownable(initialOwner) {}

    /**
     * @dev 铸造新的代币。
     * 创建 `amount` 数量的新代币，并将其发送给 `to` 地址。
     * 这是一个受限函数，只有合约的当前所有者才能调用。
     * 在我们的设计中，所有者将是 FederatedLearning 主合约。
     * @param to 接收新代币的地址。
     * @param amount 要铸造的代币数量 (以最小单位表示)。
     */
    function mint(address to, uint256 amount) public onlyOwner {
        // 调用 ERC20 内部的 _mint 函数来执行实际的铸币操作
        _mint(to, amount);
    }
}