import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Low Float Ticker List", layout="wide")
st.title("📈 Finviz Screener: Micro Cap Stocks with Low Float & High Short Interest")

# --- Finviz Scraper Function ---
def get_finviz_tickers():
    url = "https://finviz.com/screener.ashx?v=111&f=cap_microunder,sh_float_u10,sh_short_o10&ft=4"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error("Failed to fetch data from Finviz")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    tickers = []
    for row in soup.select(".screener-body-table-nw tr[valign='top']")[1:]:
        cells = row.find_all("td")
        if len(cells) > 1:
            tickers.append(cells[1].text.strip())

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
