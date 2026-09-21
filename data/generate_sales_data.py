"""
Realistic Multi-Dimensional Sales & Operational Data Generator
Generates 10,000+ transaction lines across 24 months with realistic margin drops,
price-volume-mix dynamics, and writes directly into DuckDB and CSV.
"""

import os
import duckdb
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

def generate_sales_warehouse(num_orders=12000, output_dir="data"):
    os.makedirs(output_dir, exist_ok=True)
    print(f"Generating realistic enterprise sales data with {num_orders} orders...")

    # Products Catalog
    products = [
        {"product_id": "PROD-101", "name": "UltraBook Pro 16", "category": "Electronics", "base_cost": 850.0, "base_price": 1299.0},
        {"product_id": "PROD-102", "name": "4K Curved Monitor 34\"", "category": "Electronics", "base_cost": 320.0, "base_price": 549.0},
        {"product_id": "PROD-103", "name": "Noise-Canceling Headset", "category": "Electronics", "base_cost": 95.0, "base_price": 199.0},
        {"product_id": "PROD-104", "name": "4K Studio Webcam", "category": "Electronics", "base_cost": 65.0, "base_price": 149.0},
        
        {"product_id": "PROD-201", "name": "ErgoPro Mesh Chair", "category": "Home Office", "base_cost": 180.0, "base_price": 389.0},
        {"product_id": "PROD-202", "name": "Dual-Motor Standing Desk", "category": "Home Office", "base_cost": 240.0, "base_price": 529.0},
        {"product_id": "PROD-203", "name": "Acoustic Desk Privacy Panel", "category": "Home Office", "base_cost": 45.0, "base_price": 119.0},
        
        {"product_id": "PROD-301", "name": "Smart Folding Treadmill", "category": "Fitness & Wellness", "base_cost": 480.0, "base_price": 899.0},
        {"product_id": "PROD-302", "name": "Adjustable Dumbbell Set", "category": "Fitness & Wellness", "base_cost": 140.0, "base_price": 299.0},
        {"product_id": "PROD-303", "name": "Percussive Massage Gun", "category": "Fitness & Wellness", "base_cost": 55.0, "base_price": 159.0},
        
        {"product_id": "PROD-401", "name": "Thunderbolt 4 Docking Station", "category": "Cloud Accessories", "base_cost": 110.0, "base_price": 249.0},
        {"product_id": "PROD-402", "name": "Wireless Mechanical Keyboard", "category": "Cloud Accessories", "base_cost": 50.0, "base_price": 129.0},
        {"product_id": "PROD-403", "name": "Precision Ergonomic Mouse", "category": "Cloud Accessories", "base_cost": 32.0, "base_price": 79.0},
        
        {"product_id": "PROD-501", "name": "Waterproof Commuter Backpack", "category": "Apparel & Gear", "base_cost": 40.0, "base_price": 110.0},
        {"product_id": "PROD-502", "name": "All-Weather Technical Parka", "category": "Apparel & Gear", "base_cost": 85.0, "base_price": 220.0}
    ]

    df_products = pd.DataFrame(products)

    # Order generation
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)
    total_days = (end_date - start_date).days

    order_ids = [f"ORD-{100000 + i}" for i in range(num_orders)]
    customer_ids = [f"CUST-{np.random.randint(1000, 3500)}" for _ in range(num_orders)]
    customer_types = np.random.choice(["Enterprise", "Mid-Market", "Consumer"], size=num_orders, p=[0.25, 0.40, 0.35])
    regions = np.random.choice(["North America", "Europe", "Asia-Pacific", "Latin America"], size=num_orders, p=[0.45, 0.30, 0.18, 0.07])
    channels = np.random.choice(["Direct Sales", "Online Marketplace", "Retail Partner"], size=num_orders, p=[0.35, 0.45, 0.20])

    random_days = np.random.randint(0, total_days + 1, size=num_orders)
    order_dates = [start_date + timedelta(days=int(d)) for d in random_days]

    # Assign products
    prod_indices = np.random.randint(0, len(products), size=num_orders)
    chosen_products = [products[idx] for idx in prod_indices]

    rows = []
    for i in range(num_orders):
        p = chosen_products[i]
        dt = order_dates[i]
        year = dt.year
        quarter_num = (dt.month - 1) // 3 + 1
        quarter_str = f"Q{quarter_num}-{year}"

        cost = p["base_cost"]
        price = p["base_price"]
        category = p["category"]
        ctype = customer_types[i]

        # Realistic volume logic
        if ctype == "Enterprise":
            qty = int(np.random.randint(5, 30))
            base_discount = np.random.uniform(0.08, 0.18)
        elif ctype == "Mid-Market":
            qty = int(np.random.randint(2, 10))
            base_discount = np.random.uniform(0.04, 0.12)
        else:
            qty = int(np.random.randint(1, 4))
            base_discount = np.random.uniform(0.0, 0.08)

        # Injected Business Anomaly 1: Q3-2025 Home Office Heavy Discounting War (Price Drop)
        if quarter_str == "Q3-2025" and category == "Home Office":
            discount = base_discount + float(np.random.uniform(0.20, 0.32)) # Deep 25-35% discounts
        # Injected Business Anomaly 2: Q3-2025 Electronics Air Freight Inflation (Cost Hike)
        elif quarter_str == "Q3-2025" and category == "Electronics":
            cost = cost * float(np.random.uniform(1.22, 1.35)) # 25-35% cost spike
            discount = base_discount
        # Injected Business Anomaly 3: Q4 Holiday Season Promotion
        elif quarter_num == 4:
            discount = base_discount + float(np.random.uniform(0.05, 0.12))
        else:
            discount = base_discount

        discount = min(discount, 0.50) # Cap at 50%
        effective_price = round(price * (1.0 - discount), 2)
        gross_revenue = round(effective_price * qty, 2)
        total_cogs = round(cost * qty, 2)
        gross_margin = round(gross_revenue - total_cogs, 2)
        gross_margin_pct = round((gross_margin / gross_revenue) * 100.0, 2) if gross_revenue > 0 else 0.0

        rows.append({
            "order_id": order_ids[i],
            "order_date": dt.strftime("%Y-%m-%d"),
            "year": year,
            "quarter": quarter_str,
            "month": dt.strftime("%Y-%m"),
            "customer_id": customer_ids[i],
            "customer_type": ctype,
            "product_id": p["product_id"],
            "product_name": p["name"],
            "category": category,
            "region": regions[i],
            "sales_channel": channels[i],
            "unit_cost": round(cost, 2),
            "unit_price": round(price, 2),
            "discount_pct": round(discount * 100, 2),
            "effective_price": effective_price,
            "quantity": qty,
            "gross_revenue": gross_revenue,
            "cogs": total_cogs,
            "gross_margin": gross_margin,
            "gross_margin_pct": gross_margin_pct
        })

    df_sales = pd.DataFrame(rows)
    df_sales = df_sales.sort_values(by="order_date").reset_index(drop=True)

    # Save CSVs
    df_products.to_csv(os.path.join(output_dir, "products.csv"), index=False)
    df_sales.to_csv(os.path.join(output_dir, "sales_orders.csv"), index=False)

    # Save directly to DuckDB
    duckdb_path = os.path.join(output_dir, "analytics_warehouse.duckdb")
    if os.path.exists(duckdb_path):
        os.remove(duckdb_path)

    con = duckdb.connect(duckdb_path)
    con.execute("CREATE TABLE products AS SELECT * FROM df_products")
    con.execute("CREATE TABLE sales_orders AS SELECT * FROM df_sales")
    con.close()

    print(f"Dataset successfully created and ingested into DuckDB at: {duckdb_path}")
    print(f"Total Transactions: {len(df_sales):,}")
    print(f"Total Net Sales Revenue: ${df_sales['gross_revenue'].sum():,.2f}")
    print(f"Average Gross Margin: {df_sales['gross_margin'].sum() / df_sales['gross_revenue'].sum() * 100:.2f}%")
    return df_sales

if __name__ == "__main__":
    generate_sales_warehouse(num_orders=12000, output_dir="data")
