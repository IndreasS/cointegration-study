"""
Engle-Granger cointegration test for one ordered pair.

EG is asymmetric, so y-on-x and x-on-y are separate tests. The screen runs both.

Only the coint() p-value is kept. I had adfuller on the same residual for a
while as a comparison, but it rejects too often here: beta was fitted on the
same data the residual is tested on, which makes the residual look more
stationary than it is. coint() uses the harsher EG critical values, so it is
the one to trust.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint

MIN_OBS = 650


def cointegration(stockX, stockY, start, end, prices, universe):
    """
    Regress stockY on stockX over [start, end] and test the residual.
    universe indexed by Symbol. Returns None if the window is too short.
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
    spread_std = spread.std()

    p_value_coint = coint(y, x)[1]

    # half life: regress the change in the spread on its lagged level.
    # lam is the reversion speed, negative for a mean-reverting series.
    lagged = spread.shift(1).dropna()
    change = spread.diff().dropna()
    lam = sm.OLS(change, sm.add_constant(lagged)).fit().params.iloc[1]
    half_life = -np.log(2) / lam

    same_sector = universe.loc[stockX, "Sector"] == universe.loc[stockY, "Sector"]

    # alphabetical, so both directions of a pair share an id
    pair_id = "-".join(sorted([stockX, stockY]))

    return {
        "stockX": stockX,
        "stockY": stockY,
        "alpha": alpha,
        "beta": beta,
        "spread_std": spread_std,
        "p_value_coint": p_value_coint,
        "halflife": half_life,
        "pair_observations": n_obs,
        "same_sector": same_sector,
        "pair_id": pair_id,
    }


if __name__ == "__main__":
    universe = pd.read_csv("data/universe.csv").set_index("Symbol")
    prices = pd.read_parquet("data/prices.parquet")

    linked = cointegration("MSFT", "AAPL", "2015-01-01", "2018-12-31", prices, universe)
    unrelated = cointegration("JPM", "NVDA", "2015-01-01", "2018-12-31", prices, universe)

    print(linked)
    print(unrelated)
