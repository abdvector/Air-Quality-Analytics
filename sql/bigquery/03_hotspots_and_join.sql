WITH persistence AS (
 SELECT station_id,pollutant,COUNTIF(coverage_pct>=75 AND high_pct>=10) high_months
 FROM `{{project}}.air_quality.station_monthly` GROUP BY station_id,pollutant
)
SELECT a.*,s.station_name,s.city,s.state,s.latitude,s.longitude,p.high_months,p.high_months>=3 persistent,
 DENSE_RANK() OVER(PARTITION BY a.pollutant ORDER BY a.high_pct DESC) hotspot_rank
FROM `{{project}}.air_quality.station_annual` a JOIN persistence p USING(station_id,pollutant)
JOIN `{{project}}.air_quality.stations` s USING(station_id)
WHERE a.coverage_pct>=75 ORDER BY a.pollutant,hotspot_rank;
