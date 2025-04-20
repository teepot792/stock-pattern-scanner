import streamlit as st
import requests
from bs4 import BeautifulSoup

def fetch_all_finviz_tickers():
    base_url = "https://finviz.com/screener.ashx"
    headers = {"User-Agent": "Mozilla/5.0"}
    page = 1
    all_tickers = []

    while True:
        params = {
            "v": "111",
            "f": "cap_microunder,sh_float_u10,sh_short_o10",
            "ft": "4",
            "r": str((page - 1) * 20 + 1)
        }

        try:
            res = requests.get(base_url, headers=headers, params=params)
            soup = BeautifulSoup(res.text, "html.parser")

            table = soup.find("table", class_="table-light")
            if not table:
                break

            rows = table.find_all("tr")[1:]  # Skip header
            if not rows:
                break

            for row in rows:
                cols = row.find_all("td")
                if len(cols) > 1:
                    ticker_tag = cols[1].find("a")
                    if ticker_tag:
                        ticker = ticker_tag.text.strip()
                        all_tickers.append(ticker)

            page += 1

        except Exception as e:
            st.error(f"Error fetching tickers from Finviz: {e}")
            break

    return list(set(all_tickers))  # Remove duplicates


# --- Streamlit App ---
st.set_page_config(page_title="Finviz Screener", layout="wide")
st.title("📊 Finviz Screener: Micro Cap, Low Float, High Short Interest")

tickers = fetch_all_finviz_tickers()

if tickers:
    st.success(f"✅ Found {len(tickers)} tickers")
    for t in tickers:
        st.markdown(f"- **{t}** [🔗 Trading212](https://www.trading212.com/trading-instruments/invest/{t}.US)", unsafe_allow_html=True)
else:
    st.warning("⚠️ No tickers found.")
