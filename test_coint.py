"""
Validates the engine against data where the answer is known by construction.

Market data has no answer key. A hedge ratio of 1.01 could be right or it could
be a plausible looking bug. These generators set beta and the half life
explicitly so there is something to check against.

    - recovers a known hedge ratio
    - recovers a known half life
    - detects cointegrated pairs
    - rejects independent random walks at roughly 5%

Tolerances come from the measured spread rather than from guessing. Beta has
sd 0.04 over 49 seeds, so 0.15 is about 4 sd. Half life has sd 1.58 and a range
of 6.5 to 14.1, so 5 is about 3 sd. My first attempt used a half life tolerance
of 0.2, which passed on seed 1 and failed on seed 2 at 12.74.

Nothing downstream is trusted until this passes.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm

import coint

N_COINT_SEEDS = 49
N_NULL_SEEDS = 1000


# --- generators ---

def random_walk(n, sigma=1.0, s0=100.0, seed=None):
    """Driftless random walk. Non-stationary."""
    rng = np.random.default_rng(seed)
    return s0 + np.cumsum(rng.normal(0, sigma, n))


def ar1(n, half_life, sigma=1.0, seed=None):
    """
    Mean reverting AR(1). phi = exp(-ln2 / half_life) decays a deviation to
    half its size in half_life steps.
    """
    phi = np.exp(-np.log(2) / half_life)
    rng = np.random.default_rng(seed)
    shocks = rng.normal(0, sigma, n)

    e = np.zeros(n)
    for i in range(1, n):
        e[i] = e[i - 1] * phi + shocks[i]

    return e


def independent_pair(n, sigma=1.0, s0=100, seed=None):
    """
    Two unrelated random walks.

    Seeds spaced 2 apart: seed and seed+1 would make one trial's y series the
    next trial's x series.
    """
    return random_walk(n, seed=seed * 2), random_walk(n, seed=seed * 2 + 1)


def cointegrated_pair(n, beta=2.0, half_life=10, seed=None):
    """y = beta*x + e, with x a random walk and e stationary AR(1)."""
    x = random_walk(n, seed=seed * 2)
    e = ar1(n, half_life=half_life, seed=seed * 2 + 1)
    return x, beta * x + e, e


# --- plumbing ---

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


# --- tests ---

def test_recovery_on_cointegrated_pairs():
    for seed in range(1, N_COINT_SEEDS + 1):
        x, y, e = cointegrated_pair(1000, beta=2.0, half_life=10, seed=seed)
        r = run_engine(x, y)

        assert abs(r["beta"] - 2.0) < 0.15, f"beta off at seed {seed}"
        assert abs(r["halflife"] - 10) < 5, f"half life off at seed {seed}"
        assert r["p_value_coint"] < 0.05, f"true pair missed at seed {seed}"

    print(f"Cointegrated pairs: {N_COINT_SEEDS}/{N_COINT_SEEDS} passed")


def test_false_positive_rate():
    """
    p-values under the null should be uniform on [0,1]: mean 0.5,
    sd 1/sqrt(12) = 0.2887. Checking the whole distribution catches more than
    the 5% count on its own, since a test can get the tail right and still be
    wrong everywhere else.
    """
    pvalues = []

    for seed in range(1, N_NULL_SEEDS + 1):
        x, y = independent_pair(1000, sigma=1.0, s0=100, seed=seed)
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
