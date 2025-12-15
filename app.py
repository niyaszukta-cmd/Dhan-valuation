import streamlit as st
import requests
import pandas as pd
import numpy as np

# ======================================================
# CONFIG
# ======================================================

st.set_page_config(
    page_title="Stock Valuation Dashboard",
    layout="wide"
)

FMP_API_KEY = "DfUOLHcLmUGAtmeKu4UFVnvQhk3AWMMp"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# ======================================================
# SAFE API HELPERS
# ======================================================

def safe_get(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_profile(symbol):
    url = f"{BASE_URL}/profile/{symbol}?apikey={FMP_API_KEY}"
    data = safe_get(url)

    if not data or not isinstance(data, list) or len(data) == 0:
        return None

    return data[0]


def get_ratios(symbol):
    url = f"{BASE_URL}/ratios-ttm/{symbol}?apikey={FMP_API_KEY}"
    data = safe_get(url)

    if not data or not isinstance(data, list) or len(data) == 0:
        return None

    return data[0]


def get_income(symbol):
    url = f"{BASE_URL}/income-statement/{symbol}?limit=5&apikey={FMP_API_KEY}"
    data = safe_get(url)

    if not data or not isinstance(data, list):
        return []

    return data


# ======================================================
# UI
# ======================================================

st.title("📊 Stock Valuation Dashboard")
st.caption("Powered by Financial Modeling Prep (FMP API)")

st.info("Use `.NS` for Indian stocks (RELIANCE.NS, TCS.NS, INFY.NS)")

symbol = st.text_input(
    "Enter Stock Symbol",
    value="RELIANCE.NS"
).upper()

# Assumptions
st.markdown("### 🔧 Valuation Assumptions")

c1, c2, c3 = st.columns(3)

with c1:
    growth_rate = st.number_input("Expected Growth (%)", 0.0, 50.0, 10.0)

with c2:
    discount_rate = st.number_input("Discount Rate (%)", 0.0, 30.0, 12.0)

with c3:
    industry_pe = st.number_input("Assumed Industry PE", 1.0, 100.0, 20.0)

# ======================================================
# RUN VALUATION
# ======================================================

if st.button("🚀 Run Valuation", use_container_width=True):

    with st.spinner("Fetching data from FMP..."):

        profile = get_profile(symbol)
        ratios = get_ratios(symbol)
        income = get_income(symbol)

    # ---------------- ERROR HANDLING ----------------

    if profile is None:
        st.error(
            "❌ Failed to fetch company profile.\n\n"
            "Possible reasons:\n"
            "- API key invalid\n"
            "- Free tier limit exceeded\n"
            "- Symbol not supported by FMP\n\n"
            "Try again after some time or test with TCS.NS / INFY.NS"
        )
        st.stop()

    if ratios is None:
        st.warning("⚠️ Ratio data unavailable — valuation may be approximate")

    # ======================================================
    # DATA EXTRACTION (SAFE)
    # ======================================================

    price = float(profile.get("price", 0))
    company = profile.get("companyName", symbol)
    sector = profile.get("sector", "N/A")

    eps = float(ratios.get("epsTTM", 0)) if ratios else 0
    pe = float(ratios.get("peRatioTTM", 0)) if ratios else 0
    roe = float(ratios.get("roeTTM", 0)) * 100 if ratios else 0

    # ======================================================
    # VALUATION CALCULATIONS
    # ======================================================

    fair_value_pe = eps * industry_pe if eps > 0 else 0
    mos_pe = ((fair_value_pe - price) / price) * 100 if price > 0 else 0

    projected_eps = eps
    dcf_cashflows = []

    for year in range(1, 6):
        projected_eps *= (1 + growth_rate / 100)
        discounted = projected_eps / ((1 + discount_rate / 100) ** year)
        dcf_cashflows.append(discounted)

    dcf_value = sum(dcf_cashflows)
    mos_dcf = ((dcf_value - price) / price) * 100 if price > 0 else 0

    # ======================================================
    # DISPLAY
    # ======================================================

    st.markdown("---")
    st.subheader(f"🏢 {company}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Live Price", f"₹ {price:,.2f}")
    m2.metric("EPS (TTM)", f"{eps:.2f}")
    m3.metric("PE (TTM)", f"{pe:.2f}")
    m4.metric("ROE", f"{roe:.2f}%")

    st.markdown("---")
    st.subheader("📈 Valuation Results")

    v1, v2, v3, v4 = st.columns(4)
    v1.metric("PE Fair Value", f"₹ {fair_value_pe:,.2f}")
    v2.metric("DCF Value (5Y)", f"₹ {dcf_value:,.2f}")
    v3.metric("MOS (PE)", f"{mos_pe:.2f}%")
    v4.metric("MOS (DCF)", f"{mos_dcf:.2f}%")

    avg_mos = (mos_pe + mos_dcf) / 2

    st.markdown("---")

    if avg_mos > 30:
        st.success("🟢 STRONGLY UNDERVALUED")
    elif avg_mos > 10:
        st.info("🟡 MODERATELY UNDERVALUED")
    elif avg_mos > -10:
        st.warning("⚖️ FAIRLY VALUED")
    else:
        st.error("🔴 OVERVALUED")

    # ======================================================
    # FINANCIAL TABLE
    # ======================================================

    if income:
        st.markdown("---")
        st.subheader("📋 Income Statement (Last 5 Years)")

        df = pd.DataFrame(income)[
            ["calendarYear", "revenue", "netIncome"]
        ].rename(columns={
            "calendarYear": "Year",
            "revenue": "Revenue",
            "netIncome": "Net Income"
        })

        st.dataframe(df, use_container_width=True)

    st.caption("Data Source: Financial Modeling Prep (FMP)")
