import streamlit as st
import requests
from bs4 import BeautifulSoup

# --- Helper Function to Scrape Tickers from Finviz ---
def get_finviz_tickers():
    tickers = []
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        for page in range(0, 2):
            url = f"https://finviz.com/screener.ashx?v=111&f=cap_microunder,sh_float_u10,sh_short_o10&ft=4&r={1 + page * 20}"
            st.write(f"Scraping: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            table = soup.find("table", class_="table-light")
            if not table:
                st.warning("❌ No screener table found.")
                continue

            rows = table.find_all("tr", class_="table-dark-row") + table.find_all("tr", class_="table-light-row")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) > 1:
                    ticker = cols[1].text.strip()
                    tickers.append(ticker)

        return list(set(tickers))
    except Exception as e:
        st.error(f"Error fetching tickers from Finviz: {e}")
        return []

# --- Streamlit App ---
st.set_page_config(page_title="Finviz Screener Tickers", layout="centered")
st.title("📈 Finviz Screener Tickers with Trading212 Links")

with st.spinner("Fetching tickers from Finviz..."):
    tickers = get_finviz_tickers()

if not tickers:
    st.warning("⚠️ No tickers found. Try refreshing or check if Finviz is blocking the request.")
else:
    st.success(f"✅ Found {len(tickers)} tickers.")
    for ticker in tickers:
        t212_url = f"https://www.trading212.com/trading-instruments/invest/{ticker}.US"
        st.markdown(f"**{ticker}**: [View on Trading212]({t212_url})", unsafe_allow_html=True)
