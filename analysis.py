"""
Does the Engle-Granger p-value identify pairs whose spreads revert out of
sample?

    1. sort_by_pvalue   outcome by p-value decile
    2. spread_vol_check why the sort looks the way it does
    3. against_vix      whether market volatility moves the same outcome

The outcome is diverged per reversion, over pairs whose spread opened. It is a
ratio rather than a share because a spread that moves further in z units hits both barriers more often,
so the diverged and reverted shares both rise with volatility. The ratio asks
which way it resolved, not how often.

No standard errors: pair-years share stocks and years, so they are not
independent.

Saves two figures.
"""

import os
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

N_DECILES = 10
VIX_FILE = "data/vix.parquet"


def load():
    labels = pd.read_parquet("data/labels.parquet")

    # EG is run in both directions, but AAPL-MSFT and MSFT-AAPL are close to
    # the same observation twice. Keeping both makes the sample look twice as
    # big as it is. Which direction is kept is fixed by name rather than by
    # picking the smaller p-value, which would bias the sort. Not split on
    # pair_id, since BRK-B has a hyphen in it.
    labels = labels[labels["stockX"] < labels["stockY"]].copy()

    # Ranked within each year, otherwise the years with high pass rates would
    # fill the bottom deciles.
    labels["p_decile"] = (
        labels.groupby("test_year")["p_value_coint"]
              .transform(lambda s: pd.qcut(s, N_DECILES, labels=False))
    ) + 1

    labels["opened"] = labels["outcome"] != "never_opened"
    labels["diverged"] = labels["outcome"] == "diverged"
    labels["reverted"] = labels["outcome"] == "reverted"
    labels["resolved"] = labels["diverged"] | labels["reverted"]

    return labels


def outcomes(df, group):
    """Outcome columns for pairs that opened, one row per group."""
    grouped = df[df["opened"]].groupby(group)

    return pd.DataFrame({
        "n_opened": grouped.size(),
        "diverged": grouped["diverged"].sum(),
        "reverted": grouped["reverted"].sum(),
        "resolved_share": grouped["resolved"].mean(),
        "ratio": grouped["diverged"].sum() / grouped["reverted"].sum(),
    })


def sort_by_pvalue(labels):
    table = outcomes(labels, "p_decile")
    table.insert(0, "mean_p", labels.groupby("p_decile")["p_value_coint"].mean())

    print("\n=== 1. Diverged per reversion by p-value decile ===")
    print(table[["mean_p", "n_opened", "diverged", "reverted", "ratio"]]
          .round(4).to_string())
    return table


def spread_vol_check(labels):
    """
    A small p-value means a tight formation fit, so a small spread_std. That
    is the denominator of z, so the same move out of sample gives a bigger z.
    If so, low p-value pairs should open more, move more, and resolve more,
    without resolving any more often in the right direction.
    """
    grouped = labels.groupby("p_decile")

    table = pd.DataFrame({
        "open_rate": grouped["opened"].mean(),
        "resolved_share": outcomes(labels, "p_decile")["resolved_share"],
        "vol_mean": grouped["spread_vol"].mean(),
        "vol_median": grouped["spread_vol"].median(),
    })

    # rho only. Pair-years are not independent, so the p-value would be
    # meaningless.
    rho, _ = spearmanr(labels["p_value_coint"], labels["spread_vol"])

    print("\n=== 2. Spread volatility by p-value decile ===")
    print(table.round(4).to_string())
    print(f"p-value vs spread_vol, pair level: rho={rho:+.3f}")
    return table


def load_vix():
    # Cached for the same reason as prices: yfinance can revise history, and
    # the correlation below should not move between runs.
    if os.path.exists(VIX_FILE):
        return pd.read_parquet(VIX_FILE)["vix"]

    # end is exclusive in yfinance, so 2026-01-01 keeps 31 December 2025.
    vix = yf.download("^VIX", start="2013-01-01", end="2026-01-01",
                      auto_adjust=True, progress=False)["Close"]

    # One column DataFrame on newer yfinance, Series on older. Without the
    # squeeze the assignment below produces a column called ^VIX.
    if isinstance(vix, pd.DataFrame):
        vix = vix.iloc[:, 0]

    vix = vix.rename("vix")
    vix.to_frame().to_parquet(VIX_FILE)
    return vix


def against_vix(labels):
    table = outcomes(labels, "test_year")
    table["spread_vol"] = labels.groupby("test_year")["spread_vol"].mean()

    vix = load_vix()
    table["vix_mean"] = vix.groupby(vix.index.year).mean()

    print("\n=== 3. By test year, against mean VIX ===")
    print(table[["n_opened", "ratio", "spread_vol", "vix_mean"]]
          .round(4).to_string())

    # spread_vol checks whether the VIX result is step 2 at the yearly level.
    #
    # Spearman because 2020 and 2022 sit well above the other years on VIX and
    # would drag a linear fit without being extreme in rank. At n=13 a
    # correlation needs to be around 0.55 to reach p<0.05.
    print()
    for col in ["ratio", "spread_vol"]:
        rho, p = spearmanr(table["vix_mean"], table[col])
        print(f"{col:11s} vs mean VIX: rho={rho:+.3f} (p={p:.3f}, n={len(table)})")

    return table


def figures(p_table, vol_table, year_table):
    os.makedirs("figures", exist_ok=True)
    plt.close("all")

    # Side by side because the right panel is the explanation for the left.
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].plot(p_table.index, p_table["ratio"], "o-")
    axes[0].axhline(1.0, color="grey", lw=0.8, ls=":")     # diverged = reverted
    axes[0].set_ylabel("Diverged per reversion")

    axes[1].plot(vol_table.index, vol_table["vol_mean"], "o-", color="tab:grey")
    axes[1].set_ylabel("Mean test-year spread volatility (z units)")

    for ax in axes:
        ax.set_xlabel("Formation p-value decile")
        ax.set_xticks(p_table.index)

    fig.tight_layout()
    fig.savefig("figures/pvalue_deciles.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(year_table["vix_mean"], year_table["ratio"], s=60)

    for year, row in year_table.iterrows():
        ax.annotate(str(year), (row["vix_mean"], row["ratio"]),
                    xytext=(5, 3), textcoords="offset points", fontsize=9)

    rho, p = spearmanr(year_table["vix_mean"], year_table["ratio"])

    ax.axhline(1.0, color="grey", lw=0.8, ls=":")
    ax.set_xlabel("Mean VIX over test year")
    ax.set_ylabel("Diverged per reversion")
    ax.set_title(f"Spearman rho = {rho:.2f}, p = {p:.3f}, n = {len(year_table)}")

    fig.tight_layout()
    fig.savefig("figures/vix_regime.png", dpi=150)
    plt.close(fig)

    print("\nSaved figures/pvalue_deciles.png and figures/vix_regime.png")


if __name__ == "__main__":
    labels = load()
    print(f"{len(labels)} pair-years, one direction per pair")

    p_table = sort_by_pvalue(labels)
    vol_table = spread_vol_check(labels)
    year_table = against_vix(labels)

    figures(p_table, vol_table, year_table)
