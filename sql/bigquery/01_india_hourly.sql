-- GoogleSQL; UTC timestamps were explicitly converted from publisher IST clock values during ingestion.
-- A view avoids a second 27-million-row stored copy in the free Sandbox.
CREATE OR REPLACE VIEW `{{project}}.air_quality.clean_hourly` AS
SELECT station_id,pollutant,time_utc,date_local,hour_local,ANY_VALUE(unit) unit,
 AVG(concentration) concentration,COUNT(*) input_records,COUNT(DISTINCT concentration) distinct_values
FROM `{{project}}.air_quality.hourly_raw_retained` r
WHERE date_local BETWEEN '2024-01-01' AND '2024-12-31'
 AND concentration>=0 AND NOT IS_NAN(concentration) AND NOT IS_INF(concentration)
 AND time_utc IS NOT NULL AND unit=expected_unit
GROUP BY station_id,pollutant,time_utc,date_local,hour_local
HAVING COUNT(DISTINCT r.concentration)=1;

CREATE OR REPLACE TABLE `{{project}}.air_quality.hourly_daily`
CLUSTER BY pollutant,date_local,station_id AS
WITH windows AS (
 SELECT *,AVG(concentration) OVER w mean_8h,COUNT(*) OVER w count_8h
 FROM `{{project}}.air_quality.clean_hourly`
 WHERE date_local BETWEEN '2024-01-01' AND '2024-12-31'
 WINDOW w AS(PARTITION BY station_id,pollutant ORDER BY UNIX_SECONDS(time_utc) RANGE BETWEEN 25200 PRECEDING AND CURRENT ROW)
)
SELECT station_id,pollutant,date_local,ANY_VALUE(unit) unit,COUNT(*) observed_hours,
 AVG(concentration) daily_mean,MAX(IF(count_8h>=6 AND hour_local>=7,mean_8h,NULL)) max_8h_mean,
 IF(pollutant IN ('O3','CO'),MAX(IF(count_8h>=6 AND hour_local>=7,mean_8h,NULL)),AVG(concentration)) comparison_value,
 MAX(concentration) hourly_max
FROM windows GROUP BY station_id,pollutant,date_local HAVING COUNT(*)>=16;
