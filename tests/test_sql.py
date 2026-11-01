from pathlib import Path
import duckdb

ROOT=Path(__file__).resolve().parents[1]

def setup():
    con=duckdb.connect();con.execute("SET TimeZone='UTC'")
    con.execute('''CREATE TABLE hourly_input(station_id VARCHAR,pollutant VARCHAR,time_utc TIMESTAMPTZ,
      date_local DATE,hour_local INTEGER,unit VARCHAR,expected_unit VARCHAR,concentration DOUBLE)''')
    return con

def test_daily_eligibility_negatives_and_duplicates():
    con=setup()
    rows=[('A','PM2.5',f'2024-01-01 {h:02}:00:00+00','2024-01-01',h,'ug/m3','ug/m3',65) for h in range(16)]
    rows += [rows[0],('A','PM2.5','2024-01-01 22:00:00+00','2024-01-01',22,'ug/m3','ug/m3',-1)]
    con.executemany('INSERT INTO hourly_input VALUES (?,?,?,?,?,?,?,?)',rows)
    con.execute((ROOT/'sql/local/01_clean_hourly.sql').read_text())
    assert con.execute('SELECT count(*) FROM clean_hourly').fetchone()[0]==16
    assert con.execute('SELECT observed_hours,daily_mean FROM hourly_daily').fetchone()==(16,65)
    assert con.execute('SELECT negative_rows FROM hourly_quality').fetchone()[0]==1

def test_conflicting_duplicate_values_are_quarantined():
    con=setup();con.executemany('INSERT INTO hourly_input VALUES (?,?,?,?,?,?,?,?)',[
      ('A','PM2.5','2024-01-01 00:00:00+00','2024-01-01',0,'ug/m3','ug/m3',20),
      ('A','PM2.5','2024-01-01 00:00:00+00','2024-01-01',0,'ug/m3','ug/m3',40)])
    con.execute((ROOT/'sql/local/01_clean_hourly.sql').read_text())
    assert con.execute('SELECT count(*) FROM clean_hourly').fetchone()[0]==0

def test_eight_hour_range_does_not_bridge_a_long_gap():
    con=setup()
    rows=[('A','CO',f'2024-01-01 {h:02}:00:00+00','2024-01-01',h,'mg/m3','mg/m3',1) for h in range(24) if h not in [5,6,7,8]]
    con.executemany('INSERT INTO hourly_input VALUES (?,?,?,?,?,?,?,?)',rows)
    con.execute((ROOT/'sql/local/01_clean_hourly.sql').read_text())
    assert con.execute("SELECT count_8h FROM hourly_windows WHERE hour_local=9").fetchone()[0]==4
    assert con.execute('SELECT max_8h_mean FROM hourly_daily').fetchone()[0]==1
