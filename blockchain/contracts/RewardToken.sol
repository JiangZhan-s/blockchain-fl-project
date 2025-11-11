// SPDX-License-Identifier: MIT
// 指定代码的开源许可证

// 指定 Solidity 编译器版本，^0.8.20 意味着使用 0.8.20 或更高但小于 0.9.0 的版本
pragma solidity ^0.8.20;

// 从 OpenZeppelin 库导入标准的 ERC20 合约模板
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
// 导入一个权限控制模板，确保只有“所有者”才能执行某些操作
import "@openzeppelin/contracts/access/Ownable.sol";

// 定义我们的合约，它继承了 ERC20 和 Ownable 的所有功能
contract RewardToken is ERC20, Ownable {

    // 这是合约的构造函数，在部署时只会被执行一次
    // 我们需要传入一个初始所有者的地址
    constructor(address initialOwner) 
        ERC20("RewardToken", "RWT")  // 调用父合约 ERC20 的构造函数，设置代币名称和符号
        Ownable(initialOwner)        // 调用父合约 Ownable 的构造函数，设置合约的初始所有者
    {
        // 构造函数体是空的，因为我们不在部署时铸造任何代币
    }

    // 定义一个公开的 "mint" (铸造) 函数
    // 只有合约的“所有者”才能调用这个函数 (因为有 `onlyOwner` 修饰符)
    function mint(address to, uint256 amount) public onlyOwner {
        // 调用 ERC20 内部的 _mint 函数，为 `to` 地址创建 `amount` 数量的新代币
        _mint(to, amount);
    }
}