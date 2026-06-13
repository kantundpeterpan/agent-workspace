---
name: stock-valuation
description: DCF, DDM, residual income, comparable company and precedent transaction valuation methodologies
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Stock Valuation

Systematic workflow for valuing a company using DCF, DDM, residual income, and comparable analysis.

## When to Use

- Estimating intrinsic value of a stock
- Building a DCF model from financial statements
- Performing comparable company or precedent transaction analysis
- Generating a football-field valuation summary
- Sensitivity analysis on key assumptions

## DCF Valuation

### Step 1: Revenue Forecast (5-10 years)
- Analyse historical revenue growth rates (3-5 years)
- Consider addressing market size, market share trends
- Account for industry life cycle stage
- Segment revenue if business lines differ materially
- Conservative: trend toward GDP growth or industry average

### Step 2: Margin Projections
- Historical margin trends (gross, operating, EBITDA)
- Operating leverage: do margins expand with scale?
- Competitive dynamics: margin pressure from new entrants?
- Target margins based on mature peers

### Step 3: Free Cash Flow Calculation
**Unlevered FCF**:
$$UFCF = EBIT \times (1 - t) + \text{D\&A} - \text{Capex} - \Delta\text{Working Capital}$$

**Levered FCF**:
$$LFCF = \text{Net Income} + \text{D\&A} - \text{Capex} - \Delta\text{Working Capital} + \text{Net Borrowing}$$

### Step 4: WACC Calculation
$$WACC = \frac{E}{E+D} \times K_e + \frac{D}{E+D} \times K_d \times (1 - t)$$

**Cost of Equity** (CAPM):
$$K_e = R_f + \beta \times ERP$$

- $R_f$: 10-year Treasury yield
- $\beta$: Levered beta (from regression or industry average)
- ERP: Equity Risk Premium (typically 4-6%)

**Cost of Debt**:
$$K_d = R_f + \text{Credit Spread}$$

### Step 5: Terminal Value
**Gordon Growth**:
$$TV_n = \frac{FCF_n \times (1 + g)}{WACC - g}$$

**Exit Multiple**:
$$TV_n = EBITDA_n \times \text{Exit Multiple}$$

$g$ typically 2-3% (long-term nominal GDP growth).

### Step 6: Equity Value
1. Sum PV of projected FCFs + PV of terminal value = Enterprise Value
2. Add: cash and equivalents, non-operating assets
3. Subtract: total debt, minority interest, unfunded pension
4. Result = Equity Value
5. Divide by fully diluted shares = Fair Value per Share

### Sensitivity Table
| WACC \ g | 1.5% | 2.0% | 2.5% | 3.0% | 3.5% |
|----------|------|------|------|------|------|
| 7.0% | $XX | $XX | $XX | $XX | $XX |
| 8.0% | $XX | $XX | $XX | $XX | $XX |
| 9.0% | $XX | $XX | $XX | $XX | $XX |
| 10.0% | $XX | $XX | $XX | $XX | $XX |
| 11.0% | $XX | $XX | $XX | $XX | $XX |

## Dividend Discount Model (DDM)

**Gordon Growth Model** (constant growth):
$$P_0 = \frac{D_1}{r - g} = \frac{D_0 (1+g)}{r - g}$$

**Multi-stage DDM**:
1. Forecast dividends for high-growth period (3-5 years)
2. Estimate terminal value at maturity (Gordon Growth)
3. Discount all cash flows

Best for: mature, dividend-paying companies (utilities, financials, consumer staples).

## Comparable Company Analysis

### Procedure
1. Select 5-10 peer companies (similar business, size, geography)
2. Collect current trading multiples: P/E, EV/EBITDA, P/B, P/S, EV/Revenue
3. Compute LTM (last twelve months) and NTM (next twelve months) multiples
4. Calculate median, mean, 25th and 75th percentile
5. Apply to target company's metrics → implied valuation range

### Common Multiples
| Multiple | Best For | Pitfalls |
|----------|----------|----------|
| P/E | Stable, profitable companies | Distorted by capital structure, one-time items |
| EV/EBITDA | Capital-intensive industries | Ignores capex needs, working capital |
| P/B | Financials, asset-heavy | Distorted by intangibles, buybacks |
| P/S | Early-stage, unprofitable | Ignores profitability differences |
| EV/Revenue | High-growth tech | Same as P/S |

## Football-Field Summary

```
                    Bear        Base        Bull
DCF (Growth)       $XX.XX      $XX.XX      $XX.XX
DCF (Exit Mult)    $XX.XX      $XX.XX      $XX.XX
DDM                $XX.XX      $XX.XX      $XX.XX
Comp Co (P/E)      $XX.XX      $XX.XX      $XX.XX
Comp Co (EV/EBITDA) $XX.XX    $XX.XX      $XX.XX
Prec Transactions   $XX.XX     $XX.XX      $XX.XX
52-week Range      $XX.XX      $XX.XX      $XX.XX
                    └──────────────────────────────┘
                    $low                 $high
```

## Review Checklist

- [ ] Revenue forecast justified with historical trends and industry outlook
- [ ] Margins modelled realistically (not just extrapolated historically)
- [ ] WACC components documented: Rf, beta source, ERP, capital structure
- [ ] Terminal value ≤ 80% of total EV (check reasonableness)
- [ ] Sensitivity table generated for WACC vs growth rate
- [ ] Peer group justified with business similarity rationale
- [ ] All multiples documented with source and date
- [ ] Limitations noted (model uncertainty, data quality, structural breaks)
