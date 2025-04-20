import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

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

# --- CSV Upload ---
uploaded_file = st.file_uploader("📥 Upload CSV with Tickers (column: Ticker)", type=["csv"])

if uploaded_file:
    df_uploaded = pd.read_csv(uploaded_file)
    tickers = df_uploaded['Ticker'].dropna().unique().tolist()
else:
    tickers = []

if not tickers:
    st.warning("⚠️ No tickers found. Please upload a valid CSV with a 'Ticker' column.")
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
