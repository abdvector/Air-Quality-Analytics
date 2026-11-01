CREATE OR REPLACE TABLE station_daily AS
SELECT h.*,p.benchmark,p.period,round(comparison_value,8)>p.benchmark high
FROM hourly_daily h JOIN pollutant_reference p USING(pollutant)
WHERE comparison_value IS NOT NULL;

CREATE OR REPLACE TABLE station_monthly AS
SELECT station_id,pollutant,date_trunc('month',date_local)::DATE AS month,
 count(*) valid_days,day(last_day(min(date_local))) expected_days,
 100.0*count(*)/day(last_day(min(date_local))) coverage_pct,
 count(*) FILTER(WHERE high) high_days,100.0*count(*) FILTER(WHERE high)/count(*) high_pct,
 avg(comparison_value) mean_value,max(comparison_value) max_value,
 any_value(unit) unit,any_value(benchmark) benchmark
FROM station_daily GROUP BY station_id,pollutant,month;

CREATE OR REPLACE TABLE station_annual AS
SELECT station_id,pollutant,count(*) valid_days,366 expected_days,
 100.0*count(*)/366 coverage_pct,count(*) FILTER(WHERE high) high_days,
 100.0*count(*) FILTER(WHERE high)/count(*) high_pct,
 avg(comparison_value) mean_value,max(comparison_value) max_value
FROM station_daily GROUP BY station_id,pollutant;
