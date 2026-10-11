# Notes

## Universe

Top 8 by market cap in each of the 7 largest GICS sectors by aggregate cap.

| Sector | Aggregate cap |
|---|---|
| Information Technology | 24.99tn |
| Communication Services | 11.49tn |
| Financials | 8.87tn |
| Consumer Discretionary | 6.93tn |
| Health Care | 6.49tn |
| Industrials | 5.80tn |
| Consumer Staples | 3.50tn |
| Energy (8th, not included) | 2.35tn |

49% gap between 7th and 8th.

- GOOG excluded: second share class of GOOGL, statsmodels raises a
  CollinearityWarning on the pair
- GEV excluded: 441 trading days, below the 650 minimum
- 54 stocks. Pass rates changed by under 0.4pp per window across the 56, 55
  and 54 stock versions
- BRK-B contains a hyphen, so pairs are deduplicated with `stockX < stockY`
  rather than by splitting `pair_id`
- `universe.py` reads current index membership and current market caps, so it
  does not rebuild the same 54 stocks at a later date. `data/universe.csv` is
  committed to pin it

## Direction

EG is asymmetric, so the screen and bootstrap test both directions: 2,862
ordered pairs. The two directions of a pair are near duplicates, so the
outcome analysis keeps the alphabetical direction only. 36,578 pair-years
become 18,289.

36,578, not 2,862 x 13 = 37,206. Three stocks list after the start of the
sample and fall below the 650 observation minimum in the early formation
windows:

| Formation window | Short | Ordered pairs skipped |
|---|---|---|
| 2010-12 | ABBV, META, TSLA | 2862 - 51x50 = 312 |
| 2011-13 | ABBV, META | 2862 - 52x51 = 210 |
| 2012-14 | ABBV | 2862 - 53x52 = 106 |

628 in total. Pairs are not double counted when two short stocks meet, hence
the product rather than 106 per stock. `screen.py` prints the skip count per
window and these are the three non-zero ones.

## Engine validation

49 seeds, n = 1000, true beta 2.0, true half life 10.

| | Mean | sd | Range |
|---|---|---|---|
| Beta | 1.992 | 0.039 | |
| Half life | 9.618 | 1.578 | 6.5-14.1 |

- Half life sits low across the whole set. Consistent with finite sample bias
  in AR estimation
- 49/49 true pairs detected, mean p = 1.55e-05
- 1,000 independent random walks: 55 false positives, 5.5% against a nominal
  5%. Standard error at this sample size is 0.7pp
- p-values mean 0.5066 against 0.5 expected, sd 0.2900 against 0.2887. Uniform,
  so the test is calibrated across the range and not only at the threshold
- Tolerances come from the measured spread: beta 0.15, half life 5. A half
  life tolerance of 0.2 cleared seed 1 and failed on seed 2 at 12.74
- The half life tolerance is wide. At 3 sd it catches a broken estimator, not
  a mildly biased one

## Screen pass rates (p < 0.05)

| Test year | Pass rate |
|---|---|
| 2013 | 4.51% |
| 2014 | 3.54% |
| 2015 | 4.64% |
| 2016 | 6.64% |
| 2017 | 5.03% |
| 2018 | 5.66% |
| 2019 | 3.70% |
| 2020 | 5.84% |
| 2021 | 7.16% |
| 2022 | 7.79% |
| 2023 | 9.57% |
| 2024 | 8.84% |
| 2025 | 13.07% |

2013-19 averages 4.82%, then climbs to 13.07%.

First guess was post-COVID common factor co-movement inflating the count. That
would predict worse outcomes in the later years. It does not hold. See the
year table below: 2021 and 2024 are bad, 2022, 2023 and 2025 are not.

## Bootstrap null

2015-17 formation window, 20 replications per block length.

| Block | Mean | sd | q05 | q95 |
|---|---|---|---|---|
| 10 | 7.15% | 3.54pp | 2.90% | 13.94% |
| 21 | 6.16% | 4.01pp | 1.89% | 11.95% |

- The window is taken from `rolling_windows(3)` so it is the same length as
  the windows it is compared against. EG size depends on sample length
- A 4 year window (2015-18) gives 6.55% and 6.32%. Not comparable to a screen
  run on 3 years, so it is not the one quoted
- All observed pass rates sit inside the block 10 range. 2025 is above the
  block 21 q95
- Under independence a 7% rate over 2,862 tests has sd of about 0.5pp. The
  measured 3.5-4.0pp corresponds to roughly 36-52 independent tests. 2,862
  pairs from 54 stocks carry far less information than the count suggests
- 20 replications, so q05 and q95 are approximate
- Null estimated from the resample pool starting 2013, where all 54 stocks
  trade. `np.log(prices).diff().dropna()` drops any row with a gap, so the
  pool begins at the last listing date
- Politis-White-Patton block length averages 1.69 days, reflecting almost no
  linear autocorrelation in daily mega cap returns. Printed as a diagnostic
  but not used: PPW targets estimating a mean under linear dependence, and
  what matters here is whether volatility clustering inflates test size

## Outcome

- First opening only, one outcome per pair-year
- Opening day is not checked for divergence
- A day that crosses zero and lands beyond |4| counts as diverged
- `spread_mean` is not subtracted from z. It is ~0 with an intercept fitted,
  and removing it left every count unchanged
- Positions open at year end are kept as unresolved

Deduplicated, one direction per pair: 18,289 pair-years, 1,808 never opened
(9.9%), 16,481 opened. 8,061 diverged (48.9%), 4,535 reverted (27.5%), 3,885
unresolved (23.6%). Ratio 1.78.

Both directions: 36,578 pair-years, 3,678 never opened (10.06%), 32,900
opened. 16,209 diverged, 9,038 reverted, 7,653 unresolved. Ratio 1.79.

Deduplicating moves the headline ratio from 1.79 to 1.78, so it is not what
produces the result. It halves the apparent sample, which is the reason for
doing it.

Diverged and reverted shares both rise as spread vol rises, so the ratio is
used rather than either share. Shares against VIX: diverged rho -0.269
(p = 0.374), reverted +0.593 (p = 0.033).

## Decile sort

| Decile | Mean p | Opened | Diverged | Reverted | Ratio |
|---|---|---|---|---|---|
| 1 | 0.0426 | 1800 | 1023 | 601 | 1.7022 |
| 2 | 0.1372 | 1728 | 943 | 543 | 1.7366 |
| 3 | 0.2357 | 1683 | 858 | 550 | 1.5600 |
| 4 | 0.3314 | 1669 | 853 | 483 | 1.7660 |
| 5 | 0.4352 | 1640 | 749 | 496 | 1.5101 |
| 6 | 0.5364 | 1605 | 733 | 443 | 1.6546 |
| 7 | 0.6449 | 1534 | 654 | 423 | 1.5461 |
| 8 | 0.7556 | 1542 | 635 | 395 | 1.6076 |
| 9 | 0.8662 | 1549 | 661 | 338 | 1.9556 |
| 10 | 0.9622 | 1731 | 952 | 263 | 3.6198 |

Columns cross-foot to the headline totals: 16,481 opened, 8,061 diverged,
4,535 reverted.

Deciles 1 to 8 run 1.51 to 1.77 with no ordering. The spread across those
eight is smaller than the gap from decile 8 to decile 9, and far smaller than
the gap to decile 10. The p-value separates the worst tenth and nothing else.

Reverted counts trend down from 601 to 263 across the range. Diverged counts
fall to 635 at decile 8 and then rise to 952. The ratio is flat across 1 to 8
because both move together, not because nothing happens.

## Spread volatility

| Decile | Open rate | Resolved | Vol mean | Vol median |
|---|---|---|---|---|
| 1 | 0.9788 | 0.9022 | 1.8542 | 1.5915 |
| 2 | 0.9453 | 0.8600 | 1.6488 | 1.4443 |
| 3 | 0.9207 | 0.8366 | 1.6344 | 1.2978 |
| 4 | 0.9135 | 0.8005 | 1.5883 | 1.1577 |
| 5 | 0.8972 | 0.7591 | 1.2927 | 1.1061 |
| 6 | 0.8780 | 0.7327 | 1.1945 | 1.0011 |
| 7 | 0.8401 | 0.7021 | 1.1171 | 0.9238 |
| 8 | 0.8431 | 0.6680 | 1.0388 | 0.8652 |
| 9 | 0.8478 | 0.6449 | 0.9235 | 0.7544 |
| 10 | 0.9464 | 0.7019 | 0.9664 | 0.7640 |

- Pair level Spearman, p-value against spread vol: -0.412
- Mechanism: small p-value, tight formation fit, small `spread_std`, larger z
  out of sample. Resolved share falls monotonically from 90.2% at decile 1 to
  64.5% at decile 9, which is what that predicts. Open rate falls from 97.9%
  to 84.0% by decile 7 and then flattens
- Decile 10 breaks the monotonicity. It opens at 94.6% on the lowest spread
  vol in the table. Spread vol is measured around the test year mean, so a
  spread drifting steadily away from zero opens without scoring as volatile.
  Not tested

## Sector linkage

| | Opened | Diverged | Reverted | Resolved | Ratio |
|---|---|---|---|---|---|
| Same sector | 2108 | 1009 | 577 | 0.7524 | 1.7487 |
| Cross sector | 14373 | 7052 | 3958 | 0.7660 | 1.7817 |

Same sector is 12.8% of opened pair-years. The gap is 0.03 on the ratio and
1.4pp on the resolved share. No separation. Two semiconductor firms behave
like a bank paired with a soft drinks company.

Sub-industry is not cut. 54 stocks leave too few same sub-industry pairs for
the cell counts to mean anything.

## Volatility regime

| Year | Mean VIX | Ratio | Spread vol | Opened |
|---|---|---|---|---|
| 2013 | 14.23 | 4.58 | 1.22 | 1146 |
| 2014 | 14.17 | 1.89 | 1.05 | 1165 |
| 2015 | 16.67 | 1.25 | 1.40 | 1263 |
| 2016 | 15.83 | 1.82 | 1.31 | 1251 |
| 2017 | 11.09 | 2.90 | 1.23 | 1318 |
| 2018 | 16.64 | 1.45 | 1.44 | 1373 |
| 2019 | 15.39 | 1.61 | 1.19 | 1325 |
| 2020 | 29.25 | 1.05 | 2.23 | 1381 |
| 2021 | 19.66 | 2.98 | 1.18 | 1292 |
| 2022 | 25.62 | 1.19 | 1.18 | 1293 |
| 2023 | 16.87 | 1.14 | 0.88 | 1021 |
| 2024 | 15.61 | 3.54 | 1.41 | 1320 |
| 2025 | 18.98 | 1.49 | 1.47 | 1333 |

- Ratio against mean VIX: Spearman -0.654 (p = 0.015)
- Spread vol against mean VIX: +0.203 (p = 0.505). Spread vol does not move
  with VIX, so this is not the decile result at the yearly level
- Spearman rather than Pearson. 2020 at 29.25 and 2022 at 25.62 sit well above
  the other eleven years and drag a linear fit without being extreme in rank
- At n = 13 a correlation needs to be around 0.55 to reach p < 0.05
- Two groups rather than a gradient. Nine years at 1.05 to 1.89, four at 2.90
  to 4.58: 2013, 2017, 2021, 2024. Nothing between 1.89 and 2.90
- 2021 is the awkward one. VIX 19.66, third highest in the sample, and still a
  ratio of 2.98. The relationship holds in rank terms with that exception, not
  without it
- 2017 is the cleanest case the other way. Lowest VIX in the sample at 11.09
  and 2.90 divergences per reversion, against 1.05 in 2020 at VIX 29.25
- Possible mechanism: spreads keep trending in calm markets and the move that
  opens a position keeps going. Not tested
- VIX is downloaded to 2026-01-01, exclusive, so it keeps 31 December 2025.
  Prices end 30 December 2025

## Open

- Whether decile 10 opens on drift rather than volatility
- More bootstrap replications for tighter error bars
- Only 3 year formation tested, only one set of barriers
- Survivorship bias. Current index membership and current market caps, run
  back to 2010. Fixing it needs point in time constituent data