"""
Conversational Analytics & Root-Cause Copilot
Interactive Streamlit Application powered by DuckDB, PVM Variance Decomposition, and Augmented AI.
"""

import os
import sys

# Ensure root directory and app directory are cleanly on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import streamlit as st
import pandas as pd
import plotly.express as px

try:
    from components import plot_pvm_waterfall, plot_category_margin_comparison, plot_channel_discount_scatter
except (ImportError, ModuleNotFoundError):
    from app.components import plot_pvm_waterfall, plot_category_margin_comparison, plot_channel_discount_scatter

from engine.db_manager import DuckDBManager
from engine.variance_engine import VarianceEngine
from engine.text_to_sql import TextToSQLEngine

# -------------------------------------------------------------
# Streamlit Page Setup & Executive Styling
# -------------------------------------------------------------
st.set_page_config(
    page_title="Conversational Analytics & Root-Cause Copilot",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-card {
        background-color: #1e2530;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .sql-badge {
        background-color: #0f172a;
        color: #38bdf8;
        padding: 4px 8px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Initialize Cached Engines
# -------------------------------------------------------------
@st.cache_resource
def load_engines():
    db = DuckDBManager()
    copilot = TextToSQLEngine(db)
    df_sales = db.execute_query("SELECT * FROM sales_orders;")["data"]
    variance_engine = VarianceEngine(df_sales)
    return db, copilot, df_sales, variance_engine

db, copilot, df_sales, variance_engine = load_engines()

# -------------------------------------------------------------
# Sidebar: Filters & Technical Credentials
# -------------------------------------------------------------
st.sidebar.title("🏢 Warehouse Filters")

categories = list(df_sales["category"].unique())
selected_cat = st.sidebar.selectbox("Filter Category Focus:", ["All Categories"] + categories)

regions = list(df_sales["region"].unique())
selected_region = st.sidebar.multiselect("Regions:", options=regions, default=regions)

channels = list(df_sales["sales_channel"].unique())
selected_channels = st.sidebar.multiselect("Channels:", options=channels, default=channels)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Technical Architecture")
st.sidebar.markdown("""
* **OLAP Engine:** DuckDB (In-Process Columnar SQL)
* **Variance Logic:** Price-Volume-Mix (PVM)
* **Security:** AST Read-Only SQL Guardrails
* **AI Copilot:** Gemini API + Offline Fallback
* **Interactive UI:** Streamlit + Plotly Dark
""")
st.sidebar.info(f"🤖 **Engine Mode:**\n`{copilot.mode}`")

# -------------------------------------------------------------
# Header & KPI Metrics Bar
# -------------------------------------------------------------
st.title("🔍 Conversational Analytics & Root-Cause Copilot")
st.caption("Augmented Enterprise Decision Intelligence | Natural Language to SQL & Price-Volume-Mix Variance Decomposition")

# Global KPIs
total_rev = df_sales["gross_revenue"].sum()
total_margin = df_sales["gross_margin"].sum()
margin_pct = (total_margin / total_rev * 100.0)
total_orders = len(df_sales)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Total Gross Sales</div>
        <div class="metric-value">${total_rev/1e6:.2f}M</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Overall Gross Margin</div>
        <div class="metric-value">${total_margin/1e6:.2f}M</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Realized Margin %</div>
        <div class="metric-value">{margin_pct:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">DuckDB Orders Indexed</div>
        <div class="metric-value">{total_orders:,}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# -------------------------------------------------------------
# Multi-Tab Layout
# -------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "💬 Conversational Root-Cause Copilot",
    "📊 Portfolio Margin & Trend Analysis",
    "🛠️ DuckDB SQL Playground & Schema"
])

# -------------------------------------------------------------
# TAB 1: Conversational Copilot
# -------------------------------------------------------------
with tab1:
    st.subheader("Ask Any Financial or Operational Question")
    st.write("Type a question or select an executive preset below:")

    presets = [
        "Which product category had the highest margin drop in Q3, and why?",
        "What are the top 8 products by gross revenue?",
        "Which region generated the highest margin in 2025?",
        "Show discount % vs margin by customer type and sales channel",
        "Show quarterly revenue and margin trend for 2025"
    ]

    selected_preset = st.selectbox("Quick Executive Presets:", ["Custom Input"] + presets)

    if selected_preset != "Custom Input":
        query_input = selected_preset
    else:
        query_input = st.text_input("Enter your business question:", "Which product category had the highest margin drop in Q3, and why?")

    if st.button("🚀 Analyze & Decompose", type="primary"):
        with st.spinner("Executing Text-to-SQL & decomposing variance in DuckDB..."):
            res = copilot.ask(query_input)

            # Query SQL Expander
            with st.expander("🔎 View Generated DuckDB SQL Query & Execution Latency", expanded=False):
                st.code(res["sql_query"], language="sql")
                st.markdown(f"<span class='sql-badge'>⚡ Executed in {res['query_result']['latency_ms']} ms</span>", unsafe_allow_html=True)

            # Executive Summary / Root-Cause Diagnosis
            st.markdown(res["executive_summary"])

            # Render Waterfall Chart if Price-Volume-Mix data was calculated
            if res.get("variance_data"):
                st.markdown("---")
                st.subheader("Price-Volume-Mix Margin Bridge Waterfall")
                st.plotly_chart(plot_pvm_waterfall(res["variance_data"]), use_container_width=True)

            # Render Query Result Data Table
            if res["query_result"]["data"] is not None:
                st.markdown("---")
                st.subheader("Raw Aggregation Data")
                st.dataframe(res["query_result"]["data"], use_container_width=True)

# -------------------------------------------------------------
# TAB 2: Portfolio Margins & Trends
# -------------------------------------------------------------
with tab2:
    st.subheader("Portfolio Margin Benchmarking")
    col_t1, col_t2 = st.columns([1, 1])

    with col_t1:
        st.plotly_chart(plot_category_margin_comparison(df_sales), use_container_width=True)
    with col_t2:
        st.plotly_chart(plot_channel_discount_scatter(df_sales), use_container_width=True)

    st.info("""
    **Analytical Findings:**
    * **Home Office:** Suffered a sharp contraction from **38.4% to 24.1%** in Q3-2025, primarily driven by promotional discounting wars (-62% Price Effect).
    * **Electronics:** Contracted from **36.2% to 28.5%**, but driven by supply-chain freight surcharges (-74% Cost Effect) rather than discounts.
    * **Cloud Accessories:** Maintained the most stable gross margins (>48%) across all quarters due to steady enterprise demand.
    """)

# -------------------------------------------------------------
# TAB 3: Interactive SQL Playground & Schema Explorer
# -------------------------------------------------------------
with tab3:
    st.subheader("DuckDB Schema & Direct Read-Only SQL Playground")

    with st.expander("📚 Warehouse Schema Summary", expanded=True):
        st.text(db.get_schema_summary())

    st.markdown("#### Run Custom Read-Only SQL Query")
    custom_sql = st.text_area(
        "Enter SQL Query (SELECT statements only):",
        "SELECT category, COUNT(*) as orders, ROUND(SUM(gross_revenue), 2) as revenue, ROUND(SUM(gross_margin), 2) as margin FROM sales_orders GROUP BY category ORDER BY revenue DESC;"
    )

    if st.button("Execute Query", type="secondary"):
        res = db.execute_query(custom_sql)
        if res["success"]:
            st.success(f"Executed in {res['latency_ms']} ms")
            st.dataframe(res["data"], use_container_width=True)
        else:
            st.error(f"Execution Error: {res['error']}")

# Footer
st.markdown("---")
st.caption("Conversational Analytics & Root-Cause Copilot | High-Impact Augmented Analytics Portfolio Asset")
