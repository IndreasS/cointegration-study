# Working notes

## Universe

Seven largest GICS sectors by aggregate S&P 500 market cap, top 8 by cap in each.

| Sector | Aggregate cap |
|---|---|
| Information Technology | 24.99tn |
| Communication Services | 11.49tn |
| Financials | 8.87tn |
| Consumer Discretionary | 6.93tn |
| Health Care | 6.49tn |
| Industrials | 5.80tn |
| Consumer Staples | 3.50tn |
| Energy (8th, excluded) | 2.35tn |

49% gap between 7th and 8th.

Exclusions:
- GOOG. Second share class of GOOGL. statsmodels raises a CollinearityWarning
  on this pair in both directions. Also explains GOOGL/GOOG coming back at
  p = 0.092 over 2015-18 despite being the most obviously linked pair.
- GEV. Spun off March 2024, 441 trading days against a 650 minimum.

54 stocks, 2,862 ordered pairs.

Pass rates moved less than 0.4pp per window across the 56, 55 and 54 stock
versions.

## Direction

EG is asymmetric, so y-on-x and x-on-y are separate tests. Running both gives
2,862 ordered pairs rather than 1,431, and 2,862 is the multiple testing
denominator.

The two orientations are near perfectly dependent. One relationship looked at
twice, not two independent tests. Weakens the dependency assumption behind BH.

## Engine validation

49 seeds, n = 1000, true beta 2.0, true half life 10.

| | Mean | sd | Range |
|---|---|---|---|
| Beta | 1.992 | 0.039 | |
| Half life | 9.618 | 1.578 | 6.5 to 14.1 |

Half life sits low across the whole set. Consistent with finite sample bias in
AR estimation.

True pairs detected 49/49, mean p = 1.55e-05.

Independent random walks, n = 1000: 55 false positives, so 5.5% against a
nominal 5%. The standard error at this sample size is 0.7pp.

p-values came out mean 0.5066 against 0.5 expected, sd 0.2900 against 0.2887.
That is uniform, so the test is calibrated across the whole range and not just
at the 5% threshold.

First half life tolerance of 0.2 cleared seed 1 and failed on seed 2 at 12.74.
Set tolerances from the measured distributions after that.

## Screen

3 year formation, 1 year test, 13 windows.

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
would predict worse economics in the later years. It does not hold. See the
stop ratios below.

## Bootstrap null

20 replications at each of block 10 and 21, on the 2015-17 window.

| Block | Mean pass rate | sd |
|---|---|---|
| 10 | 6.55% | 2.40pp |
| 21 | 6.32% | 4.81pp |

Null is about 6.4%, not the 5.5% from independent random walks. The test is
oversized on data with real dependence structure.

Makes 2013-19 stronger: 4.82% against 6.4% means real pairs cointegrate less
often than noise with the same dependence structure. Shrinks 2025 from 2.6x
nominal to 2.0x the measured null.

Block 21 sd of 4.81pp is large. Longer blocks mean fewer distinct resamples.

Null estimated on 2013-25, where all 54 constituents trade. Earlier would need
dropping ABBV or letting non-contiguous series into the resample.

## Labelling

36,578 pair-years, none skipped. Persistence 32.88%. 10.06% never traded.

Off-by-one in the inherited crossing count: `(signs != signs.shift(1)).sum()`
always counts position 0, because shift puts a NaN there and `x != NaN` is
True. So "crossings >= 2" was testing "crossings >= 1". I have not run the
buggy version on this universe, so I cannot say how many labels it flipped.

## How trades closed

47,130 trades: 12,733 reverted (27%), 21,672 stopped (46%), 12,725 marked at
the window end (27%).

A pair that passes the screen and diverges to 2 sd is 1.7 times more likely to
blow through a 4 sd stop than to come back.

The version I started from discarded open positions at the window end. That
deletes 27% of outcomes, and mostly the bad ones.

## Decile sort

Persistence is not monotone in the p-value. Inverted U.

| Decile | Mean p | Persistence | Median return | Stop/revert |
|---|---|---|---|---|
| 1 | 0.043 | 25.8% | -0.0245 | 1.52 |
| 5 | 0.447 | 39.3% | -0.0238 | 1.42 |
| 7 | 0.659 | 42.2% | -0.0242 | 1.51 |
| 10 | 0.968 | 13.6% | -0.0587 | 3.88 |

Pairs at p around 0.5 to 0.7 persist at 42% against 26% for the most
significant. Every decile loses money on median.

The only place the p-value carries information is decile 10, at 3.9 stops per
reversion against about 1.5 elsewhere.

Possible explanation. The label is `crossings >= 2 AND max|z| < 4`. A very
significant p-value means a tight spread relative to the formation std, so out
of sample it may barely move and cross zero only once. Decile 10 spreads wander
far enough to breach 4 sd. Either way the label fails. So it may be picking up
moderate spread volatility rather than mean reversion. Not tested.

## Sector linkage

| | Persistence | Median return | Stop/revert |
|---|---|---|---|
| Cross sector | 32.83% | -0.0342 | 1.71 |
| Same sector | 33.19% | -0.0276 | 1.68 |
| Different sub-industry | 32.88% | -0.0333 | 1.70 |
| Same sub-industry (n=822) | 32.97% | -0.0277 | 1.68 |

No difference. Two semiconductor firms behave like a bank paired with a soft
drinks company.

## Volatility regime

Stop/revert by year: 3.84, 1.57, 1.52, 1.49, 3.30, 1.49, 1.42, 1.21, 2.70,
1.20, 1.12, 3.22, 1.43.

Four bad years: 2013, 2017, 2021, 2024. Scattered rather than concentrated
after 2020. frac_losing tracks the stop ratio, at 70-77% in the bad years
against 48-56% elsewhere.

Against mean VIX:

| Metric | Pearson | Spearman |
|---|---|---|
| stop/revert | -0.484 (p=0.094) | -0.643 (p=0.018) |
| frac losing | -0.504 (p=0.079) | -0.599 (p=0.031) |
| median return | +0.457 (p=0.116) | +0.500 (p=0.082) |
| persistence | +0.188 (p=0.539) | +0.225 (p=0.459) |

The bad years are the calm ones. 2017, lowest VIX in the sample at 11.1, gave
3.3 stops per reversion. 2020 at VIX 29.3 gave 1.21.

Spearman beats Pearson because most years sit between 11 and 20 while 2020 is
at 29.3 and 2022 at 25.6. Those two drag a linear fit but are not outliers in
rank terms. At n=13 the Spearman figure is the one to quote.

The scatter is two clusters rather than a gradient: ten years at 1.1-1.6, four
at 2.7-3.8, nothing between. 2021 is the exception at VIX 19.7 and still bad.

Possible mechanism. Calm markets trend, so a spread that opens keeps opening
until it hits the stop. Volatile markets shake spreads back across zero.

Persistence shows no VIX relationship while the trading outcomes do.

## Open

- Whether the persistence label is confounded by spread volatility
- More bootstrap replications for tighter error bars
- Only 3 year formation tested
- Survivorship bias. The universe uses current index membership and current
  market caps, then runs back to 2010. Fixing it needs point in time
  constituent data. Biases toward survivors.