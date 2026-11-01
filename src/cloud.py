"""BigQuery authentication shared by local Streamlit and Community Cloud; never log secrets."""
import re
from pathlib import Path
from src.config import ROOT

def load_settings():
    # Streamlit's secrets loader supports local TOML and hosted private Secrets.
    import streamlit as st
    try:
        return st.secrets.to_dict()
    except FileNotFoundError:
        return {}

def cloud_config(settings):
    cfg=dict(settings.get('bigquery',{}))
    project=cfg.get('project','')
    dataset=cfg.get('dataset','air_quality')
    if not re.fullmatch(r'[a-z][a-z0-9-]{4,61}[a-z0-9]',project):
        raise ValueError('Set a valid bigquery.project in private Streamlit secrets.')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',dataset):
        raise ValueError('Invalid BigQuery dataset ID.')
    limit=int(cfg.get('maximum_bytes_billed',1_000_000_000))
    if limit<=0:raise ValueError('maximum_bytes_billed must be positive.')
    cfg.update(project=project,dataset=dataset,location=cfg.get('location','US'),maximum_bytes_billed=limit)
    return cfg

def make_client(settings=None):
    from google.cloud import bigquery
    from google.oauth2 import service_account
    settings=load_settings() if settings is None else settings
    cfg=cloud_config(settings)
    info=settings.get('gcp_service_account')
    filename=cfg.get('credentials_file')
    if info:
        credentials=service_account.Credentials.from_service_account_info(dict(info))
    elif filename:
        path=Path(filename).expanduser()
        if not path.is_absolute():path=ROOT/path
        if not path.is_file():raise ValueError('Configured credentials_file does not exist. Check the path in private secrets.')
        credentials=service_account.Credentials.from_service_account_file(str(path))
    else:
        # Supports user ADC for pipeline work without assigning write access to the viewer identity.
        credentials=None
    return bigquery.Client(project=cfg['project'],location=cfg['location'],credentials=credentials)