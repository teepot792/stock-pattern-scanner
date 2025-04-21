import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema

# SETTINGS
TICKERS = ['VERB', 'SINT', 'COSM', 'TOP', 'HCDI', 'HUDI']  # Replace with your low-float list
START_DATE = "2023-01-01"
END_DATE = "2024-01-01"
SMOOTHING_WINDOW = 3
WINDOW_SIZE = 50
TOLERANCE = 0.05  # For halfway level match

results = []

def detect_pattern(ticker):
    df = yf.download(ticker, start=START_DATE, end=END_DATE)
    if df.empty or len(df) < WINDOW_SIZE:
        return None

    df['Smoothed'] = df['Close'].rolling(SMOOTHING_WINDOW).mean()
    df.dropna(inplace=True)
    prices = df['Smoothed'].values
    dates = df.index
    matches = []

    for i in range(len(prices) - WINDOW_SIZE):
        window = prices[i:i + WINDOW_SIZE]
        local_min = argrelextrema(window, np.less, order=2)[0]
        local_max = argrelextrema(window, np.greater, order=2)[0]

        if len(local_min) >= 2 and len(local_max) >= 2:
            u1_bottom_idx = local_min[0]
            u1_top_idx = local_max[0]

            if u1_bottom_idx < u1_top_idx:
                u1_bottom = window[u1_bottom_idx]
                u1_top = window[u1_top_idx]
                halfway_level = (u1_bottom + u1_top) / 2

                u2_bottom_idx = local_min[1]
                if u2_bottom_idx > u1_top_idx:
                    u2_top_candidates = [idx for idx in local_max if idx > u2_bottom_idx]
                    if u2_top_candidates:
                        u2_top_idx = u2_top_candidates[0]
                        post_u2 = window[u2_top_idx:]
                        if len(post_u2) > 3:
                            final_price = post_u2[-1]
                            if abs(final_price - halfway_level) / halfway_level < TOLERANCE:
                                match_date = dates[i].strftime('%Y-%m-%d')
                                matches.append((match_date, i))

    if matches:
        return {'ticker': ticker, 'matches': matches}
    else:
        return None

# RUN SCAN
for ticker in TICKERS:
    print(f"Scanning {ticker}...")
    result = detect_pattern(ticker)
    if result:
        results.append(result)

# SHOW RESULTS
print("\nPattern Matches:")
for res in results:
    print(f"\n{res['ticker']}:")
    for match_date, _ in res['matches']:
        print(f"  - Pattern detected starting around: {match_date}")
