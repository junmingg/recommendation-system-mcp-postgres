CREATE TABLE transactions (
  invoice_no   text,
  stock_code   text,
  description  text,
  quantity     int,
  invoice_date timestamp,
  unit_price   numeric,
  customer_id  text,
  country      text
);
CREATE INDEX ON transactions (customer_id);
CREATE INDEX ON transactions (stock_code);

-- READ-ONLY role the MCP server uses (the real safety layer)
CREATE ROLE readonly LOGIN PASSWORD 'readonly';
GRANT CONNECT ON DATABASE demo TO readonly;
GRANT USAGE  ON SCHEMA public   TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly;
