import requests
from bs4 import BeautifulSoup
import time
import random
import csv

def get_finviz_tickers(pages=3):
    base_url = "https://finviz.com/screener.ashx?v=111&f=cap_microunder,sh_float_u10,sh_short_o10&ft=4&r="
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    tickers = []

    for page in range(pages):
        offset = 1 + page * 20
        url = f"{base_url}{offset}"
        print(f"Scraping: {url}")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            table = soup.find("table", class_="table-light")
            if not table:
                print("❌ No screener table found.")
                continue

            rows = table.find_all("tr", class_=["table-dark-row-cp", "table-light-row-cp"])
            for row in rows:
                cols = row.find_all("td")
                if len(cols) > 1:
                    ticker = cols[1].text.strip()
                    tickers.append(ticker)

            time.sleep(random.uniform(1.5, 3.5))

        except Exception as e:
            print(f"Error: {e}")

    return list(set(tickers))

def generate_trading212_links(tickers):
    return {ticker: f"https://www.trading212.com/trading-instruments/invest/{ticker}.US" for ticker in tickers}

def save_to_csv(ticker_links, filename="finviz_trading212_links.csv"):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Ticker", "Trading212 Link"])
        for ticker, link in ticker_links.items():
            writer.writerow([ticker, link])
    print(f"✅ Saved to {filename}")

if __name__ == "__main__":
    tickers = get_finviz_tickers()
    print(f"\n✅ Found {len(tickers)} tickers.\n")

    ticker_links = generate_trading212_links(tickers)

    for ticker, link in ticker_links.items():
        print(f"{ticker}: {link}")

    # Optional: Save to CSV
    save_to_csv(ticker_links)
