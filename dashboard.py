import streamlit as st
import pandas as pd
import os
import time
import json
from web3 import Web3

# --- 文件路径和常量 ---
STATUS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'status.json'))
HISTORY_LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'logs', 'history.csv'))
PLOT_SAVE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'plots', 'accuracy_vs_rounds.png'))
ENV_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '.env'))
ABI_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'blockchain', 'artifacts', 'contracts', 'FederatedLearning.sol', 'FederatedLearning.json'))

# --- 页面配置 ---
st.set_page_config(page_title="联邦学习实时仪表盘", page_icon="🛰️", layout="wide")

# --- 辅助函数 ---
@st.cache_data(ttl=5) # 缓存5秒，避免过于频繁地请求
def get_blockchain_state():
    """连接到区块链并获取实时状态"""
    try:
        # 从 .env 文件读取合约地址
        if not os.path.exists(ENV_FILE): return None
        with open(ENV_FILE, 'r') as f:
            line = f.readline()
            if 'CONTRACT_ADDRESS' not in line: return None
            contract_address = line.split('=')[1].strip()

        # 连接 web3
        w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        if not w3.isConnected(): return None

        # 加载合约
        with open(ABI_PATH, 'r') as f:
            abi = json.load(f)['abi']
        contract = w3.eth.contract(address=contract_address, abi=abi)

        # 获取链上数据
        current_round = contract.functions.currentRound().call()
        updates_count = contract.functions.getRoundUpdatesCount(current_round).call()
        updates_needed = contract.functions.updatesNeeded().call()
        block_number = w3.eth.block_number

        return {
            "contract_address": contract_address,
            "block_number": block_number,
            "onchain_round": current_round,
            "updates_received": updates_count,
            "updates_needed": updates_needed,
        }
    except Exception:
        return None

# --- 主渲染函数 ---
def main():
    st.title("🛰️ 联邦学习与区块链实时监控仪表盘")
    
    placeholder = st.empty()

    while True:
        with placeholder.container():
            # --- 创建三列主布局 ---
            col_fl, col_bc, col_results = st.columns([2, 1.5, 2.5])

            # --- 1. 联邦学习监控列 ---
            with col_fl:
                st.subheader("⚙️ 联邦学习进程")
                if os.path.exists(STATUS_FILE):
                    with open(STATUS_FILE, 'r') as f:
                        status_data = json.load(f)
                    
                    st.metric("服务器总状态", status_data.get('overall_status', 'N/A'))
                    
                    prog_value = (status_data.get('current_round', 0) / status_data.get('total_rounds', 1))
                    st.progress(prog_value, text=f"总进度: 第 {status_data.get('current_round', 0)} / {status_data.get('total_rounds', 1)} 轮")

                    st.info(f"**当前步骤:** {status_data.get('current_step', '等待中...')}")

                    st.markdown("**实时日志输出:**")
                    log_box = st.container(height=300, border=True)
                    for line in status_data.get('log_output', []):
                        log_box.code(line, language=None)
                else:
                    st.warning("⚠️ 找不到状态文件 (status.json)。请先运行 `server.py`。")

            # --- 2. 区块链状态列 ---
            with col_bc:
                st.subheader("🔗 区块链状态")
                bc_state = get_blockchain_state()
                if bc_state:
                    st.metric("当前区块高度", bc_state['block_number'])
                    st.metric("链上当前轮次", bc_state['onchain_round'])
                    st.progress(
                        bc_state['updates_received'] / bc_state['updates_needed'],
                        text=f"本轮更新进度: {bc_state['updates_received']} / {bc_state['updates_needed']}"
                    )
                    st.markdown("**合约地址:**")
                    st.code(bc_state['contract_address'], language=None)
                else:
                    st.warning("⚠️ 无法连接到区块链或找不到合约。")

            # --- 3. 结果分析列 ---
            with col_results:
                st.subheader("📈 结果分析")
                if os.path.exists(PLOT_SAVE_PATH):
                    st.image(PLOT_SAVE_PATH, use_column_width=True)
                else:
                    st.info("准确率图表将在实验结束后生成。")
                
                if os.path.exists(HISTORY_LOG_PATH):
                    st.markdown("**历史数据详情:**")
                    df = pd.read_csv(HISTORY_LOG_PATH)
                    st.dataframe(df, use_container_width=True)

        # 每3秒刷新一次
        time.sleep(3)

if __name__ == "__main__":
    main()