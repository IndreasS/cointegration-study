"""
Runs the engine over every ordered pair in every rolling window.

Both directions tested since EG is asymmetric: 2,862 ordered pairs per window
from 54 stocks.

Keeps every result, passing or not. The bootstrap and multiple testing work
needs the full p-value cross section.

~30 minutes. Saves screen_3yr.parquet.
"""

import itertools
import time
import pandas as pd
from statsmodels.tsa.stattools import coint as eg_coint

import coint

MIN_OBS = 650


def rolling_windows(formation_years):
    """(form_start, form_end, test_start, test_end), stepped annually."""
    windows = []

    for year in range(2010, 2026 - formation_years):
        windows.append((
            f"{year}-01-01",
            f"{year + formation_years - 1}-12-31",
            f"{year + formation_years}-01-01",
            f"{year + formation_years}-12-31",
        ))

    return windows


def screen(tickers, start, end, prices, universe):
    """
    Screen one formation window. Returns successes, pairs skipped for short
    history, and pairs that raised. Different things, counted separately.
    """
    success, skipped, errors = [], [], []

    for stockX, stockY in itertools.permutations(tickers, 2):
        try:
            result = coint.cointegration(stockX, stockY, start, end, prices, universe)
            if result is None:
                skipped.append((stockX, stockY))
                continue
            success.append(result)
        except Exception as e:
            errors.append((stockX, stockY, str(e)))

    return success, skipped, errors


def screen_pvalues_only(tickers, start, end, prices):
    """
    Same screen, EG p-values only. The bootstrap re-runs this per replication
    and only needs the pass count. Skipping the OLS fit and the half life
    regression cuts runtime from 134s to 82s per window.
    """
    pvalues = []

    for stockX, stockY in itertools.permutations(tickers, 2):
        try:
            pair = prices[[stockY, stockX]].loc[start:end].dropna()
            if len(pair) < MIN_OBS:
                continue
            pvalues.append(eg_coint(pair[stockY], pair[stockX])[1])
        except Exception:
            continue

    return pvalues


if __name__ == "__main__":
    prices = pd.read_parquet("data/prices.parquet")
    universe = pd.read_csv("data/universe.csv").set_index("Symbol")
    tickers = universe.index.tolist()

    all_results = []

    for form_start, form_end, test_start, test_end in rolling_windows(3):
        print(f"\n{form_start[:4]}-{form_end[:4]} -> {test_start[:4]}")

        t0 = time.time()
        success, skipped, errors = screen(tickers, form_start, form_end, prices, universe)
        elapsed = time.time() - t0

        df = pd.DataFrame(success)
        df["Training Dates"] = f"{form_start} to {form_end}"
        df["Test Dates"] = f"{test_start} to {test_end}"

        pass_rate = (df["p_value_coint"] < 0.05).sum() / len(df)

        print(f"  {elapsed:.0f}s | tested {len(success)}, skipped {len(skipped)}, "
              f"errors {len(errors)}")
        print(f"  pass rate at p<0.05: {pass_rate:.2%}")

        all_results.append(df)

    screen_results = pd.concat(all_results, ignore_index=True)
    screen_results.to_parquet("data/screen_3yr.parquet")
    print(f"\nSaved {len(screen_results)} rows to data/screen_3yr.parquet")