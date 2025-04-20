import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Pattern Detection Logic ---
def detect_u_pattern(df):
    pattern_points = []

    for i in range(30, len(df) - 10):
        window = df.iloc[i - 30:i + 10]

        min1_idx = window['Low'].iloc[:10].idxmin()
        max1_idx = window['High'].iloc[10:20].idxmax()
        min2_idx = window['Low'].iloc[20:30].idxmin()
        latest_idx = window.index[-1]

        try:
            min1_price = window.loc[min1_idx, 'Low']
            max1_price = window.loc[max1_idx, 'High']
            min2_price = window.loc[min2_idx, 'Low']
            last_price = window.iloc[-1]['Close']
        except:
            continue

        midpoint = (min1_price + min2_price) / 2

        if (min1_idx < max1_idx < min2_idx and
            min1_price < min2_price and
            midpoint <= last_price <= min2_price):
            pattern_points.append((df.index.get_loc(min1_idx),
                                   df.index.get_loc(max1_idx),
                                   df.index.get_loc(min2_idx),
                                   df.index.get_loc(latest_idx)))
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

tickers = st.text_input("Enter tickers (comma-separated)", "NVDA,AMD,SOUN").upper().split(",")

for ticker in tickers:
    ticker = ticker.strip()
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
