-- =====================================================================
-- 06 · Monthly trend: when does lateness spike, and which stage slows down?
-- Months with fewer than 500 orders (start and end of the data) are left out.
-- =====================================================================

SELECT
  FORMAT_DATE('%Y-%m', DATE(o.order_purchase_timestamp))                                     AS order_month,
  COUNT(*)                                                                                   AS delivered_orders,
  ROUND(100 * COUNTIF(DATE(o.order_delivered_customer_date)
                      > DATE(o.order_estimated_delivery_date)) / COUNT(*), 1)               AS late_pct,
  ROUND(AVG(DATE_DIFF(DATE(o.order_delivered_carrier_date),
                      DATE(o.order_purchase_timestamp), DAY)), 1)                           AS avg_seller_days,
  ROUND(AVG(DATE_DIFF(DATE(o.order_delivered_customer_date),
                      DATE(o.order_delivered_carrier_date), DAY)), 1)                       AS avg_carrier_days,
  ROUND(AVG(DATE_DIFF(DATE(o.order_estimated_delivery_date),
                      DATE(o.order_purchase_timestamp), DAY)), 1)                           AS avg_promised_days
FROM olist.orders o
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_delivered_carrier_date  IS NOT NULL
GROUP BY order_month
HAVING COUNT(*) >= 500
ORDER BY order_month;
