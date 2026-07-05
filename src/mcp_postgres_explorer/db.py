import os
import psycopg

DSN = os.environ.get("DATABASE_URL", "postgresql://readonly:readonly@localhost:5432/demo")


def connect():
    conn = psycopg.connect(DSN, autocommit=True)
    with conn.cursor() as cur:
        cur.execute("SET default_transaction_read_only = on")  # driver-layer belt
        cur.execute("SET statement_timeout = 5000")            # 5s cap
    return conn
