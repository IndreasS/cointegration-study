"""
Trades one pair's frozen spread over a test window.

Enter at |z| >= 2, exit on reversion past the mean or on a 4 sd stop. A
re-entry gate stops the strategy thrashing a spread that stays outside the band.

Three fixes to the version I started from:

- Overshoot. z_captured is sign(entry_z) * (entry_z - exit_z). Using
  abs(entry_z) - abs(exit_z) understates profit when the spread overshoots the
  mean before the exit fires.
- Negative beta. Entry capital uses absolute values, otherwise y + beta*x
  collapses toward zero and the return explodes.
- Open positions marked to market at the window end rather than discarded.
  Discarding deletes the losses the strategy should be judged on.

Stop fills capped at the stop level. Real gap fills can be worse.
"""

import numpy as np
import pandas as pd


def simulate_trades(z, spread_std, x_price, y_price, beta,
                    entry=2.0, exit=0.0, stop=4.0, cost=0.001, slippage=0.0005):
    """
    z          : z-score of the frozen spread over the test window
    spread_std : frozen formation std, converts z captured into price terms
    cost       : round trip cost as a fraction (0.001 = 10bp)

    Returns (trade_return, reason) tuples. reason is reverted, stopped or marked.
    """
    trades = []
    in_trade = False
    entry_z = None
    entry_index = None
    can_enter = True

    for t in range(len(z)):
        zt = z.iloc[t]

        if not in_trade:
            if can_enter and abs(zt) >= entry:
                in_trade = True
                entry_z = zt
                entry_index = t
                can_enter = False
            elif abs(zt) < entry:
                can_enter = True            # spread back in the band, re-arm

        else:
            # entered high means we shorted the spread and profit as it falls
            if entry_z > 0:
                reverted = zt <= exit
            else:
                reverted = zt >= exit

            stopped = abs(zt) >= stop

            if reverted or stopped:
                exit_z = np.sign(zt) * stop if stopped else zt

                z_captured = np.sign(entry_z) * (entry_z - exit_z)
                entry_capital = (abs(y_price.iloc[entry_index])
                                 + abs(beta) * abs(x_price.iloc[entry_index]))

                trade_return = (z_captured * spread_std) / entry_capital - cost - slippage
                trades.append((trade_return, "stopped" if stopped else "reverted"))

                in_trade, entry_z, entry_index = False, None, None

    if in_trade:
        exit_z = z.iloc[-1]
        z_captured = np.sign(entry_z) * (entry_z - exit_z)
        entry_capital = (abs(y_price.iloc[entry_index])
                         + abs(beta) * abs(x_price.iloc[entry_index]))

        trade_return = (z_captured * spread_std) / entry_capital - cost - slippage
        trades.append((trade_return, "marked"))

    return trades


if __name__ == "__main__":
    flat = lambda n: pd.Series(n * [100.0])

    z1 = pd.Series([0, 2.5, 1.0, 0.0, -2.5, 0.0])       # short, exits at mean
    z2 = pd.Series([0, 2.5, 2.0, 2.2])                  # still open at the end
    z3 = pd.Series([0, 2.5, 1.0, 0.0, -1.0, -2.5, 0.0]) # short then long
    z4 = pd.Series([0, 2.5, 3.0, 4.5])                  # stops out

    print(simulate_trades(z1, 1, flat(6), flat(6), 1))   # 0.011, reverted
    print(simulate_trades(z2, 1, flat(4), flat(4), 1))   # ~0, marked
    print(simulate_trades(z3, 1, flat(7), flat(7), 1))   # two trades, 0.011 each
    print(simulate_trades(z4, 1, flat(4), flat(4), 1))   # -0.009, stopped