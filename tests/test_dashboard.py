from pathlib import Path
from datetime import date
import pytest
from streamlit.testing.v1 import AppTest
from src.config import PATHS
ROOT=Path(__file__).resolve().parents[1]
pytestmark=pytest.mark.skipif(not (PATHS['audit']/'pipeline_run.json').exists(),reason='Run India pipeline first')

def test_all_pollutants_and_combined_view():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
    assert not app.exception
    assert app.title[0].value=='India Air Quality Atlas'
    for name in ['PM10','NO2','SO2','O3','CO','NH3','PM2.5']:
        app.selectbox[0].set_value(name).run();assert not app.exception,name
    app.radio[0].set_value('Combined pollution level').run()
    assert not app.exception
    assert any('pollutants_available' in t.value.columns for t in app.dataframe)

def test_india_state_city_and_short_period():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
    app.selectbox[1].set_value('Delhi').run();assert not app.exception
    app.date_input[0].set_value((date(2024,1,1),date(2024,1,2))).run();assert not app.exception
