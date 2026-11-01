# Air Quality Analytics and Pollution Hotspot Detection in India

A Big Data Analytics (ED547) proof of concept using historical CPCB observations for 2024. The dashboard queries Google BigQuery for coverage-aware pollution rankings, monthly patterns and station comparisons.

## Run the application

Python 3.12 is the tested version. Install the dependencies and configure private BigQuery credentials as described in [setup](docs/SETUP.md).

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open http://localhost:8501. **app.py is the only application entry point.** The dashboard requires internet and authenticated BigQuery access. It does not switch to local data when a cloud query fails.

## Verified study

- 46,937,170 readings acquired from twelve original monthly Parquet files.
- 27,021,875 CPCB readings selected across seven pollutants and 533 stations.
- 1,115,522 eligible pollutant-station-days and 165,652 combined station-days.
- A reading is one pollutant measurement at one station and time.
- PM2.5, PM10, NO2, SO2, O3, CO and NH3 have separate units and averaging rules.
- Combined pollution level is the worst eligible CPCB band on a 0-5 scale. It requires at least three pollutants including particulate matter. It is a derived screening measure, not official numeric AQI.

At default settings, PM2.5 has 416 coverage-eligible stations and 342 persistent hotspots. These are station-level screening results, not estimates for every place in India.

## Project structure

```text
app.py                     Streamlit dashboard, the only app launcher
src/                       BigQuery queries, configuration and analysis rules
scripts/                   Data preparation, cloud processing and verification
sql/bigquery/              GoogleSQL cleaning, joins and aggregations
sql/local/                 Independent DuckDB validation reference
tests/                    SQL, science rules and dashboard tests
data/india/audit/          Small provenance and executed-job records
data/india/{raw,bronze,silver,gold}/   Local reproducible data, ignored by Git
output/india/             Findings, rankings, charts and verification results
docs/                     Methodology, setup and academic deliverables
.streamlit/               Public config and secret-free credential example
```

## Data lifecycle

1. `scripts/download_data.py` acquires the original monthly files and records checksums and publisher row counts.
2. `scripts/ingest.py` selects CPCB records, preserves provenance, standardizes units and creates explicit UTC keys with IST calendar dates.
3. `scripts/process.py` builds the independent DuckDB reference, checks data quality and exports partitioned silver Parquet and analytical gold tables.
4. `scripts/bigquery_run.py` uploads the selected records, runs GoogleSQL and checks cloud outputs against that reference.
5. `app.py` runs filtered aggregation in BigQuery, transfers small summaries and caches results for ten minutes.

These scripts are preparation/validation utilities, not alternative applications. See [setup](docs/SETUP.md) for their commands. Large source and intermediate files remain outside Git. The tracked audit and result files preserve the verified evidence.

## Why BigQuery helps

BigQuery performs real cloud SQL over 27 million measurements, including joins, time windows and grouped summaries. Filtered dashboard calculations run in the warehouse, so the web app does not download the national daily dataset for each interaction. Parameter binding and query-byte ceilings control queries. DuckDB is an independent local correctness reference, not the dashboard backend. This scale can also run on a capable laptop, so the project makes no unsupported claim that BigQuery is necessary or faster.

The Sandbox layout uses clustering and a clean-data view to limit duplicate storage. Historical 2024 event-date partitions would expire immediately under Sandbox retention. Tables still expire 60 days after creation and must be rebuilt before a later demonstration. The dataset's US location is a computing region; the observations are Indian.

## Method, scope and limitations

Coverage uses all calendar days in the selected period. Missing days are never treated as clean days. The default persistence screen requires at least 75% overall day coverage and three adequately observed months with at least 10% high-pollution days. Thresholds are project choices and are adjustable. O3 and CO use eligible eight-hour windows, while the other pollutants use daily means.

The application describes historical 2024 monthly patterns. It does not predict pollution, identify causes or establish regulatory non-attainment. Missing pollutants can conceal a worse combined level. Stations without coordinates remain in the ranking but cannot appear on the map.

[Methodology](docs/METHODOLOGY.md), [data dictionary](docs/DATA_DICTIONARY.md), [member preparation](docs/MEMBER_GUIDE.md) and [attribution](docs/DATA_ATTRIBUTION.md).

## Source

India Air Quality Database, XKDR Forum (2026), compiling CPCB CAAQM observations. Compilation licensed CC BY 4.0. https://airquality.xkdr.org/

## Academic deliverables

- [Project report, 13 pages](docs/report/India_Air_Quality_Report.pdf): grayscale LaTeX report with the architecture, methods, dashboard outputs, results and limitations.
- [Presentation PDF, 10 content slides](docs/presentation/India_Air_Quality_Deck.pdf): compiled Beamer deck following the supplied academic style.
- [Editable PowerPoint](docs/presentation/India_Air_Quality_Deck.pptx): matching content with editable text, tables and architecture diagram. It uses Arial for compatibility; the PDF uses Latin Modern fonts.

Title pages are intentionally omitted for the authors to add. Both LaTeX sources and original dashboard captures are in docs/. Each document uses three references.
