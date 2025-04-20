import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Low Float Ticker List", layout="wide")
st.title("📈 Finviz Screener: Micro Cap Stocks with Low Float & High Short Interest")

# --- Finviz Scraper Function ---
def get_finviz_tickers():
    tickers = []
    base_url = "https://finviz.com/screener.ashx"
    params = {
        "v": "111",
        "f": "cap_microunder,sh_float_u10,sh_short_o10",
        "ft": "4",
        "r": "1"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(base_url, params=params, headers=headers)
        soup = BeautifulSoup(response.text, 'html5lib')
        table = soup.find("table", class_="table-light")
        rows = table.find_all("tr", valign="top")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) > 1:
                tickers.append(cols[1].text.strip())
    except Exception as e:
        st.error(f"Error fetching tickers from Finviz: {e}")

    return tickers

# --- App Logic ---
tickers = get_finviz_tickers()

if tickers:
    st.success(f"✅ {len(tickers)} tickers found from Finviz")
    st.write("### Ticker List:")
    for ticker in tickers:
        t212_link = f"https://www.trading212.com/trading-instruments/invest/{ticker}.US"
        st.markdown(f"- **{ticker}** → [🔗 Trading212]({t212_link})")
else:
    st.warning("No tickers found or failed to load data.")
