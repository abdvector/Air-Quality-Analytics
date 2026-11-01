-- CPCB station observations only; source networks are not mixed.
CREATE OR REPLACE TABLE hourly_quality AS
SELECT pollutant,count(*) input_rows,
 count(*) FILTER(WHERE concentration IS NULL OR NOT isfinite(concentration)) invalid_value_rows,
 count(*) FILTER(WHERE concentration<0) negative_rows,
 count(*) FILTER(WHERE time_utc IS NULL OR date_local IS NULL) invalid_timestamp_rows,
 count(*) FILTER(WHERE unit!=expected_unit) unexpected_unit_rows
FROM hourly_input GROUP BY pollutant;

CREATE OR REPLACE TABLE grouped_hours AS
SELECT station_id,pollutant,time_utc,date_local,hour_local,any_value(unit) unit,
 avg(concentration) concentration,count(*) input_records,count(DISTINCT concentration) distinct_values
FROM hourly_input
WHERE concentration>=0 AND isfinite(concentration) AND time_utc IS NOT NULL
 AND unit=expected_unit AND date_local BETWEEN DATE '2024-01-01' AND DATE '2024-12-31'
GROUP BY station_id,pollutant,time_utc,date_local,hour_local;

-- Quarantine conflicting duplicate values rather than arbitrarily choosing one.
CREATE OR REPLACE TABLE clean_hourly AS SELECT * FROM grouped_hours WHERE distinct_values=1;

CREATE OR REPLACE TABLE hourly_windows AS
SELECT *,avg(concentration) OVER w mean_8h,count(*) OVER w count_8h
FROM clean_hourly WINDOW w AS (
 PARTITION BY station_id,pollutant ORDER BY time_utc RANGE BETWEEN INTERVAL 7 HOURS PRECEDING AND CURRENT ROW
);

CREATE OR REPLACE TABLE hourly_daily AS
SELECT station_id,pollutant,date_local,any_value(unit) unit,
 count(*) observed_hours,avg(concentration) daily_mean,
 max(mean_8h) FILTER(WHERE count_8h>=6 AND hour_local>=7) max_8h_mean,
 CASE WHEN pollutant IN ('O3','CO') THEN max(mean_8h) FILTER(WHERE count_8h>=6 AND hour_local>=7)
 ELSE avg(concentration) END comparison_value
FROM hourly_windows GROUP BY station_id,pollutant,date_local HAVING count(*)>=16;
