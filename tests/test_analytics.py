import pandas as pd
import pytest
from src.analytics import summarize,aqi_category
from src.india_bands import band,combine_bands

def test_missing_days_and_leap_year():
    d=pd.DataFrame({'location_id':['A','A'],'date_local':['2024-01-01','2024-01-02'],'comparison_value':[65,45],'high':[True,False]})
    r=summarize(d,'2024-01-01','2024-12-31').iloc[0]
    assert r.expected_days==366 and r.high_pct==50
    assert r.coverage_pct==pytest.approx(200/366) and not r.eligible

def test_partial_month_persistence():
    d=pd.DataFrame({'location_id':['A','A'],'date_local':['2024-02-28','2024-02-29'],'level':[3,2],'high':[True,False]})
    r=summarize(d,'2024-02-28','2024-02-29',min_months=1).iloc[0]
    assert r.coverage_pct==100 and r.persistent

def test_duplicates_fail():
    d=pd.DataFrame({'location_id':['A','A'],'date_local':['2024-01-01']*2,'aqi':[200,201]})
    with pytest.raises(ValueError,match='Duplicate'):summarize(d,'2024-01-01','2024-01-31')

@pytest.mark.parametrize('value,label',[(50,'Good'),(51,'Satisfactory'),(100,'Satisfactory'),(101,'Moderate'),(200,'Moderate'),(201,'Poor'),(301,'Very Poor'),(401,'Severe')])
def test_india_categories(value,label):assert aqi_category(value)==label

@pytest.mark.parametrize('pollutant,value,expected',[('PM2.5',30,0),('PM2.5',60,1),('PM2.5',90,2),('PM2.5',250,4),('PM2.5',251,5),('CO',2,1),('CO',2.1,2),('NO2',80,1)])
def test_band_boundaries(pollutant,value,expected):assert band(pollutant,value)==expected

def test_ozone_uses_one_hour_for_upper_bands():
    assert band('O3',170,190)==3
    assert band('O3',170,250)==4
    assert band('O3',170,800)==5

def test_composite_missing_pollutants_and_particulate_requirement():
    d=pd.DataFrame({'station_id':['A','A','A','B','B','B','C','C'], 'date_local':['2024-01-01']*8,
      'pollutant':['PM2.5','NO2','CO','SO2','NO2','CO','PM10','CO'],'band':[3,0,1,3,1,0,5,1]})
    out=combine_bands(d)
    assert out.station_id.tolist()==['A']
    assert out.iloc[0].level==3 and out.iloc[0].pollutants_available==3

def test_invalid_concentrations():
    assert band('PM2.5',-1) is None
    assert band('CO',float('nan')) is None

def test_float_noise_does_not_move_an_exact_boundary():
    assert band('PM2.5',60+1e-12)==1
    assert band('PM2.5',90+1e-12)==2
