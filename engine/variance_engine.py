"""
Price-Volume-Mix (PVM) Variance Decomposition Engine
Performs institutional-grade FP&A root-cause decomposition isolating:
1. Price Variance: Impact of price discounting or hikes
2. Volume Variance: Impact of unit volume expansion or contraction
3. Cost Variance: Impact of COGS inflation or supply chain surcharges
"""

import pandas as pd
import numpy as np

class VarianceEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def decompose_margin_variance(
        self,
        category: str = None,
        period_prior: str = "Q2-2025",
        period_current: str = "Q3-2025"
    ) -> dict:
        """
        Decomposes the change in gross margin between two quarters.
        Formula:
          Total Delta = Margin_Current - Margin_Prior
          Price Variance  = (Price_2 - Price_1) * Volume_2
          Cost Variance   = (Cost_1 - Cost_2)   * Volume_2
          Volume Variance = (Volume_2 - Volume_1) * UnitMargin_1
        """
        data = self.df.copy()
        if category and category.lower() != "all":
            data = data[data["category"].str.lower() == category.lower()]

        prior_df = data[data["quarter"] == period_prior]
        curr_df = data[data["quarter"] == period_current]

        # Period 1 (Prior) Aggregates
        v1 = prior_df["quantity"].sum()
        rev1 = prior_df["gross_revenue"].sum()
        cogs1 = prior_df["cogs"].sum()
        m1 = rev1 - cogs1

        # Period 2 (Current) Aggregates
        v2 = curr_df["quantity"].sum()
        rev2 = curr_df["gross_revenue"].sum()
        cogs2 = curr_df["cogs"].sum()
        m2 = rev2 - cogs2

        if v1 == 0 or v2 == 0:
            return {"error": "Insufficient transaction volume in selected periods."}

        p1 = rev1 / v1
        p2 = rev2 / v2
        c1 = cogs1 / v1
        c2 = cogs2 / v2
        unit_m1 = p1 - c1
        unit_m2 = p2 - c2

        total_margin_change = m2 - m1
        pct_margin_change = ((m2 - m1) / m1 * 100.0) if m1 != 0 else 0.0

        # Mathematical Decomposition
        price_variance = (p2 - p1) * v2
        cost_variance = (c1 - c2) * v2
        volume_variance = (v2 - v1) * unit_m1

        # Reconciled total
        reconciled_delta = price_variance + cost_variance + volume_variance

        # Relative contribution percentages
        abs_sum = abs(price_variance) + abs(cost_variance) + abs(volume_variance)
        price_impact_pct = (abs(price_variance) / abs_sum * 100.0) if abs_sum > 0 else 0.0
        cost_impact_pct = (abs(cost_variance) / abs_sum * 100.0) if abs_sum > 0 else 0.0
        volume_impact_pct = (abs(volume_variance) / abs_sum * 100.0) if abs_sum > 0 else 0.0

        # Determine primary root cause
        variances = {
            "Price Erosion / Discounting": price_variance,
            "Supply Chain & Cost Inflation": cost_variance,
            "Unit Volume Demand Contraction": volume_variance
        }
        primary_driver = min(variances, key=variances.get) # Most negative factor

        return {
            "category": category or "All Portfolio Categories",
            "period_prior": period_prior,
            "period_current": period_current,
            "prior_revenue": rev1,
            "current_revenue": rev2,
            "prior_margin": m1,
            "current_margin": m2,
            "prior_margin_pct": (m1 / rev1 * 100.0) if rev1 > 0 else 0.0,
            "current_margin_pct": (m2 / rev2 * 100.0) if rev2 > 0 else 0.0,
            "total_margin_delta": total_margin_change,
            "pct_margin_delta": pct_margin_change,
            "price_variance": price_variance,
            "cost_variance": cost_variance,
            "volume_variance": volume_variance,
            "price_impact_pct": price_impact_pct,
            "cost_impact_pct": cost_impact_pct,
            "volume_impact_pct": volume_impact_pct,
            "primary_driver": primary_driver,
            "p1": p1,
            "p2": p2,
            "c1": c1,
            "c2": c2,
            "v1": v1,
            "v2": v2
        }

    def generate_narrative_diagnosis(self, res: dict) -> str:
        """
        Translates variance numbers into a crisp 3-bullet executive diagnosis.
        """
        cat = res["category"]
        prior_p = res["period_prior"]
        curr_p = res["period_current"]
        delta_m = res["total_margin_delta"]
        pct_delta = res["pct_margin_delta"]
        p_var = res["price_variance"]
        c_var = res["cost_variance"]
        v_var = res["volume_variance"]
        driver = res["primary_driver"]

        trend_word = "dropped" if delta_m < 0 else "expanded"
        direction = "contraction" if delta_m < 0 else "gain"

        narrative = f"""### 🎯 C-Suite Root-Cause Diagnosis: {cat} ({prior_p} vs. {curr_p})

* **The Bottom Line:** Gross margin for **{cat}** {trend_word} by **${abs(delta_m):,.2f} ({pct_delta:+.1f}%)**, shifting from **{res['prior_margin_pct']:.1f}%** down to **{res['current_margin_pct']:.1f}%**.
* **Primary Root Cause:** **{driver}** was the dominant driver, accounting for **${abs(p_var if 'Price' in driver else (c_var if 'Cost' in driver else v_var)):,.2f}** of the variance.
* **Operational Breakdown (Price vs. Volume vs. Cost):**
  1. **Price Effect (${p_var:+,.2f}):** Average realized unit price shifted from **${res['p1']:.2f} to ${res['p2']:.2f}** ({'promotional discounting' if p_var < 0 else 'price realization'}).
  2. **Cost Effect (${c_var:+,.2f}):** Average unit COGS shifted from **${res['c1']:.2f} to ${res['c2']:.2f}** ({'supply chain cost inflation' if c_var < 0 else 'production efficiency'}).
  3. **Volume Effect (${v_var:+,.2f}):** Total unit volume moved from **{res['v1']:,} to {res['v2']:,} units**.
"""
        return narrative

if __name__ == "__main__":
    df = pd.read_csv("data/sales_orders.csv")
    engine = VarianceEngine(df)
    res = engine.decompose_margin_variance(category="Home Office", period_prior="Q2-2025", period_current="Q3-2025")
    print(engine.generate_narrative_diagnosis(res))
