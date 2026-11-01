"""Read-only connection preflight; prints no credential contents."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.cloud import load_settings,cloud_config,make_client
from google.cloud import bigquery

def main():
    settings=load_settings();cfg=cloud_config(settings)
    print('Checking project:',cfg['project'],flush=True)
    with make_client(settings) as client:
        # This is a real query job, but SELECT 1 scans no measurement table.
        job=client.query('SELECT 1 AS connection_ok',job_config=bigquery.QueryJobConfig(maximum_bytes_billed=cfg['maximum_bytes_billed']))
        assert list(job.result())[0].connection_ok==1
        print('Query permission: PASS; job ID:',job.job_id,flush=True)
        tables=list(client.list_tables(f"{cfg['project']}.{cfg['dataset']}"))
        names={t.table_id for t in tables}
        print('Dataset listing: PASS;',len(names),'tables',flush=True)
        required={'stations','station_daily','overall_daily','station_monthly','station_annual','hourly_quality'}
        missing=required-names
        print('Required dashboard tables:', 'READY' if not missing else 'MISSING: '+', '.join(sorted(missing)),flush=True)
        if missing:print('Authentication works. Upload/build tables using the pipeline account before enabling BigQuery dashboard mode.')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        # Credential errors can include key-related details; never print raw exception payloads here.
        print(f'Preflight failed ({type(exc).__name__}). Check the private credentials path, project, dataset permissions and network access.')
        sys.exit(1)
