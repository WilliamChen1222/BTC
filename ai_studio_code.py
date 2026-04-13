import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# 設定頁面配置
st.set_page_config(page_title="BTC Sentinel 2026", layout="wide")

# --- 數據獲取函數 ---
def fetch_btc_data():
    url = "https://api.binance.com/api/v3/klines"
    params = {'symbol': 'BTCUSDT', 'interval': '1h', 'limit': 100}
    res = requests.get(url, params=params).json()
    df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'q_vol', 'trades', 't_b_vol', 't_q_vol', 'ignore'])
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    return df

def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def fetch_fng():
    res = requests.get('https://api.alternative.me/fng/').json()
    return res['data'][0]

# --- 介面設計 ---
st.title("₿ BTC Sentinel 2026 監控系統")
st.caption(f"最後更新時間: {datetime.now().strftime('%H:%M:%S')}")

# 獲取數據
df = fetch_btc_data()
df['rsi'] = calculate_rsi(df)
fng = fetch_fng()

# 動態支撐與阻力
support = df['low'].min()
resistance = df['high'].max()
current_price = df['close'].iloc[-1]
current_rsi = df['rsi'].iloc[-1]

# 頂部指標
col1, col2, col3 = st.columns(3)
col1.metric("當前價格", f"${current_price:,.2f}")
col2.metric("RSI (14)", f"{current_rsi:.2f}")
col3.metric("恐懼與貪婪", f"{fng['value']} ({fng['value_classification']})")

# 買賣建議邏輯
st.subheader("🤖 Sentinel 策略建議")
if current_rsi < 35 and current_price <= support * 1.02:
    st.success("🟢 建議進場：指標顯示超賣且接近動態支撐位。")
elif current_rsi > 70 or current_price >= resistance * 0.98:
    st.error("🔴 建議下車：指標顯示超買或接近動態阻力位。")
else:
    st.warning("🟡 震盪觀望：目前處於中性區間。")

# 圖表
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['time'], y=df['close'], name="BTC 價格", line=dict(color='#10b981')))
fig.add_hline(y=support, line_dash="dash", line_color="red", annotation_text="支撐位")
fig.add_hline(y=resistance, line_dash="dash", line_color="blue", annotation_text="阻力位")
fig.update_layout(title="BTC 價格軌跡 (100H)", template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

st.info(f"💡 動態支撐位: ${support:,.0f} | 動態阻力位: ${resistance:,.0f}")