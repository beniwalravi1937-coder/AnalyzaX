import json
import os
import openpyxl
import polars as pl

fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
os.makedirs(fixtures_dir, exist_ok=True)

# 1. small_sales.csv
sales_path = os.path.join(fixtures_dir, "small_sales.csv")
with open(sales_path, "w", encoding="utf-8") as f:
    f.write("id,product,price,quantity\n1,Widget A,19.99,5\n2,Widget B,29.99,2\n3,Gadget X,99.50,1\n")

# 2. small_customers.csv (semicolon delimited)
customers_path = os.path.join(fixtures_dir, "small_customers.csv")
with open(customers_path, "w", encoding="utf-8") as f:
    f.write("customer_id;name;country\n101;Alice;USA\n102;Bob;Canada\n103;Charlie;UK\n")

# 3. sample.json (array of objects)
json_path = os.path.join(fixtures_dir, "sample.json")
json_data = [
    {"order_id": "ord_1", "customer": "Alice", "total": 99.95},
    {"order_id": "ord_2", "customer": "Bob", "total": 59.98},
    {"order_id": "ord_3", "customer": "Charlie", "total": 99.50},
]
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2)

# 4. sample.parquet
parquet_path = os.path.join(fixtures_dir, "sample.parquet")
df = pl.DataFrame({
    "employee_id": [1, 2, 3],
    "department": ["Engineering", "Marketing", "Sales"],
    "salary": [120000, 95000, 85000],
})
df.write_parquet(parquet_path)

# 5. sample.xlsx
xlsx_path = os.path.join(fixtures_dir, "sample.xlsx")
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "MonthlyRevenue"
ws.append(["month", "revenue", "expenses"])
ws.append(["Jan", 50000, 30000])
ws.append(["Feb", 55000, 32000])
ws.append(["Mar", 60000, 31000])
wb.save(xlsx_path)

# 6. invalid.csv (empty)
invalid_path = os.path.join(fixtures_dir, "invalid.csv")
with open(invalid_path, "w", encoding="utf-8") as f:
    f.write("")

# 7. unsupported.txt
unsupported_path = os.path.join(fixtures_dir, "unsupported.txt")
with open(unsupported_path, "w", encoding="utf-8") as f:
    f.write("Hello world unsupported format\n")

print("All fixtures generated successfully.")
