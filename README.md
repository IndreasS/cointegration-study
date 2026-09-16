# Does the cointegration p-value pick pairs that revert?

Pairs are usually selected with an Engle-Granger test, with a smaller p-value
taken to mean a better pair. This study tests that out of sample.

## Data

- 54 S&P 500 stocks: top 8 by market cap in each of the 7 largest GICS sectors
  (GOOG excluded as a second share class of GOOGL, GEV for short history)
- 13 rolling windows: 3 year formation, 1 year test (test years 2013-2025)
- Both directions of each pair are screened (2,862 ordered pairs per window).
  The outcome analysis keeps one direction per pair: 18,289 pair-years
- Alpha, beta and spread std are fitted on formation and held fixed in the test
  year

## Outcome

In the test year, a spread opens the first time |z| reaches 2. It is then:

- **reverted** if z crosses zero
- **diverged** if |z| reaches 4 first
- **unresolved** if neither happens by year end

The measure is diverged per reversion. Overall: 16,481 opened, 8,061 diverged,
4,535 reverted, 3,885 unresolved, a ratio of 1.78.

## Results

### 1. The screen's pass rate is within noise

A block bootstrap resamples returns with the same blocks for every stock, which
removes cointegration but keeps cross-sectional correlation and volatility
clustering. On the 2015-17 formation window (20 replications each):

| Block length | Mean pass rate | sd | 5th-95th percentile |
|---|---|---|---|
| 10 days | 7.15% | 3.54pp | 2.9%-13.9% |
| 21 days | 6.16% | 4.01pp | 1.9%-12.0% |

Observed pass rates at p < 0.05 range from 3.54% to 13.07%. All are inside the
block 10 range.

### 2. The p-value does not rank pairs below decile 9

Deciles are formed within each test year.

![p-value deciles](figures/pvalue_deciles.png)

| Decile | Mean p | Opened | Diverged | Reverted | Ratio |
|---|---|---|---|---|---|
| 1 | 0.043 | 1,800 | 1,023 | 601 | 1.70 |
| 2 | 0.137 | 1,728 | 943 | 543 | 1.74 |
| 3 | 0.236 | 1,683 | 858 | 550 | 1.56 |
| 4 | 0.331 | 1,669 | 853 | 483 | 1.77 |
| 5 | 0.435 | 1,640 | 749 | 496 | 1.51 |
| 6 | 0.536 | 1,605 | 733 | 443 | 1.65 |
| 7 | 0.645 | 1,534 | 654 | 423 | 1.55 |
| 8 | 0.756 | 1,542 | 635 | 395 | 1.61 |
| 9 | 0.866 | 1,549 | 661 | 338 | 1.96 |
| 10 | 0.962 | 1,731 | 952 | 263 | 3.62 |

The ratio has no ordering across deciles 1-8.

### 3. The p-value tracks spread volatility

| Decile | Open rate | Resolved share | Mean spread vol |
|---|---|---|---|
| 1 | 97.9% | 90.2% | 1.85 |
| 5 | 89.7% | 75.9% | 1.29 |
| 8 | 84.3% | 66.8% | 1.04 |
| 10 | 94.6% | 70.2% | 0.97 |

Spread vol is the standard deviation of the test year z-score. Pair-level
Spearman correlation with the p-value: -0.41.

A small p-value comes from a tight formation fit, so a small `spread_std`. As
the denominator of z, that makes out-of-sample moves larger in z units. Low
p-value pairs therefore open and resolve more often, in both directions, which
is why the counts change across deciles and the ratio does not.

### 4. The ratio is higher in low volatility years

![VIX regime](figures/vix_regime.png)

| Against mean VIX (n = 13 years) | Spearman rho | p |
|---|---|---|
| Diverged per reversion | -0.654 | 0.015 |
| Mean spread vol | +0.203 | 0.505 |

Spread vol does not move with VIX, so this is not the result in 3 at the yearly
level. Year-by-year figures are in `notes.md`.

## Validation

On synthetic data the engine recovers a hedge ratio of 2.0 to within 0.4%
across 49 seeds and detects every true pair. On 1,000 independent random walks
the false positive rate is 5.5% and p-values are approximately uniform.

## Running it

```bash
pip install -r requirements.txt

python universe.py      # stock universe
python prices.py        # adjusted closes
python test_coint.py    # engine validation, ~20 min
python screen.py        # screen, ~30 min
python bootstrap.py     # null distribution, ~1 hr
python labels.py        # outcome per pair-year
python analysis.py      # tables and figures
```

## Limitations

- Survivorship bias: current index members and caps are used back to 2010
- The VIX result rests on 13 years
- No standard errors on the decile table, since pair-years share stocks and years
- The null is estimated on one window with 20 replications
- Barrier levels (2 and 4) and formation length (3 years) are not varied
- Prices end on 30 December 2025
