"""
Study universe: 7 largest GICS sectors by aggregate S&P 500 market cap, top 8
constituents by cap in each.

Excluded:
- GOOG, second share class of GOOGL. Near-identical series, statsmodels flags
  the EG test as unreliable.
- GEV, spun off March 2024. 441 trading days against a 650 minimum.

54 stocks.
"""

import pandas as pd
import yfinance as yf
import os
import requests
from io import StringIO

UNIVERSE_FILE = "data/universe.csv"
EXCLUDED = ["GOOG", "GEV"]


def build_universe():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}     # default agent gets blocked
    html = requests.get(url, headers=headers).text
    sp500_df = pd.read_html(StringIO(html))[0]
    print("Columns found:", sp500_df.columns.tolist())

    sp500_df = sp500_df.rename(columns={
        "GICS Sector": "Sector",
        "GICS Sub-Industry": "SubIndustry",
    })

    records, failed = [], []

    for row in sp500_df.itertuples():
        symbol = row.Symbol.replace(".", "-")   # Yahoo writes BRK.B as BRK-B
        try:
            mcap = yf.Ticker(symbol).info.get("marketCap")
            if mcap is None:
                failed.append((symbol, "no marketCap"))
                continue
            records.append({
                "Symbol": symbol,
                "Sector": row.Sector,
                "SubIndustry": row.SubIndustry,
                "marketcap": mcap,
            })
        except Exception as e:
            failed.append((symbol, str(e)))

    print(f"Fetched {len(records)}, failed {len(failed)}")
    if failed:
        print("Failures:", failed)

    df = pd.DataFrame(records)

    # Aggregate by sector first, then pick the top 7, then take the top 8
    # within them. Doing it the other way round would rank sectors on 8 stocks
    # each rather than on all their constituents.
    sectorcaps = df.groupby("Sector")["marketcap"].sum()
    print(sectorcaps)

    top_sectors = sectorcaps.nlargest(7).index
    df_top = df[df["Sector"].isin(top_sectors)]

    universe = df_top.sort_values("marketcap", ascending=False).groupby("Sector").head(8)
    universe = universe[~universe["Symbol"].isin(EXCLUDED)]

    counts = universe.groupby("Sector").size()
    print(counts)
    assert len(universe) == 54, f"expected 54 stocks, got {len(universe)}"
    assert (counts == 7).sum() == 2, "expected 2 sectors short by one exclusion"
    assert (counts == 8).sum() == 5, "expected 5 full sectors"

    os.makedirs("data", exist_ok=True)
    universe.to_csv(UNIVERSE_FILE, index=False)
    return universe


if __name__ == "__main__":
    if os.path.exists(UNIVERSE_FILE):
        universe = pd.read_csv(UNIVERSE_FILE)
        print("Loaded universe from cache.")
    else:
        universe = build_universe()

    print(universe.shape)
    print(universe.groupby("Sector").size())