CREATE SCHEMA IF NOT EXISTS `fennmoor-dw.ml_scores` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-dw.ml_scores.churn_score_v2` (
  `score_date` DATE NOT NULL,
  `customer_key` INT64 NOT NULL,
  `cif_number` STRING,
  `churn_score` FLOAT64,
  `model_version` STRING
)
PARTITION BY score_date;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.ml_scores.churn_score_v3` (
  `score_date` DATE NOT NULL,
  `customer_key` INT64 NOT NULL,
  `churn_probability` FLOAT64,
  `risk_band` STRING,
  `top_reason_codes` ARRAY<STRING>,
  `model_version` STRING
)
PARTITION BY score_date
CLUSTER BY customer_key;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.ml_scores.next_best_offer` (
  `score_date` DATE NOT NULL,
  `customer_key` INT64 NOT NULL,
  `offer_product_code` STRING,
  `propensity` FLOAT64,
  `rank` INT64
)
PARTITION BY score_date;
