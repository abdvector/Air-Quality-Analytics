CREATE OR REPLACE TABLE `{{project}}.air_quality.station_daily`
CLUSTER BY pollutant,date_local,station_id AS
WITH reference AS (
 SELECT 'PM2.5' pollutant,60.0 benchmark,'24-hour mean' period UNION ALL
 SELECT 'PM10',100.0,'24-hour mean' UNION ALL SELECT 'NO2',80.0,'24-hour mean' UNION ALL
 SELECT 'SO2',80.0,'24-hour mean' UNION ALL SELECT 'O3',100.0,'highest eligible 8-hour mean' UNION ALL
 SELECT 'CO',2.0,'highest eligible 8-hour mean' UNION ALL SELECT 'NH3',400.0,'24-hour mean'
), values_with_reference AS (
 SELECT h.*,r.benchmark,r.period,ROUND(h.comparison_value,8) band_value,ROUND(h.hourly_max,8) band_hourly_max
 FROM `{{project}}.air_quality.hourly_daily` h JOIN reference r USING(pollutant)
 WHERE date_local BETWEEN '2024-01-01' AND '2024-12-31' AND comparison_value IS NOT NULL
)
SELECT station_id,pollutant,date_local,unit,observed_hours,daily_mean,max_8h_mean,comparison_value,
 benchmark,period,band_value>benchmark high,hourly_max,
 CASE pollutant
 WHEN 'PM2.5' THEN CASE WHEN band_value<=30 THEN 0 WHEN band_value<=60 THEN 1 WHEN band_value<=90 THEN 2 WHEN band_value<=120 THEN 3 WHEN band_value<=250 THEN 4 ELSE 5 END
 WHEN 'PM10' THEN CASE WHEN band_value<=50 THEN 0 WHEN band_value<=100 THEN 1 WHEN band_value<=250 THEN 2 WHEN band_value<=350 THEN 3 WHEN band_value<=430 THEN 4 ELSE 5 END
 WHEN 'NO2' THEN CASE WHEN band_value<=40 THEN 0 WHEN band_value<=80 THEN 1 WHEN band_value<=180 THEN 2 WHEN band_value<=280 THEN 3 WHEN band_value<=400 THEN 4 ELSE 5 END
 WHEN 'SO2' THEN CASE WHEN band_value<=40 THEN 0 WHEN band_value<=80 THEN 1 WHEN band_value<=380 THEN 2 WHEN band_value<=800 THEN 3 WHEN band_value<=1600 THEN 4 ELSE 5 END
 WHEN 'NH3' THEN CASE WHEN band_value<=200 THEN 0 WHEN band_value<=400 THEN 1 WHEN band_value<=800 THEN 2 WHEN band_value<=1200 THEN 3 WHEN band_value<=1800 THEN 4 ELSE 5 END
 WHEN 'CO' THEN CASE WHEN band_value<=1 THEN 0 WHEN band_value<=2 THEN 1 WHEN band_value<=10 THEN 2 WHEN band_value<=17 THEN 3 WHEN band_value<=34 THEN 4 ELSE 5 END
 WHEN 'O3' THEN CASE WHEN band_hourly_max>748 THEN 5 WHEN band_hourly_max>208 THEN 4 WHEN band_value<=50 THEN 0 WHEN band_value<=100 THEN 1 WHEN band_value<=168 THEN 2 ELSE 3 END
 END band
FROM values_with_reference;

CREATE OR REPLACE TABLE `{{project}}.air_quality.overall_daily`
CLUSTER BY date_local,station_id AS
WITH eligible AS (
 SELECT station_id,date_local,MAX(band) level,COUNT(DISTINCT pollutant) pollutants_available,
 ARRAY_AGG(pollutant ORDER BY band DESC,pollutant LIMIT 1)[OFFSET(0)] defining_pollutant
 FROM `{{project}}.air_quality.station_daily`
 WHERE date_local BETWEEN '2024-01-01' AND '2024-12-31' AND band IS NOT NULL
 GROUP BY station_id,date_local
 HAVING COUNT(DISTINCT pollutant)>=3 AND COUNTIF(pollutant IN ('PM2.5','PM10'))>=1
)
SELECT station_id,date_local,level,defining_pollutant,pollutants_available,
 ['Good','Satisfactory','Moderate','Poor','Very Poor','Severe'][OFFSET(level)] category,
 level>=3 high FROM eligible;

CREATE OR REPLACE TABLE `{{project}}.air_quality.station_monthly` AS
SELECT station_id,pollutant,DATE_TRUNC(date_local,MONTH) month,COUNT(*) valid_days,
 EXTRACT(DAY FROM LAST_DAY(MIN(date_local))) expected_days,
 100.0*COUNT(*)/EXTRACT(DAY FROM LAST_DAY(MIN(date_local))) coverage_pct,
 COUNTIF(high) high_days,100.0*COUNTIF(high)/COUNT(*) high_pct,
 AVG(comparison_value) mean_value,MAX(comparison_value) max_value,ANY_VALUE(unit) unit,ANY_VALUE(benchmark) benchmark
FROM `{{project}}.air_quality.station_daily`
WHERE date_local BETWEEN '2024-01-01' AND '2024-12-31' GROUP BY station_id,pollutant,month;

CREATE OR REPLACE TABLE `{{project}}.air_quality.station_annual` AS
SELECT station_id,pollutant,COUNT(*) valid_days,366 expected_days,100.0*COUNT(*)/366 coverage_pct,
 COUNTIF(high) high_days,100.0*COUNTIF(high)/COUNT(*) high_pct,AVG(comparison_value) mean_value,MAX(comparison_value) max_value
FROM `{{project}}.air_quality.station_daily`
WHERE date_local BETWEEN '2024-01-01' AND '2024-12-31' GROUP BY station_id,pollutant;
