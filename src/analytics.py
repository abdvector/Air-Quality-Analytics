"""Coverage-aware India screening. Concentration and reported AQI remain separate metrics."""
import pandas as pd

def summarize(daily,start,end,min_coverage=75,high_month_pct=10,min_months=3):
    start=pd.Timestamp(start);end=pd.Timestamp(end)
    if start>end:raise ValueError('Start must not be after end')
    if daily.empty:return pd.DataFrame()
    data=daily.copy();data['date_local']=pd.to_datetime(data.date_local)
    data=data[data.date_local.between(start,end)]
    if data.empty:return pd.DataFrame()
    if data.duplicated(['location_id','date_local']).any():raise ValueError('Duplicate location/date observations')
    if 'high' not in data:data['high']=data.aqi>200
    value='comparison_value' if 'comparison_value' in data else ('level' if 'level' in data else 'aqi')
    data['month']=data.date_local.dt.to_period('M').astype(str)
    monthly=data.groupby(['location_id','month']).agg(valid_days=('high','size'),high_days=('high','sum')).reset_index()
    def expected(month):
        first=pd.Timestamp(month+'-01');last=first+pd.offsets.MonthEnd()
        return (min(end,last)-max(start,first)).days+1
    monthly['expected_days']=monthly.month.map(expected)
    monthly['coverage_pct']=100*monthly.valid_days/monthly.expected_days
    monthly['high_pct']=100*monthly.high_days/monthly.valid_days
    monthly['eligible_month']=monthly.coverage_pct>=min_coverage
    monthly['high_month']=monthly.eligible_month&(monthly.high_pct>=high_month_pct)
    months=monthly.groupby('location_id').agg(eligible_months=('eligible_month','sum'),high_months=('high_month','sum'))
    result=data.groupby('location_id').agg(valid_days=('high','size'),high_days=('high','sum'),mean_value=(value,'mean'),max_value=(value,'max')).join(months).reset_index()
    result['expected_days']=(end-start).days+1
    result['coverage_pct']=100*result.valid_days/result.expected_days
    result['high_pct']=100*result.high_days/result.valid_days
    result['eligible']=result.coverage_pct>=min_coverage
    result['persistent']=result.eligible&(result.high_months>=min_months)
    return result.sort_values(['eligible','high_pct','valid_days','location_id'],ascending=[False,False,False,True]).reset_index(drop=True)

def aqi_category(value):
    if pd.isna(value) or value<0:return 'Insufficient data'
    for bound,label in [(50,'Good'),(100,'Satisfactory'),(200,'Moderate'),(300,'Poor'),(400,'Very Poor')]:
        if value<=bound:return label
    return 'Severe'
