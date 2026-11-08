-- =====================================================================
-- 07 · Where should Operations focus? Size of each lever.
-- Lever A: sellers miss the handover deadline
-- Lever B: carrier delays in Rio de Janeiro + the Northeast (high late %)
-- Each late order is tagged with the FIRST lever it belongs to (no double counting).
-- =====================================================================

WITH order_deadline AS (
  SELECT order_id, MAX(shipping_limit_date) AS shipping_limit_date
  FROM olist.order_items
  GROUP BY order_id
),
tagged AS (
  SELECT
    CASE
      WHEN o.order_delivered_carrier_date > d.shipping_limit_date
        THEN 'A. Seller missed handover deadline'
      WHEN c.customer_state IN ('RJ', 'BA', 'CE', 'PE', 'MA', 'PB', 'PI', 'RN', 'AL', 'SE')
        THEN 'B. Carrier delay: Rio + Northeast'
      ELSE 'C. Carrier delay: rest of Brazil'
    END                                                                              AS cause,
    DATE(o.order_delivered_customer_date) > DATE(o.order_estimated_delivery_date)    AS is_late
  FROM olist.orders o
  JOIN order_deadline   d ON d.order_id    = o.order_id
  JOIN olist.customers  c ON c.customer_id = o.customer_id
  WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    AND o.order_delivered_carrier_date  IS NOT NULL
)
SELECT
  cause,
  COUNT(*)                                                         AS orders,
  COUNTIF(is_late)                                                 AS late_orders,
  ROUND(100 * COUNTIF(is_late) / COUNT(*), 1)                      AS late_pct,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)                 AS share_of_orders_pct,
  ROUND(100 * COUNTIF(is_late) / SUM(COUNTIF(is_late)) OVER (), 1) AS share_of_late_pct
FROM tagged
GROUP BY cause
ORDER BY cause;
