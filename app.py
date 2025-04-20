import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup

# --- Function to Fetch Tickers from Finviz ---
def fetch_finviz_tickers():
    url = "https://finviz.com/screener.ashx?v=111&f=cap_microunder,sh_float_u10,sh_short_o10&ft=4"
    headers = {'User-Agent': 'Mozilla/5.0'}
    tickers = []

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='table-light')
        if table:
            rows = table.find_all('tr')[1:]  # Skip header row
            for row in rows:
                cols = row.find_all('td')
                if cols:
                    ticker = cols[1].text.strip()
                    tickers.append(ticker)
    except Exception as e:
        st.error(f"Error fetching tickers from Finviz: {e}")

    return tickers

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

# --- App Layout ---
st.set_page_config(page_title="Stock Pattern Scanner", layout="wide")
st.title("📉 Stock Pattern Scanner (U → ∩ → Drop)")

tickers = fetch_finviz_tickers()
if not tickers:
    st.warning("No tickers fetched from Finviz.")
else:
    st.write(f"Fetched {len(tickers)} tickers from Finviz.")

    for ticker in tickers:
        ticker = ticker.strip()
        try:
            info = yf.Ticker(ticker).info
            market_cap = info.get("marketCap", None)

            if market_cap is None:
                st.warning(f"⚠️ No market cap data for {ticker}, skipping.")
                continue

            if market_cap > 20_000_000:
                st.info(f"⛔ Skipping {ticker}: Market cap is too high (${market_cap:,})")
                continue

            df = yf.download(ticker, interval="5m", period="5d", progress=False)
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
