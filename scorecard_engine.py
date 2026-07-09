"""
Working-Capital Credit Scorecard - Core Engine
===============================================
Weighted risk scorecard + k-Means clustering + credit limit engine
for fintech SME lending underwriting.

Author: Kasturi Dash
Date: July 2026
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class ScorecardResult:
    """Result of credit scorecard evaluation."""
    merchant_id: str
    risk_score: float
    risk_grade: str
    risk_cluster: int
    credit_limit: float
    recommendation: str

    def to_dict(self) -> Dict:
        return {
            'merchant_id': self.merchant_id,
            'risk_score': self.risk_score,
            'risk_grade': self.risk_grade,
            'risk_cluster': self.risk_cluster,
            'credit_limit': self.credit_limit,
            'recommendation': self.recommendation
        }


class RiskScorecard:
    """
    Weighted risk scorecard for merchant working-capital eligibility.

    Score components:
    - Transaction Behavior (25%): Volume, active days, growth trend
    - Risk Ratios (30%): Refund ratio, chargeback ratio  
    - Financial Health (25%): DSCR, settlement score, GST score
    - Stability & Maturity (20%): Vintage, seasonality, entity type

    Base score: 70 (neutral), Range: 10-100
    """

    def __init__(self, merchants_df: pd.DataFrame):
        self.df = merchants_df
        self._precompute_percentiles()

    def _precompute_percentiles(self):
        """Precompute dataset percentiles for relative scoring."""
        self.vol_min = self.df['monthly_volume_lakhs'].min()
        self.vol_max = self.df['monthly_volume_lakhs'].max()
        self.ticket_min = self.df['avg_ticket_size'].min()
        self.ticket_max = self.df['avg_ticket_size'].max()

    def calculate_score(self, row: pd.Series) -> float:
        """Calculate weighted risk score for a merchant."""
        score = 70.0

        # === 1. TRANSACTION BEHAVIOR (~25 points) ===
        vol_pct = (row['monthly_volume_lakhs'] - self.vol_min) / (self.vol_max - self.vol_min + 0.01)
        score += (vol_pct - 0.5) * 10

        active_pct = row['active_days_per_month'] / 30
        score += (active_pct - 0.5) * 8

        if row['growth_trend'] > 0.10: score += 6
        elif row['growth_trend'] > 0.05: score += 3
        elif row['growth_trend'] > 0: score += 1
        elif row['growth_trend'] < -0.05: score -= 5
        else: score -= 2

        ticket_pct = (row['avg_ticket_size'] - self.ticket_min) / (self.ticket_max - self.ticket_min + 0.01)
        score += (ticket_pct - 0.5) * 4

        # === 2. RISK RATIOS (~30 points - DEDUCTIONS) ===
        score -= min(18, row['refund_ratio'] * 150)
        score -= min(22, row['chargeback_ratio'] * 800)

        # === 3. FINANCIAL HEALTH (~25 points) ===
        if row['dscr'] >= 3.0: score += 12
        elif row['dscr'] >= 2.0: score += 8
        elif row['dscr'] >= 1.5: score += 4
        elif row['dscr'] >= 1.0: score += 0
        elif row['dscr'] >= 0.7: score -= 6
        else: score -= 12

        score += (row['settlement_score'] - 60) / 8
        score += (row['gst_score'] - 60) / 10

        inflow_ratio = row['bank_inflow_lakhs'] / (row['monthly_volume_lakhs'] + 0.01)
        if 0.7 <= inflow_ratio <= 1.3: score += 5
        elif 0.5 <= inflow_ratio <= 1.5: score += 2
        else: score -= 5

        # === 4. STABILITY & MATURITY (~20 points) ===
        if row['vintage_months'] >= 36: score += 10
        elif row['vintage_months'] >= 24: score += 7
        elif row['vintage_months'] >= 18: score += 5
        elif row['vintage_months'] >= 12: score += 3
        elif row['vintage_months'] >= 6: score += 1
        else: score -= 8

        if row['seasonality_index'] <= 1.1: score += 5
        elif row['seasonality_index'] <= 1.4: score += 2
        elif row['seasonality_index'] <= 1.8: score -= 2
        else: score -= 6

        if row['entity_type'] == 'Private Limited': score += 3
        elif row['entity_type'] == 'LLP': score += 1
        elif row['entity_type'] == 'Partnership': score += 0
        else: score -= 2

        score += (row['website_score'] - 50) / 15

        return max(10, min(100, round(score, 2)))

    def score_all(self) -> pd.DataFrame:
        """Apply scorecard to all merchants."""
        self.df['risk_score'] = self.df.apply(self.calculate_score, axis=1)
        return self.df


class RiskClustering:
    """k-Means clustering for risk segmentation into grades A-D."""

    FEATURES = [
        'monthly_volume_lakhs', 'refund_ratio', 'chargeback_ratio',
        'settlement_score', 'dscr', 'seasonality_index', 'vintage_months',
        'risk_score', 'active_days_per_month', 'growth_trend'
    ]

    def __init__(self, n_clusters: int = 4, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cluster merchants and assign risk grades."""
        X = df[self.FEATURES]
        X_scaled = self.scaler.fit_transform(X)
        df['risk_cluster'] = self.kmeans.fit_predict(X_scaled)

        # Map clusters to grades based on risk score
        cluster_scores = {}
        for c in range(self.n_clusters):
            cluster_scores[c] = df[df['risk_cluster'] == c]['risk_score'].mean()

        sorted_clusters = sorted(cluster_scores.items(), key=lambda x: x[1], reverse=True)
        grade_map = {cluster: grade for cluster, grade in zip([c for c, _ in sorted_clusters], ['A', 'B', 'C', 'D'])}

        df['risk_grade'] = df['risk_cluster'].map(grade_map)
        return df


class CreditLimitEngine:
    """Dynamic credit limit calculator based on risk grade and capacity."""

    GRADE_MULTIPLIERS = {'A': 3.0, 'B': 2.0, 'C': 1.0, 'D': 0.3}
    BASE_PCT = 0.50  # 50% of monthly volume
    MAX_LIMIT = 500  # ₹500 lakhs cap

    def calculate(self, row: pd.Series) -> float:
        """
        Calculate credit limit.

        Formula: Limit = 50% of monthly volume × grade multiplier × DSCR adjustment
        """
        base = row['monthly_volume_lakhs'] * self.BASE_PCT
        multiplier = self.GRADE_MULTIPLIERS.get(row['risk_grade'], 0.5)
        dscr_adj = min(2.0, max(0.5, row['dscr'] / 2.0))

        limit = base * multiplier * dscr_adj
        limit = max(0, limit)
        return round(min(limit, self.MAX_LIMIT), 2)

    def apply_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply credit limit calculation to all merchants."""
        df['credit_limit_lakhs'] = df.apply(self.calculate, axis=1)
        return df


class ApprovalEngine:
    """Approval recommendation engine based on composite risk assessment."""

    @staticmethod
    def recommend(row: pd.Series) -> str:
        """
        Generate approval recommendation.

        Rules:
        - Auto-Approve: Grade A, CB < 1.5%, DSCR > 2.0, vintage >= 12, refund < 10%
        - Likely Approve: Grade A/B, CB < 3%, DSCR > 1.2, vintage >= 6, refund < 18%
        - Conditional: Grade B/C, CB < 4.5%, DSCR > 0.8, vintage >= 3, refund < 25%
        - Reject: Everything else
        """
        grade = row['risk_grade']
        cb = row['chargeback_ratio']
        dscr = row['dscr']
        refund = row['refund_ratio']
        vintage = row['vintage_months']

        if (grade == 'A' and cb < 0.015 and dscr > 2.0 and vintage >= 12 and refund < 0.10):
            return 'Auto-Approve'

        if (grade in ['A', 'B'] and cb < 0.03 and dscr > 1.2 and vintage >= 6 and refund < 0.18):
            return 'Manual Review - Likely Approve'

        if (grade in ['B', 'C'] and cb < 0.045 and dscr > 0.8 and vintage >= 3 and refund < 0.25):
            return 'Manual Review - Conditional'

        return 'Reject / High Risk'

    def apply_all(self, df: pd.DataFrame) -> pd.DataFrame:
        df['recommendation'] = df.apply(self.recommend, axis=1)
        return df


class CreditScorecardPipeline:
    """End-to-end pipeline: Score → Cluster → Limit → Recommend."""

    def __init__(self, merchants_df: pd.DataFrame):
        self.df = merchants_df.copy()
        self.scorecard = RiskScorecard(self.df)
        self.clustering = RiskClustering()
        self.limit_engine = CreditLimitEngine()
        self.approval_engine = ApprovalEngine()

    def run(self) -> pd.DataFrame:
        """Execute full pipeline."""
        print("[1/4] Calculating risk scores...")
        self.df = self.scorecard.score_all()

        print("[2/4] Clustering merchants into risk grades...")
        self.df = self.clustering.fit_transform(self.df)

        print("[3/4] Calculating credit limits...")
        self.df = self.limit_engine.apply_all(self.df)

        print("[4/4] Generating approval recommendations...")
        self.df = self.approval_engine.apply_all(self.df)

        return self.df

    def get_summary(self) -> Dict:
        """Generate executive summary of results."""
        return {
            'total_merchants': len(self.df),
            'avg_risk_score': round(self.df['risk_score'].mean(), 2),
            'total_credit_exposure': round(self.df['credit_limit_lakhs'].sum(), 2),
            'avg_credit_limit': round(self.df['credit_limit_lakhs'].mean(), 2),
            'grade_distribution': self.df['risk_grade'].value_counts().to_dict(),
            'recommendation_distribution': self.df['recommendation'].value_counts().to_dict(),
            'auto_approve_rate': round(
                len(self.df[self.df['recommendation'] == 'Auto-Approve']) / len(self.df) * 100, 2
            )
        }


def main():
    """Demo: Run full credit scorecard pipeline."""
    print("=" * 60)
    print("Working-Capital Credit Scorecard - Engine Demo")
    print("=" * 60)

    # Load data (run generate_merchant_data.py first)
    try:
        df = pd.read_csv('merchants.csv')
    except FileNotFoundError:
        print("\nError: merchants.csv not found. Run generate_merchant_data.py first.")
        return

    pipeline = CreditScorecardPipeline(df)
    results = pipeline.run()

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    summary = pipeline.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Save results
    results.to_csv('scorecard_results.csv', index=False)
    print("\n  Results saved → scorecard_results.csv")
    print("=" * 60)


if __name__ == '__main__':
    main()
