import subprocess
import sys
import os

# --- 配置参数 ---
# 你想让实验自动运行多少轮？
NUM_ROUNDS = 3
# 你总共有多少个客户端？
NUM_CLIENTS = 2

def run_command(command):
    """
    执行一个 shell 命令，并实时打印输出。
    如果命令执行失败，则抛出异常。
    """
    # 使用 Popen 来实时获取输出
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8'
    )
    
    # 实时打印子进程的输出
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
            
    # 等待命令结束并获取返回码
    return_code = process.poll()
    if return_code != 0:
        # 如果命令失败，抛出异常
        raise subprocess.CalledProcessError(return_code, command)

def main():
    """
    联邦学习服务器主函数，负责调度整个多轮实验流程。
    """
    print("="*50)
    print("🚀 联邦学习自动化服务器已启动 🚀")
    print(f"计划执行轮数: {NUM_ROUNDS}")
    print(f"客户端数量: {NUM_CLIENTS}")
    print("="*50)

    # 确保我们使用的是正确的 python 解释器
    python_executable = sys.executable
    print(f"将使用 Python 解释器: {python_executable}\n")

    # --- 准备工作：清理旧的产物 ---
    print("🧹 正在清理旧的实验产物 (logs, plots, saved_models)...")
    # 使用 shell=True 来方便地执行复杂的 shell 命令
    run_command("rm -rf logs/ plots/ saved_models/ .env")
    print("✅ 清理完成。\n")

    # --- 启动区块链 ---
    print("🔗 正在启动本地区块链并部署合约...")
    # 注意：start_local_node.sh 是一个后台进程，所以我们不需要等待它完成
    subprocess.Popen("./blockchain/start_local_node.sh", shell=True)
    # 等待几秒钟，确保节点和合约都已准备就绪
    import time
    time.sleep(10)
    print("✅ 区块链已启动。\n")

    # --- 主循环：按顺序执行多轮联邦学习 ---
    for r in range(1, NUM_ROUNDS + 1):
        print(f"\n{'='*20} 开启第 {r}/{NUM_ROUNDS} 轮 {'='*20}")

        # 1. 依次运行所有客户端
        print(f"▶️  第 {r} 轮：开始调度客户端训练...")
        for i in range(NUM_CLIENTS):
            print(f"\n--- 正在运行客户端 {i} ---")
            client_command = f"{python_executable} client/client.py {i}"
            try:
                run_command(client_command)
                print(f"--- ✅ 客户端 {i} 完成 ---")
            except subprocess.CalledProcessError:
                print(f"--- ❌ 客户端 {i} 运行失败！服务器终止。 ---")
                return # 任何一个客户端失败，则终止整个实验

        # 2. 运行聚合器
        print("\n▶️  第 {r} 轮：所有客户端完成，开始调度聚合器...")
        aggregator_command = f"{python_executable} aggregator/aggregator.py"
        try:
            run_command(aggregator_command)
            print(f"--- ✅ 聚合器完成 ---")
        except subprocess.CalledProcessError:
            print(f"--- ❌ 聚合器运行失败！服务器终止。 ---")
            return

        print(f"\n{'='*20} 第 {r}/{NUM_ROUNDS} 轮成功结束 {'='*20}")

    # --- 实验结束：生成可视化图表 ---
    print("\n🎉 所有联邦学习轮次已完成！ 🎉")
    print("📊 正在生成最终的准确率图表...")
    plotter_command = f"{python_executable} utils/plotter.py"
    try:
        run_command(plotter_command)
        print("✅ 图表生成成功！")
        print(f"请在 'plots/accuracy_vs_rounds.png' 查看结果。")
    except subprocess.CalledProcessError:
        print("❌ 图表生成失败！")

    print("\n👋 服务器任务完成，正在关闭。")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n💥 服务器遇到意外错误: {e}")
    finally:
        # --- 清理工作：关闭区块链节点 ---
        print("\n🛑 正在关闭本地区块链节点...")
        # 使用 Popen 确保即使主程序有错，也能尝试执行
        subprocess.Popen("./blockchain/stop_local_node.sh", shell=True)
        print("👋 再见！")
