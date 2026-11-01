# Responsibilities and preparation

## Data preparation

Own `scripts/download_data.py`, `scripts/ingest.py`, provenance and units. Demonstrate the 12 verified monthly bulk files, 46.9 million acquired records and 27.0 million selected CPCB records. Explain that these are pollutant measurements, not that many distinct station-hours. Explain IST conversion, invalid values, missingness and the retained original files.

## SQL and big data processing

Own `sql/`, `scripts/process.py` and BigQuery execution evidence. Demonstrate joins, duplicate/conflict handling, time-based windows, aggregation and partitioned Parquet. Explain why elapsed-time windows matter when readings are missing. Distinguish local DuckDB from distributed BigQuery; show actual cloud job IDs only after execution.

## Analysis and validation

Own `src/analytics.py`, `src/india_bands.py`, tests and findings. Explain daily benchmark exceedances, coverage and persistence. Explain why the combined level is a maximum of ordinal CPCB bands, why three pollutants including PM are required, and why it is not an official numeric AQI. Show coverage sensitivity and missing-pollutant limitations.

## Dashboard and integration

Own `app.py`, maps, heatmaps, exports and report presentation. Demonstrate state/union-territory and city filters, pollutant selection, coverage checks, combined level and station comparison. Test short windows, no matching observations and missing coordinates. Verify displayed results with the analytical outputs.

## Shared preparation

Read the generated India findings, source attribution and method. Understand the raw -> bronze -> silver -> gold lifecycle and the limitations of station-based observational analysis. No presentation time allocation is imposed.

## Suggested academic submission checklist

Clear question; real large-scale Indian dataset; reproducible processing; SQL joins/windows; transparent quality checks; appropriate benchmarks; useful visualizations; validated results; honest cloud execution status; individual deliverables. This is a preparation checklist, not an official 20-mark rubric or a guarantee of marks.
