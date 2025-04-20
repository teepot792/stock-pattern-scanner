import streamlit as st
import requests
from bs4 import BeautifulSoup

def fetch_finviz_tickers():
    tickers = []
    base_url = "https://finviz.com/screener.ashx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

    for page_start in range(1, 201, 20):  # first 10 pages (200 tickers max)
        params = {
            "v": "111",
            "f": "cap_microunder,sh_float_u10,sh_short_o10",
            "ft": "4",
            "r": str(page_start)
        }

        try:
            res = requests.get(base_url, headers=headers, params=params, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            # Find all links that look like ticker symbols
            ticker_links = soup.select('a.screener-link-primary')
            if not ticker_links:
                break  # No more pages

            for link in ticker_links:
                ticker = link.text.strip()
                if ticker:
                    tickers.append(ticker)

        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")
            break

    return list(set(tickers))

# --- Streamlit Interface ---
st.set_page_config(page_title="Finviz Screener", layout="wide")
st.title("📈 Tickers: Micro Cap, Low Float, High Short Interest")

tickers = fetch_finviz_tickers()

if tickers:
    st.success(f"✅ Found {len(tickers)} tickers")
    for t in tickers:
        st.markdown(f"- **{t}** [🔗 Trading212](https://www.trading212.com/trading-instruments/invest/{t}.US)", unsafe_allow_html=True)
else:
    st.warning("⚠️ No tickers found. Try refreshing or check if Finviz is blocking the request.")
