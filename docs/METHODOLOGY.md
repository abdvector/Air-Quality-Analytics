# India methodology

## Question and scope

Which Indian monitoring stations repeatedly exceed pollutant-specific reference concentrations during 2024, and how much observed data supports the ranking? What is the worst available CPCB pollution band at each adequately monitored station/day?

## Provenance

The source is the India Air Quality Database, XKDR Forum (2026), https://airquality.xkdr.org/, CC BY 4.0. The full compilation includes CPCB and embassy monitoring; this project selects **CPCB CAAQM source rows only**. Original monthly Parquet files and publisher metadata are preserved. Bulk downloads are unrestricted in row count; the publisher's public demo token authorizes the 2024 files. Per-query API row caps are not used to obtain samples or silently truncate data.

All acquired monthly row counts are verified against publisher metadata and SHA-256 checksums are recorded. The selected seven pollutants are a real subset of the acquired observations; no wide-to-long transformation is used to inflate the measurement count. Values are as reported by the networks, without upstream gap filling or calibration. Source data may be preliminary.

The alternative Vonter published AQI mirror ends in 2023 and is **not used**. Therefore no official historical numeric AQI is claimed for 2024. Derived concentration and band outputs use only the 2024 CPCB observations.

## Normalization and quality

Publisher `collected_at` values are already Indian Standard Time. Convert them once to UTC for unique time keys while deriving calendar dates and hours from IST. Preserve original units, then normalize spelling (micro symbols and superscript 3), not physical magnitudes. PM2.5, PM10, NO2, SO2, O3 and NH3 use ug/m3; CO uses mg/m3. Do not silently convert ppb/ppm to mass units.

Reject missing/non-finite/negative values and unexpected units from analytical data, retaining raw/bronze evidence and exclusion counts. Negative readings may reflect near-detection-limit behavior; exclusion can bias concentration means upward slightly. High positive values are retained rather than automatically discarded. No gaps are filled.

Group station/pollutant/UTC keys. Collapse identical duplicate values, but quarantine conflicting duplicate values rather than choose a higher or lower value arbitrarily. Metadata joins are left joins so a station without coordinates remains in rankings and coverage tables. Missing coordinates are never invented.

## Daily comparison metrics

An eligible day has at least 16 usable hourly observations for that pollutant. For PM2.5, PM10, NO2, SO2 and NH3, compare the daily mean with the 24-hour India NAAQS reference. For CO and O3, compare the highest eligible eight-hour mean within the IST calendar day. An eight-hour window needs at least six observed hours; elapsed-time windows prevent long gaps from being mistaken for consecutive observations. Restrict endpoints to 07:00-23:00 IST so windows remain within the same day.

| Pollutant | Benchmark | Period |
|---|---:|---|
| PM2.5 | 60 ug/m3 | 24-hour mean |
| PM10 | 100 ug/m3 | 24-hour mean |
| NO2 | 80 ug/m3 | 24-hour mean |
| SO2 | 80 ug/m3 | 24-hour mean |
| NH3 | 400 ug/m3 | 24-hour mean |
| O3 | 100 ug/m3 | eight-hour mean |
| CO | 2 mg/m3 | eight-hour mean |

An exceedance requires a comparison value strictly above the reference. Round comparison values to eight decimal places only for threshold and band decisions, preventing binary floating-point summation differences between DuckDB and BigQuery from classifying an exactly-on-threshold day differently. Original concentration summaries retain their numerical precision. This is a descriptive daily screening approach. It does not implement all legal annual compliance forms or official running-AQI publication rules.

## Combined level

Assign an ordinal severity band from the CPCB breakpoint table: 0 Good, 1 Satisfactory, 2 Moderate, 3 Poor, 4 Very Poor, 5 Severe. The upper concentration boundaries for the first five bands are:

| Pollutant | Good | Satisfactory | Moderate | Poor | Very Poor |
|---|---:|---:|---:|---:|---:|
| PM2.5 | 30 | 60 | 90 | 120 | 250 |
| PM10 | 50 | 100 | 250 | 350 | 430 |
| NO2 | 40 | 80 | 180 | 280 | 400 |
| SO2 | 40 | 80 | 380 | 800 | 1600 |
| NH3 | 200 | 400 | 800 | 1200 | 1800 |
| CO (mg/m3) | 1 | 2 | 10 | 17 | 34 |

Above the last boundary is Severe. O3 uses eight-hour boundaries 50, 100, 168 and 208 for the first four bands; its upper bands use the source table's one-hour convention: observed hourly maximum >208 is Very Poor and >748 is Severe. Band assignment uses upper-inclusive boundaries and rounds only the classification inputs to eight decimal places to remove floating-point noise. This is a documented screening convention rather than a reproduction of official AQI rounding.

At each station/day, require at least three distinct eligible pollutants including PM2.5 or PM10. The combined level is the maximum available band. Ties for the displayed defining pollutant are broken alphabetically; other pollutants can share the same worst band. Lead is unavailable and is not fabricated. This score is ordinal: differences between levels do not quantify equal changes in health risk. It is **not official reported AQI**. Missing pollutants can conceal a worse band, so the available-pollutant count is shown.

## Coverage and persistence

Coverage is valid observed days divided by calendar days in the selected period. Missing days never count as clean. For individual pollutants, a high day exceeds its concentration benchmark. For the combined view, a high day has level >=3 (Poor or worse). These different criteria are labelled explicitly.

Defaults: overall coverage >=75%; an eligible month also has >=75% day coverage; a high month has high pollution on >=10% of observed days; a persistent hotspot has at least three high months and passes overall coverage. These are project choices. Sensitivity checks use 60%, 75% and 90% coverage. The denominator is conservative and can exclude partial-year or deliberately intermittent operation; low coverage does not automatically mean a faulty sensor.

Monthly concentration means and poor-day fractions are descriptive. One year supports within-year monthly patterns, not a claim of recurring multi-year seasonality. No traffic, industry, weather or crop-burning cause is inferred from concentration alone.

## Sources

- Dataset, metadata and licence: https://airquality.xkdr.org/
- Publisher documentation: https://github.com/xKDR/Air-Quality-Database
- Government AQI bands, units and minimum pollutants: https://ies.gov.in/arthapedia/concept/national-air-quality-index
- Government ambient standards: https://www.ies.gov.in/index.php/arthapedia/concept/ambient-air-quality-standards-india
- MPCB official report describing AQI periods and completeness: https://mpcb.gov.in/sites/default/files/focus-area-reports-documents/Air_Quality_Report_2018_19_Eng_11062019.pdf
