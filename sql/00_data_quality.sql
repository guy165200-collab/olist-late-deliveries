-- =====================================================================
-- 00 · Data quality checks
-- Question: Can we trust the data, and what do we need to clean?
-- Engine: Google BigQuery (Standard SQL). Dataset name: olist
-- =====================================================================

-- 1) Row count per table
SELECT 'orders' AS table_name, COUNT(*) AS row_count FROM olist.orders
UNION ALL SELECT 'order_items',    COUNT(*) FROM olist.order_items
UNION ALL SELECT 'order_reviews',  COUNT(*) FROM olist.order_reviews
UNION ALL SELECT 'order_payments', COUNT(*) FROM olist.order_payments
UNION ALL SELECT 'customers',      COUNT(*) FROM olist.customers
UNION ALL SELECT 'sellers',        COUNT(*) FROM olist.sellers
UNION ALL SELECT 'products',       COUNT(*) FROM olist.products;

-- 2) Order status: only 'delivered' orders can be on time or late
SELECT order_status, COUNT(*) AS orders
FROM olist.orders
GROUP BY order_status
ORDER BY orders DESC;

-- 3) Delivered orders with missing dates (excluded from the analysis)
SELECT
  COUNTIF(order_delivered_customer_date IS NULL) AS missing_customer_delivery_date,
  COUNTIF(order_delivered_carrier_date  IS NULL) AS missing_carrier_pickup_date
FROM olist.orders
WHERE order_status = 'delivered';

-- 4) Some orders have more than one review -> we average the score per order
SELECT
  COUNT(*)                 AS reviews,
  COUNT(DISTINCT order_id) AS orders_with_review
FROM olist.order_reviews;

-- 5) Orders with items from more than one seller (1.3%)
SELECT COUNT(*) AS multi_seller_orders
FROM (
  SELECT order_id
  FROM olist.order_items
  GROUP BY order_id
  HAVING COUNT(DISTINCT seller_id) > 1
);
