"""Ordinal CPCB-band screening. No numeric AQI interpolation or toxicity weighting."""
import numpy as np
import pandas as pd

BANDS={
 'PM2.5':[30,60,90,120,250], 'PM10':[50,100,250,350,430],
 'NO2':[40,80,180,280,400], 'SO2':[40,80,380,800,1600],
 'CO':[1,2,10,17,34], 'NH3':[200,400,800,1200,1800],
 'O3':[50,100,168,208],
}
LABELS=['Good','Satisfactory','Moderate','Poor','Very Poor','Severe']

def band(pollutant,value,hourly_max=None):
    if value is None or not np.isfinite(value) or value<0:return None
    # Stabilize exact-boundary classification across SQL engines; preserve measured values elsewhere.
    value=round(float(value),8)
    if hourly_max is not None and np.isfinite(hourly_max):hourly_max=round(float(hourly_max),8)
    if pollutant=='O3':
        # CPCB's upper O3 bands refer to one-hour concentrations, not eight-hour means.
        if hourly_max is None or not np.isfinite(hourly_max):return None
        if hourly_max>748:return 5
        if hourly_max>208:return 4
        return min(int(np.searchsorted(BANDS['O3'],value,side='left')),3)
    return int(np.searchsorted(BANDS[pollutant],value,side='left'))

def combine_bands(daily):
    """Require >=3 valid pollutant bands including particulate matter; never fill missing with zero."""
    d=daily.dropna(subset=['band']).copy()
    if d.empty:return pd.DataFrame(columns=['station_id','date_local','level','pollutants_available','defining_pollutant','category','high'])
    d['band']=d['band'].astype(int)
    groups=d.groupby(['station_id','date_local'])
    counts=groups.agg(pollutants_available=('pollutant','nunique'),has_pm=('pollutant',lambda p:bool(set(p)&{'PM2.5','PM10'})))
    worst=d.sort_values(['station_id','date_local','band','pollutant'],ascending=[True,True,False,True]).drop_duplicates(['station_id','date_local'])
    out=worst[['station_id','date_local','band','pollutant']].rename(columns={'band':'level','pollutant':'defining_pollutant'}).merge(counts,on=['station_id','date_local'])
    out=out[(out.pollutants_available>=3)&out.has_pm].drop(columns='has_pm')
    out['category']=out.level.map(dict(enumerate(LABELS)));out['high']=out.level>=3
    return out.reset_index(drop=True)
