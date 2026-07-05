from mcp.server.fastmcp import FastMCP

try:  # normal: imported as a package (console script, `python -m ...`)
    from .db import connect
    from .guard import assert_readonly
    from . import recs
except ImportError:  # fallback: file run directly (`python server.py`, `mcp dev server.py`)
    from mcp_postgres_explorer.db import connect
    from mcp_postgres_explorer.guard import assert_readonly
    from mcp_postgres_explorer import recs

mcp = FastMCP("postgres-explorer")


@mcp.tool()
def list_tables() -> list[str]:
    """List all tables in the public schema."""
    with connect() as c, c.cursor() as cur:
        cur.execute("""SELECT table_name FROM information_schema.tables
                       WHERE table_schema='public' ORDER BY table_name""")
        return [r[0] for r in cur.fetchall()]


@mcp.tool()
def describe_table(name: str) -> list[dict]:
    """Return columns and types for a table. Call this before writing a query."""
    with connect() as c, c.cursor() as cur:
        cur.execute("""SELECT column_name, data_type FROM information_schema.columns
                       WHERE table_schema='public' AND table_name=%s
                       ORDER BY ordinal_position""", (name,))
        return [{"column": col, "type": typ} for col, typ in cur.fetchall()]


@mcp.tool()
def query(sql: str, limit: int = 100) -> dict:
    """Run a READ-ONLY SQL query and return rows. Rejects any write or DDL.
    Use when the user gives you SQL directly, or after you've written SQL from a question."""
    assert_readonly(sql)
    safe = sql.strip().rstrip(";")
    with connect() as c, c.cursor() as cur:
        cur.execute(f"SELECT * FROM ({safe}) AS _q LIMIT {int(limit)}")
        cols = [d.name for d in cur.description]
        return {"columns": cols, "rows": [dict(zip(cols, r)) for r in cur.fetchall()]}


@mcp.resource("schema://public")
def schema() -> str:
    """The full DB schema, so the model can see structure without a tool call."""
    with connect() as c, c.cursor() as cur:
        cur.execute("""SELECT table_name, column_name, data_type FROM information_schema.columns
                       WHERE table_schema='public' ORDER BY table_name, ordinal_position""")
        return "\n".join(f"{t}.{col} :: {typ}" for t, col, typ in cur.fetchall())


@mcp.prompt()
def analyze_table(name: str) -> str:
    return (f"Profile the `{name}` table: row count, null rate per column, and notable "
            f"distributions. Use describe_table then query.")


@mcp.tool()
def recommend_for_user(customer_id: str, k: int = 10) -> list[dict]:
    """Recommend top-k products for a customer, using a trained ALS collaborative-filtering model.
    Use when the user asks what to recommend / offer / cross-sell to a specific customer."""
    return recs.recommend_for_user(customer_id, k)


@mcp.tool()
def similar_items(stock_code: str, k: int = 10) -> list[dict]:
    """Return products frequently bought alongside a given product (item-item neighbors) —
    a 'customers also bought' list. Use for product-to-product recommendations."""
    return recs.similar_items(stock_code, k)


def main():
    # Default stdio (used by local clients like Claude Code / Claude Desktop config).
    # Set MCP_TRANSPORT=streamable-http to serve over HTTP at http://localhost:8000/mcp
    # for HTTP-based MCP clients (or behind an HTTPS tunnel for remote-connector UIs).
    import os
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
