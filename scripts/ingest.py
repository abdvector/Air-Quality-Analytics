"""Normalize the CPCB subset from full India bulk Parquet; preserve original monthly sources."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import duckdb
import pandas as pd
from src.config import ROOT,PATHS,POLLUTANTS,ensure_dirs

def quote(path):return "'"+str(path).replace('\\','/').replace("'","''")+"'"

def reference():
    return pd.DataFrame([{'parameter_name':key,'pollutant':v['name'],'expected_unit':v['unit'],'benchmark':v['benchmark'],'period':v['period']} for key,v in POLLUTANTS.items()])

def main():
    ensure_dirs();con=duckdb.connect();con.execute("SET memory_limit='1GB'; SET threads=4")
    ref=reference();con.register('reference',ref);audit=[]
    for month in range(1,13):
        source=PATHS['raw']/f'measurements_2024_{month:02d}.parquet'
        target=PATHS['bronze']/source.name
        start=time.perf_counter()
        if not target.exists():
            con.execute(f'''COPY (
             SELECT h.station_id,h.station_name,h.state_name AS state,h.city_name AS city,
              r.pollutant,h.parameter_name,h.unit AS original_unit,
              replace(replace(replace(lower(trim(h.unit)),'µ','u'),'μ','u'),'³','3') AS unit,
              r.expected_unit,r.benchmark,r.period,
              timezone('Asia/Kolkata',h.collected_at) AS time_utc,
              CAST(h.collected_at AS DATE) AS date_local,hour(h.collected_at)::INTEGER AS hour_local,
              h.value AS concentration,'{source.name}' AS source_file
             FROM read_parquet({quote(source)}) h JOIN reference r USING(parameter_name)
             WHERE h.source='cpcb_caaqm'
            ) TO {quote(target.with_suffix('.part'))} (FORMAT PARQUET,COMPRESSION ZSTD)''')
            target.with_suffix('.part').replace(target)
        rows=con.execute(f'SELECT count(*) FROM read_parquet({quote(target)})').fetchone()[0]
        acquired=con.execute(f'SELECT count(*) FROM read_parquet({quote(source)})').fetchone()[0]
        audit.append({'month':month,'acquired_rows':acquired,'selected_cpcb_rows':rows,'bronze_bytes':target.stat().st_size,'seconds':round(time.perf_counter()-start,2)})
        print(f'INGESTED India {month:02d}: {rows:,} CPCB pollutant measurements from {acquired:,} source rows',flush=True)
    metadata=json.loads((PATHS['raw']/'stations.json').read_text(encoding='utf-8'))['data']
    stations=pd.DataFrame(metadata)[['station_id','station_name','state_name','city_name','latitude','longitude','source']]
    stations.to_parquet(PATHS['bronze']/'station_metadata.parquet',index=False)
    (PATHS['audit']/'ingestion.json').write_text(json.dumps(audit,indent=2))
    print('Selected CPCB measurements:',sum(x['selected_cpcb_rows'] for x in audit),flush=True)

if __name__=='__main__':main()
