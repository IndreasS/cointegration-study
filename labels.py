"""
Evaluates every screened pair on its test year using frozen formation
parameters.

Alpha, beta and spread std all come from formation. Re-fitting any of them on
the test window would be lookahead.

Two things come out per pair-year:

    outcome      what happened the first time the spread widened to 2 sd
    spread_vol   how much the z-score moved over the test year

Only the first opening is kept. Counting every opening needs a re-entry rule,
and a pair that opens six times would then weigh six times as much as one that
opens once. One pair-year, one outcome.

spread_vol is not an outcome. It is there for the second step in analysis.py.

Saves labels.parquet.
"""

import numpy as np
import pandas as pd

MIN_TEST_OBS = 200
ENTRY = 2.0
DIVERGE = 4.0


def first_opening(z, entry=ENTRY, diverge=DIVERGE):
    """
    never_opened, reverted, diverged or unresolved.

    Reverted means z comes back through zero on the side it opened from.
    """
    z = np.asarray(z, dtype=float)

    opened = np.flatnonzero(np.abs(z) >= entry)
    if len(opened) == 0:
        return "never_opened"

    t0 = opened[0]
    side = np.sign(z[t0])
    after = z[t0 + 1:]

    # The opening day itself is not checked for divergence, so a spread that
    # jumps straight to 4.5 still gets one more day to come back.
    back = np.flatnonzero(side * after <= 0)
    blown = np.flatnonzero(np.abs(after) >= diverge)

    t_back = back[0] if len(back) else np.inf
    t_blown = blown[0] if len(blown) else np.inf

    if np.isinf(t_back) and np.isinf(t_blown):
        return "unresolved"

    # <= so that a day which crosses zero and lands beyond 4 on the other side
    # counts as diverged. That spread would not have been a comfortable exit.
    return "diverged" if t_blown <= t_back else "reverted"


def check_first_opening():
    cases = [
        ([0, 2.5, 1.0, 0.0],           "reverted"),
        ([0, -2.5, -1.0, 0.5],         "reverted"),
        ([0, 2.5, 2.0, 2.2],           "unresolved"),
        ([0, 2.5, 3.0, 4.5, 0.0],      "diverged"),
        ([0, 0.5, 1.0, 1.5],           "never_opened"),
        ([0, 2.5, 0.0, 4.5],           "reverted"),     # only the first opening counts
        ([0, 3.0, -4.5],               "diverged"),
    ]
    for z, expected in cases:
        got = first_opening(z)
        assert got == expected, f"{z}: expected {expected}, got {got}"


def label_pair(row, prices, min_obs=MIN_TEST_OBS):
    """None if the test window is too short."""
    x, y = row.stockX, row.stockY

    pair = prices[[y, x]].loc[row.test_start:row.test_end].dropna()

    if len(pair) < min_obs:
        return None

    spread = pair[y] - (row.alpha + row.beta * pair[x])
    z = spread / row.spread_std

    return {
        "pair_id": row.pair_id,
        "stockX": x,
        "stockY": y,
        "test_year": int(row.test_start[:4]),
        "p_value_coint": row.p_value_coint,
        "outcome": first_opening(z),
        "spread_vol": float(z.std()),
    }


if __name__ == "__main__":
    check_first_opening()

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

    print(f"Labelled {len(labels)}, skipped {skipped}")
    print(labels["outcome"].value_counts().to_string())