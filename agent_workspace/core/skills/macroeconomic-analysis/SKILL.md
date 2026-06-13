---
name: macroeconomic-analysis
description: Economic indicator interpretation, yield curve analysis, central bank policy assessment, cycle positioning, FX and commodity outlook
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Macroeconomic Analysis

Systematic workflow for top-down macroeconomic analysis, covering indicators, central banks, yield curves, and cycle positioning.

## When to Use

- Assessing the current state of the economic cycle
- Forecasting GDP, inflation, and interest rates
- Analysing central bank policy and forward guidance
- Informing asset allocation and sector rotation decisions
- Building a macro framework for country or regional analysis

## Key Economic Indicators

### Growth Indicators
| Indicator | Frequency | Source | What It Tells Us |
|-----------|-----------|--------|-----------------|
| Real GDP | Quarterly | BEA | Broadest measure of economic output |
| Industrial Production | Monthly | Fed | Manufacturing, mining, utilities output |
| ISM Manufacturing PMI | Monthly | ISM | > 50 = expansion; < 50 = contraction |
| ISM Services PMI | Monthly | ISM | Services sector activity (larger share of GDP) |
| Retail Sales | Monthly | Census Bureau | Consumer spending health |
| Durable Goods Orders | Monthly | Census Bureau | Business investment proxy |
| Housing Starts | Monthly | Census Bureau | Construction sector health |

### Labour Market Indicators
| Indicator | Frequency | Source | What It Tells Us |
|-----------|-----------|--------|-----------------|
| Non-Farm Payrolls | Monthly | BLS | Net job creation (most watched) |
| Unemployment Rate (U-3) | Monthly | BLS | Headline unemployment |
| U-6 Underemployment | Monthly | BLS | Broader measure incl. part-time for economic reasons |
| Initial Jobless Claims | Weekly | DOL | Timeliest labour market signal |
| JOLTS Job Openings | Monthly | BLS | Labour demand strength |
| Average Hourly Earnings | Monthly | BLS | Wage growth (wage-price spiral risk) |

### Inflation Indicators
| Indicator | Frequency | Source | What It Tells Us |
|-----------|-----------|--------|-----------------|
| CPI (Headline + Core) | Monthly | BLS | Consumer price inflation |
| PPI (Final Demand) | Monthly | BLS | Pipeline inflation pressure |
| PCE (Headline + Core) | Monthly | BEA | Fed's preferred inflation gauge |
| 5Y5Y Forward Breakeven | Daily | Market | Long-term inflation expectations |
| Univ. of Michigan Inflation Exp. | Monthly | Survey | Consumer inflation expectations |
| ISM Prices Paid | Monthly | ISM | Business input cost pressure |

### Monetary & Financial Conditions
| Indicator | Frequency | Source | What It Tells Us |
|-----------|-----------|--------|-----------------|
| Fed Funds Rate | Real-time | Fed | Policy rate |
| SOFR/OIS Rates | Daily | Market | Market-implied rate expectations |
| 10Y-2Y Treasury Spread | Daily | Market | Yield curve slope / recession signal |
| Chicago Fed NFCI | Weekly | Chicago Fed | Broad financial conditions index |
| High Yield Spread | Daily | Market | Credit market stress gauge |
| TIPS Breakevens | Daily | Market | Market-implied inflation expectations |

## Yield Curve Analysis

### Key Spreads
- **2Y-10Y**: Most watched; inversion = recession signal (lead time 6-24 months)
- **3M-10Y**: Near-term vs long-term rates; preferred by some researchers
- **Fed Funds - 2Y**: Near-term policy expectations; steep when market expects cuts

### Decomposition
$$y_t^{(n)} = \underbrace{\frac{1}{n} \sum_{i=0}^{n-1} \mathbb{E}_t[r_{t+i}]}_{\text{Expectations component}} + \underbrace{tp_t^{(n)}}_{\text{Term premium}}$$

Term premium estimated via ACM (Adrian-Crump-Moench) or KW (Kim-Wright) models.

### Curve Regimes
| Curve Shape | Spread | Interpretation | Historical Context |
|-------------|--------|----------------|-------------------|
| Steep (normal) | > 100bp | Expansion; growth + inflation expected | Early-mid cycle |
| Flattening | 50-100bp | Late cycle; market expects tightening | Late cycle |
| Flat | 0-50bp | Transition; high uncertainty | Cycle turning point |
| Inverted | < 0bp | Recession signal; market expects easing | Pre-recession |

## Central Bank Analysis

### Fed (FOMC)
- 8 scheduled meetings per year + emergency
- Key tools: Fed Funds rate, IOER, ON RRP, balance sheet (QE/QT)
- Communication: statement, dot plot (SEP), press conference, minutes (3 weeks later)

### ECB
- Governing Council meets every 6 weeks
- Key tools: deposit facility rate, MRO, APP/PEPP, TLTRO
- Communication: statement, press conference, accounts (4 weeks later)

### BOJ
- Monetary Policy Meetings 8x/year
- Key tools: policy rate, YCC (yield curve control), ETF purchases
- Communication: statement, outlook report, press conference, summary of opinions

### Policy Path Probability
Market-implied probabilities from Fed Funds futures:
$$\text{Prob(hike)} = \frac{\text{FFR implied} - \text{Current FFR}}{\text{25bp step}}$$

(Adjust for meeting timing, days in month, and binary outcomes.)

## Cycle Positioning Framework

| Phase | Growth | Inflation | Monetary Policy | Equities | Bonds | Commodities |
|-------|--------|-----------|----------------|----------|-------|-------------|
| Recovery | Below trend, accelerating | Low | Easing / accommodative | Cyclicals, small-cap, high beta | Short duration, HY | Industrial metals |
| Expansion | Above trend | Rising toward target | Neutral / beginning tightening | Broad market, growth + value | Neutral duration | Broad commodities |
| Late Cycle | Decelerating, above trend | Above target | Tightening | Quality, defensives, large-cap | Long duration, IG | Gold, energy |
| Recession | Contracting | Falling | Easing | Defensives, cash, gold | Long duration (duration) | Gold, cash |

## Reporting Standards

### One-Page Macro Dashboard
- GDP: latest print, forecast, trend arrow
- CPI / PCE: latest, core, trend, vs target
- Unemployment: rate, NFP momentum, wage growth
- Central bank: current rate, next meeting date, implied path
- Yield curve: 10Y level, 2s10s spread, 3M10Y spread
- VIX / credit spreads: current level and percentile
- USD index: level, 1m/3m change, trend
- Key risks: top 3 risks with probability assessment
