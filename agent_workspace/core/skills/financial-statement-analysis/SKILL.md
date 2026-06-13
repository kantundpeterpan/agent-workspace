---
name: financial-statement-analysis
description: Read and analyse 10-K/10-Q financial statements, ratio analysis, cash flow analysis, quality of earnings assessment
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Financial Statement Analysis

Systematic workflow for analysing financial statements, computing key ratios, and assessing earnings quality.

## When to Use

- Analysing a company's 10-K or 10-Q filings
- Computing and interpreting financial ratios
- Assessing earnings quality and detecting red flags
- Comparing financials across peer companies
- Building a financial model foundation

## Financial Statements Overview

### Income Statement
Revenue → COGS → Gross Profit → Operating Expenses → EBIT → Interest/Taxes → Net Income

Key line items:
- Revenue (sales, interest income, fee income)
- COGS (direct costs of producing goods/services)
- SG&A (selling, general, administrative)
- R&D, depreciation, amortisation
- Interest income/expense, tax provision
- EPS (basic and diluted), shares outstanding

### Balance Sheet
Assets = Liabilities + Shareholders' Equity

Key line items:
- **Current assets**: cash, receivables, inventory, prepaid expenses
- **Non-current assets**: PP&E, goodwill, intangibles, investments
- **Current liabilities**: payables, short-term debt, accrued expenses
- **Non-current liabilities**: long-term debt, lease obligations, pension
- **Equity**: common stock, retained earnings, treasury stock, AOCI

### Cash Flow Statement
Starting cash + CFO + CFI + CFF = Ending cash

- **Operating (CFO)**: net income + non-cash adjustments ± working capital
- **Investing (CFI)**: capex, acquisitions, asset sales, investment purchases
- **Financing (CFF)**: debt issuance/repayment, dividends, share buybacks

## Ratio Analysis Framework

### Profitability Ratios
| Ratio | Formula | Interpretation |
|-------|---------|----------------|
| Gross margin | (Revenue - COGS) / Revenue | Pricing power and production efficiency |
| Operating margin | EBIT / Revenue | Core business profitability |
| Net margin | Net Income / Revenue | Bottom-line efficiency |
| ROE | Net Income / Avg Equity | Return to shareholders; decompose via DuPont |
| ROA | Net Income / Avg Total Assets | Asset efficiency |
| ROIC | NOPAT / Invested Capital | Returns above cost of capital |

### Liquidity Ratios
| Ratio | Formula | Healthy Range |
|-------|---------|--------------|
| Current ratio | Current Assets / Current Liabilities | > 1.5 |
| Quick ratio | (CA - Inventory) / CL | > 1.0 |
| Cash ratio | Cash / Current Liabilities | > 0.5 |
| Operating CF ratio | CFO / Current Liabilities | > 0.4 |

### Leverage Ratios
| Ratio | Formula |
|-------|---------|
| Debt-to-Equity | Total Debt / Total Equity |
| Debt-to-EBITDA | Total Debt / EBITDA |
| Interest coverage | EBIT / Interest Expense |
| Debt-to-Assets | Total Debt / Total Assets |

### Efficiency Ratios
| Ratio | Formula |
|-------|---------|
| Asset turnover | Revenue / Avg Total Assets |
| Inventory turnover | COGS / Avg Inventory |
| DSO (Days Sales Out.) | AR / (Revenue/365) |
| DPO (Days Payable Out.) | AP / (COGS/365) |
| Cash conversion cycle | DIO + DSO - DPO |

### Valuation Ratios
| Ratio | Formula |
|-------|---------|
| P/E | Price / EPS |
| EV/EBITDA | EV / EBITDA |
| P/B | Price / Book Value per Share |
| P/S | Price / Sales per Share |
| PEG | P/E / Earnings Growth Rate |

## DuPont Decomposition

**Traditional 3-factor**:
$$ROE = \frac{\text{Net Income}}{\text{Equity}} = \frac{\text{Net Income}}{\text{Sales}} \times \frac{\text{Sales}}{\text{Assets}} \times \frac{\text{Assets}}{\text{Equity}} = \text{Net Margin} \times \text{Asset Turnover} \times \text{Equity Multiplier}$$

**Extended 5-factor**:
$$ROE = \text{Tax Burden} \times \text{Interest Burden} \times \text{Op Margin} \times \text{Asset Turnover} \times \text{Leverage}$$

## Earnings Quality Assessment

### Red Flags
- Revenue growth significantly outpaces cash flow from operations
- Accounts receivable growing faster than revenue
- Inventory build-up without corresponding sales growth
- Frequent one-time/non-recurring charges
- Large gap between GAAP and non-GAAP (adjusted) earnings
- Sudden changes in accounting policies or estimates
- Related-party transactions at non-market terms
- Aggressive revenue recognition (bill-and-hold, channel stuffing)
- Capitalising expenses that peers expense
- Decline in reserve accounts while receivables grow

### Cash Flow vs Earnings
- Compare CFO with Net Income over multiple periods
- FCF = CFO - Capex; persistent negative FCF is concerning
- Cash conversion ratio: CFO / Net Income (should be near or above 1.0)
- Quality of earnings ratio: CFO / Net Income

## Analysis Workflow

1. Download financial statements (SEC EDGAR, yfinance)
2. Normalise line items across periods and peers
3. Compute all ratios for at least 5 years of history
4. Perform trend analysis: are ratios improving or deteriorating?
5. Benchmark against industry peers and sector medians
6. Run DuPont decomposition; identify drivers of ROE
7. Assess earnings quality with cash flow reconciliation
8. Flag any accounting red flags or unusual items

## Review Checklist

- [ ] Income statement, balance sheet, and cash flows reviewed (5+ years)
- [ ] All key ratios computed and trended
- [ ] DuPont decomposition performed
- [ ] Peer comparison completed (5+ comparable companies)
- [ ] Earnings quality assessment done
- [ ] Red flags documented with materiality assessment
- [ ] Limitations and data sources cited
