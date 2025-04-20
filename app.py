import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime

# --- Selenium Scraper for Finviz ---
def get_finviz_tickers_selenium(pages=1):
    tickers = []
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        for page in range(pages):
            start_row = 1 + page * 20
            url = f"https://finviz.com/screener.ashx?v=111&f=cap_microunder,sh_float_u10,sh_short_o10&ft=4&r={start_row}"
            driver.get(url)
            time.sleep(2)

            rows = driver.find_elements(By.CSS_SELECTOR, "table.table-light tr[valign='top']")

            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) > 1:
                        ticker = cells[1].text.strip()
                        tickers.append(ticker)
                except Exception as e:
                    print(f"Error parsing row: {e}")

    finally:
        driver.quit()

    return list(set(tickers))

# --- Pattern Detection Logic ---
def detect_u_pattern(df):
    pattern_points = []
    for i in range(30, len(df) - 10):
        window = df.iloc[i - 30:i + 10]
        min1 = window['Low'].iloc[:10].idxmin()
        max1 = window['High'].iloc[10:20].idxmax()
        min2 = window['Low'].iloc[20:30].idxmin()
        last_price = window['Close'].iloc[-1]

        if (min1 < max1 < min2 and
            window['Low'].loc[min1] < window['Low'].loc[min2] and
            last_price <= (window['Low'].loc[min1] + window['Low'].loc[min2]) / 2 and
            last_price >= window['Low'].loc[min1]):
            pattern_points.append((min1, max1, min2, i + 9))
    return pattern_points

# --- Candlestick Plot ---
def plot_candlestick(df, ticker, pattern_points):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=ticker
    ))
    for p in pattern_points:
        min1, max1, min2, latest = p
        fig.add_trace(go.Scatter(x=[df.index[min1]], y=[df['Low'][min1]],
                                 mode='markers', marker=dict(color='green', size=10), name='Small U'))
        fig.add_trace(go.Scatter(x=[df.index[max1]], y=[df['High'][max1]],
                                 mode='markers', marker=dict(color='orange', size=10), name='Big ∩'))
        fig.add_trace(go.Scatter(x=[df.index[min2]], y=[df['Low'][min2]],
                                 mode='markers', marker=dict(color='red', size=10), name='Retest'))
    fig.update_layout(title=f"{ticker} Pattern Detection", xaxis_title="Time", yaxis_title="Price")
    return fig

# --- Streamlit App ---
st.set_page_config(page_title="Stock Pattern Scanner", layout="wide")
st.title("📉 Stock Pattern Scanner (U → ∩ → Drop)")

with st.spinner("Fetching tickers from Finviz using Selenium..."):
    tickers = get_finviz_tickers_selenium(pages=2)

if not tickers:
    st.warning("⚠️ No tickers found. Try refreshing or check if Finviz is blocking the request.")
else:
    for ticker in tickers:
        try:
            df = yf.download(ticker, interval="5m", period="1d", progress=False)
            if df.empty:
                st.warning(f"No data for {ticker}")
                continue

            df.dropna(inplace=True)
            pattern_points = detect_u_pattern(df)

            if pattern_points:
                latest_pattern_date = df.index[pattern_points[-1][-1]].strftime("%Y-%m-%d %H:%M")
                st.subheader(f"✅ Pattern Found for {ticker}")
                st.write(f"🕒 Latest Pattern Date: {latest_pattern_date}")
                st.markdown(f"[🔗 View {ticker} on Trading212](https://www.trading212.com/trading-instruments/invest/{ticker}.US)", unsafe_allow_html=True)
                fig = plot_candlestick(df, ticker, pattern_points)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No pattern found for {ticker}")

        except Exception as e:
            st.error(f"Error processing {ticker}: {e}")
