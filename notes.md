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

- GOOG excluded: second share class of GOOGL, statsmodels raises a
  CollinearityWarning on the pair
- GEV excluded: 441 trading days, below the 650 minimum
- 54 stocks. Pass rates changed by under 0.4pp per window across the 56, 55
  and 54 stock versions
- BRK-B contains a hyphen, so pairs are deduplicated with `stockX < stockY`
  rather than by splitting `pair_id`

## Direction

EG is asymmetric, so the screen and bootstrap test both directions (2,862
ordered pairs). The two directions of a pair are near duplicates, so the
outcome analysis keeps the alphabetical direction only: 36,578 pair-years
become 18,289.

## Engine validation

49 seeds, n = 1000, true beta 2.0, true half life 10.

| | Mean | sd | Range |
|---|---|---|---|
| Beta | 1.992 | 0.039 | |
| Half life | 9.618 | 1.578 | 6.5-14.1 |

- Half life is biased low, consistent with finite sample bias in AR estimation
- 49/49 true pairs detected, mean p = 1.55e-05
- 1,000 independent random walks: 5.5% false positives (se 0.7pp); p-values
  mean 0.5066, sd 0.2900 against 0.5 and 0.2887 for a uniform
- Test tolerances set from the measured spread (beta 0.15, half life 5)

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

## Bootstrap null

2015-17 formation window, 20 replications per block length.

| Block | Mean | sd | q05 | q95 |
|---|---|---|---|---|
| 10 | 7.15% | 3.54pp | 2.90% | 13.94% |
| 21 | 6.16% | 4.01pp | 1.89% | 11.95% |

- All observed pass rates are inside the block 10 range; 2025 is above the
  block 21 q95
- A 4 year window (2015-18) gave 6.55% and 6.32%. The window must match the
  screen's 3 years, since EG size depends on sample length
- Under independence a 7% rate over 2,862 tests has sd of about 0.5pp. The
  measured sd corresponds to roughly 36-52 independent tests
- With 20 replications, q05 and q95 are approximate
- Politis-White-Patton block length averages 1.69 days. Not used, since it
  targets linear dependence rather than volatility clustering

## Outcome

- First opening only, one outcome per pair-year
- Opening day is not checked for divergence
- A day that crosses zero and lands beyond |4| counts as diverged
- `spread_mean` is not subtracted from z; it is ~0 with an intercept fitted
  and removing it left every count unchanged
- Positions open at year end are kept as unresolved

Totals (deduplicated): 18,289 pair-years, 1,808 never opened (9.9%), 16,481
opened: 8,061 diverged (48.9%), 4,535 reverted (27.5%), 3,885 unresolved
(23.6%). Ratio 1.78.

Counting every opening instead (both directions) gave a ratio of 1.70, with
the same 10.06% never opened.

Diverged and reverted shares both rise as spread vol rises, so the ratio is
used instead of either share. Shares against VIX: diverged rho -0.269
(p = 0.374), reverted +0.593 (p = 0.033).

## Decile sort

| Decile | Mean p | Opened | Diverged | Reverted | Ratio |
|---|---|---|---|---|---|
| 1 | 0.0426 | 1800 | 1023 | 601 | 1.70 |
| 2 | 0.1372 | 1728 | 943 | 543 | 1.74 |
| 3 | 0.2357 | 1683 | 858 | 550 | 1.56 |
| 4 | 0.3314 | 1669 | 853 | 483 | 1.77 |
| 5 | 0.4352 | 1640 | 749 | 496 | 1.51 |
| 6 | 0.5364 | 1605 | 733 | 443 | 1.65 |
| 7 | 0.6449 | 1534 | 654 | 423 | 1.55 |
| 8 | 0.7556 | 1542 | 635 | 395 | 1.61 |
| 9 | 0.8662 | 1549 | 661 | 338 | 1.96 |
| 10 | 0.9622 | 1731 | 952 | 263 | 3.62 |

## Spread volatility

| Decile | Open rate | Resolved | Vol mean | Vol median |
|---|---|---|---|---|
| 1 | 0.979 | 0.902 | 1.85 | 1.59 |
| 2 | 0.945 | 0.860 | 1.65 | 1.44 |
| 3 | 0.921 | 0.837 | 1.63 | 1.30 |
| 4 | 0.914 | 0.801 | 1.59 | 1.16 |
| 5 | 0.897 | 0.759 | 1.29 | 1.11 |
| 6 | 0.878 | 0.733 | 1.19 | 1.00 |
| 7 | 0.840 | 0.702 | 1.12 | 0.92 |
| 8 | 0.843 | 0.668 | 1.04 | 0.87 |
| 9 | 0.848 | 0.645 | 0.92 | 0.75 |
| 10 | 0.946 | 0.702 | 0.97 | 0.76 |

- Pair-level Spearman, p-value vs spread vol: -0.412
- Mechanism: small p-value, tight formation fit, small `spread_std`, larger z
  out of sample
- Decile 10 opens often with low spread vol. Spread vol is measured around the
  test year mean, so a spread drifting away from zero opens without scoring as
  volatile. Not tested

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

- Ratio vs VIX: Spearman -0.654 (p = 0.015). Counting every opening gave
  -0.643 (p = 0.018)
- Spread vol vs VIX: +0.203 (p = 0.505)
- Spearman used because 2020 and 2022 are far above the other years on VIX
- Two groups rather than a gradient: nine years at 1.05-1.89, four at
  2.90-4.58 (2013, 2017, 2021, 2024)
- Possible mechanism: spreads keep trending in calm markets. Not tested
- VIX download ends 2026-01-01 (end is exclusive); prices end 2025-12-30


