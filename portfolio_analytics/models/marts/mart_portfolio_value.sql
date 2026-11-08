WITH valuation_dates AS (
    SELECT DISTINCT price_date
    FROM {{ ref('stg_stock_prices') }}
),

tickers AS (
    SELECT DISTINCT ticker
    FROM {{ ref('stg_trades') }}
),

daily_holdings AS (
    SELECT
        d.price_date,
        t.ticker,
        SUM(tr.shares_bought) AS shares_held,
        SUM(tr.shares_bought * tr.price_paid_usd) AS cost_basis_usd
    FROM valuation_dates d
    CROSS JOIN tickers t
    JOIN {{ ref('stg_trades') }} tr
        ON tr.ticker = t.ticker
       AND tr.trade_date <= d.price_date
    GROUP BY d.price_date, t.ticker
    HAVING SUM(tr.shares_bought) > 0
),

position_values AS (
    SELECT
        h.price_date,
        h.ticker,
        h.shares_held,
        h.cost_basis_usd,
        p.close AS closing_price_usd,
        h.shares_held * p.close AS market_value_usd,
        (h.shares_held * p.close) - h.cost_basis_usd
            AS unrealized_gain_loss_usd
    FROM daily_holdings h
    JOIN LATERAL (
        SELECT close
        FROM {{ ref('stg_stock_prices') }} p
        WHERE p.ticker = h.ticker
          AND p.price_date <= h.price_date
        ORDER BY p.price_date DESC
        LIMIT 1
    ) p ON TRUE
),

portfolio_totals AS (
    SELECT
        price_date,
        SUM(market_value_usd) AS portfolio_value_usd
    FROM position_values
    GROUP BY price_date
),

exchange_rates AS (
    SELECT
        d.price_date,
        fx.rate AS usd_ngn_rate
    FROM valuation_dates d
    LEFT JOIN LATERAL (
        SELECT rate
        FROM {{ ref('stg_exchange_rates') }} fx
        WHERE fx.base_currency = 'USD'
          AND fx.quote_currency = 'NGN'
          AND fx.rate_date <= d.price_date
        ORDER BY fx.rate_date DESC
        LIMIT 1
    ) fx ON TRUE
)

SELECT
    p.price_date,
    p.ticker,
    p.shares_held,
    p.closing_price_usd,
    p.cost_basis_usd,
    p.market_value_usd,
    p.unrealized_gain_loss_usd,
    t.portfolio_value_usd,
    e.usd_ngn_rate,
    t.portfolio_value_usd * e.usd_ngn_rate
        AS portfolio_value_ngn
FROM position_values p
JOIN portfolio_totals t
    ON p.price_date = t.price_date
LEFT JOIN exchange_rates e
    ON p.price_date = e.price_date