import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# ======================================================
# DHAN CONFIG
# ======================================================

DHAN_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY1ODY4MjUwLCJhcHBfaWQiOiJjOTNkM2UwOSIsImlhdCI6MTc2NTc4MTg1MCwidG9rZW5Db25zdW1lclR5cGUiOiJBUFAiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDQ4MDM1NCJ9.PN4ersyCLxbgtjtsaoBiyOvE9Oj-bxZ5F06xlgMuOdIcmRzFoUjZYAcS7C_FLf4Ggb5JTeUXkcsWC27ZY58yBA"

BASE_URL = "https://api.dhan.co"

HEADERS = {
    "access-token": DHAN_ACCESS_TOKEN,
    "Content-Type": "application/json"
}

# ======================================================
# STOCK DATABASE (NSE SECURITY IDS)
# ======================================================

STOCK_DB = {
    "RELIANCE": "2885",
    "TCS": "11536",
    "INFY": "1594",
    "HDFCBANK": "1333",
    "ICICIBANK": "4963",
    "SBIN": "3045",
    "ITC": "1660",
    "LT": "11483",
    "AXISBANK": "5900",
    "MARUTI": "10999"
}

# ======================================================
# DHAN LTP (OFFICIAL & WORKING)
# ======================================================

def dhan_ltp(security_id: str) -> float:
    url = f"{BASE_URL}/v2/marketdata/ltp"

    payload = {
        "securities": {
            "NSE_EQ": [security_id]
        }
    }

    r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
    r.raise_for_status()

    return float(
        r.json()["data"]["NSE_EQ"][security_id]["ltp"]
    )

# ======================================================
# STREAMLIT UI
# ======================================================

st.set_page_config(
    page_title="NYZTrade – Stock Valuation Dashboard",
    layout="wide"
)

st.title("📊 NYZTrade – Stock Valuation Dashboard")
st.caption("Live price from Dhan API • Fundamental valuation")

# ======================================================
# SIDEBAR
# ======================================================

st.sidebar.header("⚙️ Controls")

stock = st.sidebar.selectbox("Select Stock", list(STOCK_DB.keys()))
security_id = STOCK_DB[stock]

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Fundamental Inputs")

eps = st.sidebar.number_input("EPS (TTM)", value=33.0, step=1.0)
growth_rate = st.sidebar.number_input("Expected Growth (%)", value=10.5, step=0.5)
discount_rate = st.sidebar.number_input("Discount Rate (%)", value=8.0, step=0.5)
industry_pe = st.sidebar.number_input("Industry PE", value=16.0, step=1.0)

# ======================================================
# FETCH LIVE PRICE
# ======================================================

try:
    price = dhan_ltp(security_id)
except Exception as e:
    st.error("❌ Failed to fetch live price from Dhan API")
    st.code(e)
    st.stop()

# ======================================================
# VALUATION
# ======================================================

fair_value_pe = eps * industry_pe
mos_pe = (fair_value_pe - price) / price * 100

cashflows = []
current_eps = eps

for year in range(1, 6):
    current_eps *= (1 + growth_rate / 100)
    discounted = current_eps / ((1 + discount_rate / 100) ** year)
    cashflows.append(discounted)

dcf_value = sum(cashflows)
mos_dcf = (dcf_value - price) / price * 100

# ======================================================
# METRICS
# ======================================================

st.subheader(f"📌 {stock} – Valuation Snapshot")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Live Price", f"₹ {price:,.2f}")
c2.metric("Fair Value (PE)", f"₹ {fair_value_pe:,.2f}")
c3.metric("MOS (PE)", f"{mos_pe:.2f}%")
c4.metric("DCF Value", f"₹ {dcf_value:,.2f}")
c5.metric("MOS (DCF)", f"{mos_dcf:.2f}%")

# ======================================================
# VERDICT
# ======================================================

st.markdown("---")
if mos_pe > 30 and mos_dcf > 30:
    st.success("🟢 Strongly Undervalued")
elif mos_pe > 10 or mos_dcf > 10:
    st.info("🟡 Moderately Undervalued")
elif mos_pe < -10 and mos_dcf < -10:
    st.error("🔴 Overvalued")
else:
    st.warning("⚖️ Fairly Valued")

# ======================================================
# CHART
# ======================================================

fig = go.Figure()
fig.add_bar(name="Live Price", x=["Price"], y=[price])
fig.add_bar(name="PE Fair Value", x=["PE"], y=[fair_value_pe])
fig.add_bar(name="DCF Value", x=["DCF"], y=[dcf_value])

fig.update_layout(barmode="group", template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# ======================================================
# FOOTER
# ======================================================

st.markdown("---")
st.caption("⚠️ Educational purpose only. Not investment advice.")
