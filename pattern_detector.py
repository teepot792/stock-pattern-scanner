import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests

# --- Streamlit config
st.set_page_config(page_title="Low-Float Momentum Scanner", layout="wide")
st.title("📈 Low-Float Momentum Scanner")
st.caption("Detects fast-moving, low-float, low-market-cap stocks in real time.")

# --- Auto-refresh every 24 hours
REFRESH_INTERVAL_HOURS = 24
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = datetime.now()

if datetime.now() - st.session_state["last_refresh"] > timedelta(hours=REFRESH_INTERVAL_HOURS):
    st.session_state["last_refresh"] = datetime.now()
    st.experimental_rerun()

st.caption(f"Last scanned: {st.session_state['last_refresh'].strftime('%Y-%m-%d %H:%M:%S')}")

# --- Discord Alert
def send_discord_alert(message, webhook_url):
    payload = { "content": message }
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code != 204:
            st.warning(f"⚠️ Discord webhook failed: {response.text}")
    except Exception as e:
        st.error(f"⚠️ Discord error: {e}")

# --- Input tickers
tickers_input = st.text_input("Enter tickers (comma-separated):", "HOLO,GNS,ILAG,HUDI,TOP,MEGL,SNTG")
tickers = [t.strip().upper() for t in tickers_input.split(",")]

# --- Main scanning function
def get_momentum_stocks(ticker_list):
    results = []
    for ticker in ticker_list:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d", interval="5m")

            if len(hist) < 2:
                continue

            last_close = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2]
            percent_change = ((last_close - prev_close) / prev_close) * 100

            if percent_change > 5:  # 🔼 momentum threshold
                info = stock.info
                market_cap = info.get("marketCap", 0)
                float_shares = info.get("floatShares", 0)
                shares_outstanding = info.get("sharesOutstanding", 0)

                if market_cap and market_cap < 20_000_000 and float_shares and float_shares < 10_000_000:
                    trading212_url = f"https://www.trading212.com/en/invest/instruments/{ticker}"
                    results.append({
                        "Ticker": ticker,
                        "Price": round(last_close, 4),
                        "% Change (5m)": round(percent_change, 2),
                        "Market Cap": market_cap,
                        "Float": float_shares,
                        "Outstanding": shares_outstanding,
                        "Trading212 Link": trading212_url
                    })

                    # Discord alert
                    if "webhook_sent" not in st.session_state:
                        st.session_state["webhook_sent"] = set()
                    alert_key = f"{ticker}-{datetime.now().date()}"
                    if alert_key not in st.session_state["webhook_sent"]:
                        if "discord_webhook" in st.secrets:
                            discord_message = (
                                f"🚨 **Momentum Alert: {ticker}**\n"
                                f"Price: ${round(last_close, 4)}\n"
                                f"Change: {round(percent_change, 2)}%\n"
                                f"[View on Trading212]({trading212_url})"
                            )
                            send_discord_alert(discord_message, st.secrets["discord_webhook"])
                            st.session_state["webhook_sent"].add(alert_key)

        except Exception as e:
            st.warning(f"Error with {ticker}: {e}")

    return pd.DataFrame(results)

# --- Run scanner
data = get_momentum_stocks(tickers)

# --- Show results if any
if not data.empty:
    data["Trading212 Link"] = data["Trading212 Link"].apply(lambda x: f"[Link]({x})")
    st.dataframe(data.to_html(escape=False, index=False), unsafe_allow_html=True)

    selected_ticker = st.selectbox("📊 Select a flagged ticker to view intraday chart", data["Ticker"].tolist())

    chart_interval = st.selectbox("Chart Interval", ["5m", "15m", "30m", "1h"], index=2)
    interval_period_map = {
        "5m": "7d",
        "15m": "30d",
        "30m": "30d",
        "1h": "60d"
    }
    chart_period = interval_period_map.get(chart_interval, "7d")

    if selected_ticker:
        st.subheader(f"📈 {selected_ticker} - {chart_interval} Candlestick Chart")
        chart_data = yf.download(selected_ticker, period=chart_period, interval=chart_interval)

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=chart_data.index,
            open=chart_data['Open'],
            high=chart_data['High'],
            low=chart_data['Low'],
            close=chart_data['Close'],
            name="Candles"
        ))
        fig.update_layout(
            title=f"{selected_ticker} - {chart_interval} Chart",
            xaxis_title="Time",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No momentum stocks found right now.")

# --- Always-available chart viewer
st.markdown("---")
st.subheader("📊 View Any Ticker Chart")

custom_ticker = st.text_input("Enter any ticker to view chart:", value="HOLO").upper()
custom_interval = st.selectbox("Custom Interval", ["5m", "15m", "30m", "1h"], index=2)
custom_period = interval_period_map.get(custom_interval, "7d")

if custom_ticker:
    chart_data = yf.download(custom_ticker, period=custom_period, interval=custom_interval)
    if not chart_data.empty:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=chart_data.index,
            open=chart_data['Open'],
            high=chart_data['High'],
            low=chart_data['Low'],
            close=chart_data['Close'],
            name="Candles"
        ))
        fig.update_layout(
            title=f"{custom_ticker} - {custom_interval} Chart",
            xaxis_title="Time",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No chart data available.")
