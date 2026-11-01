"""Fetch the publisher's unrestricted 2024 bulk files using its documented PUBLIC demo token."""
import concurrent.futures
import hashlib
import json
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import requests
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/india/raw';AUDIT=ROOT/'data/india/audit'
BASE='https://airquality.xkdr.org'
# This is the public example token advertised by the publisher, not a user credential.
PUBLIC_DEMO='aqi_demo_wbf92Qx21zX-Wa_Tg8Dx1nXe'

def download(item):
    target=RAW/item['name']
    for attempt in range(4):
        try:
            if not target.exists():
                with requests.get(item['url'],headers=item.get('headers',{}),timeout=(20,120),stream=True) as response:
                    response.raise_for_status()
                    with target.with_suffix('.part').open('wb') as stream:
                        for chunk in response.iter_content(256*1024):stream.write(chunk)
                target.with_suffix('.part').replace(target)
            if target.suffix=='.parquet':
                meta=pq.ParquetFile(target).metadata
                rows=meta.num_rows
            else:rows=None
            if 'expected_rows' in item and rows!=item['expected_rows']:raise ValueError('Publisher/file row counts differ')
            with target.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
            result={k:v for k,v in item.items() if k!='headers'}
            result.update(bytes=target.stat().st_size,rows=rows,sha256=sha,verified_utc=datetime.now(timezone.utc).isoformat())
            print('VERIFIED',item['name'],f'{rows:,} rows' if rows else '',flush=True)
            return result
        except Exception:
            if attempt==3:raise
            time.sleep(2**attempt)

def main():
    RAW.mkdir(parents=True,exist_ok=True);AUDIT.mkdir(parents=True,exist_ok=True)
    h={'Authorization':'Bearer '+PUBLIC_DEMO}
    for endpoint in ['meta','files','stations','parameters']:
        r=requests.get(BASE+'/v1/'+endpoint,headers=h,timeout=60);r.raise_for_status()
        (RAW/f'{endpoint}.json').write_text(r.text,encoding='utf-8')
    listing=json.loads((RAW/'files.json').read_text())
    files=[{'name':f'measurements_2024_{x["month"]:02d}.parquet','url':BASE+'/v1/files/'+x['key'],
      'headers':h,'expected_rows':x['rows']} for x in listing['files'] if x.get('year')==2024]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(download,files))
    manifest={'study_year':2024,'bulk_source':BASE,'files':results,
      'attribution':'India Air Quality Database, XKDR Forum (CC BY 4.0); underlying CPCB CAAQM network. Only CPCB source rows are analyzed.',
      'excluded_candidate':'Vonter/india-cpcb-aqi published AQI archive was inspected but ends in 2023; it is not used in 2024 outputs.'}
    (AUDIT/'download_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Verified measurement rows:',sum(x['rows'] for x in results if x['name'].startswith('measurements')),flush=True)

if __name__=='__main__':main()
