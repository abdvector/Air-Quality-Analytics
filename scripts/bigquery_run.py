"""Authenticated India BigQuery execution, exported-result validation and job audit."""
import argparse,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import NotFound
from src.config import ROOT,PATHS

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);parser.add_argument('--run',action='store_true')
    parser.add_argument('--analysis-only',action='store_true',help='Resume SQL and validation after the input load has been verified.')
    parser.add_argument('--summary-only',action='store_true',help='With --analysis-only, reuse the verified hourly daily table and refresh derived summaries.')
    args=parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9-]{4,61}[a-z0-9]',args.project):raise ValueError('Invalid project ID')
    client=bigquery.Client(project=args.project,location='US')
    dataset=bigquery.Dataset(f'{args.project}.air_quality');dataset.location='US';dataset.default_table_expiration_ms=60*86400000
    client.create_dataset(dataset,exists_ok=True)
    audit_file=PATHS['audit']/'bigquery_jobs.json'
    jobs=json.loads(audit_file.read_text()) if audit_file.exists() else []
    def record(job,label):
        jobs.append({'label':label,'job_id':job.job_id,'bytes_processed':getattr(job,'total_bytes_processed',None),'slot_millis':getattr(job,'slot_millis',None),'state':job.state})
        (PATHS['audit']/'bigquery_jobs.json').write_text(json.dumps(jobs,indent=2))
    # Sandbox expires event-date partitions immediately for historical observations.
    # Use table-level retention with date clustering and a slim raw schema instead.
    table=f'{args.project}.air_quality.hourly_raw_retained'
    sources=sorted(PATHS['bronze'].glob('measurements_2024_*.parquet'))
    if len(sources)!=12:raise RuntimeError('Expected all 12 India monthly source files before cloud loading.')
    import pyarrow.parquet as pq
    for path in sources:
        if args.analysis_only:continue
        expected_rows=pq.ParquetFile(path).metadata.num_rows
        try:
            job=client.query(f"SELECT COUNT(*) n FROM `{table}` WHERE date_local BETWEEN '2024-01-01' AND '2024-12-31' AND source_file=@name",
              job_config=bigquery.QueryJobConfig(maximum_bytes_billed=2_000_000_000,query_parameters=[bigquery.ScalarQueryParameter('name','STRING',path.name)]))
            loaded_rows=list(job.result())[0].n
            if loaded_rows:
                if loaded_rows!=expected_rows:raise RuntimeError(f'Existing source row count differs for {path.name}; refusing to append duplicates.')
                print('Already loaded',path.name,flush=True);continue
        except NotFound:pass
        upload_dir=PATHS['bronze'].parent/'cloud_upload';upload_dir.mkdir(exist_ok=True)
        upload=upload_dir/path.name
        slim=pq.read_table(path,columns=['station_id','pollutant','time_utc','date_local','hour_local','unit','expected_unit','concentration','source_file'])
        pq.write_table(slim,upload,compression='zstd')
        cfg=bigquery.LoadJobConfig(source_format='PARQUET',write_disposition='WRITE_APPEND',clustering_fields=['pollutant','date_local','station_id'])
        with upload.open('rb') as stream:job=client.load_table_from_file(stream,table,job_config=cfg)
        job.result();record(job,path.name);print('Loaded',path.name,flush=True)
    count_job=client.query(f"SELECT COUNT(*) n FROM `{table}` WHERE date_local BETWEEN '2024-01-01' AND '2024-12-31'",
      job_config=bigquery.QueryJobConfig(maximum_bytes_billed=2_000_000_000))
    cloud_rows=list(count_job.result())[0].n
    if cloud_rows!=sum(pq.ParquetFile(p).metadata.num_rows for p in sources):
        raise RuntimeError('Cloud hourly row count differs from the verified input total.')
    record(count_job,'verified full hourly input count')
    print('Verified cloud hourly rows:',cloud_rows,flush=True)
    with (PATHS['gold']/'stations.parquet').open('rb') as stream:
        job=client.load_table_from_file(stream,f'{args.project}.air_quality.stations',job_config=bigquery.LoadJobConfig(source_format='PARQUET',write_disposition='WRITE_TRUNCATE'))
    job.result();record(job,'stations')
    # The dashboard's quality panel is an acquisition audit, not a recomputed cloud measurement table.
    with (PATHS['gold']/'hourly_quality.parquet').open('rb') as stream:
        job=client.load_table_from_file(stream,f'{args.project}.air_quality.hourly_quality',job_config=bigquery.LoadJobConfig(source_format='PARQUET',write_disposition='WRITE_TRUNCATE'))
    job.result();record(job,'hourly_quality acquisition audit')
    if args.run:
        for name in ['01_india_hourly.sql','02_india_analysis.sql']:
            if args.summary_only and name=='01_india_hourly.sql':continue
            sql=(ROOT/'sql/bigquery'/name).read_text().replace('{{project}}',args.project)
            print('Running BigQuery SQL:',name,flush=True)
            job=client.query(sql,job_config=bigquery.QueryJobConfig(maximum_bytes_billed=30_000_000_000,use_query_cache=False))
            try:job.result()
            finally:record(job,name)
            print('Completed BigQuery SQL:',name,flush=True)
        outputs={}
        for name in ['station_daily','overall_daily','station_monthly','station_annual']:
            where=" WHERE date_local BETWEEN '2024-01-01' AND '2024-12-31'" if name.endswith('_daily') else ''
            ref=pd.read_parquet(PATHS['gold']/f'{name}.parquet')
            frames=[]
            selections=sorted(ref.pollutant.unique()) if name=='station_daily' else [None]
            for pollutant in selections:
                clause=where
                params=[]
                if pollutant:
                    clause+=' AND pollutant=@pollutant';params=[bigquery.ScalarQueryParameter('pollutant','STRING',pollutant)]
                print('Downloading validation output:',name,pollutant or '',flush=True)
                job=client.query(f'SELECT * FROM `{args.project}.air_quality.{name}`'+clause,
                    job_config=bigquery.QueryJobConfig(maximum_bytes_billed=2_000_000_000,query_parameters=params))
                part=job.to_dataframe(create_bqstorage_client=False)
                frames.append(part);record(job,'download '+name+(' '+pollutant if pollutant else ''))
                print('Downloaded',name,pollutant or '',len(part),'rows',flush=True)
            frame=pd.concat(frames,ignore_index=True)
            for col in ['date_local','month']:
                if col in ref:frame[col]=pd.to_datetime(frame[col]);ref[col]=pd.to_datetime(ref[col])
            keys=[x for x in ['station_id','pollutant','date_local','month'] if x in ref]
            pd.testing.assert_frame_equal(frame[ref.columns].sort_values(keys).reset_index(drop=True),ref.sort_values(keys).reset_index(drop=True),check_dtype=False,check_exact=False,rtol=1e-8,atol=1e-8)
            outputs[name]=frame;record(job,'validated '+name)
            print('Validated cloud/local parity:',name,len(frame),'rows',flush=True)
        for name,frame in outputs.items():frame.to_parquet(PATHS['gold']/f'{name}.parquet',index=False)
        audit=json.loads((PATHS['audit']/'pipeline_run.json').read_text());audit.update(cloud_executed=True,cloud_project=args.project,engine='DuckDB local reference and validated BigQuery execution')
        (PATHS['audit']/'pipeline_run.json').write_text(json.dumps(audit,indent=2))
        (PATHS['audit']/'cloud_execution.json').write_text(json.dumps({'executed':True,'project':args.project,'jobs':jobs},indent=2))

if __name__=='__main__':main()
