import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import requests
import random
from datetime import datetime

# --- Free Proxy Support ---
def get_free_proxy():
    proxy_url = "https://free-proxy-list.net/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(proxy_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table", id="proxylisttable")
        proxies = []
        for row in table.tbody.find_all("tr"):
            cols = row.find_all("td")
            if cols[6].text == "yes":  # HTTPS support
                ip = cols[0].text
                port = cols[1].text
                proxies.append(f"http://{ip}:{port}")
        return random.choice(proxies) if proxies else None
    except Exception as e:
        print(f"Failed to get proxy list: {e}")
        return None

# --- Helper Function to Scrape Tickers from Finviz ---
def get_finviz_tickers():
    tickers = []
    headers = {"User-Agent": "Mozilla/5.0"}
    proxy = get_free_proxy()
    proxies = {"http": proxy, "https": proxy} if proxy else None

    try:
        for page in range(0, 2):
            url = f"https://finviz.com/screener.ashx?v=111&f=cap_microunder,sh_float_u10,sh_short_o10&ft=4&r={1 + page * 20}"
            st.text(f"Scraping: {url}")  # Debug

            response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            # Find the screener table
            table = soup.find("table", class_="table-light")
            if not table:
                st.text("❌ No screener table found.")
                continue

            rows = table.find_all("tr")[1:]  # Skip header
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    ticker = cols[1].text.strip()
                    if ticker.isalpha():
                        tickers.append(ticker)

        tickers = list(set(tickers))  # De-duplicate
        st.text(f"✅ Final ticker list: {tickers}")
        return tickers

    except Exception as e:
        st.error(f"Error fetching tickers from Finviz: {e}")
        return []

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

with st.spinner("Fetching tickers from Finviz..."):
    tickers = get_finviz_tickers()

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
