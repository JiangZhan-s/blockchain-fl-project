import subprocess
import sys
import os
import json
import time

# --- 配置参数 ---
NUM_ROUNDS = 3
NUM_CLIENTS = 2
STATUS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'status.json'))

# --- 状态更新函数 ---
def update_status(data):
    """将状态数据写入 status.json 文件，增加错误处理。"""
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"警告：无法写入状态文件: {e}")

def run_command(command, status_data, step_name):
    """
    执行命令，并实时更新状态文件中的日志。
    """
    status_data['current_step'] = step_name
    status_data['log_output'] = []
    update_status(status_data)
    
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
        text=True, encoding='utf-8', bufsize=1
    )
    
    log_buffer = []
    for line in iter(process.stdout.readline, ''):
        if line:
            clean_line = line.strip()
            print(clean_line)
            log_buffer.append(clean_line)
            if len(log_buffer) > 20: log_buffer.pop(0)
            status_data['log_output'] = log_buffer
            update_status(status_data)
            
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command)

def main():
    """
    联邦学习服务器主函数，负责调度并实时播报状态。
    """
    python_executable = f"{sys.executable} -u"
    
    print("="*60)
    print("🚀 联邦学习自动化服务器已启动 🚀")
    print(f"  - 计划执行轮数: {NUM_ROUNDS}")
    print(f"  - 客户端数量: {NUM_CLIENTS}")
    print(f"  - Python 解释器: {python_executable}")
    print("="*60)
    
    status_data = {
        'overall_status': 'Initializing', 'current_round': 0, 'total_rounds': NUM_ROUNDS,
        'current_step': '清理旧文件', 'log_output': [], 'blockchain_info': {}
    }
    update_status(status_data)

    try:
        print("\n[ 1/3 ] 🧹 清理旧的实验产物...")
        run_command("rm -rf logs/ plots/ saved_models/ .env status.json", status_data, "清理旧文件")
        print("✅ 清理完成。")
        
        print("\n[ 2/3 ] 🔗 启动本地区块链并部署合约...")
        status_data.update({'overall_status': 'Starting Blockchain'})
        subprocess.Popen("./blockchain/start_local_node.sh", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("⏳ 等待10秒，确保节点和合约部署就绪...")
        time.sleep(10)
        print("✅ 区块链已就绪。")

        print("\n[ 3/3 ] 🤖 开始执行联邦学习主循环...")
        for r in range(1, NUM_ROUNDS + 1):
            print(f"\n{'='*25} ROUND {r}/{NUM_ROUNDS} {'='*25}")
            status_data.update({'overall_status': f'Running Round {r}', 'current_round': r})

            for i in range(NUM_CLIENTS):
                print(f"\n--- 客户端 {i} 开始训练 ---")
                client_command = f"{python_executable} client/client.py {i}"
                run_command(client_command, status_data, f"第 {r} 轮：客户端 {i} 训练中")
                print(f"--- ✅ 客户端 {i} 完成 ---")

            print(f"\n--- 聚合器开始工作 ---")
            aggregator_command = f"{python_executable} aggregator/aggregator.py"
            run_command(aggregator_command, status_data, f"第 {r} 轮：聚合器运行中")
            print(f"--- ✅ 聚合器完成 ---")
            
        # --- 实验结束 ---
        status_data.update({'overall_status': 'Finished', 'current_step': '所有任务完成'})
        update_status(status_data)
        print("\n\n🎉🎉🎉 所有联邦学习任务已成功完成！ 🎉🎉🎉")
        print(f"请在 'plots/accuracy_vs_rounds.png' 查看最终结果。")

    except Exception as e:
        print(f"\n💥 服务器遇到意外错误: {e}")
        status_data.update({'overall_status': 'Error', 'current_step': f'错误: {e}'})
        update_status(status_data)
    finally:
        print("\n🛑 正在关闭本地区块链节点...")
        subprocess.Popen("./blockchain/stop_local_node.sh", shell=True)
        print("👋 服务器已关闭。")

if __name__ == "__main__":
    main()