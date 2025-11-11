import pandas as pd
import matplotlib.pyplot as plt
import os

# --- 全局参数 ---
# 定义日志文件和图表保存的路径
HISTORY_LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'history.csv'))
PLOT_SAVE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plots', 'accuracy_vs_rounds.png'))

def plot_accuracy():
    """
    读取 history.csv 文件并绘制准确率随轮次变化的图表。
    """
    # 检查日志文件是否存在
    if not os.path.exists(HISTORY_LOG_PATH):
        print(f"错误：找不到日志文件 {HISTORY_LOG_PATH}")
        print("请先运行几轮联邦学习以生成日志。")
        return

    # 使用 pandas 读取 CSV 文件
    try:
        df = pd.read_csv(HISTORY_LOG_PATH)
    except pd.errors.EmptyDataError:
        print(f"错误：日志文件 {HISTORY_LOG_PATH} 是空的。")
        return
        
    # 检查数据是否有效
    if 'Round' not in df.columns or 'Accuracy' not in df.columns:
        print("错误：CSV文件缺少 'Round' 或 'Accuracy' 列。")
        return

    # 开始绘图
    # --- 这是修改的地方 ---
    plt.style.use('ggplot') # 替换为一个更通用的样式
    # --- 修改结束 ---
    fig, ax = plt.subplots(figsize=(10, 6))

    # 绘制折线图
    ax.plot(df['Round'], df['Accuracy'], marker='o', linestyle='-', color='b', label='Global Model Accuracy')

    # 设置图表标题和坐标轴标签
    ax.set_title('Model Accuracy vs. Federated Learning Rounds', fontsize=16)
    ax.set_xlabel('Round', fontsize=12)
    ax.set_ylabel('Accuracy (%)', fontsize=12)
    
    # 设置 X 轴为整数刻度
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    # 添加图例和网格
    ax.legend()
    ax.grid(True)

    # 确保 'plots' 目录存在
    os.makedirs(os.path.dirname(PLOT_SAVE_PATH), exist_ok=True)

    # 保存图表到文件
    plt.savefig(PLOT_SAVE_PATH, dpi=300)
    print(f"图表已保存到: {PLOT_SAVE_PATH}")

    # 显示图表 (如果你在图形界面环境中，这会弹出一个窗口)
    # plt.show()

if __name__ == "__main__":
    # 运行绘图函数
    plot_accuracy()