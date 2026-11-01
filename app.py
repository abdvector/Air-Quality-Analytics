"""India Air Quality Atlas: CPCB observations, coverage and ordinal combined pollution levels."""
import json
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import PATHS,POLLUTANTS
from src.repository import read_cloud,read_cloud_analysis,read_cloud_comparison
from src.india_bands import LABELS

st.set_page_config(page_title='India Air Quality Atlas',page_icon='',layout='wide')
st.markdown('''<style>.block-container{padding-top:3rem;max-width:1480px}h1{letter-spacing:-.04em}
[data-testid="stMetric"]{border:1px solid #dce4ec;border-radius:12px;padding:14px}</style>''',unsafe_allow_html=True)
st.caption('INDIA  /  CPCB MONITORING STATIONS  /  HISTORICAL DATA, 2024')
st.title('India Air Quality Atlas')
st.write('Explore pollution hotspots across Indian cities. Check how much data supports each result.')
if not (PATHS['audit']/'pipeline_run.json').exists():
    st.info('Run metadata is missing. Restore the verified audit files before starting the dashboard.');st.stop()

@st.cache_data(ttl=600,max_entries=64)
def load(name,where='',params=None):
    return read_cloud(name,where,params)

@st.cache_data(ttl=600,max_entries=32)
def cloud_analysis(pollutant,combined,start,end,station_ids,coverage,fraction,months):
    return read_cloud_analysis(pollutant,combined,start,end,station_ids,coverage,fraction,months)

@st.cache_data(ttl=600,max_entries=32)
def cloud_comparison(pollutant,combined,start,end,station_ids):
    return read_cloud_comparison(pollutant,combined,start,end,station_ids)

stations=load('stations');stats=json.loads((PATHS['audit']/'pipeline_run.json').read_text())
with st.sidebar:
    st.header('Explore India')
    mode=st.radio('Analysis view',['Individual pollutant','Combined pollution level'])
    combined=mode=='Combined pollution level'
    pollutant=st.selectbox('Pollutant',[m['name'] for m in POLLUTANTS.values()],disabled=combined)
    state=st.selectbox('State / union territory',['All states']+sorted(stations.state.dropna().unique().tolist()))
    scope=stations if state=='All states' else stations[stations.state==state]
    city=st.selectbox('City',['All cities']+sorted(scope.city.dropna().unique().tolist()))
    dates=st.date_input('Analysis period',(date(2024,1,1),date(2024,12,31)),min_value=date(2024,1,1),max_value=date(2024,12,31))
    coverage=st.slider('Minimum day coverage (%)',50,95,75,5)
    with st.expander('Persistence rule'):
        fraction=st.slider('High-pollution days per month (%)',5,30,10,5)
        months=st.slider('Required high-pollution months',1,6,3)
    st.caption('Default persistence: at least 10% high days in at least three adequately observed months. These are project screening choices.')
    st.caption('Data source: Google BigQuery (cached up to 10 minutes).')
if len(dates)!=2:st.info('Select a start and end date.');st.stop()
start,end=dates
if city!='All cities':scope=scope[scope.city==city]
if combined:
    value='level';unit='level (0-5)';threshold=3
    st.info('Combined level = worst available CPCB pollutant band, from 0 (Good) to 5 (Severe). At least three valid pollutants, including PM2.5 or PM10, are required. This derived screening score is not an official reported AQI.')
    metric_label='Days at Poor or worse (%)'
else:
    config=next(v for v in POLLUTANTS.values() if v['name']==pollutant)
    value='comparison_value';unit=config['short_unit'];threshold=config['benchmark']
    st.caption(f"{pollutant}  /  {config['period']}  /  benchmark: {threshold:g} {unit}  /  India NAAQS reference")
    metric_label='Days above benchmark (%)'
rank,cloud_monthly=cloud_analysis(pollutant,combined,start,end,tuple(scope.station_id),coverage,fraction,months)
if rank.empty:st.warning('No observations match this selection. Try another city, pollutant or period.');st.stop()
rank=rank.merge(scope.rename(columns={'station_id':'location_id'}),on='location_id',how='left')
rank['label']=rank.city.fillna('Station')+'  /  '+rank.location_id
eligible=rank[rank.eligible]
cols=st.columns(4)
cols[0].metric('Measurements',f"{stats['counts']['hourly_input']/1e6:.1f}M",help='Selected CPCB observations, across seven pollutants.')
cols[1].metric('Stations',f'{len(rank):,}');cols[2].metric('Coverage eligible',f'{len(eligible):,}')
cols[3].metric('Persistent',f'{int(rank.persistent.sum()):,}')
st.caption(f"{stats['counts']['acquired_all_parameter_rows']:,} source readings acquired; {stats['counts']['hourly_input']:,} CPCB readings selected for the seven pollutants. All displayed locations are in India.")
tabs=st.tabs(['Hotspots','Monthly patterns','Compare stations','Data & method'])
with tabs[0]:
    st.subheader('Where high pollution repeats')
    if eligible.empty:st.warning('No stations meet the coverage rule. Adjust the period or threshold to explore further.')
    else:
        mapped=eligible.dropna(subset=['latitude','longitude']).copy();mapped['marker_size']=mapped.high_pct.clip(lower=1)
        offline=st.toggle('Offline coordinate map',False)
        common=dict(color='high_pct',size='marker_size',size_max=23,hover_name='station_name',
          hover_data={'city':True,'state':True,'coverage_pct':':.1f','valid_days':True,'marker_size':False},
          labels={'high_pct':metric_label},color_continuous_scale='YlOrRd',range_color=[0,100])
        fig=px.scatter(mapped,x='longitude',y='latitude',**common) if offline else px.scatter_map(mapped,
          lat='latitude',lon='longitude',**common,map_style='carto-positron',center={'lat':22.5,'lon':80},zoom=3.2)
        fig.update_layout(height=480,margin=dict(l=0,r=0,t=0,b=0));st.plotly_chart(fig,width='stretch')
        missing=len(eligible)-len(mapped)
        st.caption(f'{missing} eligible stations have no source coordinates and remain in the ranking. The online basemap depicts monitored points, not interpolated pollution across India.')
        fig=px.bar(eligible.head(15),x='high_pct',y='label',orientation='h',color='persistent',
          labels={'high_pct':metric_label,'label':'Station','persistent':'Persistent'},color_discrete_map={True:'#a43d2d',False:'#376a8a'})
        fig.update_layout(yaxis={'categoryorder':'total ascending'},height=470,margin=dict(t=10));st.plotly_chart(fig,width='stretch')
    with st.expander('All stations and coverage'):
        shown=rank[['location_id','station_name','city','state','valid_days','expected_days','coverage_pct','high_days','high_pct','high_months','eligible','persistent']]
        st.dataframe(shown.round(2),hide_index=True,width='stretch')
        st.download_button('Download ranking',shown.to_csv(index=False),'india_hotspots.csv','text/csv')

with tabs[1]:
    st.subheader('Monthly pollution and data coverage')
    monthly=cloud_monthly.copy();monthly['month']=pd.to_datetime(monthly.month).dt.strftime('%Y-%m')
    monthly=monthly.merge(rank[['location_id','label']],on='location_id')
    shown=monthly.copy();chosen_metric='high_pct' if combined else 'mean_value'
    shown.loc[shown.coverage_pct<coverage,chosen_metric]=float('nan')
    matrix=shown.pivot(index='label',columns='month',values=chosen_metric).reindex(columns=pd.period_range(start,end,freq='M').astype(str))
    title='Days at Poor or worse (%)' if combined else f'Mean daily comparison value ({unit})'
    st.plotly_chart(px.imshow(matrix,aspect='auto',color_continuous_scale='YlOrRd',labels={'color':title,'x':'Month','y':'Station'}),width='stretch')
    st.caption('Blank cells lack sufficient day coverage. A monthly concentration summary or poor-day fraction is descriptive, not an official monthly AQI.')
    matrix=monthly.pivot(index='label',columns='month',values='coverage_pct')
    st.plotly_chart(px.imshow(matrix,aspect='auto',range_color=[0,100],color_continuous_scale='Blues',labels={'color':'Coverage (%)'}),width='stretch')

with tabs[2]:
    st.subheader('Compare stations over the same dates')
    labels=dict(zip(rank.location_id,rank.label))
    picks=st.multiselect('Stations',rank.location_id.tolist(),default=rank.head(2).location_id.tolist(),format_func=lambda v:labels[v],max_selections=3)
    if picks:
        comparison=cloud_comparison(pollutant,combined,start,end,tuple(picks))
        series=comparison.copy();series['date_local']=pd.to_datetime(series.date_local)
        calendar=pd.MultiIndex.from_product([picks,pd.date_range(start,end)],names=['location_id','date_local']).to_frame(index=False)
        series=calendar.merge(series,on=['location_id','date_local'],how='left');series['Station']=series.location_id.map(labels)
        fig=px.line(series,x='date_local',y=value,color='Station',labels={value:('Combined level (0-5)' if combined else f'Concentration ({unit})'),'date_local':'Date'})
        fig.add_hline(y=2.5 if combined else threshold,line_dash='dash',annotation_text='Poor starts at level 3' if combined else 'India benchmark')
        if combined:fig.update_yaxes(tickvals=list(range(6)),ticktext=LABELS,range=[-.1,5.1])
        st.plotly_chart(fig,width='stretch')
        with st.expander('Daily source-derived details'):
            columns=['location_id','date_local','level','category','pollutants_available','defining_pollutant'] if combined else ['location_id','date_local','observed_hours','daily_mean','comparison_value','unit','benchmark','high']
            detail=comparison[columns].sort_values('date_local',ascending=False)
            st.dataframe(detail,hide_index=True,width='stretch')
            st.download_button('Download daily details',detail.to_csv(index=False),'india_station_daily.csv','text/csv')
        if combined:
            counts=comparison.groupby('defining_pollutant').size().reset_index(name='Days')
            st.plotly_chart(px.bar(counts,x='defining_pollutant',y='Days',labels={'defining_pollutant':'Pollutant setting the worst band'}),width='stretch')
    else:st.info('Choose up to three stations.')

with tabs[3]:
    st.subheader('Data, definitions and execution evidence')
    st.success('Dashboard queries are running against Google BigQuery. Cached results refresh after ten minutes.')
    cloud_audit=PATHS['audit']/'cloud_execution.json'
    if cloud_audit.exists():
        with st.expander('Executed BigQuery jobs'):
            evidence=json.loads(cloud_audit.read_text())
            st.dataframe(pd.DataFrame(evidence.get('jobs',[])),hide_index=True,width='stretch')
    st.json(stats);st.dataframe(load('hourly_quality'),hide_index=True,width='stretch')
    st.markdown('''
- **India source:** India Air Quality Database, XKDR Forum (2026), compiling CPCB CAAQM observations. This project selects CPCB stations only; embassy monitors and other chemicals are excluded from the analytical subset.
- **Time:** publisher timestamps are already IST. UTC hourly keys are created explicitly; calendar grouping remains IST.
- **Eligibility:** at least 16 observed hours per day. For CO and O3, use the highest eight-hour mean with at least six readings, ending within the same IST day after 07:00. No gaps are filled.
- **Individual pollutant:** compare to its matching India NAAQS reference and averaging period. Exceedance is a screening result, not a regulatory non-attainment determination.
- **Combined level:** worst CPCB band among available eligible pollutants, requiring at least three including PM2.5 or PM10. Lead is not available. The score is ordinal (0-5), not official numeric AQI or a validated combined health-risk measure. Missing pollutants may hide worse conditions.
- **Ozone:** the top two CPCB bands use the maximum observed one-hour value, reflecting the source table's one-hour footnote; lower bands use the eight-hour comparison value.
- **Coverage:** observed valid days divided by all calendar days in the selected period. Missing days are not clean days. Seasonal schedules or partial operation can reduce coverage.
- **Scope:** monthly patterns within 2024; no prediction or attribution of pollution causes.
- **Execution:** the run audit above records BigQuery processing and query evidence. Local DuckDB results provide an independent validation reference. Historical BigQuery tables use date clustering, avoiding Sandbox expiry of 2024 event-date partitions.

[Dataset and attribution](https://airquality.xkdr.org/)  /  [India AQI bands](https://ies.gov.in/arthapedia/concept/national-air-quality-index)  /  [India standards](https://www.ies.gov.in/index.php/arthapedia/concept/ambient-air-quality-standards-india)
''')
