-- =====================================================================
-- 05 · Seller scorecard: which sellers repeatedly miss the handover deadline?
-- Sellers with 50+ delivered orders. Use this list for warnings / penalties.
-- =====================================================================

WITH order_seller AS (               -- one row per order and seller
  SELECT order_id, seller_id, MAX(shipping_limit_date) AS shipping_limit_date
  FROM olist.order_items
  GROUP BY order_id, seller_id
),
reviews AS (
  SELECT order_id, AVG(review_score) AS review_score
  FROM olist.order_reviews
  GROUP BY order_id
),
seller_orders AS (
  SELECT
    os.seller_id,
    o.order_id,
    o.order_delivered_carrier_date > os.shipping_limit_date                          AS missed_deadline,
    DATE(o.order_delivered_customer_date) > DATE(o.order_estimated_delivery_date)    AS is_late,
    r.review_score
  FROM order_seller os
  JOIN olist.orders o ON o.order_id = os.order_id
  LEFT JOIN reviews r ON r.order_id = o.order_id
  WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    AND o.order_delivered_carrier_date  IS NOT NULL
)
SELECT
  so.seller_id,
  s.seller_state,
  COUNT(*)                                              AS delivered_orders,
  ROUND(100 * COUNTIF(missed_deadline) / COUNT(*), 1)   AS missed_deadline_pct,
  ROUND(100 * COUNTIF(is_late) / COUNT(*), 1)           AS late_pct,
  ROUND(AVG(review_score), 2)                           AS avg_review_score
FROM seller_orders so
JOIN olist.sellers s ON s.seller_id = so.seller_id
GROUP BY so.seller_id, s.seller_state
HAVING COUNT(*) >= 50
ORDER BY missed_deadline_pct DESC
LIMIT 20;
