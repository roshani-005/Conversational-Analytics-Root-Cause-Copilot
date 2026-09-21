"""
Plotly Visualizations & Financial Waterfall Charts
Generates high-contrast, publication-quality interactive charts for financial variance analysis.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def plot_pvm_waterfall(v_data: dict) -> go.Figure:
    """
    Renders an institutional-grade Price-Volume-Mix Waterfall Chart.
    """
    cat = v_data.get("category", "Portfolio")
    p1 = v_data.get("period_prior", "Prior")
    p2 = v_data.get("period_current", "Current")

    m1 = v_data.get("prior_margin", 0)
    p_var = v_data.get("price_variance", 0)
    c_var = v_data.get("cost_variance", 0)
    v_var = v_data.get("volume_variance", 0)
    m2 = v_data.get("current_margin", 0)

    fig = go.Figure(go.Waterfall(
        name="PVM Variance",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=[
            f"{p1} Base Margin",
            "Price Effect (Discounting)",
            "Cost Effect (Inflation)",
            "Volume Effect (Demand)",
            f"{p2} Ending Margin"
        ],
        textposition="outside",
        text=[
            f"${m1/1e3:,.1f}K",
            f"{p_var/1e3:+,.1f}K",
            f"{c_var/1e3:+,.1f}K",
            f"{v_var/1e3:+,.1f}K",
            f"${m2/1e3:,.1f}K"
        ],
        y=[m1, p_var, c_var, v_var, m2],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#ef4444"}},
        increasing={"marker": {"color": "#10b981"}},
        totals={"marker": {"color": "#3b82f6"}}
    ))

    fig.update_layout(
        title=f"<b>Price-Volume-Mix Margin Bridge: {cat} ({p1} → {p2})</b>",
        showlegend=False,
        height=420,
        yaxis_title="Gross Margin ($USD)",
        template="plotly_dark",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

def plot_category_margin_comparison(df: pd.DataFrame) -> go.Figure:
    """
    Bar chart comparing Q2 vs Q3 margins across all product categories.
    """
    q_filtered = df[df["quarter"].isin(["Q2-2025", "Q3-2025"])]
    grouped = q_filtered.groupby(["category", "quarter"]).agg(
        revenue=("gross_revenue", "sum"),
        margin=("gross_margin", "sum")
    ).reset_index()
    grouped["margin_pct"] = (grouped["margin"] / grouped["revenue"]) * 100.0

    fig = px.bar(
        grouped,
        x="category",
        y="margin_pct",
        color="quarter",
        barmode="group",
        title="<b>Gross Margin % by Category (Q2-2025 vs. Q3-2025)</b>",
        labels={"margin_pct": "Gross Margin (%)", "category": "Product Category"},
        color_discrete_map={"Q2-2025": "#3b82f6", "Q3-2025": "#f59e0b"},
        template="plotly_dark"
    )
    fig.update_layout(height=380, margin=dict(l=40, r=40, t=50, b=30))
    return fig

def plot_channel_discount_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Scatter plot of discount % vs gross margin % across sales channels.
    """
    sample_df = df.sample(min(800, len(df)))
    fig = px.scatter(
        sample_df,
        x="discount_pct",
        y="gross_margin_pct",
        color="sales_channel",
        title="<b>Discount % vs. Realized Gross Margin % by Sales Channel</b>",
        labels={"discount_pct": "Promotional Discount Applied (%)", "gross_margin_pct": "Realized Margin (%)"},
        template="plotly_dark",
        opacity=0.6
    )
    fig.update_layout(height=380)
    return fig
