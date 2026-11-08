SELECT
    TRIM(trade_id) AS trade_id,
    CAST(trade_date AS DATE) AS trade_date,
    UPPER(TRIM(ticker)) AS ticker,
    shares_bought,
    price_paid_usd
FROM {{ source('warehouse', 'trades') }}
WHERE trade_id IS NOT NULL
  AND trade_date IS NOT NULL
  AND ticker IS NOT NULL