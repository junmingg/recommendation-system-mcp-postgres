import os
import pandas as pd
import psycopg

ADMIN_DSN = os.environ.get("DATABASE_URL_ADMIN", "postgresql://app:app@localhost:5432/demo")
SRC = os.environ.get("RETAIL_FILE", "data/online_retail.xlsx")

if SRC.endswith(".csv"):
    df = pd.read_csv(SRC, encoding="ISO-8859-1")
else:
    df = pd.read_excel(SRC)
df = df.dropna(subset=["CustomerID"])
df = df[df["Quantity"] > 0]
df["CustomerID"] = df["CustomerID"].astype(int).astype(str)   # keep as text throughout

cols = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"]
rows = list(df[cols].itertuples(index=False, name=None))

with psycopg.connect(ADMIN_DSN) as c, c.cursor() as cur:
    cur.execute("TRUNCATE transactions")
    with cur.copy("COPY transactions "
                  "(invoice_no,stock_code,description,quantity,invoice_date,unit_price,customer_id,country) "
                  "FROM STDIN") as cp:
        for r in rows:
            cp.write_row(r)
    c.commit()
print(f"Loaded {len(rows):,} rows")
