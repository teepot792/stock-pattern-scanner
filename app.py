import streamlit as st
import requests
from bs4 import BeautifulSoup

# --- Function to fetch tickers from Finviz ---
def fetch_finviz_tickers():
    url = "https://finviz.com/screener.ashx?v=111&f=cap_microunder,sh_float_u10,sh_short_o10&ft=4"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    tickers = []

    try:
        table = soup.find_all("table", class_="table-light")[0]
        rows = table.find_all("tr")[1:]  # skip header

        for row in rows:
            cells = row.find_all("td")
            if len(cells) > 1:
                ticker = cells[1].text.strip()
                tickers.append(ticker)
    except Exception as e:
        st.error(f"Error fetching tickers from Finviz: {e}")

    return tickers


# --- Streamlit App UI ---
st.set_page_config(page_title="Low Float Stock List", layout="wide")
st.title("📈 Low Market Cap, Low Float, High Short Interest Stocks")
st.caption("Pulled live from Finviz screener")

tickers = fetch_finviz_tickers()

if tickers:
    st.success(f"✅ Found {len(tickers)} tickers")
    for ticker in tickers:
        st.markdown(
            f"- **{ticker}** [🔗 Trading212](https://www.trading212.com/trading-instruments/invest/{ticker}.US)",
            unsafe_allow_html=True
        )
else:
    st.warning("No tickers found or failed to load data.")
