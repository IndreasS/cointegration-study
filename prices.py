"""
15 years of daily adjusted closes for the universe, cached to Parquet.

Parquet not CSV: CSV stores everything as text, so the DatetimeIndex reloads as
strings and every .loc[start:end] slice becomes a string comparison rather than
a date range. Fails silently.
"""

import pandas as pd
import yfinance as yf
import os

PRICES_FILE = "data/prices.parquet"
UNIVERSE_FILE = "data/universe.csv"


def get_prices(tickers, start="2010-01-01", end="2025-12-31"):
    # auto_adjust set explicitly. The default has changed between yfinance
    # versions and a silent switch to raw close would corrupt every spread.
    data = yf.download(tickers, start=start, end=end, auto_adjust=True)
    return data["Close"]


if __name__ == "__main__":
    if os.path.exists(PRICES_FILE):
        price_data = pd.read_parquet(PRICES_FILE)
        print("Loaded prices from cache.")
    else:
        tickers = pd.read_csv(UNIVERSE_FILE)["Symbol"].tolist()
        price_data = get_prices(tickers)
        price_data.to_parquet(PRICES_FILE)
        print("Downloaded and cached prices.")

    print(price_data.shape)
    assert price_data.shape[1] == 54, f"expected 54 tickers, got {price_data.shape[1]}"

    # Leading NaNs just mean a stock had not listed yet. NaNs after the first
    # real price are internal gaps, which corrupt a regression silently.
    # Count them separately.
    summary = pd.DataFrame({
        "first_valid": price_data.apply(lambda c: c.first_valid_index()),
        "total_nans": price_data.isna().sum(),
        "internal_nans": price_data.apply(
            lambda c: c.loc[c.first_valid_index():].isna().sum()
        ),
    })
    print(summary)

    print("\nTickers with internal gaps (should be none):")
    print(summary[summary["internal_nans"] > 0])