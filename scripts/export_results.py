"""Produce India-only findings, grayscale figures and a formal report from executed outputs."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.config import ROOT,PATHS,OUTPUT,POLLUTANTS
from src.repository import read_gold
from src.analytics import summarize

def main():
    OUTPUT.mkdir(parents=True,exist_ok=True);figs=OUTPUT/'figures';figs.mkdir(exist_ok=True)
    stats=json.loads((PATHS['audit']/'pipeline_run.json').read_text())
    manifest=json.loads((PATHS['audit']/'download_manifest.json').read_text())
    stations=read_gold('stations');daily=read_gold('station_daily');overall=read_gold('overall_daily')
    findings=[];ranks=[];sensitivity=[]
    for cfg in POLLUTANTS.values():
        pollutant=cfg['name'];d=daily[daily.pollutant==pollutant].rename(columns={'station_id':'location_id'})
        rank=summarize(d,'2024-01-01','2024-12-31').merge(stations.rename(columns={'station_id':'location_id'}),on='location_id',how='left')
        rank['pollutant']=pollutant;ranks.append(rank);eligible=rank[rank.eligible]
        if len(eligible):
            top=eligible.iloc[0]
            findings.append(f"{pollutant}: {len(eligible)} stations meet 75% day coverage; {int(rank.persistent.sum())} meet the persistence rule. The highest benchmark-exceedance fraction is {top.high_pct:.1f}% at {top.station_name} ({top.city}, {top.state}), based on {int(top.valid_days)} valid days.")
        else:findings.append(f'{pollutant}: no stations meet the 75% annual coverage screen.')
        for coverage in [60,75,90]:
            x=summarize(d,'2024-01-01','2024-12-31',coverage)
            sensitivity.append({'pollutant':pollutant,'coverage_threshold':coverage,'eligible_stations':int(x.eligible.sum()),'persistent_hotspots':int(x.persistent.sum())})
    combined=summarize(overall.rename(columns={'station_id':'location_id'}),'2024-01-01','2024-12-31').merge(stations.rename(columns={'station_id':'location_id'}),on='location_id',how='left')
    # Do not communicate means of ordinal level numbers as health-risk quantities.
    combined.drop(columns=['mean_value'],errors='ignore').to_csv(OUTPUT/'combined_rankings.csv',index=False)
    findings.append(f"Combined level: {int(combined.eligible.sum())} stations meet annual coverage, and {int(combined.persistent.sum())} meet the persistence rule for Poor-or-worse days. This ordinal summary uses at least three pollutants including particulate matter and is not official numeric AQI.")
    r=pd.concat(ranks,ignore_index=True);r.to_csv(OUTPUT/'station_rankings.csv',index=False)
    pd.DataFrame(sensitivity).to_csv(OUTPUT/'coverage_sensitivity.csv',index=False)
    pm=[x for x in sensitivity if x['pollutant']=='PM2.5']
    findings.append('PM2.5 coverage sensitivity: '+ '; '.join(f"{x['coverage_threshold']}% coverage gives {x['eligible_stations']} eligible stations and {x['persistent_hotspots']} persistent hotspots" for x in pm)+'.')
    headline=f"India, 2024: {stats['counts']['acquired_all_parameter_rows']:,} source measurements acquired; {stats['counts']['hourly_input']:,} CPCB measurements selected; {stats['counts']['stations']:,} stations."
    (OUTPUT/'findings.md').write_text('# India findings\n\n'+headline+'\n\n'+'\n\n'.join('- '+x for x in findings)+'\n\nThese are observed station-level screening results, not causal explanations or regulatory non-attainment determinations.\n',encoding='utf-8')
    q=read_gold('hourly_quality');q.to_csv(OUTPUT/'data_quality.csv',index=False)
    pmr=r[(r.pollutant=='PM2.5')&r.eligible].head(10).iloc[::-1]
    fig,ax=plt.subplots(figsize=(9,4.5));ax.barh(pmr.city+' / '+pmr.location_id,pmr.high_pct,color='0.3')
    ax.set(xlabel='Valid days above 60 ug/m3 (%)',title='India: PM2.5 benchmark exceedances among eligible stations')
    ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(figs/'india_pm25_hotspots.png',dpi=180);plt.close(fig)
    ids=pmr.location_id.iloc[::-1].head(8).tolist();monthly=read_gold('station_monthly')
    mm=monthly[(monthly.pollutant=='PM2.5')&monthly.station_id.isin(ids)].copy();mm['month']=pd.to_datetime(mm.month).dt.month
    mm.loc[mm.coverage_pct<75,'mean_value']=np.nan
    matrix=mm.pivot(index='station_id',columns='month',values='mean_value').reindex(index=ids,columns=range(1,13))
    fig,ax=plt.subplots(figsize=(9,4));im=ax.imshow(matrix,aspect='auto',cmap='Greys',vmin=0)
    ax.set_xticks(range(12),['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']);ax.set_yticks(range(len(ids)),ids)
    ax.set_title('PM2.5 monthly mean: selected Indian stations');fig.colorbar(im,ax=ax,label='ug/m3')
    fig.tight_layout();fig.savefig(figs/'india_monthly_heatmap.png',dpi=180);plt.close(fig)
    print(headline,flush=True);print('\n'.join(findings),flush=True)

if __name__=="__main__":main()
