import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import time

# --- 1. SETUP ---
st.set_page_config(page_title="ELVIS VISUAL PRO", layout="wide", page_icon="🚀")

st.sidebar.header("🕹️ Institutional Logic")
SYMBOLS = st.sidebar.multiselect("Assets", ["SOL-USD", "BTC-USD", "ETH-USD", "XRP-USD"], default=["SOL-USD", "BTC-USD"])
vol_thresh = st.sidebar.slider("Volume Spike (Institutional)", 1.0, 3.0, 1.5) # Dialed back to 1.5 to find more zones
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
        return df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
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

st.title("🔥 ELVIS INSTITUTIONAL MAP")
st.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S')} | Refreshing every {refresh_rate}m")

if st.button("🔄 Force Refresh Now"):
    st.rerun()

cols = st.columns(len(SYMBOLS) if len(SYMBOLS) > 0 else 1)

for i, sym in enumerate(SYMBOLS):
    with cols[i]:
        df = get_data(sym)
        if df.empty: continue
        
        # --- BIG BULL/BEAR % CALCULATION ---
        last_24h = df.tail(24)
        bull_vol = last_24h['Volume'][last_24h['Close'] > last_24h['Open']].sum()
        bear_vol = last_24h['Volume'][last_24h['Close'] < last_24h['Open']].sum()
        total_v = bull_vol + bear_vol
        bull_p = (bull_vol / total_v * 100) if total_v > 0 else 50
        bear_p = 100 - bull_p
        
        price = df["Close"].iloc[-1]
        all_structs = find_structure(df)
        fresh_zones = [s for s in all_structs if is_fresh(df, s)]
        best_zone = fresh_zones[-1] if fresh_zones else None
        
        with st.container(border=True):
            st.header(f"{sym} : ${price:,.2f}")
            
            # --- BIG BULL/BEAR DISPLAY ---
            m1, m2 = st.columns(2)
            m1.metric("🐂 BULL %", f"{bull_p:.1f}%")
            m2.metric("🐻 BEAR %", f"{bear_p:.1f}%")

            # 🕯️ CHART
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                name=sym, increasing_line_color='#00ff00', decreasing_line_color='#ff0000'
            )])
            
            if best_zone:
                z_color = "rgba(0, 255, 0, 0.4)" if best_zone['type'] == "DEMAND" else "rgba(255, 0, 0, 0.4)"
                fig.add_shape(type="rect", x0=best_zone['time'], y0=best_zone['low'], x1=df.index[-1], y1=best_zone['high'], fillcolor=z_color, line_width=0)
            
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # --- ALWAYS-ON EXPLANATION BOX ---
            trend = "BULLISH" if bull_p > 50 else "BEARISH"
            note_color = "success" if trend == "BULLISH" else "error"
            
            st.info(f"📝 **ELVIS SNIPER NOTE:** Market is **{trend}**. Whales are moving {bull_p:.1f}% volume to the upside. Scanning for big entries.")
            
            if best_zone:
                st.success(f"🎯 **TARGET {best_zone['type']} ZONE:** ${best_zone['low']:.2f} - ${best_zone['high']:.2f}")
            else:
                st.warning(f"⚠️ No massive fresh zones at {vol_thresh} spike. Lower the slider to see minor bank levels.")

# --- SAFETY REFRESH ---
time.sleep(refresh_rate * 60)
st.rerun()