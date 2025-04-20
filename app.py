import streamlit as st
import requests
from bs4 import BeautifulSoup

def fetch_finviz_tickers():
    url = "https://finviz.com/screener.ashx?v=111&f=cap_microunder,sh_float_u10,sh_short_o10&ft=4"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all <a> tags inside screener table area with link format to quote
        ticker_links = soup.select('a.screener-link')

        tickers = []
        for link in ticker_links:
            href = link.get('href')
            if href and href.startswith("quote.ashx?t="):
                ticker = link.text.strip()
                if ticker.isalpha() and ticker not in tickers:
                    tickers.append(ticker)

        if not tickers:
            raise ValueError("No tickers extracted. Page structure may have changed.")

        return tickers

    except Exception as e:
        st.error(f"Error fetching tickers from Finviz: {e}")
        return []

# --- Streamlit UI ---
st.set_page_config(page_title="Low Float Screener", layout="wide")
st.title("📉 Finviz Screener - Low Float + High Short Stocks")
st.caption("Filtering: Market Cap < $20M, Float < 10M, Short % > 10%")

tickers = fetch_finviz_tickers()

if tickers:
    st.success(f"✅ Found {len(tickers)} tickers:")
    for ticker in tickers:
        st.markdown(f"- **{ticker}** [🔗 Trading212](https://www.trading212.com/trading-instruments/invest/{ticker}.US)", unsafe_allow_html=True)
else:
    st.warning("No tickers found.")
