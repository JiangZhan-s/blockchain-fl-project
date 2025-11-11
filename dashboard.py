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

# 这个函数不缓存，因为它创建了无法被序列化的对象
def get_web3_objects():
    """创建并返回 Web3 和 Contract 实例。"""
    try:
        if not os.path.exists(ENV_FILE): return None, None
        with open(ENV_FILE, 'r') as f:
            contract_address = f.readline().split('=')[1].strip()

        w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        if not w3.isConnected(): return None, None

        with open(ABI_PATH, 'r') as f:
            abi = json.load(f)['abi']
        contract = w3.eth.contract(address=contract_address, abi=abi)
        return w3, contract
    except Exception:
        return None, None

# 这个函数可以被缓存，因为它只接收和返回纯数据
@st.cache_data(ttl=3)
def get_blockchain_state(_w3, _contract):
    """从链上获取状态数据。"""
    if not _w3 or not _contract: return None
    current_round = _contract.functions.currentRound().call()
    return {
        "contract_address": _contract.address,
        "block_number": _w3.eth.block_number,
        "onchain_round": current_round,
        "updates_received": _contract.functions.getRoundUpdatesCount(current_round).call(),
        "updates_needed": _contract.functions.updatesNeeded().call(),
    }

@st.cache_data(ttl=3)
def get_transaction_history(_w3, _contract, latest_block_number):
    """扫描并解码交易历史。"""
    if not _w3 or not _contract: return []
    history = []
    scan_depth = min(latest_block_number, 50)
    
    for i in range(scan_depth):
        block = _w3.eth.get_block(latest_block_number - i, full_transactions=True)
        for tx in block.transactions:
            if tx['to'] and tx['to'].lower() == _contract.address.lower():
                try:
                    func_obj, func_params = _contract.decode_function_input(tx.input)
                    params_str = ", ".join(f"{k}: {str(v)[:30]}..." if len(str(v)) > 30 else f"{k}: {v}" for k, v in func_params.items())
                    history.append({
                        "block": tx.blockNumber, "hash": tx.hash.hex(),
                        "from": tx['from'], "func": func_obj.fn_name, "params": params_str
                    })
                except ValueError:
                    pass
    return history

# --- 主渲染函数 ---
def main():
    st.title("🛰️ 联邦学习与区块链实时监控仪表盘")
    
    placeholder = st.empty()

    while True:
        with placeholder.container():
            col_fl, col_bc, col_results = st.columns([2, 1.5, 2.5])

            # --- 1. 联邦学习监控列 ---
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

            # --- 2. 区块链状态列 ---
            with col_bc:
                st.subheader("🔗 区块链状态")
                # 在循环的每次迭代中，重新创建 web3 对象
                w3, contract = get_web3_objects()
                if w3 and contract:
                    bc_state = get_blockchain_state(w3, contract)
                    st.metric("当前区块高度", bc_state['block_number'])
                    st.metric("链上当前轮次", bc_state['onchain_round'])
                    st.progress(bc_state['updates_received'] / bc_state['updates_needed'], text=f"本轮更新进度: {bc_state['updates_received']} / {bc_state['updates_needed']}")
                    st.markdown("**合约地址:**")
                    st.code(bc_state['contract_address'], language=None)

                    with st.expander("📜 **最近交易历史**", expanded=True):
                        tx_history = get_transaction_history(w3, contract, bc_state['block_number'])
                        if tx_history:
                            for tx in tx_history:
                                st.markdown(f"""- **Block {tx['block']}**: ` {tx['func']}({tx['params']}) `
                                                  - *From: `{tx['from'][:10]}...`*
                                                  - *TxHash: `{tx['hash'][:10]}...`*""")
                        else:
                            st.info("暂无相关交易...")
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

        time.sleep(3)

if __name__ == "__main__":
    main()