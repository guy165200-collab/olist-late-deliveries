-- =====================================================================
-- 04 · Who causes the delay: the seller or the carrier?
-- Seller stage : purchase -> handed to carrier (deadline = shipping_limit_date)
-- Carrier stage: handed to carrier -> delivered to customer
-- =====================================================================

WITH order_deadline AS (
  SELECT order_id, MAX(shipping_limit_date) AS shipping_limit_date
  FROM olist.order_items
  GROUP BY order_id
),
delivered AS (
  SELECT
    o.order_id,
    DATE(o.order_delivered_customer_date) > DATE(o.order_estimated_delivery_date)              AS is_late,
    o.order_delivered_carrier_date > d.shipping_limit_date                                     AS seller_missed_deadline,
    DATE_DIFF(DATE(o.order_delivered_carrier_date),  DATE(o.order_purchase_timestamp), DAY)    AS seller_days,
    DATE_DIFF(DATE(o.order_delivered_customer_date), DATE(o.order_delivered_carrier_date), DAY) AS carrier_days
  FROM olist.orders o
  JOIN order_deadline d ON d.order_id = o.order_id
  WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    AND o.order_delivered_carrier_date  IS NOT NULL
)

-- 1) Days spent in each stage: late vs on-time orders
SELECT
  IF(is_late, 'Late', 'On time')                                   AS delivery,
  COUNT(*)                                                         AS orders,
  ROUND(AVG(seller_days), 1)                                       AS avg_seller_days,
  ROUND(AVG(carrier_days), 1)                                      AS avg_carrier_days,
  ROUND(100 * COUNTIF(seller_missed_deadline) / COUNT(*), 1)       AS seller_missed_deadline_pct
FROM delivered
GROUP BY delivery;

-- 2) Late rate when the seller hands over on time vs. after the deadline
WITH order_deadline AS (
  SELECT order_id, MAX(shipping_limit_date) AS shipping_limit_date
  FROM olist.order_items
  GROUP BY order_id
)
SELECT
  IF(o.order_delivered_carrier_date > d.shipping_limit_date,
     'Seller missed deadline', 'Seller on time')                                     AS seller_handover,
  COUNT(*)                                                                           AS orders,
  ROUND(100 * COUNTIF(DATE(o.order_delivered_customer_date)
                      > DATE(o.order_estimated_delivery_date)) / COUNT(*), 1)       AS late_pct
FROM olist.orders o
JOIN order_deadline d ON d.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_delivered_carrier_date  IS NOT NULL
GROUP BY seller_handover;
