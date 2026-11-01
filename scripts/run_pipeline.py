"""Run the local lifecycle in dependency order, failing immediately on a bad stage."""
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
for script in ['download_data.py','ingest.py','process.py']:
    subprocess.run([sys.executable,str(root/'scripts'/script)],cwd=root,check=True)
print('Pipeline complete. Run scripts/bigquery_run.py to publish and validate cloud tables, then launch app.py.')
