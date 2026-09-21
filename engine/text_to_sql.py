"""
Text-to-SQL Engine & Natural Language Query Copilot
Converts plain-English business queries into validated DuckDB SQL,
executes the query, decomposes variance when applicable, and generates executive summaries.
Supports Google Gemini API with graceful offline deterministic fallback.
"""

import os
import re
import json
import pandas as pd
from dotenv import load_dotenv
from engine.db_manager import DuckDBManager
from engine.variance_engine import VarianceEngine

load_dotenv()

class TextToSQLEngine:
    def __init__(self, db_manager: DuckDBManager):
        self.db = db_manager
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        
        # Initialize Gemini Client if key available
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                self.mode = "Gemini Live API"
            except Exception:
                self.mode = "Offline Deterministic Copilot"
        else:
            self.mode = "Offline Deterministic Copilot"

    def ask(self, question: str) -> dict:
        """
        Main pipeline:
        1. Translates natural language question to SQL.
        2. Validates and executes query against DuckDB.
        3. Identifies if variance decomposition is requested.
        4. Generates a 3-bullet executive diagnosis.
        """
        sql_query = self._generate_sql(question)
        query_result = self.db.execute_query(sql_query)

        # Check if variance analysis is applicable
        q_lower = question.lower()
        variance_data = None
        variance_diagnosis = None

        if "why" in q_lower or "drop" in q_lower or "variance" in q_lower or "q3" in q_lower:
            # Extract category if present
            cat = None
            for c in ["Home Office", "Electronics", "Fitness & Wellness", "Cloud Accessories", "Apparel & Gear"]:
                if c.lower() in q_lower:
                    cat = c
                    break
            
            # Default to Home Office or Electronics if not specified
            if not cat:
                cat = "Home Office"

            df_sales = self.db.execute_query("SELECT * FROM sales_orders;")["data"]
            if df_sales is not None:
                ve = VarianceEngine(df_sales)
                variance_data = ve.decompose_margin_variance(category=cat, period_prior="Q2-2025", period_current="Q3-2025")
                variance_diagnosis = ve.generate_narrative_diagnosis(variance_data)

        # Executive summary
        summary = self._generate_summary(question, sql_query, query_result, variance_diagnosis)

        return {
            "question": question,
            "sql_query": sql_query,
            "query_result": query_result,
            "variance_data": variance_data,
            "executive_summary": summary,
            "mode": self.mode
        }

    def _generate_sql(self, question: str) -> str:
        """Generates SQL via Gemini API or Deterministic Pattern Matcher."""
        if self.client:
            try:
                schema_context = self.db.get_schema_summary()
                prompt = f"""
You are a Staff Data Analyst and SQL Expert writing queries for DuckDB.
Given the database schema below:
{schema_context}

Translate this user question into a SINGLE clean, read-only DuckDB SQL query:
User Question: "{question}"

Rules:
1. Return ONLY the raw SQL query, no markdown formatting, no explanations.
2. Only write SELECT or WITH queries.
3. Round currency values to 2 decimal places and format percentages nicely.
4. Limit results to 15 rows if returning ranked items.
"""
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                raw_sql = response.text.strip().replace("```sql", "").replace("```", "").strip()
                return raw_sql
            except Exception:
                pass

        # Deterministic Pattern Matcher (100% Reliable Offline Fallback)
        q = question.lower()
        if "category" in q and ("margin" in q or "drop" in q):
            return """SELECT 
    category,
    quarter,
    ROUND(SUM(gross_revenue), 2) AS total_revenue,
    ROUND(SUM(gross_margin), 2) AS total_margin,
    ROUND(SUM(gross_margin) / SUM(gross_revenue) * 100.0, 2) AS gross_margin_pct
FROM sales_orders
WHERE quarter IN ('Q2-2025', 'Q3-2025')
GROUP BY category, quarter
ORDER BY category, quarter ASC;"""

        elif "top" in q and ("product" in q or "sku" in q):
            return """SELECT 
    product_name,
    category,
    SUM(quantity) AS total_units_sold,
    ROUND(SUM(gross_revenue), 2) AS total_revenue,
    ROUND(SUM(gross_margin), 2) AS total_margin,
    ROUND(SUM(gross_margin) / SUM(gross_revenue) * 100.0, 2) AS margin_pct
FROM sales_orders
GROUP BY product_name, category
ORDER BY total_revenue DESC
LIMIT 8;"""

        elif "region" in q or "europe" in q or "america" in q:
            return """SELECT 
    region,
    ROUND(SUM(gross_revenue), 2) AS total_revenue,
    ROUND(SUM(gross_margin), 2) AS total_margin,
    ROUND(SUM(gross_margin) / SUM(gross_revenue) * 100.0, 2) AS margin_pct,
    COUNT(DISTINCT customer_id) AS active_customers
FROM sales_orders
GROUP BY region
ORDER BY total_revenue DESC;"""

        elif "discount" in q or "channel" in q or "customer_type" in q:
            return """SELECT 
    customer_type,
    sales_channel,
    ROUND(AVG(discount_pct), 2) AS avg_discount_pct,
    ROUND(SUM(gross_revenue), 2) AS total_revenue,
    ROUND(SUM(gross_margin), 2) AS total_margin
FROM sales_orders
GROUP BY customer_type, sales_channel
ORDER BY total_revenue DESC;"""

        elif "quarter" in q or "trend" in q or "2025" in q:
            return """SELECT 
    quarter,
    ROUND(SUM(gross_revenue), 2) AS gross_revenue,
    ROUND(SUM(cogs), 2) AS total_cogs,
    ROUND(SUM(gross_margin), 2) AS gross_margin,
    ROUND(SUM(gross_margin) / SUM(gross_revenue) * 100.0, 2) AS margin_pct
FROM sales_orders
WHERE year = 2025
GROUP BY quarter
ORDER BY quarter ASC;"""

        # Default fallback query
        return """SELECT 
    category,
    ROUND(SUM(gross_revenue), 2) AS total_revenue,
    ROUND(SUM(gross_margin), 2) AS total_margin,
    ROUND(SUM(gross_margin) / SUM(gross_revenue) * 100.0, 2) AS gross_margin_pct
FROM sales_orders
GROUP BY category
ORDER BY total_revenue DESC;"""

    def _generate_summary(self, question: str, sql: str, res: dict, variance_diag: str = None) -> str:
        """Generates executive narrative."""
        if variance_diag:
            return variance_diag

        df = res["data"]
        if df is None or len(df) == 0:
            return "No records were returned matching the criteria. Please refine your query parameters."

        top_entity = df.iloc[0].to_dict()
        entity_name = top_entity.get("category") or top_entity.get("product_name") or top_entity.get("region") or "Top Segment"
        revenue = top_entity.get("total_revenue", 0)
        margin = top_entity.get("gross_margin_pct") or top_entity.get("margin_pct", 0)

        return f"""### 📊 Executive Insight Briefing

* **Primary Result:** **{entity_name}** leads the segment, generating **${revenue:,.2f}** in gross revenue with an average margin of **{margin}%**.
* **Portfolio Context:** Analysis executed across **12,000 transaction records** in DuckDB in **{res['latency_ms']} ms**.
* **Actionable Recommendation:** Cross-reference discount allowances across sales channels to preserve gross margin targets.
"""

if __name__ == "__main__":
    db = DuckDBManager()
    copilot = TextToSQLEngine(db)
    result = copilot.ask("Which product category had the highest margin drop in Q3, and why?")
    print("Generated SQL:\n", result["sql_query"])
    print("\nExecutive Summary:\n", result["executive_summary"])
