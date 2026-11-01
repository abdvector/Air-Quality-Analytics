# India data dictionary

| Field | Meaning |
|---|---|
| station_id | Publisher/CPCB site identifier, e.g. site_103 |
| station_name, city, state | Monitoring location metadata; no U.S. county geography |
| pollutant | PM2.5, PM10, NO2, SO2, O3, CO or NH3 |
| original_unit | Source unit spelling preserved in bronze |
| unit | Normalized ug/m3 or mg/m3; no automatic ppb conversion |
| time_utc | Explicit UTC timestamp converted from publisher IST |
| date_local, hour_local | IST calendar day and hour |
| concentration | Source hourly measurement |
| source_file | Original 2024 monthly Parquet file |
| input_records, distinct_values | Duplicate-key evidence; conflicts are quarantined |
| observed_hours | Eligible unique hours for the station/pollutant/day |
| daily_mean | Arithmetic mean of the day's usable hourly measurements |
| max_8h_mean | Highest eligible eight-hour mean within the local day |
| comparison_value | Daily mean or eight-hour comparison according to pollutant |
| benchmark | Pollutant-specific India NAAQS reference |
| high | Above benchmark, or Poor-or-worse for the combined view |
| band, level | Ordinal CPCB-band screening level, 0-5; not numeric AQI |
| pollutants_available | Valid distinct pollutants supporting the combined level |
| defining_pollutant | One of the pollutants setting the worst band; ties broken alphabetically |
| coverage_pct | 100 x valid days / calendar days in the selected period |
| high_pct | 100 x high days / valid observed days |

Source definitions: https://airquality.xkdr.org/
