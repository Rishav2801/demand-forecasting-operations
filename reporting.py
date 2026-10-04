"""Small, local reporting layer. No server, credentials or external JS required."""
from pathlib import Path
import hashlib
import html
import json
import urllib.request
import ssl
import certifi
import plotly.io as pio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent

def fetch(url, name):
    cache = ROOT / '.cache'
    cache.mkdir(exist_ok=True)
    path = cache / name
    if not path.exists():
        request = urllib.request.Request(url, headers={'User-Agent': 'analytics-portfolio/1.0'})
        with urllib.request.urlopen(request, timeout=120, context=ssl.create_default_context(cafile=certifi.where())) as response:
            payload = response.read()
        path.write_bytes(payload)
    return path

def manifest(paths):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def save_json(name, obj):
    (ROOT / name).write_text(json.dumps(obj, indent=2, allow_nan=False, default=str)+'\n')

def report(title, subtitle, metrics, figures, sections):
    cards = ''.join(f'<div class="card"><small>{html.escape(str(k))}</small><strong>{html.escape(str(v))}</strong></div>' for k,v in metrics.items())
    charts = ''
    for i, fig in enumerate(figures):
        fig.update_layout(template='plotly_white', font=dict(family='Arial', size=13), margin=dict(l=65,r=30,t=65,b=65), height=440, paper_bgcolor='#ffffff', colorway=['#087f8c','#f0a34a','#6273cf','#d05f74'])
        charts += '<section>'+pio.to_html(fig, full_html=False, include_plotlyjs=True if i==0 else False, config={'responsive':True, 'displaylogo':False})+'</section>'
    notes = ''.join(f'<section><h2>{html.escape(k)}</h2><p>{html.escape(v)}</p></section>' for k,v in sections.items())
    page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+html.escape(title)+'</title><style>body{margin:0;background:#eef3f5;color:#152c3b;font:16px/1.65 system-ui}main{max-width:1180px;margin:auto;padding:36px 22px}header{padding:18px 0 30px;border-bottom:1px solid #c9d5dc}h1{font-size:clamp(30px,4vw,48px);line-height:1.12;letter-spacing:-1.5px;margin:12px 0}h2{font-size:21px}header small{color:#087f8c;letter-spacing:2px;font-weight:700}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:15px;margin:24px 0}.card,section{background:white;border:1px solid #dce5e9;border-radius:12px;padding:22px;margin-bottom:20px}.card small{display:block;color:#506777}.card strong{display:block;font-size:28px}section{overflow:hidden}p{max-width:100ch}footer{font-size:13px;color:#506777}</style><main><header><small>ANALYTICS / DECISION SYSTEMS</small><h1>'+html.escape(title)+'</h1><p>'+html.escape(subtitle)+'</p></header><div class="cards">'+cards+'</div>'+charts+notes+'<footer>Reproduce with python pipeline.py. Methods, source attribution and limitations are documented in README.md and DATA.md.</footer></main></html>'
    (ROOT/'dashboard.html').write_text(page)

def preview(title, labels, values, ylabel):
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
    fig, ax = plt.subplots(figsize=(12,5), facecolor='#f4f7fa')
    ax.set_facecolor('#f4f7fa')
    ax.bar(labels,values,color='#087f8c',width=.6)
    ax.set_title(title,loc='left',fontsize=19,pad=20,weight='bold')
    ax.set_ylabel(ylabel)
    ax.grid(axis='y',alpha=.15)
    ax.set_axisbelow(True)
    fig.tight_layout(pad=2)
    fig.savefig(ROOT/'preview.png',dpi=140)
    plt.close(fig)

def export_sql_results(frame, table):
    """Execute the committed analytical query against the exact output population."""
    import sqlite3
    import pandas as pd
    with sqlite3.connect(':memory:') as connection:
        frame.to_sql(table, connection, index=False)
        result = pd.read_sql((ROOT/'analysis.sql').read_text(), connection)
    if result.empty:
        raise ValueError('SQL report unexpectedly returned no rows')
    result.to_csv(ROOT/'sql_results.csv', index=False)
    return result
