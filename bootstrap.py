"""
Null distribution for the screen's pass rate.

The nominal 5% assumes conditions this data does not meet. Returns are fat
tailed, volatility clusters, and the 2,862 pairs come from 54 stocks that share
legs and load on a common factor. The random walk test had none of that, so its
5.5% may not carry over.

The resampler destroys cointegration and keeps the rest:

- Resamples returns, not prices. Reshuffling price levels gives impossible
  jumps; reshuffling returns and cumulating gives a plausible path.
- Blocks rather than single days, so volatility clustering inside a block
  survives.
- Same block sequence for every column, so a given week moves position for all
  54 stocks together. Preserves contemporaneous correlation. Shuffling columns
  separately would destroy it.

The null is estimated on one formation window, taken from rolling_windows so
it is the same length as the windows it is compared against. The size of the
EG test depends on sample length.
"""

import numpy as np
import pandas as pd
from arch.bootstrap import optimal_block_length

from screen import screen_pvalues_only, rolling_windows


def resample_prices(prices, block_length, seed):
    """Price frame with cointegration destroyed by construction."""
    returns = np.log(prices).diff().dropna()

    rng = np.random.default_rng(seed)
    n = len(returns)
    n_blocks = int(np.ceil(n / block_length))

    starts = rng.integers(0, n - block_length + 1, n_blocks)
    positions = np.concatenate([np.arange(s, s + block_length) for s in starts])[:n]

    # .iloc on the whole frame moves entire rows, so every stock's day travels
    # with every other stock's day
    shuffled = returns.iloc[positions]
    shuffled.index = returns.index

    # rescale to the first date that survived the dropna, not the first date in
    # prices, which is NaN for a late lister
    return np.exp(shuffled.cumsum()) * prices.loc[returns.index[0]]


def run_bootstrap(prices, universe, block_length, n_reps, start, end):
    """
    Re-run the screen on resampled data n_reps times. Stores p-value quantiles
    as well as the pass count, so the null can also give a calibrated critical
    value.
    """
    tickers = universe["Symbol"].tolist()
    results = []

    for seed in range(n_reps):
        resampled = resample_prices(prices, block_length, seed)
        pvalues = screen_pvalues_only(tickers, start, end, resampled)

        n_pairs = len(pvalues)
        n_passing = sum(1 for p in pvalues if p < 0.05)
        q = np.percentile(pvalues, [5, 25, 50, 75, 95])

        results.append({
            "seed": seed,
            "block_length": block_length,
            "n_pairs": n_pairs,
            "n_passing": n_passing,
            "pass_rate": n_passing / n_pairs,
            "p05": q[0], "p25": q[1], "p50": q[2], "p75": q[3], "p95": q[4],
        })

        if (seed + 1) % 10 == 0:
            print(f"  block={block_length}, {seed + 1}/{n_reps} done")

    return pd.DataFrame(results)


if __name__ == "__main__":
    prices = pd.read_parquet("data/prices.parquet")
    universe = pd.read_csv("data/universe.csv")
    returns = np.log(prices).diff().dropna()

    # Politis-White-Patton block length, reported as a diagnostic only.
    # It comes back at a mean of 1.69 days, reflecting almost no linear
    # autocorrelation in daily mega cap returns. But PPW optimises for
    # estimating a mean under linear dependence, and what matters here is
    # whether volatility clustering inflates the size of a cointegration test.
    # Different objective, so I test a range of block lengths instead.
    #
    # print(optimal_block_length(returns).describe())

    N_REPS = 20
    BLOCK_LENGTHS = [10, 21]

    # 2015 is the first formation start where all 54 stocks trade for the
    # whole window.
    form_start, form_end, _, _ = next(
        w for w in rolling_windows(3) if w[0].startswith("2015")
    )

    all_runs = []
    for bl in BLOCK_LENGTHS:
        print(f"=== block length {bl} ===")
        all_runs.append(run_bootstrap(prices, universe, bl, N_REPS,
                                      form_start, form_end))

    null_dist = pd.concat(all_runs, ignore_index=True)
    null_dist.to_parquet("data/bootstrap_null.parquet")

    summary = null_dist.groupby("block_length")["pass_rate"].agg(
        mean="mean", sd="std",
        q05=lambda s: s.quantile(0.05),
        q95=lambda s: s.quantile(0.95),
    )
    print("\nNull distribution of the screen pass rate:")
    print(summary.round(4).to_string())