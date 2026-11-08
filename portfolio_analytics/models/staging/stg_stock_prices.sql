SELECT
    CAST(date AS DATE) AS price_date,
    UPPER(TRIM(ticker)) AS ticker,
    open,
    high,
    low,
    close,
    volume,
    dividends,
    stock_splits
FROM {{ source('warehouse', 'stock_prices') }}
WHERE date IS NOT NULL
  AND ticker IS NOT NULL