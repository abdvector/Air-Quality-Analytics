from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YEAR = 2024
POLLUTANTS = {
 'PM2.5': {'name':'PM2.5','unit':'ug/m3','short_unit':'ug/m3','benchmark':60.0,'period':'24-hour mean'},
 'PM10': {'name':'PM10','unit':'ug/m3','short_unit':'ug/m3','benchmark':100.0,'period':'24-hour mean'},
 'NO2': {'name':'NO2','unit':'ug/m3','short_unit':'ug/m3','benchmark':80.0,'period':'24-hour mean'},
 'SO2': {'name':'SO2','unit':'ug/m3','short_unit':'ug/m3','benchmark':80.0,'period':'24-hour mean'},
 'Ozone': {'name':'O3','unit':'ug/m3','short_unit':'ug/m3','benchmark':100.0,'period':'highest eligible 8-hour mean'},
 'CO': {'name':'CO','unit':'mg/m3','short_unit':'mg/m3','benchmark':2.0,'period':'highest eligible 8-hour mean'},
 'NH3': {'name':'NH3','unit':'ug/m3','short_unit':'ug/m3','benchmark':400.0,'period':'24-hour mean'},
}
SOURCE = 'https://airquality.xkdr.org/'
PATHS = {x: ROOT / 'data' / 'india' / x for x in ['raw','bronze','silver','gold','audit']}
OUTPUT = ROOT / 'output' / 'india'

def ensure_dirs():
    for path in PATHS.values():
        path.mkdir(parents=True, exist_ok=True)
