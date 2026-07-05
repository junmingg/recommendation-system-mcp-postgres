import sqlglot

ALLOWED = {"SELECT", "WITH"}   # SELECT and CTEs only


def assert_readonly(sql: str) -> None:
    stmts = sqlglot.parse(sql, read="postgres")
    if len(stmts) != 1 or stmts[0] is None:
        raise ValueError("Send exactly one SQL statement.")
    kind = stmts[0].key.upper()
    if kind not in ALLOWED:
        raise ValueError(f"Only read-only SELECT queries are allowed (got {kind}).")
