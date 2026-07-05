import pytest
from mcp_postgres_explorer.guard import assert_readonly


def test_allows_select():
    assert_readonly("SELECT * FROM transactions")
    assert_readonly("WITH t AS (SELECT 1) SELECT * FROM t")


@pytest.mark.parametrize("sql", [
    "DROP TABLE transactions", "DELETE FROM transactions",
    "UPDATE transactions SET quantity=0", "INSERT INTO transactions (quantity) VALUES (1)",
    "SELECT 1; DROP TABLE transactions", "TRUNCATE transactions",
    "ALTER TABLE transactions ADD COLUMN c int",
])
def test_rejects_writes(sql):
    with pytest.raises(ValueError):
        assert_readonly(sql)
