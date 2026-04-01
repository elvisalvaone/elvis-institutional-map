import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import time

# --- 1. SETUP ---
st.set_page_config(page_title="ELVIS MASTER SNIPER", layout="wide", page_icon="🎯")

# Sidebar for Logic Adjustments
st.sidebar.header("🕹️ Institutional Logic")

TOP_10_CRYPTOS = ["BTC-USD", "SOL-USD", "ETH-USD", "XRP-USD", "BNB-USD", "DOGE-USD", "ADA-USD", "TRX-USD", "LINK-USD", "AVAX-USD"]

target_sym = st.sidebar.selectbox("🎯 Target Asset", TOP_10_CRYPTOS, index=1)
vol_thresh = st.sidebar.slider("Volume Spike (Institutional)", 1.0, 3.0, 1.3)
body_ratio = st.sidebar.slider("Base Candle %", 0.1, 0.6, 0.4)
refresh_rate = st.sidebar.selectbox("Refresh (Min)", [1, 5, 15], index=0)

# =========================
# 2. THE ENGINE
# =========================

def get_data(symbol):
    try:
        df = yf.download(symbol, period="10d", interval="1h", progress=False)
        if df.empty: return df
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = [col[0] for col in df.columns]
        # 20-period EMA: The King's Springboard
        df['TrendLine'] = df['Close'].ewm(span=20, adjust=False).mean()
        return df[['Open', 'High', 'Low', 'Close', 'Volume', 'TrendLine']].dropna()
    except Exception as e:
        st.error(f"Data Error for {symbol}: {e}")
        return pd.DataFrame()

def find_structure(data):
    structs = []
    for i in range(5, len(data) - 1):
        h, l, o, c = data["High"].iloc[i], data["Low"].iloc[i], data["Open"].iloc[i], data["Close"].iloc[i]
        vol_strength = data["Volume"].iloc[i] / data["Volume"].iloc[i-1] if data["Volume"].iloc[i-1] > 0 else 1
        body = abs(o - c)
        rng = h - l
        if rng > 0 and body < (rng * body_ratio) and vol_strength > vol_thresh:
            next_c = data["Close"].iloc[i+1]
            if next_c > h: 
                structs.append({"type": "DEMAND", "low": l, "high": h, "idx": i, "time": data.index[i]})
            elif next_c < l: 
                structs.append({"type": "SUPPLY", "low": l, "high": h, "idx": i, "time": data.index[i]})
    return structs

def is_fresh(data, s):
    for j in range(s["idx"] + 1, len(data)):
        if data["Low"].iloc[j] <= s["high"] and data["High"].iloc[j] >= s["low"]:
            return False
    return True

# =========================
# 3. DASHBOARD UI
# =========================

st.title(f"🔥 ELVIS MASTER SNIPER: {target_sym}")

# Global Clocks Row (Slim Header)
with st.container(border=True):
    t1, t2, t3, t4, t5 = st.columns(5)
    t1.caption(f"🗽 NY: {(datetime.now() + pd.Timedelta(hours=3)).strftime('%I:%M %p')}")
    t2.caption(f"🏰 LDN: {(datetime.now() + pd.Timedelta(hours=8)).strftime('%I:%M %p')}")
    t3.caption(f"🗼 TKY: {(datetime.now() + pd.Timedelta(hours=16)).strftime('%I:%M %p')}")
    t4.caption(f"🇸🇬 SGP: {(datetime.now() + pd.Timedelta(hours=15)).strftime('%I:%M %p')}")
    t5.caption(f"🕌 DXB: {(datetime.now() + pd.Timedelta(hours=11)).strftime('%I:%M %p')}")

df = get_data(target_sym)
if not df.empty:
    price = df["Close"].iloc[-1]
    trend_val = df["TrendLine"].iloc[-1]
    
    # Sentiment Calculation
    last_24h = df.tail(24)
    bull_vol = last_24h['Volume'][last_24h['Close'] > last_24h['Open']].sum()
    bear_vol = last_24h['Volume'][last_24h['Close'] < last_24h['Open']].sum()
    total_v = bull_vol + bear_vol
    bull_p = (bull_vol / total_v * 100) if total_v > 0 else 50
    
    is_bullish = price > trend_val
    all_structs = find_structure(df)
    fresh_zones = [s for s in all_structs if is_fresh(df, s)]
    best_zone = fresh_zones[-1] if fresh_zones else None
    
    # --- TOP METRICS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 PRICE", f"${price:,.2f}")
    m2.metric("🐂 BULL %", f"{bull_p:.1f}%")
    m3.metric("🐻 BEAR %", f"{100-bull_p:.1f}%")
    
    # --- MAIN CHART ---
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name=target_sym))
    fig.add_trace(go.Scatter(x=df.index, y=df['TrendLine'], line=dict(color='yellow', width=2.5), name="Elvis Trend"))
    
    if best_zone:
        z_color = "rgba(0, 255, 0, 0.4)" if best_zone['type'] == "DEMAND" else "rgba(255, 0, 0, 0.4)"
        fig.add_shape(type="rect", x0=best_zone['time'], y0=best_zone['low'], x1=df.index[-1], y1=best_zone['high'], fillcolor=z_color, line_width=0)
    
    fig.update_layout(template="plotly_dark", height=550, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- THE ELVIS MASTER ANALYSIS (EXTENDED) ---
    dist = ((price - trend_val) / trend_val) * 100
    st.markdown("---")
    st.header("🏛️ ELVIS FIELD ANALYSIS")
    
    a1, a2, a3 = st.columns(3)
    
    with a1:
        st.subheader("🧐 The Playbook")
        if is_bullish:
            if dist > 1.8:
                st.warning(f"**NO MAN'S LAND:** Price is overextended ({dist:.1f}%). "
                           "The wind is at your back, but don't be the retail guy buying the top of the spike. "
                           "A sniper waits for a return to the Yellow Line.")
            elif dist < 0.5:
                st.success("**SNIPER ENTRY:** Price is 'kissing' the yellow trend line. "
                           "The last 3 green candles jumped off this line like a springboard. Enter here.")
            else:
                st.info("**RUN PHASE:** Trend is confirmed. We are in the middle of a move. "
                        "Look for a new Green Demand Box to form before adding more.")
        else:
            st.error("**BEARISH TRAP:** Price is below the floor. Whales are dumping. "
                     "Wait for the next Institutional Base to form.")

    with a2:
        st.subheader("🕵️ Whale Activity")
        if best_zone:
            st.success(f"**FOOTPRINT FOUND:** Fresh {best_zone['type']} at ${best_zone['low']:.2f}. "
                       "The Whales have built a concrete wall here. Use this as your defensive line.")
        else:
            st.info(f"**WHALES ARE HIDING:** No massive base at {vol_thresh}x spike. "
                    "The Whales are currently driving the price up, not stacking new orders yet.")

    with a3:
        st.subheader("🚀 Global Strategy")
        ldn_hour = (datetime.now() + pd.Timedelta(hours=8)).hour
        if 7 <= ldn_hour <= 9:
            st.warning(f"**LONDON OPEN:** It's {ldn_hour}:{(datetime.now() + pd.Timedelta(hours=8)).minute:02d} AM in London. "
                       "Expect a 'Fake Move' or stop-hunt in this hour as Europeans log in. Wait for the settle.")
        else:
            st.info("**MARKET FLOW:** Standard volume across the global hubs. Follow the Bull/Bear sentiment.")

# --- SAFETY REFRESH ---
time.sleep(refresh_rate * 60)
st.rerun()
