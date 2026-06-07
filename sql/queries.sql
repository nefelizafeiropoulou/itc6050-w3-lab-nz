-- Q1 — Monthly revenue trend (GROUP BY + date_trunc)
SELECT
    date_trunc('month', order_date) AS month,
    COUNT(*) AS orders,
    SUM(total) AS revenue
FROM shop.orders
GROUP BY 1
ORDER BY 1;


-- Q2 — Top 10 products by revenue (JOIN + aggregation)
SELECT
    p.name AS product_name,
    SUM(oi.quantity) AS total_qty,
    SUM(oi.quantity * oi.unit_price_at_sale) AS revenue
FROM shop.order_item oi
JOIN shop.product p
    ON p.product_id = oi.product_id
GROUP BY p.product_id, p.name
ORDER BY revenue DESC
LIMIT 10;


-- Q3 — Average order value by status (aggregation + median)
SELECT
    status,
    COUNT(*) AS order_count,
    AVG(total) AS avg_total,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total) AS median_total
FROM shop.orders
GROUP BY status
ORDER BY status;


-- Q4 — Dormant customers (no orders in last 90 days)
WITH last_orders AS (
    SELECT
        c.customer_id,
        c.email,
        MAX(o.order_date) AS last_order_date
    FROM shop.customer c
    LEFT JOIN shop.orders o
        ON o.customer_id = c.customer_id
    GROUP BY c.customer_id, c.email
)
SELECT
    email,
    last_order_date,
    CASE
        WHEN last_order_date IS NULL THEN NULL
        ELSE (CURRENT_DATE - last_order_date::date)
    END AS days_dormant
FROM last_orders
WHERE last_order_date IS NULL
   OR last_order_date < NOW() - INTERVAL '90 days'
ORDER BY days_dormant DESC NULLS LAST;


-- Q5 — Top customers by lifetime spend (window functions: RANK + LAG)
WITH customer_spend AS (
    SELECT
        c.customer_id,
        c.email,
        SUM(o.total) AS lifetime_spend
    FROM shop.customer c
    JOIN shop.orders o
        ON o.customer_id = c.customer_id
    GROUP BY c.customer_id, c.email
),
ranked AS (
    SELECT
        email,
        lifetime_spend,
        RANK() OVER (ORDER BY lifetime_spend DESC) AS rank,
        LAG(lifetime_spend) OVER (ORDER BY lifetime_spend DESC) AS prev_spend
    FROM customer_spend
)
SELECT
    rank,
    email,
    lifetime_spend,
    (prev_spend - lifetime_spend) AS gap_to_previous
FROM ranked
ORDER BY rank
LIMIT 20;