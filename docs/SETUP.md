# Setup and reproduction

## Local dashboard

Install Python 3.12 and run `python -m pip install -r requirements.txt` from the project root. Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml`. Set `credentials_file` to the downloaded viewer JSON outside this project. Keep credentials private. The viewer requires BigQuery Job User on the project and BigQuery Data Viewer on dataset `air_quality`.

Run `python scripts/check_bigquery.py` to verify access, then `python -m streamlit run app.py`. The local URL is http://localhost:8501. There is one dashboard entry point and one BigQuery backend.

## Rebuild the study

The preparation pipeline uses the project owner's Application Default Credentials. It must not give the viewer account write access. Install the Google Cloud CLI separately and run `gcloud auth application-default login` when rebuilding cloud tables.

```powershell
python scripts/run_pipeline.py
python scripts/bigquery_run.py --project my-project-2796-512407 --run
python scripts/export_results.py
python scripts/verify_cloud_dashboard.py
python -m pytest tests -q
```

`run_pipeline.py` runs acquisition, ingestion and the DuckDB reference in order. Dataset sizes and checksums are recorded under `data/india/audit`. BigQuery processing validates station_daily, overall_daily, station_monthly and station_annual against that reference before reporting success. The cloud dashboard requires existing cloud tables, private credentials and the tracked run metadata, not the large local Parquet files.

## Streamlit Community Cloud

Select this repository, branch `main`, entry point `app.py`. In the app's private Secrets settings, set `[bigquery]` project, dataset, location and maximum_bytes_billed. Omit credentials_file. Add the downloaded JSON fields under a private `[gcp_service_account]` section. Never add real credentials to GitHub or documentation. The app does not require the local Google Cloud CLI.

## Retention and quotas

The current BigQuery Sandbox has no billing account. Sandbox tables expire 60 days after creation. The historical raw table is unpartitioned and clustered by pollutant, date_local and station_id. clean_hourly is a view, avoiding a second stored hourly copy. Keep source files locally to rebuild expired tables. The dashboard caches queries for ten minutes and uses a maximum_bytes_billed ceiling. Quota availability and source availability may change. See https://docs.cloud.google.com/bigquery/docs/sandbox.

## Validation

`python -m pytest tests -q` covers scientific rules, SQL edge cases, parameter binding and Streamlit views. Dashboard tests use the real configured BigQuery account. `python scripts/verify_cloud_dashboard.py` compares cloud aggregation against the local reference in national PM2.5, combined-level and partial-period Delhi O3 scenarios. These correctness checks are not a speed benchmark.
