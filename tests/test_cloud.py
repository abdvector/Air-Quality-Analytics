import pytest
from src.cloud import cloud_config
from src.repository import build_cloud_query

SETTINGS={'bigquery':{'project':'my-project-2796-512407','dataset':'air_quality'}}

def test_cloud_filter_values_are_bound():
    sql,cfg=build_cloud_query('station_daily','WHERE pollutant=? AND date_local BETWEEN ? AND ?',
      ["PM2.5' OR 1=1",'2024-01-01','2024-12-31'],SETTINGS)
    assert "OR 1=1" not in sql
    assert '@pollutant' in sql
    assert cfg.query_parameters[0].value=="PM2.5' OR 1=1"
    assert cfg.maximum_bytes_billed==1_000_000_000

def test_unknown_filters_and_tables_rejected():
    with pytest.raises(ValueError):build_cloud_query('stations','; DROP TABLE x',[],SETTINGS)
    with pytest.raises(ValueError):build_cloud_query('untrusted','',[],SETTINGS)
    with pytest.raises(ValueError):build_cloud_query('station_daily','WHERE date_local BETWEEN ? AND ?',[],SETTINGS)

def test_cloud_identifier_validation():
    with pytest.raises(ValueError):cloud_config({'bigquery':{'project':'invalid;query'}})
    with pytest.raises(ValueError):cloud_config({'bigquery':{'project':'valid-project','dataset':'x;query'}})
