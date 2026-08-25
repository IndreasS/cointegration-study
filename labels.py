"""
Evaluates every screened pair on its test year using frozen formation
parameters. Records the persistence label and the trading outcome.

Alpha, beta, spread mean and spread std all come from formation. Re-fitting any
of them on the test window would be lookahead.

Saves labels.parquet.
"""

import numpy as np
import pandas as pd

from simulate import simulate_trades

MIN_TEST_OBS = 200


def label_pair(row, prices, min_obs=MIN_TEST_OBS):
    """Evaluate one screened pair on its test year. None if the window is short."""
    x, y = row.stockX, row.stockY

    pair = prices[[y, x]].loc[row.test_start:row.test_end].dropna()

    if len(pair) < min_obs:
        return None

    x_price = pair[x]
    y_price = pair[y]

    spread = y_price - (row.alpha + row.beta * x_price)
    z = (spread - row.spread_mean) / row.spread_std

    # The version I started from counted crossings as
    # (signs != signs.shift(1)).sum(), which always counts position 0 because
    # shift puts a NaN there and x != NaN is True. So "crossings >= 2" was
    # really testing "crossings >= 1".
    crossings = int((np.diff(np.sign(z.values)) != 0).sum())
    max_abs_z = float(abs(z).max())

    persisted = bool((crossings >= 2) and (max_abs_z < 4))

    trades = simulate_trades(z, row.spread_std, x_price, y_price, row.beta)
    returns = [t[0] for t in trades]
    reasons = [t[1] for t in trades]

    return {
        "pair_id": row.pair_id,
        "stockX": x,
        "stockY": y,
        "test_year": row.test_start[:4],
        "p_value_coint": row.p_value_coint,
        "p_value_adf": row.p_value_adf,
        "halflife": row.halflife,
        "beta": row.beta,
        "crossings": crossings,
        "max_abs_z": max_abs_z,
        "persisted": persisted,
        "n_trades": len(trades),
        "n_reverted": reasons.count("reverted"),
        "n_stopped": reasons.count("stopped"),
        "n_marked": reasons.count("marked"),
        "total_return": sum(returns) if returns else 0.0,
        "worst_trade": min(returns) if returns else np.nan,
        "same_sector": row.same_sector,
        "same_sub_industry": row.same_sub_industry,
    }


if __name__ == "__main__":
    prices = pd.read_parquet("data/prices.parquet")
    screen = pd.read_parquet("data/screen_3yr.parquet")

    screen[["test_start", "test_end"]] = screen["Test Dates"].str.split(" to ", expand=True)

    results, skipped = [], 0

    for row in screen.itertuples():
        out = label_pair(row, prices)
        if out is None:
            skipped += 1
            continue
        results.append(out)

    labels = pd.DataFrame(results)
    labels.to_parquet("data/labels.parquet")

    traded = labels[labels["n_trades"] > 0]

    print(f"Labelled {len(labels)}, skipped {skipped}")
    print(f"Overall persistence rate: {labels['persisted'].mean():.2%}")
    print(f"Pairs that never traded:  {(labels['n_trades'] == 0).mean():.2%}")

    print("\nPersistence by test year:")
    print(labels.groupby("test_year")["persisted"].mean())

    print("\nMedian return by test year (traded pairs):")
    print(traded.groupby("test_year")["total_return"].median())

    print("\nHow trades closed:")
    print(f"  reverted: {labels['n_reverted'].sum()}")
    print(f"  stopped:  {labels['n_stopped'].sum()}")
    print(f"  marked:   {labels['n_marked'].sum()}")