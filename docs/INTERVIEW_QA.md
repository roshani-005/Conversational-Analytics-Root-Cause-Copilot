# 💡 Technical Interview Q&A: Text-to-SQL & Variance Analytics

### Q1: "Why choose DuckDB over standard SQLite or Pandas for this project?"
**Answer:** *"Pandas performs in-memory row-oriented transformations which can become slow and memory-intensive as transactions scale. SQLite is row-oriented and designed for OLTP (transactional workloads). DuckDB, on the other hand, is an in-process **columnar OLAP database** equipped with a vectorized execution engine. It can scan millions of rows, compute group-by aggregations, and return results in under 15 milliseconds while supporting full standard SQL."*

### Q2: "What is Price-Volume-Mix (PVM) variance decomposition, and why does it matter?"
**Answer:** *"In corporate finance and data analytics, when gross margin changes between two quarters (\(\Delta M\)), simply saying 'sales dropped' is incomplete. PVM isolates:
1. **Price Variance:** \((P_2 - P_1) \times V_2\) — isolating how much profit was lost due to discounting.
2. **Volume Variance:** \((V_2 - V_1) \times M_1\) — isolating the profit change from selling more or fewer units.
3. **Cost Variance:** \((C_1 - C_2) \times V_2\) — isolating the impact of raw material and freight inflation.
By doing this, an executive immediately knows whether to fire their supply chain partner (Cost issue) or rein in their sales discounts (Price issue)."*

### Q3: "How do you prevent SQL Injection and dangerous operations in Text-to-SQL?"
**Answer:** *"I implemented a multi-layered defense:
1. **Read-Only Database Connection:** The connection pool opens DuckDB in strict read-only mode (`read_only=True`).
2. **AST & Keyword Validation:** The validation engine checks incoming queries and rejects any statements that contain prohibited keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`).
3. **Prefix Enforcement:** Queries must strictly begin with `SELECT` or `WITH`.
4. **Sandboxing:** No untrusted `eval()` or OS shell execution is used."*

### Q4: "How does the engine handle ambiguous or vague executive queries?"
**Answer:** *"The engine passes the complete schema context and sample values into the LLM system prompt. If an executive query lacks a time period, the model defaults to the latest fiscal quarter (e.g. Q3-2025) and explicitly notes this assumption in the executive briefing memo. Additionally, the app features one-click executive presets for standard queries."*
