import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Multi-Ticker Pattern Scanner", layout="wide")
st.title("Live Finviz Scanner: Small u → Big U → Drop to Halfway")

# Get tickers from Finviz screener
@st.cache_data(ttl=3600)
def get_finviz_tickers():
    url = "https://finviz.com/screener.ashx?v=111&f=cap_microunder,sh_float_u10,sh_short_o10&ft=4"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.find("table", class_="table-light")
    tickers = []

    if table:
        for row in table.find_all("a", class_="screener-link-primary"):
            tickers.append(row.text.strip())

    return list(set(tickers))[:15]  # Limit to first 15 for speed

# Pattern detection
def detect_pattern(df):
    window_size = 80

    for i in range(len(df) - window_size):
        segment = df.iloc[i:i + window_size]
        prices = segment['Close'].values
        smooth = pd.Series(prices).rolling(window=5, center=True).mean().fillna(method='bfill').fillna(method='ffill')

        min1_idx = smooth[:15].idxmin()
        max1_idx = smooth[min1_idx:min1_idx+15].idxmax()
        min2_idx = smooth[max1_idx:max1_idx+40].idxmin()

        if min1_idx < max1_idx < min2_idx:
            small_u_range = smooth[max1_idx] - smooth[min1_idx]
            big_u_range = smooth[max1_idx] - smooth[min2_idx]
            halfway = smooth[min1_idx] + (small_u_range / 2)
            recent_price = smooth[min2_idx]

            if big_u_range > small_u_range * 1.5 and abs(recent_price - halfway) / halfway < 0.1:
                time_min1 = segment.iloc[min1_idx]['Datetime']
                time_max1 = segment.iloc[max1_idx]['Datetime']
                time_min2 = segment.iloc[min2_idx]['Datetime']

                fig = go.Figure(data=[go.Candlestick(
                    x=segment['Datetime'],
                    open=segment['Open'],
                    high=segment['High'],
                    low=segment['Low'],
                    close=segment['Close'],
                    name='Price'
                )])

                fig.add_trace(go.Scatter(x=[time_min1], y=[float(smooth[min1_idx])], mode='markers+text',
                                         text=["Small u start"], textposition="top center",
                                         marker=dict(color='blue', size=10)))

                fig.add_trace(go.Scatter(x=[time_max1], y=[float(smooth[max1_idx])], mode='markers+text',
                                         text=["Big U peak"], textposition="bottom center",
                                         marker=dict(color='orange', size=10)))

                fig.add_trace(go.Scatter(x=[time_min2], y=[float(smooth[min2_idx])], mode='markers+text',
                                         text=["Drop to halfway"], textposition="top center",
                                         marker=dict(color='red', size=10)))

                fig.update_layout(title=f"Pattern Detected",
                                  xaxis_title="Time", yaxis_title="Price",
                                  xaxis_rangeslider_visible=False)

                return True, fig, segment.iloc[-1]['Datetime']

    return False, None, None

# Main logic
tickers = get_finviz_tickers()
st.subheader(f"Scanning {len(tickers)} tickers from Finviz...")

end_date = datetime.now()
start_date = end_date - timedelta(days=4)

matched = 0

for ticker in tickers:
    try:
        st.write(f"Checking {ticker}...")
        df = yf.download(ticker, start=start_date, end=end_date, interval="5m", progress=False)
        df.dropna(inplace=True)
        df.reset_index(inplace=True)

        found, fig, latest_time = detect_pattern(df)

        if found:
            st.success(f"**{ticker}** matched! Latest point: {latest_time}")
            st.plotly_chart(fig, use_container_width=True)
            matched += 1
        else:
            st.write(f"{ticker}: No pattern")

        time.sleep(1)  # small pause to avoid rate limits

    except Exception as e:
        st.error(f"Error checking {ticker}: {e}")

if matched == 0:
    st.warning("No matching patterns found.")
