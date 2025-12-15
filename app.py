import streamlit as st
import requests
import pandas as pd
import numpy as np

# ======================================================
# CONFIG
# ======================================================

st.set_page_config(
    page_title="Stock Valuation Dashboard (FMP)",
    layout="wide"
)

FMP_API_KEY = "DfUOLHcLmUGAtmeKu4UFVnvQhk3AWMMp"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# ======================================================
# API FUNCTIONS
# ======================================================

def get_profile(symbol):
    url = f"{BASE_URL}/profile/{symbol}?apikey={FMP_API_KEY}"
    r = requests.get(url)
    data = r.json()
    return data[0] if data else None


def get_income_statement(symbol):
    url = f"{BASE_URL}/income-statement/{symbol}?limit=5&apikey={FMP_API_KEY}"
    r = requests.get(url)
    return r.json()


def get_cashflow(symbol):
    url = f"{BASE_URL}/cash-flow-statement/{symbol}?limit=5&apikey={FMP_API_KEY}"
    r = requests.get(url)
    return r.json()


def get_ratios(symbol):
    url = f"{BASE_URL}/ratios-ttm/{symbol}?apikey={FMP_API_KEY}"
    r = requests.get(url)
    data = r.json()
    return data[0] if data else None


# ======================================================
# UI
# ======================================================

st.title("📊 Stock Valuation Dashboard")
st.caption("Powered by Financial Modeling Prep (FMP) API")

st.info("Use `.NS` for Indian stocks (e.g., RELIANCE.NS, TCS.NS)")

symbol = st.text_input(
    "Enter Stock Symbol",
    value="RELIANCE.NS"
).upper()

# User assumptions
st.markdown("### 🔧 Valuation Assumptions")

col1, col2, col3 = st.columns(3)

with col1:
    growth_rate = st.number_input(
        "Expected Growth Rate (%)",
        value=10.0
    )

with col2:
    discount_rate = st.number_input(
        "Discount Rate (%)",
        value=12.0
    )

with col3:
    industry_pe = st.number_input(
        "Assumed Industry PE",
        value=20.0
    )

# ======================================================
# FETCH DATA
# ======================================================

if st.button("🚀 Run Valuation", use_container_width=True):

    with st.spinner("Fetching data..."):

        profile = get_profile(symbol)
        income = get_income_statement(symbol)
        cashflow = get_cashflow(symbol)
        ratios = get_ratios(symbol)

    if not profile:
        st.error("Invalid symbol or API limit exceeded")
        st.stop()

    # ==================================================
    # BASIC DATA
    # ==================================================

    price = float(profile["price"])
    market_cap = profile.get("mktCap", 0)
    company = profile["companyName"]
    sector = profile.get("sector", "N/A")

    eps = float(ratios["epsTTM"]) if ratios and ratios.get("epsTTM") else 0
    pe = float(ratios["peRatioTTM"]) if ratios and ratios.get("peRatioTTM") else 0
    roe = float(ratios["roeTTM"]) * 100 if ratios and ratios.get("roeTTM") else 0

    # ==================================================
    # PE VALUATION
    # ==================================================

    fair_value_pe = eps * industry_pe
    mos_pe = ((fair_value_pe - price) / price) * 100 if price > 0 else 0

    # ==================================================
    # DCF VALUATION (EPS BASED)
    # ==================================================

    projected_eps = eps
    discounted_cashflows = []

    for year in range(1, 6):
        projected_eps *= (1 + growth_rate / 100)
        discounted = projected_eps / ((1 + discount_rate / 100) ** year)
        discounted_cashflows.append(discounted)

    dcf_value = sum(discounted_cashflows)
    mos_dcf = ((dcf_value - price) / price) * 100 if price > 0 else 0

    # ==================================================
    # DISPLAY METRICS
    # ==================================================

    st.markdown("---")
    st.subheader(f"🏢 {company}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Live Price", f"₹ {price:,.2f}")
    c2.metric("EPS (TTM)", f"{eps:.2f}")
    c3.metric("PE (TTM)", f"{pe:.2f}")
    c4.metric("ROE", f"{roe:.2f}%")

    st.markdown("---")
    st.subheader("📈 Valuation Results")

    v1, v2, v3, v4 = st.columns(4)
    v1.metric("PE Fair Value", f"₹ {fair_value_pe:,.2f}")
    v2.metric("DCF Value (5Y)", f"₹ {dcf_value:,.2f}")
    v3.metric("MOS (PE)", f"{mos_pe:.2f}%")
    v4.metric("MOS (DCF)", f"{mos_dcf:.2f}%")

    # ==================================================
    # VALUATION SIGNAL
    # ==================================================

    st.markdown("---")

    avg_mos = (mos_pe + mos_dcf) / 2

    if avg_mos > 30:
        st.success("🟢 STRONGLY UNDERVALUED")
    elif avg_mos > 10:
        st.info("🟡 MODERATELY UNDERVALUED")
    elif avg_mos > -10:
        st.warning("⚖️ FAIRLY VALUED")
    else:
        st.error("🔴 OVERVALUED")

    # ==================================================
    # FINANCIAL SUMMARY TABLE
    # ==================================================

    if income and isinstance(income, list):
        st.markdown("---")
        st.subheader("📋 Financial Summary (Last 5 Years)")

        df_income = pd.DataFrame(income)[
            ["calendarYear", "revenue", "netIncome"]
        ].rename(columns={
            "calendarYear": "Year",
            "revenue": "Revenue",
            "netIncome": "Net Income"
        })

        st.dataframe(df_income, use_container_width=True)

    st.caption("Data Source: Financial Modeling Prep (FMP)")
