"""India-only SQL processing, ordinal composite, provenance and checks."""
import json,sys,time,uuid
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import duckdb
from src.config import ROOT,PATHS,ensure_dirs
from src.india_bands import band,combine_bands
from scripts.ingest import quote,reference

def main():
    ensure_dirs();start=time.perf_counter();con=duckdb.connect(str(ROOT/'data/india/warehouse.duckdb'))
    con.execute("SET memory_limit='1500MB'; SET threads=4; SET TimeZone='UTC'")
    spill=ROOT/'data/india/spill';spill.mkdir(exist_ok=True);con.execute(f'SET temp_directory={quote(spill)}')
    con.execute(f'CREATE OR REPLACE VIEW hourly_input AS SELECT * FROM read_parquet({quote(PATHS["bronze"]/"measurements_2024_*.parquet")})')
    ref=reference().drop(columns='parameter_name').rename(columns={'expected_unit':'unit'})
    con.register('pollutant_reference',ref)
    steps=[]
    for name in ['01_clean_hourly.sql','02_aqi_summaries.sql']:
        print('START',name,flush=True);t=time.perf_counter()
        con.execute((ROOT/'sql/local'/name).read_text())
        steps.append({'step':name,'seconds':round(time.perf_counter()-t,2)})
        print('DONE',name,steps[-1]['seconds'],'seconds',flush=True)
    con.execute(f'''CREATE OR REPLACE TABLE stations AS
      SELECT h.station_id,coalesce(any_value(m.station_name),any_value(h.station_name),h.station_id) station_name,
       coalesce(any_value(m.state_name),any_value(h.state)) state,
       coalesce(any_value(m.city_name),any_value(h.city)) city,
       any_value(m.latitude) latitude,any_value(m.longitude) longitude
      FROM hourly_input h LEFT JOIN read_parquet({quote(PATHS['bronze']/'station_metadata.parquet')}) m USING(station_id)
      GROUP BY h.station_id''')
    # Band assignment is explicit ordinal screening, not reconstruction of official continuous AQI.
    con.execute('ALTER TABLE hourly_daily ADD COLUMN IF NOT EXISTS hourly_max DOUBLE')
    con.execute('''UPDATE hourly_daily d SET hourly_max=h.maximum FROM (
       SELECT station_id,pollutant,date_local,max(concentration) maximum FROM clean_hourly GROUP BY station_id,pollutant,date_local
       ) h WHERE d.station_id=h.station_id AND d.pollutant=h.pollutant AND d.date_local=h.date_local''')
    daily=con.execute('''SELECT d.*,h.hourly_max FROM station_daily d JOIN hourly_daily h USING(station_id,pollutant,date_local)''').fetchdf()
    daily['band']=[band(p,v,m) for p,v,m in zip(daily.pollutant,daily.comparison_value,daily.hourly_max)]
    overall=combine_bands(daily)
    con.register('overall_frame',overall);con.execute('CREATE OR REPLACE TABLE overall_daily AS SELECT * FROM overall_frame')
    con.register('daily_frame',daily);con.execute('CREATE OR REPLACE TABLE station_daily_enriched AS SELECT * FROM daily_frame')
    exports={'stations':'stations','station_daily':'station_daily_enriched','station_monthly':'station_monthly',
      'station_annual':'station_annual','overall_daily':'overall_daily','hourly_quality':'hourly_quality'}
    for target,table in exports.items():
        dest=PATHS['gold']/f'{target}.parquet';tmp=dest.with_suffix('.part')
        con.execute(f'COPY {table} TO {quote(tmp)} (FORMAT PARQUET,COMPRESSION ZSTD)');tmp.replace(dest)
    partition=PATHS['silver']/'hourly';staging=PATHS['silver']/f'hourly_build_{uuid.uuid4().hex[:8]}'
    con.execute(f'''COPY (SELECT *,strftime(date_local,'%Y-%m') AS month FROM clean_hourly)
      TO {quote(staging)} (FORMAT PARQUET,PARTITION_BY(month,pollutant),COMPRESSION ZSTD)''')
    if partition.exists():partition.rename(PATHS['silver']/f'hourly_previous_{uuid.uuid4().hex[:8]}')
    staging.rename(partition)
    ingest=json.loads((PATHS['audit']/'ingestion.json').read_text())
    counts={name:con.execute(f'SELECT count(*) FROM {name}').fetchone()[0] for name in ['hourly_input','clean_hourly','station_daily','stations','overall_daily']}
    counts['acquired_all_parameter_rows']=sum(x['acquired_rows'] for x in ingest)
    checks={
     'acquired_rows_match_publisher':counts['acquired_all_parameter_rows']==sum(x['expected_rows'] for x in json.loads((PATHS['audit']/'download_manifest.json').read_text())['files'] if x['name'].startswith('measurements')),
     'bronze_row_reconciliation':counts['hourly_input']==sum(x['selected_cpcb_rows'] for x in ingest),
     'unique_clean_hours':con.execute('SELECT count(*)=count(DISTINCT(station_id,pollutant,time_utc)) FROM clean_hourly').fetchone()[0],
     'unique_station_days':not daily.duplicated(['station_id','pollutant','date_local']).any(),
     'seven_pollutants':daily.pollutant.nunique()==7,
     'composite_requires_three':bool((overall.pollutants_available>=3).all()),
     'composite_level_bounds':bool(overall.level.between(0,5).all()),
     'overall_unique_station_days':not overall.duplicated(['station_id','date_local']).any(),
     'silver_export_matches_clean':con.execute(f'SELECT count(*) FROM read_parquet({quote(partition/"**/*.parquet")},hive_partitioning=true)').fetchone()[0]==counts['clean_hourly'],
     'metadata_join_preserves_rows':con.execute('SELECT (SELECT count(*) FROM station_daily)=(SELECT count(*) FROM station_daily JOIN stations USING(station_id))').fetchone()[0],
    }
    quality=con.execute('SELECT * FROM hourly_quality').fetchdf();quality.to_csv(PATHS['audit']/'hourly_quality.csv',index=False)
    stats={'country':'India','year':2024,'engine':'DuckDB local','cloud_executed':False,
      'counts':counts,'steps':steps,'validation':{k:bool(v) for k,v in checks.items()},
      'conflicting_duplicate_hours':con.execute('SELECT count(*) FROM grouped_hours WHERE distinct_values>1').fetchone()[0],
      'stations_without_coordinates':int(con.execute('SELECT count(*) FROM stations WHERE latitude IS NULL OR longitude IS NULL').fetchone()[0]),
      'elapsed_seconds':round(time.perf_counter()-start,2),'created_utc':datetime.now(timezone.utc).isoformat()}
    (PATHS['audit']/'pipeline_run.json').write_text(json.dumps(stats,indent=2))
    con.close();print(json.dumps(stats,indent=2),flush=True)
    if not all(checks.values()):raise RuntimeError('India validation failed')

if __name__=='__main__':main()
