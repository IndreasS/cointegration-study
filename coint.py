"""
Engle-Granger cointegration test for one ordered pair.

- p_value_coint (statsmodels coint) is what the screen uses
- p_value_adf is adfuller on the same residual, kept for comparison

They differ because beta was fitted on the same data the residual is tested on.
That makes the residual look more stationary than it is, so ordinary ADF
critical values reject too often. coint() uses the harsher EG values.

EG is asymmetric, so y-on-x and x-on-y are separate tests.
"""

import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint
import numpy as np

MIN_OBS = 650


def cointegration(stockX, stockY, start, end, prices, universe):
    """
    Regress stockY on stockX over [start, end] and test the residual.
    universe indexed by Symbol. None if the window is too short.
    """
    pair = prices[[stockY, stockX]].loc[start:end].dropna()
    n_obs = len(pair)

    if n_obs < MIN_OBS:
        return None

    x = pair[stockX]
    y = pair[stockY]

    X = sm.add_constant(x)                  # fit an intercept, not through origin
    results = sm.OLS(y, X).fit()

    beta = results.params.iloc[1]
    alpha = results.params["const"]

    spread = results.resid
    spread_mean = spread.mean()             # ~0, since we fitted an intercept
    spread_std = spread.std()

    p_value_adf = adfuller(spread)[1]
    p_value_coint = coint(y, x)[1]

    # half life: regress the change in the spread on its lagged level.
    # lam is the reversion speed, negative for a mean-reverting series.
    lagged = spread.shift(1).dropna()
    change = spread.diff().dropna()
    lam = sm.OLS(change, sm.add_constant(lagged)).fit().params.iloc[1]
    half_life = -np.log(2) / lam

    same_sector = universe.loc[stockX, "Sector"] == universe.loc[stockY, "Sector"]
    same_sub_industry = universe.loc[stockX, "SubIndustry"] == universe.loc[stockY, "SubIndustry"]

    # alphabetical, so both directions of a pair share an id
    pair_id = "-".join(sorted([stockX, stockY]))

    return {
        "stockX": stockX,
        "stockY": stockY,
        "alpha": alpha,
        "beta": beta,
        "spread_mean": spread_mean,
        "spread_std": spread_std,
        "p_value_coint": p_value_coint,
        "p_value_adf": p_value_adf,
        "halflife": half_life,
        "pair_observations": n_obs,
        "same_sector": same_sector,
        "same_sub_industry": same_sub_industry,
        "pair_id": pair_id,
    }


if __name__ == "__main__":
    universe = pd.read_csv("data/universe.csv").set_index("Symbol")
    prices = pd.read_parquet("data/prices.parquet")

    # Two mega-cap tech names in the same sector, and two unrelated stocks.
    # Neither cointegrates. JPM/NVDA also shows the ADF over-rejection: it
    # passes adfuller at 0.021 and fails coint() at 0.072.
    same_sector = cointegration("MSFT", "AAPL", "2015-01-01", "2018-12-31", prices, universe)
    cross_sector = cointegration("JPM", "NVDA", "2015-01-01", "2018-12-31", prices, universe)

    print(same_sector)
    print(cross_sector)