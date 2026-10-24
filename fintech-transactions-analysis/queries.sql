-- The same analysis in SQL. Table name: transactions
-- (Import the CSV into SQLite / MySQL / PostgreSQL and run these)

-- 1. Total volume and average ticket size (successful only)
SELECT COUNT(*)            AS successful_txns,
       ROUND(SUM(amount),2) AS total_volume,
       ROUND(AVG(amount),2) AS avg_ticket
FROM transactions
WHERE status = 'Success';

-- 2. Failure rate by payment method
SELECT payment_method,
       ROUND(100.0 * SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct
FROM transactions
GROUP BY payment_method
ORDER BY failure_rate_pct DESC;

-- 3. Category-wise volume
SELECT category, ROUND(SUM(amount),2) AS volume
FROM transactions
WHERE status = 'Success'
GROUP BY category
ORDER BY volume DESC;

-- 4. Top 10 customers
SELECT customer_id, ROUND(SUM(amount),2) AS total_spent
FROM transactions
WHERE status = 'Success'
GROUP BY customer_id
ORDER BY total_spent DESC
LIMIT 10;

-- 5. Month-over-month growth (window function)
WITH monthly AS (
    SELECT SUBSTR(timestamp, 1, 7) AS month, SUM(amount) AS volume
    FROM transactions
    WHERE status = 'Success'
    GROUP BY SUBSTR(timestamp, 1, 7)
)
SELECT month,
       ROUND(volume,2) AS volume,
       ROUND(100.0 * (volume - LAG(volume) OVER (ORDER BY month)) / LAG(volume) OVER (ORDER BY month), 2) AS mom_growth_pct
FROM monthly;

-- 6. Rank of each customer within their city (RANK)
SELECT city, customer_id, ROUND(SUM(amount),2) AS spent,
       RANK() OVER (PARTITION BY city ORDER BY SUM(amount) DESC) AS city_rank
FROM transactions
WHERE status = 'Success'
GROUP BY city, customer_id;
