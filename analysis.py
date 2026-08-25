"""
Four cuts of the labelled results.

1. By formation p-value decile. Does the ranking predict anything?
2. By test year. Is the pattern stable?
3. By sector and sub-industry. Does economic linkage matter?
4. Against VIX. What drives performance, if not the p-value?

Saves two figures.
"""

import os
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

labels = pd.read_parquet("data/labels.parquet")

# Rank within each test year before cutting into deciles. Pooling across years
# would let one year's p-value distribution dominate the buckets, since the
# pass rate varies from 3.5% to 13% across the sample.
labels["decile"] = (
    labels.groupby("test_year")["p_value_coint"]
          .transform(lambda s: pd.qcut(s, 10, labels=False, duplicates="drop"))
) + 1

# A pair that never triggered an entry has a return of exactly zero, which is
# not the same as a losing trade. Return stats use traded pairs only.
traded = labels[labels["n_trades"] > 0]


# --- 1. does formation significance predict anything? ---
by_decile = pd.DataFrame({
    "n_pairs":       labels.groupby("decile").size(),
    "mean_pvalue":   labels.groupby("decile")["p_value_coint"].mean(),
    "persist_rate":  labels.groupby("decile")["persisted"].mean(),
    "median_return": traded.groupby("decile")["total_return"].median(),
    "mean_return":   traded.groupby("decile")["total_return"].mean(),
    "frac_losing":   traded.groupby("decile")["total_return"].apply(lambda s: (s < 0).mean()),
    "worst_trade":   labels.groupby("decile")["worst_trade"].min(),
    "mean_trades":   labels.groupby("decile")["n_trades"].mean(),
})

by_decile["stop_revert_ratio"] = (
    labels.groupby("decile")["n_stopped"].sum()
    / labels.groupby("decile")["n_reverted"].sum()
)

print("=== By formation p-value decile (1 = most significant) ===")
print(by_decile.round(4).to_string())

print("\n=== Median return by decile and test year (traded pairs) ===")
print(traded.pivot_table(index="decile", columns="test_year",
                         values="total_return", aggfunc="median").round(4).to_string())

top = traded[traded["decile"] == 1]
bottom = traded[traded["decile"] == 10]

print("\n=== Decile 1 vs decile 10 ===")
print(f"  median return: {top['total_return'].median():.4f}  vs  {bottom['total_return'].median():.4f}")
print(f"  mean return:   {top['total_return'].mean():.4f}  vs  {bottom['total_return'].mean():.4f}")
print(f"  frac losing:   {(top['total_return'] < 0).mean():.2%}  vs  {(bottom['total_return'] < 0).mean():.2%}")
print(f"  persist rate:  {labels[labels['decile'] == 1]['persisted'].mean():.2%}"
      f"  vs  {labels[labels['decile'] == 10]['persisted'].mean():.2%}")


# --- 2. is the pattern stable across years? ---
by_year = pd.DataFrame({
    "n_pairs":       labels.groupby("test_year").size(),
    "persist_rate":  labels.groupby("test_year")["persisted"].mean(),
    "median_return": traded.groupby("test_year")["total_return"].median(),
    "frac_losing":   traded.groupby("test_year")["total_return"].apply(lambda s: (s < 0).mean()),
    "n_reverted":    labels.groupby("test_year")["n_reverted"].sum(),
    "n_stopped":     labels.groupby("test_year")["n_stopped"].sum(),
    "n_marked":      labels.groupby("test_year")["n_marked"].sum(),
})
by_year["stop_revert_ratio"] = by_year["n_stopped"] / by_year["n_reverted"]

print("\n=== By test year ===")
print(by_year.round(4).to_string())


# --- 3. does economic linkage matter? ---
def sector_cut(df, traded_df, flag):
    return pd.DataFrame({
        "n_pairs":       df.groupby(flag).size(),
        "persist_rate":  df.groupby(flag)["persisted"].mean(),
        "median_return": traded_df.groupby(flag)["total_return"].median(),
        "mean_return":   traded_df.groupby(flag)["total_return"].mean(),
        "frac_losing":   traded_df.groupby(flag)["total_return"].apply(lambda s: (s < 0).mean()),
        "stop_revert":   df.groupby(flag)["n_stopped"].sum() / df.groupby(flag)["n_reverted"].sum(),
    })

print("\n=== Same sector vs cross sector ===")
print(sector_cut(labels, traded, "same_sector").round(4).to_string())

# only 822 same sub-industry pair-years, so these estimates are noisy
print("\n=== Same sub-industry vs not ===")
print(sector_cut(labels, traded, "same_sub_industry").round(4).to_string())


# --- 4. what does drive performance? ---
vix = yf.download("^VIX", start="2013-01-01", end="2025-12-31", auto_adjust=True)["Close"]
vix_yearly = vix.groupby(vix.index.year).agg(["mean", "max"])
vix_yearly.columns = ["vix_mean", "vix_max"]

regime = by_year[["persist_rate", "median_return", "frac_losing", "stop_revert_ratio"]].copy()
regime.index = regime.index.astype(int)
regime = regime.join(vix_yearly)

print("\n=== Outcome vs volatility regime ===")
print(regime.round(4).to_string())

# Spearman as well as Pearson. Most years sit between 11 and 20 on mean VIX,
# but 2020 is at 29.3 and 2022 at 25.6. Those two drag a linear fit without
# being outliers in rank terms. At n=13 a correlation needs to be around 0.55
# to reach p<0.05, so treat anything weaker as suggestive.
print()
for col in ["stop_revert_ratio", "median_return", "frac_losing", "persist_rate"]:
    r, p = pearsonr(regime["vix_mean"], regime[col])
    rho, prho = spearmanr(regime["vix_mean"], regime[col])
    print(f"{col:20s} vs mean VIX:  r={r:+.3f} (p={p:.3f})   rho={rho:+.3f} (p={prho:.3f})")


# --- figures ---
os.makedirs("figures", exist_ok=True)

# Twin axes because persistence is a rate in [0,1] and returns are small
# negatives. One axis would flatten the return line to nothing.
fig, ax1 = plt.subplots(figsize=(8, 5))

ax1.plot(by_decile.index, by_decile["persist_rate"], "o-", color="tab:blue")
ax1.set_xlabel("Formation p-value decile (1 = most significant)")
ax1.set_ylabel("Persistence rate", color="tab:blue")
ax1.tick_params(axis="y", labelcolor="tab:blue")
ax1.set_xticks(by_decile.index)

ax2 = ax1.twinx()
ax2.plot(by_decile.index, by_decile["median_return"], "s--", color="tab:red")
ax2.axhline(0, color="grey", lw=0.8, ls=":")
ax2.set_ylabel("Median return (traded pairs)", color="tab:red")
ax2.tick_params(axis="y", labelcolor="tab:red")

plt.title("Out-of-sample outcome by formation p-value decile")
fig.tight_layout()
fig.savefig("figures/decile_sort.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 5))

ax.scatter(regime["vix_mean"], regime["stop_revert_ratio"], s=60, color="tab:blue")

for year, row in regime.iterrows():
    ax.annotate(str(year), (row["vix_mean"], row["stop_revert_ratio"]),
                xytext=(5, 3), textcoords="offset points", fontsize=9)

ax.axhline(1.0, color="grey", lw=0.8, ls=":")   # stops = reversions
ax.set_xlabel("Mean VIX over test year")
ax.set_ylabel("Stop-outs per reversion")
ax.set_title("Pairs trading fares worse in calm markets\n(Spearman rho = -0.64, p = 0.018)")

fig.tight_layout()
fig.savefig("figures/vix_regime.png", dpi=150)
plt.close(fig)

print("\nSaved figures/decile_sort.png and figures/vix_regime.png")