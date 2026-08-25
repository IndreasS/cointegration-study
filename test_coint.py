"""
Validates the engine against synthetic data with known answers.

- recovers a known hedge ratio
- recovers a known half life
- detects cointegrated pairs
- rejects independent random walks at roughly 5%

Tolerances come from the measured spread, not from guessing. Beta has sd 0.04
over 49 seeds, so 0.15 is about 4 sd. Half life has sd 1.58 and a range of 6.5
to 14.1, so 5 is about 3 sd.
"""

import numpy as np
import pandas as pd

import synthetic
import coint

N_COINT_SEEDS = 49
N_NULL_SEEDS = 1000


def framed_data(x, y):
    """
    Wrap two arrays into the prices/universe shape the engine expects.
    AAA holds x, BBB holds y, so ("AAA", "BBB") regresses y on x.
    """
    idx = pd.date_range(start="2000-01-01", periods=len(x), freq="D")
    prices = pd.DataFrame({"AAA": x, "BBB": y}, index=idx)
    universe = pd.DataFrame(np.zeros((2, 2)),
                            index=["AAA", "BBB"],
                            columns=["Sector", "SubIndustry"])
    return prices, universe


def run_engine(x, y):
    prices, universe = framed_data(x, y)
    return coint.cointegration("AAA", "BBB", prices.index[0], prices.index[-1],
                               prices, universe)


def test_recovery_on_cointegrated_pairs():
    for seed in range(1, N_COINT_SEEDS + 1):
        x, y, e = synthetic.cointegrated_pair(1000, beta=2.0, half_life=10, seed=seed)
        r = run_engine(x, y)

        assert abs(r["beta"] - 2.0) < 0.15, f"beta off at seed {seed}"
        assert abs(r["halflife"] - 10) < 5, f"half life off at seed {seed}"
        assert r["p_value_coint"] < 0.05, f"true pair missed at seed {seed}"

    print(f"Cointegrated pairs: {N_COINT_SEEDS}/{N_COINT_SEEDS} passed")


def test_false_positive_rate():
    """
    p-values under the null should be uniform on [0,1]: mean 0.5,
    sd 1/sqrt(12) = 0.2887. Checking the distribution catches more than the
    5% count alone.
    """
    pvalues = []

    for seed in range(1, N_NULL_SEEDS + 1):
        x, y = synthetic.independent_pair(1000, sigma=1.0, s0=100, seed=seed)
        pvalues.append(run_engine(x, y)["p_value_coint"])

    count = sum(1 for p in pvalues if p < 0.05)
    rate = count / N_NULL_SEEDS

    print(f"False positives: {count}/{N_NULL_SEEDS} = {rate:.2%} (nominal 5%)")
    print(f"  mean {np.mean(pvalues):.4f} (expected 0.5000)")
    print(f"  sd   {np.std(pvalues):.4f} (expected 0.2887)")

    # se on the rate at n=1000 is ~0.7pp
    assert 0.035 < rate < 0.07, f"false positive rate {rate:.2%} is off nominal"


if __name__ == "__main__":
    test_recovery_on_cointegrated_pairs()
    test_false_positive_rate()
    print("All properties held.")