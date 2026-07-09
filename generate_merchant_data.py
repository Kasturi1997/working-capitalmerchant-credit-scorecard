"""
Working-Capital Credit Scorecard - Synthetic Data Generator
===========================================================
Generates realistic merchant profiles with cashflow and payment behavior data
for simulating fintech SME lending underwriting workflows.

Author: Kasturi Dash
Date: July 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime
import random
import json

# Configuration
N_MERCHANTS = 150
RANDOM_SEED = 2026

np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# Business categories with distinct risk and volume profiles
CATEGORY_PROFILES = {
    'E-commerce':    {'base_volume': 45, 'vol_std': 25, 'refund_base': 0.12, 'cb_base': 0.015, 'seasonality': 1.4, 'growth_trend': 0.08},
    'SaaS':          {'base_volume': 30, 'vol_std': 15, 'refund_base': 0.03, 'cb_base': 0.005, 'seasonality': 0.9, 'growth_trend': 0.15},
    'Food & Beverage': {'base_volume': 22, 'vol_std': 12, 'refund_base': 0.06, 'cb_base': 0.008, 'seasonality': 1.2, 'growth_trend': 0.05},
    'EdTech':        {'base_volume': 18, 'vol_std': 14, 'refund_base': 0.18, 'cb_base': 0.025, 'seasonality': 1.6, 'growth_trend': 0.10},
    'Travel':        {'base_volume': 55, 'vol_std': 35, 'refund_base': 0.22, 'cb_base': 0.035, 'seasonality': 2.2, 'growth_trend': 0.03},
    'Healthcare':    {'base_volume': 28, 'vol_std': 10, 'refund_base': 0.02, 'cb_base': 0.003, 'seasonality': 0.8, 'growth_trend': 0.06},
    'Retail':        {'base_volume': 35, 'vol_std': 18, 'refund_base': 0.09, 'cb_base': 0.012, 'seasonality': 1.3, 'growth_trend': 0.04},
    'Logistics':     {'base_volume': 40, 'vol_std': 20, 'refund_base': 0.04, 'cb_base': 0.007, 'seasonality': 1.0, 'growth_trend': 0.07},
    'Gaming':        {'base_volume': 25, 'vol_std': 22, 'refund_base': 0.15, 'cb_base': 0.028, 'seasonality': 1.1, 'growth_trend': 0.12},
    'Financial Services': {'base_volume': 60, 'vol_std': 30, 'refund_base': 0.05, 'cb_base': 0.020, 'seasonality': 0.7, 'growth_trend': 0.09}
}

ENTITY_TYPES = ['Private Limited', 'LLP', 'Partnership', 'Proprietorship']
ENTITY_WEIGHTS = [0.35, 0.25, 0.20, 0.20]


def generate_merchants(n=N_MERCHANTS):
    """Generate synthetic merchant profiles with realistic cashflow attributes."""
    merchants = []

    for i in range(n):
        mid = f"MER{3000 + i}"
        category = random.choice(list(CATEGORY_PROFILES.keys()))
        profile = CATEGORY_PROFILES[category]

        # Vintage: months on platform (3 to 48 months)
        vintage = int(np.random.choice([6, 12, 18, 24, 36, 48], 
                                       p=[0.10, 0.15, 0.20, 0.25, 0.20, 0.10]))

        # Monthly payment volume (INR lakhs) - log-normal for realistic distribution
        volume = np.random.lognormal(np.log(profile['base_volume']), 0.4) *                  (1 + profile['growth_trend']) ** (vintage / 12)
        volume = max(2.0, volume)

        # Average ticket size
        avg_ticket = np.random.lognormal(4.5, 0.8)
        avg_ticket = max(150, min(avg_ticket, 25000))

        # Refund ratio - category base + noise
        refund_ratio = np.random.beta(2, 15) * profile['refund_base'] * 5 + np.random.uniform(0, 0.03)
        refund_ratio = min(0.35, refund_ratio)

        # Chargeback ratio
        chargeback_ratio = np.random.exponential(0.006) + profile['cb_base'] * np.random.uniform(0.5, 1.5)
        chargeback_ratio = min(0.06, chargeback_ratio)

        # Settlement score (0-100) - higher is better
        settlement_score = np.random.beta(7, 3) * 100
        if chargeback_ratio > 0.02:
            settlement_score *= np.random.uniform(0.6, 0.9)
        settlement_score = max(20, min(100, settlement_score))

        # Bank statement inflows - correlated with payment volume
        inflow_consistency = np.random.uniform(0.75, 1.25)
        bank_inflow = volume * inflow_consistency

        # Seasonality index (1.0 = stable, >1.5 = highly seasonal)
        seasonality = profile['seasonality'] * np.random.uniform(0.8, 1.3)

        # Existing debt (INR lakhs)
        debt_to_volume = np.random.uniform(0.5, 4.0)
        existing_debt = volume * debt_to_volume

        # DSCR-like ratio (Debt Service Coverage Ratio)
        monthly_debt_service = existing_debt * 0.04
        dscr = (bank_inflow * 0.7) / (monthly_debt_service + 0.5)
        dscr = max(0.3, dscr)

        # GST filing regularity (0-100)
        gst_score = np.random.beta(6, 3) * 100
        if vintage < 12:
            gst_score *= 0.85

        # Website/online presence quality
        website_score = np.random.beta(5, 4) * 100

        # Active days per month
        active_days = int(np.random.uniform(12, 30))

        # Entity type
        entity_type = np.random.choice(ENTITY_TYPES, p=ENTITY_WEIGHTS)

        # Growth trend (MoM)
        growth_trend = profile['growth_trend'] + np.random.normal(0, 0.05)

        merchants.append({
            'merchant_id': mid,
            'business_name': f"{category} Pvt Ltd {mid}",
            'category': category,
            'entity_type': entity_type,
            'vintage_months': vintage,
            'monthly_volume_lakhs': round(volume, 2),
            'avg_ticket_size': round(avg_ticket, 2),
            'refund_ratio': round(refund_ratio, 4),
            'chargeback_ratio': round(chargeback_ratio, 4),
            'settlement_score': round(settlement_score, 2),
            'bank_inflow_lakhs': round(bank_inflow, 2),
            'seasonality_index': round(seasonality, 2),
            'existing_debt_lakhs': round(existing_debt, 2),
            'dscr': round(dscr, 2),
            'gst_score': round(gst_score, 2),
            'website_score': round(website_score, 2),
            'active_days_per_month': active_days,
            'growth_trend': round(growth_trend, 4)
        })

    return pd.DataFrame(merchants)


def main():
    """Generate and save merchant dataset."""
    print("=" * 60)
    print("Working-Capital Credit Scorecard - Data Generator")
    print("=" * 60)

    print("\n[1/2] Generating merchant profiles...")
    df = generate_merchants()
    df.to_csv('merchants.csv', index=False)
    print(f"      ✓ {len(df)} merchants created → merchants.csv")

    print("\n[2/2] Summary Statistics:")
    print(f"      Categories: {df['category'].nunique()}")
    print(f"      Entity types: {df['entity_type'].nunique()}")
    print(f"      Avg monthly volume: ₹{df['monthly_volume_lakhs'].mean():.2f}L")
    print(f"      Avg DSCR: {df['dscr'].mean():.2f}x")
    print(f"      Avg refund ratio: {df['refund_ratio'].mean():.4f}")
    print(f"      Avg chargeback ratio: {df['chargeback_ratio'].mean():.4f}")

    print("\n" + "=" * 60)
    print("Data generation complete. Run scorecard_engine.py next.")
    print("=" * 60)


if __name__ == '__main__':
    main()
