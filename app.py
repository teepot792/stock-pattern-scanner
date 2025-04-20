import yfinance as yf
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Low-Float Momentum Scanner", layout="wide")

st.title("📈 Low-Float Momentum Scanner")
st.caption("Detects fast-moving, low-float, low-market-cap stocks in real time.")

# Input tickers
tickers_input = st.text_input("Enter tickers (comma-separated):", "HOLO,GNS,ILAG,HUDI,TOP,MEGL,SNTG")
tickers = [t.strip().upper() for t in tickers_input.split(",")]

def get_momentum_stocks(ticker_list):
    results = []

    for ticker in ticker_list:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d", interval="5m")

            if len(hist) < 2:
                continue

            # Calculate momentum
            last_close = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2]
            percent_change = ((last_close - prev_close) / prev_close) * 100

            # Apply filters
            if percent_change > 5:
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
        except Exception as e:
            st.warning(f"Error loading {ticker}: {e}")

    return pd.DataFrame(results)

# Run scanner
if st.button("🚀 Run Scanner"):
    data = get_momentum_stocks(tickers)

    if not data.empty:
        data["Trading212 Link"] = data["Trading212 Link"].apply(lambda x: f"[Link]({x})")
        st.dataframe(data.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info("No momentum stocks found right now.")
