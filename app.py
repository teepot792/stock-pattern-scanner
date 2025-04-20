
import streamlit as st
import yfinance as yf
from pattern_detector import detect_pattern
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Stock Pattern Scanner", layout="wide")

st.title("Small u → Big U → Halfway Drop Pattern Scanner")

# Load tickers from file
with open("tickers.txt", "r") as f:
    tickers = [line.strip() for line in f if line.strip()]

st.sidebar.subheader("Scanner Settings")
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2024-01-01"))

st.sidebar.subheader("Position Size Calculator")
budget = st.sidebar.number_input("Your Budget ($)", min_value=0.0, value=1000.0, step=100.0)
max_order = st.sidebar.number_input("Max Order per Trade ($)", min_value=0.0, value=500.0, step=50.0)
max_shares = st.sidebar.number_input("Max Shares per Ticker", min_value=1, value=1000, step=10)

results = []

for ticker in tickers:
    with st.spinner(f"Scanning {ticker}..."):
        matches, df = detect_pattern(ticker, start_date, end_date)
        if matches:
            results.append((ticker, matches, df))

st.subheader(f"Found {len(results)} pattern match(es)")

for ticker, matches, df in results:
    st.markdown(f"### {ticker}")
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df.index, df['Smoothed'], label="Smoothed Price")
    for i in matches:
        ax.axvspan(df.index[i], df.index[min(i+50, len(df)-1)], color="orange", alpha=0.3)
    ax.legend()
    st.pyplot(fig)

    latest_price = df['Close'].iloc[-1]
    raw_shares = int(budget // latest_price)
    order_cap_shares = int(max_order // latest_price)
    shares = min(raw_shares, order_cap_shares, max_shares)

        try:
        latest_price = float(df['Close'].iloc[-1])
    except Exception:
        st.markdown("⚠️ Could not fetch latest price for this ticker.")
        continue

    raw_shares       = int(budget    // latest_price)
    order_cap_shares = int(max_order // latest_price)
    shares           = min(raw_shares, order_cap_shares, max_shares)

    st.markdown(f"**Latest Price**: ${latest_price:.2f}")
    st.markdown(f"**You could buy up to `{shares}` shares** of `{ticker}` with these constraints:")
    st.markdown(f"- Budget: ${budget:.2f}")
    st.markdown(f"- Max per order: ${max_order:.2f}")
    st.markdown(f"- Max shares: {max_shares}")
    st.markdown(f"**You could buy up to `{shares}` shares** of `{ticker}` with these constraints:")
    st.markdown(f"- Budget: ${budget:.2f}")
    st.markdown(f"- Max per order: ${max_order:.2f}")
    st.markdown(f"- Max shares: {max_shares}")
