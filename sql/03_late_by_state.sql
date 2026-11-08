-- =====================================================================
-- 03 · Where are customers waiting too long?
-- Late % and delivery time by the customer's state.
-- =====================================================================

WITH delivered AS (
  SELECT
    c.customer_state,
    DATE_DIFF(DATE(o.order_delivered_customer_date), DATE(o.order_purchase_timestamp), DAY)  AS actual_days,
    DATE_DIFF(DATE(o.order_estimated_delivery_date), DATE(o.order_purchase_timestamp), DAY)  AS promised_days,
    DATE(o.order_delivered_customer_date) > DATE(o.order_estimated_delivery_date)            AS is_late
  FROM olist.orders o
  JOIN olist.customers c ON c.customer_id = o.customer_id
  WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
)
SELECT
  customer_state,
  COUNT(*)                                                        AS delivered_orders,
  COUNTIF(is_late)                                                AS late_orders,
  ROUND(100 * COUNTIF(is_late) / COUNT(*), 1)                     AS late_pct,
  ROUND(100 * COUNTIF(is_late) / SUM(COUNTIF(is_late)) OVER (), 1) AS share_of_all_late_pct,
  ROUND(AVG(actual_days), 1)                                      AS avg_actual_days,
  ROUND(AVG(promised_days), 1)                                    AS avg_promised_days
FROM delivered
GROUP BY customer_state
HAVING COUNT(*) >= 100              -- ignore very small states
ORDER BY late_orders DESC;
