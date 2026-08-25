"""
Generators for data where the answer is known by construction.

Market data has no answer key: a hedge ratio of 1.01 could be right or a
plausible looking bug. These set beta and the half life explicitly so the
engine can be checked against them.

Used by test_coint.py.
"""

import numpy as np
import statsmodels.api as sm


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


def adf_test(s):
    """Hand rolled ADF t-stat. Checked against statsmodels adfuller."""
    X = sm.add_constant(s[:-1])
    return sm.OLS(s[1:] - s[:-1], X).fit().tvalues[1]


def hedge_ratio(y, x):
    results = sm.OLS(y, sm.add_constant(x)).fit()
    return results.params[1], results.resid


def half_life(s):
    X = sm.add_constant(s[:-1])
    slope = sm.OLS(s[1:] - s[:-1], X).fit().params[1]
    return -np.log(2) / slope


if __name__ == "__main__":
    # does the half life estimator recover a known value?
    for seed in range(1, 5):
        print(half_life(ar1(5000, half_life=10, seed=seed)))