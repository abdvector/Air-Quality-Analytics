import duckdb
from src.config import PATHS

ALLOWED={'stations','station_daily','station_monthly','station_annual','overall_daily','hourly_quality','overall_join_audit'}

def build_cloud_query(name,where,params,settings):
    """Only allow the app's known filter shapes; bind values instead of interpolating them."""
    from google.cloud import bigquery
    from src.cloud import cloud_config
    cfg=cloud_config(settings)
    if name not in ALLOWED:raise ValueError('Unknown dataset')
    shapes={
      '':[],
      'WHERE date_local BETWEEN ? AND ?':[('start','DATE'),('end','DATE')],
      'WHERE pollutant=? AND date_local BETWEEN ? AND ?':[('pollutant','STRING'),('start','DATE'),('end','DATE')],
    }
    if where not in shapes:raise ValueError('Unsupported query filter')
    spec=shapes[where];params=params or []
    if len(params)!=len(spec):raise ValueError('Query parameter count mismatch')
    query_params=[]
    for (label,kind),value in zip(spec,params):
        where=where.replace('?',f'@{label}',1)
        query_params.append(bigquery.ScalarQueryParameter(label,kind,value))
    sql=f"SELECT * FROM `{cfg['project']}.{cfg['dataset']}.{name}` "+where
    job_config=bigquery.QueryJobConfig(maximum_bytes_billed=cfg['maximum_bytes_billed'],query_parameters=query_params)
    return sql,job_config

def read_gold(name, where='', params=None):
    if name not in ALLOWED: raise ValueError('Unknown dataset')
    path=str(PATHS['gold']/f'{name}.parquet').replace('\\','/').replace("'","''")
    with duckdb.connect() as con:
        return con.execute(f"SELECT * FROM read_parquet('{path}') "+where,params or []).fetchdf()

def read_cloud(name,where='',params=None):
    from src.cloud import load_settings,make_client
    settings=load_settings();sql,config=build_cloud_query(name,where,params,settings)
    with make_client(settings) as client:
        frame=client.query(sql,job_config=config).to_dataframe(create_bqstorage_client=False)
    import pandas as pd
    for col in ['date_local','month']:
        if col in frame:frame[col]=pd.to_datetime(frame[col])
    return frame

def read_cloud_analysis(pollutant,combined,start,end,station_ids,min_coverage,high_month_pct,min_months):
    """Aggregate the filtered study window in BigQuery; do not download a national daily table."""
    from google.cloud import bigquery
    from src.cloud import load_settings,cloud_config,make_client
    import pandas as pd
    settings=load_settings();cfg=cloud_config(settings)
    table='overall_daily' if combined else 'station_daily'
    value='level' if combined else 'comparison_value'
    pollutant_clause='' if combined else ' AND pollutant=@pollutant'
    params=[bigquery.ScalarQueryParameter('start','DATE',start),bigquery.ScalarQueryParameter('end','DATE',end),
      bigquery.ArrayQueryParameter('stations','STRING',list(station_ids)),
      bigquery.ScalarQueryParameter('coverage','FLOAT64',float(min_coverage)),
      bigquery.ScalarQueryParameter('fraction','FLOAT64',float(high_month_pct)),
      bigquery.ScalarQueryParameter('months','INT64',int(min_months))]
    if not combined:params.append(bigquery.ScalarQueryParameter('pollutant','STRING',pollutant))
    base=f'''WITH monthly_counts AS (
     SELECT station_id AS location_id,DATE_TRUNC(date_local,MONTH) month,
      COUNT(*) valid_days,COUNTIF(high) high_days,SUM({value}) sum_value,MAX({value}) max_value
     FROM `{cfg['project']}.{cfg['dataset']}.{table}`
     WHERE date_local BETWEEN @start AND @end AND station_id IN UNNEST(@stations){pollutant_clause}
     GROUP BY station_id,month
    ), monthly AS (
     SELECT *,DATE_DIFF(LEAST(LAST_DAY(month),@end),GREATEST(month,@start),DAY)+1 expected_days,
      100.0*valid_days/(DATE_DIFF(LEAST(LAST_DAY(month),@end),GREATEST(month,@start),DAY)+1) coverage_pct,
      100.0*high_days/valid_days high_pct,sum_value/valid_days mean_value
     FROM monthly_counts
    )'''
    rank_sql=base+''', annual AS (
      SELECT location_id,SUM(valid_days) valid_days,SUM(high_days) high_days,
       SUM(sum_value)/SUM(valid_days) mean_value,MAX(max_value) max_value,
       COUNTIF(coverage_pct>=@coverage) eligible_months,
       COUNTIF(coverage_pct>=@coverage AND high_pct>=@fraction) high_months,
       DATE_DIFF(@end,@start,DAY)+1 expected_days,
       100.0*SUM(valid_days)/(DATE_DIFF(@end,@start,DAY)+1) coverage_pct,
       100.0*SUM(high_days)/SUM(valid_days) high_pct
      FROM monthly GROUP BY location_id
    ) SELECT *,coverage_pct>=@coverage eligible,
      coverage_pct>=@coverage AND high_months>=@months persistent
      FROM annual ORDER BY eligible DESC,high_pct DESC,valid_days DESC,location_id'''
    config=bigquery.QueryJobConfig(maximum_bytes_billed=cfg['maximum_bytes_billed'],query_parameters=params)
    with make_client(settings) as client:
        rank=client.query(rank_sql,job_config=config).to_dataframe(create_bqstorage_client=False)
        # Fetch monthly summaries only for stations plotted on the heatmap.
        top_ids=rank.head(15).location_id.tolist()
        month_params=params+[bigquery.ArrayQueryParameter('top_ids','STRING',top_ids)]
        monthly=client.query(base+' SELECT * FROM monthly WHERE location_id IN UNNEST(@top_ids)',
          job_config=bigquery.QueryJobConfig(maximum_bytes_billed=cfg['maximum_bytes_billed'],query_parameters=month_params)).to_dataframe(create_bqstorage_client=False)
    if 'month' in monthly:monthly['month']=pd.to_datetime(monthly['month'])
    return rank,monthly

def read_cloud_comparison(pollutant,combined,start,end,station_ids):
    from google.cloud import bigquery
    from src.cloud import load_settings,cloud_config,make_client
    import pandas as pd
    settings=load_settings();cfg=cloud_config(settings)
    table='overall_daily' if combined else 'station_daily'
    columns='station_id,date_local,level,category,pollutants_available,defining_pollutant,high' if combined else 'station_id,date_local,observed_hours,daily_mean,comparison_value,unit,benchmark,high'
    clause='' if combined else ' AND pollutant=@pollutant'
    params=[bigquery.ScalarQueryParameter('start','DATE',start),bigquery.ScalarQueryParameter('end','DATE',end),bigquery.ArrayQueryParameter('stations','STRING',list(station_ids))]
    if not combined:params.append(bigquery.ScalarQueryParameter('pollutant','STRING',pollutant))
    sql=f'''SELECT {columns} FROM `{cfg['project']}.{cfg['dataset']}.{table}`
      WHERE date_local BETWEEN @start AND @end AND station_id IN UNNEST(@stations){clause} ORDER BY station_id,date_local'''
    with make_client(settings) as client:
        frame=client.query(sql,job_config=bigquery.QueryJobConfig(maximum_bytes_billed=cfg['maximum_bytes_billed'],query_parameters=params)).to_dataframe(create_bqstorage_client=False)
    frame['date_local']=pd.to_datetime(frame.date_local)
    return frame.rename(columns={'station_id':'location_id'})
