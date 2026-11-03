-- R6: Map each order to the latest available BRL-to-USD FX rate.
-- Use approval date when available; otherwise purchase date.
-- Never use a future FX rate.

CREATE TABLE IF NOT EXISTS order_fx_mapping (
    order_id VARCHAR(50) NOT NULL PRIMARY KEY,
    fx_date DATE DEFAULT NULL,
    exchange_rate DECIMAL(18,6) DEFAULT NULL
);

INSERT INTO order_fx_mapping (
    order_id,
    fx_date,
    exchange_rate
)
SELECT
    o.order_id,
    fx.rate_date,
    fx.exchange_rate
FROM fact_order o
LEFT JOIN ref_fx_rate fx
    ON fx.rate_date = (
        SELECT MAX(r.rate_date)
        FROM ref_fx_rate r
        WHERE r.from_currency = 'BRL'
          AND r.to_currency = 'USD'
          AND r.rate_date <= DATE(
              COALESCE(o.approved_timestamp, o.purchase_timestamp)
          )
    )
ON DUPLICATE KEY UPDATE
    fx_date = VALUES(fx_date),
    exchange_rate = VALUES(exchange_rate);

-- Apply mapped FX values to order items.
UPDATE fact_order_item i
JOIN order_fx_mapping m
    ON i.order_id = m.order_id
SET
    i.fx_rate_date_used = m.fx_date,
    i.fx_rate_brl_to_usd = m.exchange_rate;
