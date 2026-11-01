"""Guard the historical Sandbox layout against accidental event-date expiry."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_historical_cloud_sql_does_not_partition_on_old_dates():
    for name in ['01_india_hourly.sql','02_india_analysis.sql']:
        sql=(ROOT/'sql/bigquery'/name).read_text()
        assert 'PARTITION BY date_local' not in sql
    hourly=(ROOT/'sql/bigquery/01_india_hourly.sql').read_text()
    assert 'CREATE OR REPLACE VIEW' in hourly
    assert 'hourly_raw_retained' in hourly
    assert 'CLUSTER BY pollutant,date_local,station_id' in hourly
