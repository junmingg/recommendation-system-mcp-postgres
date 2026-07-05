# Postgres MCP Server + Recommender

An **MCP server** that lets any MCP-compatible client or agent — Claude Desktop, Claude Code, Cursor,
or a custom LLM harness — do two things over one e-commerce Postgres database: **read-only SQL
analytics** and **ML recommendations** (ALS collaborative filtering). Because it speaks the open
[Model Context Protocol](https://modelcontextprotocol.io), any agentic host that supports MCP can drive
it — the same data, two capabilities, one server.

![demo](assets/demo.gif)

*Analytics, an ML recommendation, and a refused `DROP` — all driven through the MCP server. Scripted walkthrough built with Remotion, using real values from the live database and trained model.*

## Quickstart

```bash
# 1. Postgres in Docker (schema.sql seeds the table + read-only role on first boot)
docker compose up -d

# 2. Python env + deps, then install this package (needed so the server imports cleanly)
uv venv --python 3.11 .venv
uv pip install "mcp[cli]" "psycopg[binary]" sqlglot pytest implicit scipy numpy pandas openpyxl
uv pip install -e .

# 3. Load the real UCI Online Retail dataset (~398k transactions)
#    Download to data/online_retail.xlsx first:
#    https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx
python scripts/load_data.py

# 4. Train + offline-eval the recommender (writes models/als.pkl)
python scripts/train_recs.py

# 5. Inspect all tools locally
mcp dev src/mcp_postgres_explorer/server.py
```

## Connect a client

Any MCP-compatible host works (Cursor, Cline, Zed, or a custom agent using an MCP SDK). Claude is shown
below as the tested example.

Use the Python from the `.venv` you installed into — clients launch the command directly and do **not**
activate a virtualenv. On Windows that's `.venv\Scripts\python.exe`; on macOS/Linux `.venv/bin/python`.
`RECS_MODEL` must be an absolute path so the recommender finds the model regardless of working directory.

**Claude Code:**
```bash
claude mcp add postgres-explorer \
  -e DATABASE_URL=postgresql://readonly:readonly@localhost:5432/demo \
  -e RECS_MODEL=/ABS/PATH/models/als.pkl \
  -- /ABS/PATH/.venv/bin/python /ABS/PATH/src/mcp_postgres_explorer/server.py
```

**Claude Desktop** — add to `claude_desktop_config.json` (Settings → Developer → Edit Config), restart:
```json
{
  "mcpServers": {
    "postgres-explorer": {
      "command": "/ABS/PATH/.venv/bin/python",
      "args": ["/ABS/PATH/src/mcp_postgres_explorer/server.py"],
      "env": {
        "DATABASE_URL": "postgresql://readonly:readonly@localhost:5432/demo",
        "RECS_MODEL": "/ABS/PATH/models/als.pkl"
      }
    }
  }
}
```

## Tools / resources / prompts

| Name | Kind | Description |
|---|---|---|
| `list_tables` | tool | List tables in the public schema. |
| `describe_table` | tool | Columns and types for a table. |
| `query` | tool | Run a **read-only** SQL query (rejects any write/DDL). |
| `recommend_for_user` | tool | Top-k product recommendations for a customer (ALS). |
| `similar_items` | tool | "Customers also bought" item-item neighbors. |
| `schema://public` | resource | Full DB schema as text. |
| `analyze_table` | prompt | Template to profile a table. |

## Safety model (three read-only layers)

A `DROP` is rejected **three** independent ways:
1. **DB role** — the server connects as `readonly`, which only holds `SELECT` (see `schema.sql`).
2. **Read-only transactions** — `SET default_transaction_read_only = on` at the driver layer (`db.py`).
3. **SQL-parser allowlist** — `guard.assert_readonly` parses with `sqlglot` and permits only `SELECT`/`WITH`.

Unit-tested in `tests/test_guard.py` (run `pytest -q`).

![DROP rejected in Claude Desktop](assets/demo-safety.png)

*Live in Claude Desktop: the agent can query freely but a `DROP TABLE` is refused by the guardrail.*

## Recommender

- **Algorithm:** ALS matrix factorization (`implicit`), 64 factors, trained on customer × product
  purchase confidence.
- **Offline eval** (leave-last-out, 4,247 held-out users): **recall@10 = 0.1095, precision@10 = 0.0109**.
- **Serving:** the trained model is pickled to `models/als.pkl` and loaded lazily by `recs.py`. Because
  it's trained on your own DB, run `scripts/train_recs.py` before serving — the model is not shipped.

![Recommendations in Claude Desktop](assets/demo-recs.png)

*Live in Claude Desktop: `recommend_for_user` returns ranked products with ALS scores for a customer.*

## License

MIT
