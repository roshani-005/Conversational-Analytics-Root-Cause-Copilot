"""
DuckDB Database Manager & Read-Only Query Executor
Provides sub-second analytical execution, schema introspection, and strict query security guardrails.
"""

import os
import re
import time
import duckdb
import pandas as pd

class DuckDBManager:
    FORBIDDEN_KEYWORDS = [
        r"\bdrop\b", r"\bdelete\b", r"\bupdate\b", r"\binsert\b",
        r"\balter\b", r"\btruncate\b", r"\bcreate\b", r"\breplace\b",
        r"\bgrant\b", r"\brevoke\b", r"\bexec\b", r"\bexecute\b"
    ]

    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            db_path = os.path.join(base_dir, "data", "analytics_warehouse.duckdb")
        
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self):
        """Ensures the DuckDB database exists; if not, triggers generator."""
        if not os.path.exists(self.db_path):
            from data.generate_sales_data import generate_sales_warehouse
            output_dir = os.path.dirname(self.db_path)
            generate_sales_warehouse(num_orders=12000, output_dir=output_dir)

    def get_connection(self, read_only=True):
        return duckdb.connect(self.db_path, read_only=read_only)

    def validate_sql(self, sql_query: str) -> tuple[bool, str]:
        """
        Validates that a SQL query is strictly read-only and free of DDL/DML mutation risks.
        """
        clean_sql = sql_query.strip().lower()
        
        # Check forbidden keywords
        for pattern in self.FORBIDDEN_KEYWORDS:
            if re.search(pattern, clean_sql):
                keyword = pattern.replace(r"\b", "")
                return False, f"Security Violation: Query contains prohibited keyword '{keyword}'. Only read-only SELECT queries are permitted."

        if not clean_sql.startswith("select") and not clean_sql.startswith("with"):
            return False, "Security Violation: Query must begin with SELECT or WITH."

        return True, "Valid"

    def execute_query(self, sql_query: str) -> dict:
        """
        Executes a validated read-only query in DuckDB, tracking latency in milliseconds.
        """
        is_valid, message = self.validate_sql(sql_query)
        if not is_valid:
            return {
                "success": False,
                "error": message,
                "data": None,
                "latency_ms": 0.0,
                "query": sql_query
            }

        start_time = time.perf_counter()
        try:
            con = self.get_connection(read_only=True)
            df = con.execute(sql_query).df()
            con.close()
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            return {
                "success": True,
                "error": None,
                "data": df,
                "latency_ms": elapsed_ms,
                "query": sql_query
            }
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "latency_ms": elapsed_ms,
                "query": sql_query
            }

    def get_schema_summary(self) -> str:
        """
        Generates schema string representation for LLM prompt context.
        """
        con = self.get_connection(read_only=True)
        tables = con.execute("SHOW TABLES").fetchall()
        schema_lines = []

        for table in tables:
            tname = table[0]
            cols = con.execute(f"DESCRIBE {tname}").fetchall()
            col_strs = [f"{c[0]} ({c[1]})" for c in cols]
            schema_lines.append(f"Table: {tname}\nColumns: {', '.join(col_strs)}")

        con.close()
        return "\n\n".join(schema_lines)

if __name__ == "__main__":
    db = DuckDBManager()
    print("Schema Summary:")
    print(db.get_schema_summary())
    res = db.execute_query("SELECT category, COUNT(*) as orders, ROUND(SUM(gross_revenue), 2) as revenue FROM sales_orders GROUP BY category ORDER BY revenue DESC;")
    print("\nTest Query Result:")
    print(res["data"])
    print(f"Latency: {res['latency_ms']} ms")
