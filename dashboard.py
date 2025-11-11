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
FINAL_STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'final_blockchain_state.json'))

# --- 页面配置 ---
st.set_page_config(page_title="联邦学习实时仪表盘", page_icon="🛰️", layout="wide")

# --- 辅助函数 ---
def get_full_blockchain_data():
    try:
        if not os.path.exists(ENV_FILE): return None
        with open(ENV_FILE, 'r') as f: contract_address = f.readline().split('=')[1].strip()
        w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        if not w3.isConnected(): return None
        with open(ABI_PATH, 'r') as f: abi = json.load(f)['abi']
        contract = w3.eth.contract(address=contract_address, abi=abi)
        latest_block_number = w3.eth.block_number
        current_round = contract.functions.currentRound().call()
        state_data = {
            "contract_address": contract.address, "block_number": latest_block_number,
            "onchain_round": current_round,
            "updates_received": contract.functions.getRoundUpdatesCount(current_round).call(),
            "updates_needed": contract.functions.updatesNeeded().call(),
        }
        history = []
        scan_depth = min(latest_block_number, 50)
        for i in range(scan_depth):
            block = w3.eth.get_block(latest_block_number - i, full_transactions=True)
            for tx in block.transactions:
                if tx['to'] and tx['to'].lower() == contract.address.lower():
                    try:
                        func_obj, func_params = contract.decode_function_input(tx.input)
                        params_str = ", ".join(f"{k}: {str(v)[:30]}..." if len(str(v)) > 30 else f"{k}: {v}" for k, v in func_params.items())
                        history.append({
                            "block": tx.blockNumber, "hash": tx.hash.hex(),
                            "from": tx['from'], "func": func_obj.fn_name, "params": params_str
                        })
                    except ValueError: pass
        state_data['history'] = history
        return state_data
    except Exception: return None

def load_final_state():
    if os.path.exists(FINAL_STATE_FILE):
        with open(FINAL_STATE_FILE, 'r') as f:
            return json.load(f)
    return None

# --- 主渲染函数 ---
def main():
    st.title("🛰️ 联邦学习与区块链实时监控仪表盘")
    placeholder = st.empty()
    while True:
        with placeholder.container():
            col_fl, col_bc, col_results = st.columns([2, 1.5, 2.5])
            
            with col_fl:
                st.subheader("⚙️ 联邦学习进程")
                if os.path.exists(STATUS_FILE):
                    with open(STATUS_FILE, 'r') as f: status_data = json.load(f)
                    st.metric("服务器总状态", status_data.get('overall_status', 'N/A'))
                    prog_value = (status_data.get('current_round', 0) / status_data.get('total_rounds', 1))
                    st.progress(prog_value, text=f"总进度: 第 {status_data.get('current_round', 0)} / {status_data.get('total_rounds', 1)} 轮")
                    st.info(f"**当前步骤:** {status_data.get('current_step', '等待中...')}")
                    st.markdown("**实时日志输出:**")
                    log_box = st.container(height=250, border=True)
                    for line in status_data.get('log_output', []): log_box.code(line, language=None)
                else:
                    st.warning("⚠️ 找不到状态文件 (status.json)。请先运行 `server.py`。")
            
            with col_bc:
                st.subheader("🔗 区块链状态")
                bc_data = get_full_blockchain_data()
                is_final_state = False
                
                if not bc_data:
                    bc_data = load_final_state()
                    if bc_data:
                        is_final_state = True

                if bc_data:
                    if is_final_state:
                        st.success("快照：实验结束时的最终状态")
                    else:
                        st.info("实时：正在从区块链实时获取数据")

                    # --- 这是修改的地方 ---
                    # 1. 创建两列
                    metric_col1, metric_col2 = st.columns(2)
                    # 2. 将指标分别放入两列
                    metric_col1.metric("区块高度", bc_data['block_number'])
                    metric_col2.metric("链上轮次", bc_data['onchain_round'])
                    # --- 修改结束 ---

                    st.progress(bc_data['updates_received'] / bc_data['updates_needed'], text=f"本轮更新进度: {bc_data['updates_received']} / {bc_data['updates_needed']}")
                    st.markdown("**合约地址:**")
                    st.code(bc_data['contract_address'], language=None)

                    with st.expander("📜 **交易历史**", expanded=True):
                        tx_container = st.container(height=300)
                        if bc_data['history']:
                            for tx in bc_data['history']:
                                tx_container.markdown(f"""- **Block {tx['block']}**: ` {tx['func']}({tx['params']}) `
                                                          - *From: `{tx['from'][:10]}...`*
                                                          - *TxHash: `{tx['hash'][:10]}...`*""")
                        else:
                            tx_container.info("暂无相关交易...")
                else:
                    st.warning("⚠️ 无法连接到区块链，也未找到最终状态快照。")
            
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

        time.sleep(3)

if __name__ == "__main__":
    main()