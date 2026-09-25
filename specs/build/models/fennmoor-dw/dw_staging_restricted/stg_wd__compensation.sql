SELECT
  src.worker_id,
  src.effective_date,
  src.base_pay_annual,
  src.bonus_target_pct,
  src.currency_code,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.workday.compensation` AS src
WHERE NOT src._fivetran_deleted
