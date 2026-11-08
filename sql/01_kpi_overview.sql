-- =====================================================================
-- 01 · Headline KPIs
-- Question: How often are orders late, and how long do customers wait?
-- LATE = delivered to the customer after the estimated delivery date
--        that Olist showed at checkout (compared as calendar dates).
-- =====================================================================

WITH delivered AS (
  SELECT
    o.order_id,
    DATE_DIFF(DATE(o.order_delivered_customer_date), DATE(o.order_purchase_timestamp), DAY)      AS actual_days,
    DATE_DIFF(DATE(o.order_estimated_delivery_date), DATE(o.order_purchase_timestamp), DAY)      AS promised_days,
    DATE(o.order_delivered_customer_date) > DATE(o.order_estimated_delivery_date)                AS is_late
  FROM olist.orders o
  WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
)
SELECT
  COUNT(*)                                        AS delivered_orders,
  COUNTIF(is_late)                                AS late_orders,
  ROUND(100 * COUNTIF(is_late) / COUNT(*), 1)     AS late_pct,
  ROUND(AVG(actual_days), 1)                      AS avg_actual_days,
  ROUND(AVG(promised_days), 1)                    AS avg_promised_days
FROM delivered;
