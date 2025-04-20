import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Pattern Scanner", layout="wide")
st.title("Small u → Big U → Drop to Halfway Pattern Scanner")

ticker = st.text_input("Enter Ticker (e.g. GCT)", "GCT")

if ticker:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=4)

    st.write(f"Loading 5-minute data for **{ticker}**...")

    try:
        df = yf.download(ticker, start=start_date, end=end_date, interval="5m", progress=False)
        df.dropna(inplace=True)
        df.reset_index(inplace=True)

        df['Timestamp'] = pd.to_datetime(df['Datetime'])

        def detect_pattern(df):
            window_size = 80  # about 6.5 hours of 5-min candles

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
                        time_min1 = segment.iloc[min1_idx]['Timestamp']
                        time_max1 = segment.iloc[max1_idx]['Timestamp']
                        time_min2 = segment.iloc[min2_idx]['Timestamp']

                        fig = go.Figure(data=[go.Candlestick(
                            x=segment['Timestamp'],
                            open=segment['Open'],
                            high=segment['High'],
                            low=segment['Low'],
                            close=segment['Close'],
                            name='Price'
                        )])

                        fig.add_trace(go.Scatter(x=[time_min1], y=[smooth[min1_idx]], mode='markers+text',
                                                 text=["Small u start"], textposition="top center",
                                                 marker=dict(color='blue', size=10)))

                        fig.add_trace(go.Scatter(x=[time_max1], y=[smooth[max1_idx]], mode='markers+text',
                                                 text=["Big U peak"], textposition="bottom center",
                                                 marker=dict(color='orange', size=10)))

                        fig.add_trace(go.Scatter(x=[time_min2], y=[smooth[min2_idx]], mode='markers+text',
                                                 text=["Drop to halfway"], textposition="top center",
                                                 marker=dict(color='red', size=10)))

                        fig.update_layout(title=f"Pattern Detected for {ticker}",
                                          xaxis_title="Time", yaxis_title="Price",
                                          xaxis_rangeslider_visible=False)
                        return True, fig, segment.iloc[-1]['Timestamp']

            return False, None, None

        found, fig, latest_time = detect_pattern(df)

        if found:
            st.success(f"Pattern detected! Latest timestamp: **{latest_time}**")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No pattern detected in recent data.")

    except Exception as e:
        st.error(f"Error loading or processing data: {e}")
