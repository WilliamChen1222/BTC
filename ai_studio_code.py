import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go
from datetime import datetime

# 設定頁面配置
st.set_page_config(page_title="BTC Sentinel 2026", layout="wide")

# --- 數據獲取函數 ---
def fetch_btc_data():
    try:
        # 使用 yfinance 抓取 BTC-USD 數據
        # period="5d" 表示抓取過去 5 天, interval="1h" 表示 1 小時 K 線
        ticker = yf.Ticker("BTC-USD")
        df = ticker.history(period="5d", interval="1h")
        
        if df.empty:
            st.warning("Yahoo Finance 未回傳數據，請檢查代號是否正確。")
            return pd.DataFrame()

        # 格式化欄位名稱以符合後續邏輯
        df = df.reset_index()
        df.rename(columns={'Datetime': 'time', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'vol'}, inplace=True)
        return df
    except Exception as e:
        st.error(f"獲取數據時發生錯誤: {e}")
        return pd.DataFrame()

def calculate_rsi(df, period=14):
    if df.empty: return pd.Series()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def fetch_fng():
    try:
        res = requests.get('https://api.alternative.me/fng/', timeout=10).json()
        return res['data'][0]
    except:
        return {"value": "N/A", "value_classification": "無法獲取"}

# --- 介面設計 ---
st.title("₿ BTC Sentinel 2026 監控系統 (Yahoo Data)")

# 獲取數據
df = fetch_btc_data()

if not df.empty:
    df['rsi'] = calculate_rsi(df)
    fng = fetch_fng()

    # 動態支撐與阻力 (取最後 100 筆數據)
    recent_df = df.tail(100)
    support = recent_df['low'].min()
    resistance = recent_df['high'].max()
    current_price = recent_df['close'].iloc[-1]
    current_rsi = recent_df['rsi'].iloc[-1]

    # 頂部指標
    col1, col2, col3 = st.columns(3)
    col1.metric("當前價格 (USD)", f"${current_price:,.2f}")
    col2.metric("RSI (14)", f"{current_rsi:.2f}" if not pd.isna(current_rsi) else "計算中")
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
    fig.add_trace(go.Scatter(x=recent_df['time'], y=recent_df['close'], name="BTC 價格", line=dict(color='#10b981')))
    fig.add_hline(y=support, line_dash="dash", line_color="red", annotation_text="支撐位")
    fig.add_hline(y=resistance, line_dash="dash", line_color="blue", annotation_text="阻力位")
    fig.update_layout(title="BTC 價格軌跡 (100H)", template="plotly_dark", xaxis_title="時間", yaxis_title="價格 (USD)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("⚠️ 無法獲取市場數據。這可能是由於 Yahoo Finance 服務暫時不可用。")