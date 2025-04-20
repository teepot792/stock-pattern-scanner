
import yfinance as yf
import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

def detect_pattern(ticker, start_date, end_date, smoothing_window=3, window_size=50, tolerance=0.05):
    df = yf.download(ticker, start=start_date, end=end_date)
    if df.empty or len(df) < window_size:
        return [], pd.DataFrame()

    df['Smoothed'] = df['Close'].rolling(smoothing_window).mean()
    df.dropna(inplace=True)
    prices = df['Smoothed'].values
    matches = []

    for i in range(len(prices) - window_size):
        window = prices[i:i + window_size]
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
                            if abs(final_price - halfway_level) / halfway_level < tolerance:
                                matches.append(i)
    return matches, df
