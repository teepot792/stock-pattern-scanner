import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

url = "https://finviz.com/screener.ashx?v=111&f=cap_microunder,sh_float_u10,sh_short_o10&ft=4"
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Debug: print HTML to inspect
print(soup.prettify()[:1000])
