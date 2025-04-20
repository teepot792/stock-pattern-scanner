import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Finviz Ticker Scanner", layout="wide")
st.title("📈 Finviz Screener + Chart Viewer")

uploaded_file = st.file_uploader("📥 Upload Finviz Exported CSV", type="csv")

def plot_candlestick(df, ticker):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=ticker
    ))
    fig.update_layout(title=f"{ticker} - 5min Candlestick", xaxis_title="Time", yaxis_title="Price")
    return fig

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if 'Ticker' in df.columns:
        tickers = df['Ticker'].dropna().unique()
        st.success(f"✅ Found {len(tickers)} tickers")

        for ticker in tickers:
            st.subheader(f"📊 {ticker}")
            try:
                stock_data = yf.download(ticker, interval="5m", period="1d", progress=False)
                if stock_data.empty:
                    st.warning(f"No data available for {ticker}")
                    continue

                fig = plot_candlestick(stock_data, ticker)
                st.plotly_chart(fig, use_container_width=True)

                st.markdown(f"[🔗 View on Trading212](https://www.trading212.com/trading-instruments/invest/{ticker}.US)", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error loading data for {ticker}: {e}")
    else:
        st.error("❌ 'Ticker' column not found in CSV.")
else:
    st.info("Upload a CSV file exported from Finviz to begin.")
