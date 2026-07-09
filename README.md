# Working-Capital Credit Scorecard for Merchants

> **Live Dashboard:** [https://yourusername.github.io/merchant-credit-scorecard/]

## Overview

AI-powered cashflow-based underwriting engine for SME lending. This project simulates how fintech lenders like **Razorpay Capital** assess working-capital eligibility for small and medium businesses using **alternative data** from payment platforms rather than traditional audited financials.

## The Problem

Traditional banks lend to large companies using:
- Audited balance sheets
- CIBIL scores and credit history
- Collateral (property, equipment)
- Quarterly financial reviews

But SMEs (small merchants on payment platforms) don't have audited books. They might be a 6-month-old D2C brand or a local restaurant. **How do you underwrite them?**

**Answer:** Use their **payment gateway data** as a proxy for financial health.

## Architecture

```
Merchant Profile → Transaction Behavior → Risk Scorecard → k-Means Clustering
                                                                  ↓
                                                    Risk Grade (A/B/C/D)
                                                                  ↓
                                              Credit Limit Engine → Approval Recommendation
```

## Scorecard Methodology

### 1. Transaction Behavior (25%)
- **Monthly payment volume**: Higher volume = more stable business
- **Active days per month**: Consistent activity indicates reliability
- **Growth trend (MoM)**: Positive growth signals expansion
- **Average ticket size**: Higher tickets = more stable revenue

### 2. Risk Ratios (30%)
- **Refund ratio**: High refunds = product quality or customer satisfaction issues
- **Chargeback ratio**: Chargebacks >2% trigger automatic risk flags
- These are the strongest predictors of merchant quality

### 3. Financial Health (25%)
- **DSCR** (Debt Service Coverage Ratio): >2.0x = healthy debt coverage
- **Settlement score**: Consistent settlement history = reliable cashflow
- **GST filing regularity**: Tax compliance = business discipline
- **Bank inflow consistency**: Should match payment volume closely

### 4. Stability & Maturity (20%)
- **Business vintage**: >24 months signals maturity and survival
- **Seasonality index**: <1.2 = stable cashflow (preferred for lending)
- **Entity type**: Pvt Ltd > LLP > Partnership > Proprietorship
- **Website quality**: Online presence indicates business investment

## Key Features

### Risk Segmentation (k-Means Clustering)
- 4 clusters using 10 features: volume, refund ratio, chargeback ratio, settlement score, DSCR, seasonality, vintage, risk score, active days, growth trend
- Clusters mapped to grades A-D based on average risk score

### Credit Limit Engine
```
Limit = 50% of monthly volume × grade multiplier × DSCR adjustment

Grade Multipliers:
- A: 3.0x
- B: 2.0x
- C: 1.0x
- D: 0.3x

Hard cap: ₹500 lakhs
```

### Approval Recommendations
| Grade | Chargeback | DSCR | Vintage | Refund | Recommendation |
|-------|-----------|------|---------|--------|----------------|
| A | <1.5% | >2.0x | ≥12mo | <10% | **Auto-Approve** |
| A/B | <3.0% | >1.2x | ≥6mo | <18% | **Manual Review - Likely Approve** |
| B/C | <4.5% | >0.8x | ≥3mo | <25% | **Manual Review - Conditional** |
| — | — | — | — | — | **Reject / High Risk** |

## Dataset

- **150 merchants** across 10 categories
- **Realistic distributions**: Log-normal volumes, beta-distributed ratios, exponential debt
- **Risk profiles**: Low (50%), Medium (35%), High (15%) with adjusted exception probabilities

## Results

| Metric | Value |
|--------|-------|
| Total Merchants | 150 |
| Average Risk Score | 73.8/100 |
| Total Credit Exposure | ₹11,772 lakhs |
| Average Credit Limit | ₹78.5 lakhs |
| Auto-Approval Rate | 18.0% (27 merchants) |
| Grade A | 55 merchants (36.7%) |
| Grade D | 38 merchants (25.3%) |
| Average DSCR | 7.76x |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Generation | Python, Pandas, NumPy |
| Scorecard Engine | Python (dataclasses, scikit-learn) |
| Clustering | scikit-learn KMeans (k=4) |
| Analysis | Jupyter Notebook, Matplotlib, Seaborn |
| Dashboard | HTML5, CSS3, Canvas API, Vanilla JavaScript |
| Deployment | GitHub Pages |

## Repository Structure

```
merchant-credit-scorecard/
├── index.html                          ← Live interactive dashboard
├── README.md                           ← This file
├── requirements.txt                    ← Python dependencies
├── .gitignore                          ← Git exclusions
├── data/
│   └── generate_merchant_data.py     ← Merchant profile generator
├── engine/
│   └── scorecard_engine.py             ← Scorecard + clustering + limit engine
├── notebooks/
│   └── credit_scorecard_analysis.ipynb ← EDA & validation
└── screenshots/
    └── dashboard_preview.png           ← For LinkedIn/GitHub preview
```

## How to Run

### 1. Generate Data
```bash
cd data
python generate_merchant_data.py
# Outputs: merchants.csv
```

### 2. Run Scorecard Engine
```bash
cd engine
python scorecard_engine.py
# Outputs: scorecard_results.csv
```

### 3. Run Analysis
```bash
cd notebooks
jupyter notebook credit_scorecard_analysis.ipynb
```

### 4. Deploy Dashboard
```bash
# Push index.html to GitHub
# Enable GitHub Pages in Settings
# Your dashboard is live at: https://yourusername.github.io/merchant-credit-scorecard/
```

## Why This Matters for Fintech

1. **Alternative Data:** Uses transaction velocity, chargeback patterns, and settlement history as credit proxies instead of balance sheets
2. **Real-Time Underwriting:** Can assess eligibility in minutes, not weeks
3. **Dynamic Pricing:** Credit limits adjust based on real-time risk grade and capacity
4. **Scalable:** Automated scorecard processes thousands of merchants simultaneously
5. **Explainable:** Every score component is transparent and auditable

## Interview Talking Points

**Q: How is this different from traditional credit appraisal?**
> At Kotak, I assessed large corporate credit using CIBIL and audited financials. This project shows I can apply the same credit discipline to SME lending — using transaction velocity and settlement patterns instead of balance sheets.

**Q: Why k-Means clustering?**
> Unsupervised learning segments merchants into natural risk groups without pre-labeled data. This mirrors how Razorpay Capital discovers merchant segments from platform behavior.

**Q: How do you handle seasonality?**
> Seasonal businesses (Travel, Retail) get higher seasonality indices. We prefer stable cashflow (index <1.2) for lending, but adjust limits for known seasonal patterns.

**Q: What about DSCR?**
> DSCR >2.0x means the merchant can cover debt service twice over from available cashflow. It's the most important financial health indicator in the scorecard.

**Q: Why different credit limits for the same grade?**
> The limit engine combines grade multiplier (A=3x) with DSCR adjustment and monthly volume. Two Grade A merchants can have very different limits based on their actual cashflow capacity.

## About the Author

**Kasturi Dash** — Credit Risk Analyst with 2+ years at Kotak Mahindra Bank, transitioning to fintech. Background in corporate credit appraisal (CIBIL, FOIR, DSCR, CAM reports) combined with fintech's alternative-data approach to risk and lending.

- 📧 kasturidash1997@gmail.com
- 📍 Bengaluru, India

## License

This project is built with synthetic data for portfolio demonstration. Not based on real merchant or financial information.

---

**Built for:** Razorpay Capital, Stripe Capital, PayU, and other fintech lending roles.
