---
name: sentiment-financial
description: NLP-based sentiment analysis of SEC filings, earnings call transcripts, financial news, and social media for investment signal generation
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Sentiment Analysis for Finance

Systematic workflow for extracting and quantifying sentiment from financial text data to generate investment signals.

## When to Use

- Analysing sentiment in 10-K/10-Q filings (Management Discussion & Analysis)
- Extracting tone from earnings call transcripts
- Monitoring news sentiment for stocks and sectors
- Analysing social media chatter (Reddit, Twitter) for retail sentiment
- Building sentiment-based alpha signals

## Data Sources

| Source | Type | Frequency | Access |
|--------|------|-----------|--------|
| SEC EDGAR | 10-K, 10-Q, 8-K filings | Quarterly / event-driven | Free API |
| Earnings call transcripts | Seeking Alpha, Motley Fool | Quarterly | Web scraping / APIs |
| Financial news | Reuters, Bloomberg, CNBC, WSJ | Daily / real-time | APIs, RSS |
| Social media | Reddit (r/wallstreetbets), StockTwits | Real-time | APIs |
| Analyst reports | Broker research | Periodic | Proprietary |
| Fed minutes/speeches | FOMC, ECB, BOJ statements | Scheduled | Free (official sites) |

## Sentiment Analysis Methods

### 1. Dictionary-Based (Loughran-McDonald)

The Loughran-McDonald (LM) sentiment dictionary is purpose-built for financial text. It contains word lists for:
- Positive, Negative, Uncertainty, Litigious, Strong Modal, Weak Modal

```python
def lm_sentiment(text, lm_dict):
    words = text.lower().split()
    pos_count = sum(1 for w in words if w in lm_dict['positive'])
    neg_count = sum(1 for w in words if w in lm_dict['negative'])
    uncertainty_count = sum(1 for w in words if w in lm_dict['uncertainty'])
    total = len(words)

    return {
        'pos_pct': pos_count / total * 100,
        'neg_pct': neg_count / total * 100,
        'net_tone': (pos_count - neg_count) / (pos_count + neg_count),
        'uncertainty_pct': uncertainty_count / total * 100,
    }
```

### 2. FinBERT

FinBERT is a BERT model fine-tuned on financial text (SEC filings). It classifies text into positive, negative, or neutral.

```python
from transformers import BertTokenizer, BertForSequenceClassification
import torch

tokenizer = BertTokenizer.from_pretrained('ProsusAI/finbert')
model = BertForSequenceClassification.from_pretrained('ProsusAI/finbert')

def finbert_sentiment(text):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)
    labels = ['positive', 'negative', 'neutral']
    return {labels[i]: probs[0, i].item() for i in range(3)}
```

### 3. GPT-Based

Use LLMs to extract nuanced sentiment, forward-looking statements, and management tone:

Prompt template:
```
Analyse the following earnings call excerpt for sentiment:
- Overall tone (1-5 scale, 5 = most positive)
- Confidence level (1-5)
- Key positive themes
- Key negative themes
- Forward-looking guidance sentiment
```

### 4. VADER (Social Media)

VADER is optimised for short social media text and handles emojis, slang, and intensifiers:

```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()
scores = analyzer.polarity_scores("AAPL to the moon! 🚀🚀")
# {'neg': 0.0, 'neu': 0.428, 'pos': 0.572, 'compound': 0.875}
```

## Signal Construction from Sentiment

### Time-Series Sentiment Signals
1. Aggregate daily sentiment scores across all news for a ticker
2. Compute rolling averages (5-day, 20-day)
3. Signal = Z-score of recent sentiment vs trailing 1-year mean
4. Test predictive power on forward returns

### Event-Based Signals
1. Identify events: earnings release, M&A announcement, management change
2. Compute pre-event sentiment baseline (30 days)
3. Measure sentiment change post-event (1-7 days)
4. Signal = post-event sentiment - pre-event sentiment

### Cross-Sectional Signals
1. Rank all stocks by sentiment score each day
2. Long top decile, short bottom decile
3. Rebalance monthly

## Quality Checks

### Validation
- Compare sentiment with actual returns to test predictive power
- Check for sentiment drift (degradation over time)
- Test across market regimes (bull/bear, high/low VIX)

### Pitfalls
- Republishing effect: same news appears multiple times
- Look-ahead bias: earnings call transcript published days after event
- Survivorship bias: stocks with more news coverage are different
- Sentiment dictionaries may not capture industry jargon
- Social media sentiment may be noise or manipulation

## 10-K/10-Q Filing Analysis

### Key Sections to Analyse
1. **Management Discussion & Analysis (MD&A)**: richest source of management sentiment
2. **Risk Factors**: count and categorise risk disclosures
3. **Legal Proceedings**: identify significant litigation
4. **Forward-Looking Statements**: extract projections and caveats

### MD&A Sentiment Metrics
- Net tone trend over 8+ quarters
- Uncertainty language changes (↑ uncertainty → ↓ earnings predictability)
- Comparison of sentiment vs actual subsequent performance
- Red flag: high positivity with deteriorating fundamentals = potential spin

## Reporting Standards

Each sentiment analysis must include:
- Data source, collection period, and sample size
- Methodology description (dictionary, ML model, or hybrid)
- Validation results: sentiment-return correlation
- Sentiment trend visualisation with key events annotated
- Comparison with peer/sector average sentiment
- Limitations: coverage bias, language constraints, timeliness
