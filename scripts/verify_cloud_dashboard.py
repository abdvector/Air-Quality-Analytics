"""Cross-check BigQuery's dashboard aggregation against the independent local daily reference."""
import json,sys,time
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src.config import PATHS
from src.analytics import summarize
from src.repository import read_gold,read_cloud_analysis

def main():
    stations=read_gold('stations');results=[]
    for pollutant,combined,start,end,state in [
      ('PM2.5',False,date(2024,1,1),date(2024,12,31),None),
      ('PM2.5',True,date(2024,1,1),date(2024,12,31),None),
      ('O3',False,date(2024,2,12),date(2024,5,19),'Delhi')]:
        ids=stations.station_id.tolist() if state is None else stations[stations.state==state].station_id.tolist()
        t=time.perf_counter()
        cloud,monthly=read_cloud_analysis(pollutant,combined,start,end,ids,75,10,3)
        local=read_gold('overall_daily' if combined else 'station_daily')
        if not combined:local=local[local.pollutant==pollutant]
        local=local[local.station_id.isin(ids)].rename(columns={'station_id':'location_id'})
        expected=summarize(local,start,end,75,10,3)
        a=cloud[expected.columns].sort_values('location_id').reset_index(drop=True)
        b=expected.sort_values('location_id').reset_index(drop=True)
        pd.testing.assert_frame_equal(a,b,check_dtype=False,check_exact=False,rtol=1e-8,atol=1e-8)
        result={'pollutant':pollutant,'combined':combined,'state':state or 'All states',
          'start':str(start),'end':str(end),'stations_compared':len(a),'monthly_rows_downloaded':len(monthly),
          'seconds':round(time.perf_counter()-t,2),'matches_local_reference':True}
        results.append(result);print(result,flush=True)
    (PATHS['audit']/'dashboard_cloud_parity.json').write_text(json.dumps(results,indent=2))

if __name__=='__main__':main()
