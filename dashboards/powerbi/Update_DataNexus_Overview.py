"""Read-only local DataNexus inventory for the Power BI end-to-end report.

Run this before Home > Refresh. Reads aggregate counts and file metadata only;
does not call external providers, change DataNexus, or run pipeline jobs.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()

def collect(repo):
    data=repo/'data/dev'; now=datetime.now(timezone.utc).isoformat()
    gold=data/'nyc_tlc/silver_gold_2024_01'
    snap=json.loads((gold/'reporting_preview.json').read_text(encoding='utf-8'))
    manifest=json.loads((gold/'transform_manifest.json').read_text(encoding='utf-8'))
    bronze=data/'nyc_tlc/yellow_tripdata_2024-01.parquet'
    validation=json.loads((data/'nyc_tlc/validation/yellow_tripdata_2024-01.parquet.validation.json').read_text(encoding='utf-8'))
    checks={
        'Original source checksum':sha(bronze)==snap['source_sha256'],
        'Complete validation evidence':validation.get('complete_row_scan') is True and validation.get('required_schema_validated') is True and validation.get('source_sha256')==snap['source_sha256'] and validation.get('row_count')==snap['validated_source_rows'],
        'Gold checksum':sha(gold/'gold_daily_trips.parquet')==snap['gold_sha256'],
        'Silver checksum':sha(gold/'silver_trips.parquet')==snap['silver_sha256'],
        'Transform manifest checksum':sha(gold/'transform_manifest.json')==snap['transform_manifest_sha256'],
        'Source row reconciliation':snap['validated_source_rows']==snap['silver_rows']+snap['quarantined_rows'],
        'Gold trip reconciliation':sum(r['trip_count'] for r in snap['daily'])==snap['silver_rows'],
        'Snapshot stage':snap['stage']=='local_historical_reporting_preview',
        'Month coverage reconciliation':snap['in_month_trip_count']+snap['outside_month_trip_count']==snap['silver_rows'] and len({r['date'] for r in snap['daily']})==len(snap['daily']),
    }
    if not all(checks.values()):raise ValueError('DataNexus snapshot failed integrity checks: '+str(checks))
    av={'events':None,'aircraft':None,'positions':None,'latest':None}
    av_series=[];aviation_path=data/'aviation.sqlite3'
    if aviation_path.is_file():
        with closing(sqlite3.connect(aviation_path.resolve().as_uri()+'?mode=ro',uri=True,timeout=3)) as db:
            db.execute('PRAGMA query_only=ON')
            row=db.execute('SELECT COUNT(*),COUNT(DISTINCT icao24),SUM(latitude IS NOT NULL AND longitude IS NOT NULL),MAX(source_time) FROM events').fetchone()
            av=dict(zip(av,row))
            av_series=[{'date':day,'events':count} for day,count in db.execute('SELECT SUBSTR(source_time,1,10),COUNT(*) FROM events GROUP BY SUBSTR(source_time,1,10) ORDER BY 1')]
    mta=[];mta_path=data/'mta/mta_aggregate.sqlite3'
    if mta_path.is_file():
        with closing(sqlite3.connect(mta_path.resolve().as_uri()+'?mode=ro',uri=True,timeout=3)) as db:
            db.execute('PRAGMA query_only=ON');db.row_factory=sqlite3.Row
            mta=[dict(r) for r in db.execute('SELECT provider_timestamp_utc,observed_at_utc,feed_id,entities,trip_updates,vehicle_positions,alerts FROM mta_aggregates ORDER BY provider_timestamp_utc')]
    latest=mta[-1] if mta else {}
    registry=load_module('datanexus_source_registry',repo/'apps/api/source_registry.py')
    gate=load_module('datanexus_release_gate',repo/'scripts/release_gate.py').readiness_report(repo/'production-evidence')
    sources=[
        {'Feed':'NYC TLC Yellow Taxi','Domain':'Urban Mobility','Mode':'Historical batch','Records':snap['validated_source_rows'],'Unit':'source trips','Observed UTC':snap['generated_at_utc'],'Status':'Validated local history','Evidence':'Parquet + validation + reconciled Gold','Scope':'January 2024 source; validated month boundaries retained'},
        {'Feed':'MTA GTFS-RT','Domain':'Urban Mobility','Mode':'Stored observations','Records':len(mta) if mta_path.is_file() else None,'Unit':'stored observations','Observed UTC':latest.get('provider_timestamp_utc'),'Status':'Stored observations' if mta else 'No stored observations','Evidence':'Read-only aggregate SQLite store','Scope':'One-shot observations; no continuous subscription verified'},
        {'Feed':'Aviation event sink','Domain':'Aviation','Mode':'Local sample','Records':av['events'],'Unit':'stored events','Observed UTC':av['latest'],'Status':'Local sample only' if av['events'] else 'No stored events','Evidence':'Read-only local SQLite event store','Scope':'Small historical sample; live OpenSky collection not established'},
    ]
    domain_coverage=[]
    for d in registry.SOURCE_CONTRACTS:
        if d['id']=='mobility':
            verified_modes=sum((x['Records'] or 0)>0 for x in sources if x['Domain']=='Urban Mobility')
            domain_coverage.append({'Domain ID':'mobility','Domain':d['name'],'Region':d['region'],
                'Historical Source':d['historical'],'Latest Source':d['latest'],
                'Historical Connection':'Verified local NYC TLC monthly snapshot',
                'Latest Connection':'Bounded stored MTA events' if mta else 'No stored MTA observations',
                'Verified Local Feeds':verified_modes,'Continuous Live Verified':False,
                'Data Available':verified_modes>0,'Connection State':'local_evidence_only' if verified_modes else 'not_connected',
                'Licensing State':'review_required','Refresh Mode':'manual_import',
                'Evidence Type':'Local files and SQLite; not provider SLA'})
        else:
            domain_coverage.append({'Domain ID':d['id'],'Domain':d['name'],'Region':d['region'],
                'Historical Source':d['historical'],'Latest Source':d['latest'],
                'Historical Connection':'Not connected','Latest Connection':'Not connected',
                'Verified Local Feeds':0,'Continuous Live Verified':False,'Data Available':False,
                'Connection State':'not_connected','Licensing State':'pending',
                'Refresh Mode':'not_configured','Evidence Type':'Catalog design only'})
    domain_coverage.append({'Domain ID':'aviation','Domain':'Aviation','Region':'Global',
        'Historical Source':'Local aviation SQLite events','Latest Source':'No verified live source',
        'Historical Connection':'Local event sample' if av['events'] else 'No local events',
        'Latest Connection':'Not connected','Verified Local Feeds':1 if av['events'] else 0,
        'Continuous Live Verified':False,'Data Available':bool(av['events']),
        'Connection State':'local_sample_only' if av['events'] else 'not_connected',
        'Licensing State':'review_required','Refresh Mode':'manual_import',
        'Evidence Type':'SQLite sample; not validated external coverage'})
    for d in registry.SOURCE_CONTRACTS:
        if d['id']=='mobility':continue
        sources.append({'Feed':d['historical'],'Domain':d['name'],'Mode':d['update_model'],'Records':None,'Unit':'unverified','Observed UTC':None,'Status':'Planned / no verified data','Evidence':'Design contract only','Scope':d['latest']})
    feed_count=sum((x['Records'] or 0)>0 for x in sources)
    domains=len(set(x['Domain'] for x in sources))
    metrics={'captured_utc':now,'local_feeds':feed_count,'catalog_feeds':len(sources),'catalog_domains':domains,'approved_controls':gate['passed'],'required_controls':gate['required'],'release_status':gate['status'],'aviation_events':av['events'],'aviation_aircraft':av['aircraft'],'aviation_positions':av['positions'],'aviation_latest':av['latest'],'mta_observations':len(mta),'mta_latest_entities':latest.get('entities'),'mta_latest_trip_updates':latest.get('trip_updates'),'mta_latest_vehicle_positions':latest.get('vehicle_positions'),'mta_latest_alerts':latest.get('alerts'),'mta_latest_provider_utc':latest.get('provider_timestamp_utc'),'mta_latest_observed_utc':latest.get('observed_at_utc'),'continuous_feeds_verified':0,'integrity_checks_passed':sum(checks.values()),'integrity_checks_total':len(checks)}
    pipeline=[
        {'Order':1,'Stage':'Acquire','Status':'Local artifact present','Count':snap['validated_source_rows'],'Unit':'source rows','Evidence':'Original NYC TLC monthly Parquet','Detail':'Source month: '+snap['source_month']},
        {'Order':2,'Stage':'Validate','Status':'Evidence recorded','Count':snap['validated_source_rows'],'Unit':'scanned rows','Evidence':'Complete row scan + source identity','Detail':'Preliminary local data-quality policy'},
        {'Order':3,'Stage':'Curate','Status':'Reconciled','Count':snap['silver_rows'],'Unit':'accepted rows','Evidence':'Source = accepted + quarantined','Detail':f"{snap['quarantined_rows']:,} distinct rows quarantined"},
        {'Order':4,'Stage':'Aggregate','Status':'Reconciled','Count':len(snap['daily']),'Unit':'daily groups','Evidence':'Gold trip sum = accepted row count','Detail':f"{snap['in_month_days']} in-month dates; {snap['outside_month_days']} outside month"},
        {'Order':5,'Stage':'Report','Status':'Integrity checked','Count':sum(checks.values()),'Unit':'passed checks','Evidence':'Snapshot hashes + reconciliations','Detail':'Same local snapshot used by the DataNexus portal'},
        {'Order':6,'Stage':'Analyze','Status':'Power BI local import','Count':6,'Unit':'report pages','Evidence':'Power BI semantic model + interactive visuals','Detail':'Refresh imports current local reporting files'},
    ]
    services=[{'Component':a,'Evidence state':b,'Meaning':c} for a,b,c in [
        ('NYC TLC batch pipeline','Verified local artifacts','Acquisition, validation, Silver, Gold and reporting outputs reconcile'),
        ('MTA observation store','Stored aggregates','Provider timestamps retained; not proof of a continuously running feed'),
        ('Aviation event store','Historical sample','Event counts are from the local SQLite sink'),
        ('Kafka / Spark / Iceberg','Runtime not monitored','Configuration and code do not establish current service health'),
        ('PostgreSQL audit / API','Runtime not checked','No authenticated runtime health or database queries performed'),
        ('ML / GenAI / agents','Evaluation not verified','No verified model accuracy, grounding or agent execution evidence'),
        ('Production release',gate['status'],f"{gate['passed']}/{gate['required']} controls have approved evidence metadata"),
    ]]
    controls=[{'Control':x['control'].replace('_',' ').title(),'Status':'Approved evidence' if x['verified'] else 'No approved evidence','Detail':x['reason'],'Approved':int(x['verified'])} for x in gate['controls']]
    return {'metrics':[metrics],'sources':sources,'pipeline':pipeline,'services':services,'controls':controls,'mta':mta,'aviation_daily':av_series,'domain_coverage':domain_coverage,'checks':[{'Check':k,'Result':'Passed' if v else 'Failed'} for k,v in checks.items()]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path.home()/'DataNexus-AI-Enterprise')
    p.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'DataNexus_Overview_Data.json')
    args=p.parse_args();payload=collect(args.repo.resolve());args.output.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.overview-',suffix='.json',dir=args.output.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(payload,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,args.output)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    print('Overview refreshed:',args.output)
    print('Local feeds:',payload['metrics'][0]['local_feeds'],'| Release:',payload['metrics'][0]['release_status'])

if __name__=='__main__':main()
