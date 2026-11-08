-- =====================================================================
-- 02 · What does a late delivery do to the review score?
-- Bad review = average score of 1 or 2 stars (out of 5).
-- =====================================================================

WITH reviews AS (
  SELECT order_id, AVG(review_score) AS review_score      -- a few orders have 2+ reviews
  FROM olist.order_reviews
  GROUP BY order_id
),
delivered AS (
  SELECT
    o.order_id,
    DATE_DIFF(DATE(o.order_delivered_customer_date), DATE(o.order_estimated_delivery_date), DAY) AS days_late
  FROM olist.orders o
  WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
)

-- 1) On time vs late
SELECT
  IF(d.days_late > 0, 'Late', 'On time')                             AS delivery,
  COUNT(*)                                                           AS orders_with_review,
  ROUND(AVG(r.review_score), 2)                                      AS avg_review_score,
  ROUND(100 * COUNTIF(r.review_score <= 2) / COUNT(*), 1)            AS bad_review_pct,
  ROUND(100 * COUNTIF(r.review_score <= 2)
        / SUM(COUNTIF(r.review_score <= 2)) OVER (), 1)              AS share_of_all_bad_reviews_pct
FROM delivered d
JOIN reviews r ON r.order_id = d.order_id
GROUP BY delivery
ORDER BY delivery;

-- 2) The later the order, the worse the review
WITH reviews AS (
  SELECT order_id, AVG(review_score) AS review_score
  FROM olist.order_reviews
  GROUP BY order_id
),
delivered AS (
  SELECT
    o.order_id,
    DATE_DIFF(DATE(o.order_delivered_customer_date), DATE(o.order_estimated_delivery_date), DAY) AS days_late
  FROM olist.orders o
  WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
)
SELECT
  CASE
    WHEN d.days_late <= 0  THEN '0. On time'
    WHEN d.days_late <= 3  THEN '1. 1-3 days late'
    WHEN d.days_late <= 7  THEN '2. 4-7 days late'
    WHEN d.days_late <= 14 THEN '3. 8-14 days late'
    ELSE                        '4. 15+ days late'
  END                                                     AS lateness,
  COUNT(*)                                                AS orders_with_review,
  ROUND(AVG(r.review_score), 2)                           AS avg_review_score,
  ROUND(100 * COUNTIF(r.review_score <= 2) / COUNT(*), 1) AS bad_review_pct
FROM delivered d
JOIN reviews r ON r.order_id = d.order_id
GROUP BY lateness
ORDER BY lateness;
