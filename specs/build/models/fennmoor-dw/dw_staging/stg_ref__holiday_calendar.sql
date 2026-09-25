SELECT
  src.holiday_date,
  src.holiday_name,
  src.is_bank_holiday,
  src.fed_closed,
  src._uploaded_at AS _loaded_at
FROM `fennmoor-raw.reference_data.holiday_calendar` AS src
