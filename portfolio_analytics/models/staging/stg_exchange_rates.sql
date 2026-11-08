SELECT
    CAST(date AS DATE) AS rate_date,
    UPPER(TRIM(base)) AS base_currency,
    UPPER(TRIM(quote)) AS quote_currency,
    rate
FROM {{ source('warehouse', 'exchange_rates') }}
WHERE date IS NOT NULL
  AND base IS NOT NULL
  AND quote IS NOT NULL
  AND rate IS NOT NULL