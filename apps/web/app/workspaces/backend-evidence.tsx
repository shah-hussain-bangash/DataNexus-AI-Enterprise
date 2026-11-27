"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import HistoricalGoldExplorer from "./historical-gold-explorer";
import {Database,ShieldCheck,RefreshCw,AlertTriangle,LockKeyhole} from "lucide-react";

type Source={id:string;name:string;historical:string;latest:string;historical_state:string;latest_state:string;approved_snapshot:string|null;verified_rows:number|null};
type Catalog={tenant_id:string;environment:string;sources:Source[]};
type Bronze={tenant_id:string;source:string;state:string;downloads:{period:string;file_name:string;bytes:number;sha256:string;stage:string;schema_validated:boolean;row_count:null}[];caveat:string};
type GoldReport={tenant_id:string;source_month:string;source_sha256:string;validated_source_rows:number;silver_rows:number;quarantined_rows:number;in_month_trip_count:number;outside_month_trip_count:number;in_month_days:number;outside_month_days:number;daily:{date:string;trip_count:number;trip_distance_sum:number;total_amount_sum:number;within_source_month:boolean}[];caveat:string};
type QualityEvidence={tenant_id:string;state:string;source_month:string;accepted_percent:number;quarantined_percent:number;source_records:number;silver_records:number;quarantined_records:number;out_of_month_trips:number;report_age_hours:number;report_age_band:string;validation_warning_counts:Record<string,number>;transformation_rejection_reasons:Record<string,number>;reconciliation_ok:boolean;production_approved:boolean;validation_completed_at_utc:string;report_generated_at_utc:string;live_source_freshness:null;caveat:string};
type MtaObservation={event_id:string;feed_id:string;provider_timestamp_utc:string;observation_age_seconds:number;entities:number;trip_updates:number;vehicle_positions:number;alerts:number};
type MtaResponse={tenant_id:string;state:string;count:number;observations:MtaObservation[];live_stream_connected:boolean;production_approved:boolean;caveat?:string};
type MtaMonitor={tenant_id:string;state:string;checked_at_utc:string;consumer_lag_messages:number|null;offset_state:string;stored_aggregate_records:number;latest_stored_source_age_seconds:number;snapshot_age_seconds:number;snapshot_stale:boolean;caveat:string};
type Readiness={tenant_id:string;release_status:string;approved_controls:number;required_controls:number;controls:{id:string;status:string}[]};
type Load<T>={state:"loading"|"ready"|"unauthorized"|"error";data?:T;message?:string};
export default function BackendEvidence(){
 const [catalog,setCatalog]=useState<Load<Catalog>>({state:"loading"});
 const [readiness,setReadiness]=useState<Load<Readiness>>({state:"loading"});
 const [bronze,setBronze]=useState<Load<Bronze>>({state:"loading"});
 const [gold,setGold]=useState<Load<GoldReport>>({state:"loading"});
 const [quality,setQuality]=useState<Load<QualityEvidence>>({state:"loading"});
 const [mta,setMta]=useState<Load<MtaResponse>>({state:"loading"});
 const [monitor,setMonitor]=useState<Load<MtaMonitor>>({state:"loading"});
 const [refresh,setRefresh]=useState(0);
 useEffect(()=>{
  let live=true;
  async function load<T>(path:string, setter:(value:Load<T>)=>void){
   try{
    const result=await fetch("/api/portal/"+path,{credentials:"same-origin",cache:"no-store"});
    if(!live)return;
    if(result.status===401||result.status===403){setter({state:"unauthorized",message:"Authentication or permission required"});return}
    if(!result.ok){setter({state:"error",message:"Backend unavailable (HTTP "+result.status+")"});return}
    setter({state:"ready",data:await result.json() as T});
   }catch{
    if(live)setter({state:"error",message:"Cannot reach backend API"});
   }
  }
  setCatalog({state:"loading"});setReadiness({state:"loading"});setBronze({state:"loading"});setGold({state:"loading"});setQuality({state:"loading"});setMta({state:"loading"});setMonitor({state:"loading"});
  void load<Catalog>("catalog",setCatalog);
  void load<Readiness>("readiness",setReadiness);
  void load<Bronze>("nyc-tlc/bronze",setBronze);
  void load<GoldReport>("nyc-tlc/reporting",setGold);
  void load<QualityEvidence>("nyc-tlc/quality",setQuality);
  void load<MtaResponse>("mta/observations",setMta);
  void load<MtaMonitor>("mta/monitor",setMonitor);
  return()=>{live=false};
 },[refresh]);
 return <section className="evidence-root" aria-label="Authenticated enterprise backend readiness">
  <div className="evidence-heading"><div><span>REAL BACKEND / VERIFIED TENANT</span><h2>Source contracts & release readiness</h2><p>These panels request data from the local authenticated FastAPI service. A passing build or UI preview is not production approval.</p></div><button onClick={()=>setRefresh(x=>x+1)}><RefreshCw size={16}/> Refresh evidence</button></div>
  <div className="evidence-grid">
   <article className="evidence-card"><div className="evidence-title"><Database size={21}/><h3>Approved source catalog</h3></div>
    {catalog.state==="loading"?<p role="status">Loading authenticated source contracts...</p>:catalog.state==="unauthorized"?<div className="evidence-alert"><LockKeyhole size={18}/> Authentication required. <Link href="/sign-in">Sign in</Link> to access this protected endpoint.</div>:catalog.state==="error"?<div className="evidence-alert"><AlertTriangle size={18}/>{catalog.message}</div>:<><p>Verified local tenant: <strong>{catalog.data?.tenant_id}</strong></p><div className="evidence-rows">{catalog.data?.sources.map(s=><div key={s.id}><strong>{s.name}</strong><span>{s.historical_state==="not_connected"?"Historical: unavailable":"Historical: "+s.historical_state} • {s.latest_state==="not_connected"?"Latest: unavailable":"Latest: "+s.latest_state}</span></div>)}</div><small>Dataset metadata contracts only. No real provider observations were imported.</small></>}
   </article>
   <article className="evidence-card"><div className="evidence-title"><ShieldCheck size={21}/><h3>Production release controls</h3></div>
    {readiness.state==="loading"?<p role="status">Loading release-readiness evidence...</p>:readiness.state==="unauthorized"?<div className="evidence-alert"><LockKeyhole size={18}/> Sign in to view tenant release-readiness status.</div>:readiness.state==="error"?<div className="evidence-alert"><AlertTriangle size={18}/>{readiness.message}</div>:<><div className="evidence-count">{readiness.data?.approved_controls} / {readiness.data?.required_controls}<span>Approved controls — {readiness.data?.release_status}</span></div><div className="evidence-rows">{readiness.data?.controls.map(c=><div key={c.id}><strong>{c.id.replaceAll("_"," ")}</strong><span>{c.status.replaceAll("_"," ")}</span></div>)}</div></>}
   </article>
  </div>
  <article className="evidence-card" style={{marginTop:12}} aria-label="MTA local monitoring snapshot">
    <div className="evidence-title"><ShieldCheck size={21}/><h3>MTA Kafka lag and freshness — local snapshot</h3></div>
    {monitor.state==="loading"?<p role="status">Checking saved monitoring evidence...</p>:monitor.state==="unauthorized"?<p>Sign in to view monitoring evidence.</p>:monitor.state==="error"?<p role="alert">Monitoring snapshot unavailable: {monitor.message}. Run the read-only monitor with --save locally.</p>:monitor.data&&<>
      <p><strong>{monitor.data.snapshot_stale?"Stale snapshot":"Recent snapshot"}</strong> • checked {monitor.data.checked_at_utc} • age {Math.round(monitor.data.snapshot_age_seconds/60).toLocaleString()} min</p>
      <div className="tlc-quality-kpis">
        <div><small>Kafka consumer lag</small><strong>{monitor.data.consumer_lag_messages===null?"Unknown":monitor.data.consumer_lag_messages.toLocaleString()}</strong></div>
        <div><small>Stored aggregates</small><strong>{monitor.data.stored_aggregate_records.toLocaleString()}</strong></div>
        <div><small>Last stored provider age</small><strong>{Math.round(monitor.data.latest_stored_source_age_seconds/60).toLocaleString()} min</strong></div>
        <div><small>Offset condition</small><strong style={{fontSize:12}}>{monitor.data.offset_state.replaceAll("_"," ")}</strong></div>
      </div>
      <small>Saved evidence only; it does not poll Kafka or the MTA from the dashboard. {monitor.data.caveat}</small>
    </>}
  </article>
  <article className="evidence-card" style={{marginTop:12}} aria-label="MTA Kafka consumed observations">
    <div className="evidence-title"><Database size={21}/><h3>MTA Kafka consumed observations</h3></div>
    {mta.state==="loading"?<p role="status">Checking the local MTA aggregate store...</p>:mta.state==="unauthorized"?<p>Sign in to access MTA observations.</p>:mta.state==="error"?<p role="alert">MTA observations unavailable: {mta.message}</p>:mta.data&&<>
      <p><strong>{mta.data.count} stored observation(s)</strong> • development-only snapshot • not a continuous live feed</p>
      {mta.data.observations.length===0?<p>No consumed aggregate observations yet.</p>:<div className="evidence-rows">
        {mta.data.observations.map(o=><div key={o.event_id}><strong>{o.feed_id.toUpperCase()} • {o.provider_timestamp_utc}</strong><span>{o.entities.toLocaleString()} entities • {o.trip_updates.toLocaleString()} trip updates • {o.vehicle_positions.toLocaleString()} vehicles • {o.alerts.toLocaleString()} alerts • observed {Math.round(o.observation_age_seconds/60).toLocaleString()} min ago</span></div>)}
      </div>}
      <small>{mta.data.caveat||"One-shot local aggregate only. No live streaming status is implied."}</small>
    </>}
  </article>
  <article className="evidence-card" style={{marginTop:12}} aria-label="NYC TLC historical quality monitoring">
   <div className="evidence-title"><ShieldCheck size={21}/><h3>NYC TLC historical quality monitoring</h3></div>
   {quality.state==="loading"?<p role="status">Checking historical quality evidence...</p>:quality.state==="unauthorized"?<p>Sign in for quality monitoring.</p>:quality.state==="error"?<p role="alert">Quality evidence unavailable: {quality.message}. No unverified metrics will be shown.</p>:quality.data&&<>
    <p><strong>{quality.data.reconciliation_ok?"Source / Silver / quarantine counts reconcile":"Reconciliation not verified"}</strong> • {quality.data.source_month} • development-only</p>
    <div className="tlc-quality-kpis">
      <div><small>Accepted</small><strong>{quality.data.accepted_percent.toFixed(2)}%</strong></div>
      <div><small>Quarantined</small><strong>{quality.data.quarantined_percent.toFixed(2)}%</strong></div>
      <div><small>Outside-month trips</small><strong>{quality.data.out_of_month_trips.toLocaleString()}</strong></div>
      <div><small>Report age</small><strong>{quality.data.report_age_hours.toLocaleString()} hours</strong></div>
    </div>
    <p>Report age is elapsed time since the local historical export. <strong>It does not indicate live-feed freshness.</strong> {quality.data.report_age_band==="over_168_hours"?"Local export is over seven days old.":""}</p>
    <div className="evidence-grid">
     <div><h4>Validation warnings (overlapping)</h4><div className="evidence-rows">{Object.entries(quality.data.validation_warning_counts).map(([name,count])=><div key={name}><strong>{name.replaceAll("_"," ")}</strong><span>{count.toLocaleString()}</span></div>)}</div></div>
     <div><h4>Transformation rejection reasons (overlapping)</h4><div className="evidence-rows">{Object.entries(quality.data.transformation_rejection_reasons).map(([name,count])=><div key={name}><strong>{name.replaceAll("_"," ")}</strong><span>{count.toLocaleString()}</span></div>)}</div></div>
    </div>
    <small>{quality.data.caveat}</small>
   </>}
  </article>
  <article className="evidence-card" style={{marginTop:12}} aria-label="Local NYC TLC Gold reporting"><div className="evidence-title"><Database size={21}/><h3>Local NYC TLC Gold reporting</h3></div>
   {gold.state==="loading"?<p role="status">Loading verified local daily aggregates...</p>:gold.state==="unauthorized"?<p>Sign in to access historical reporting.</p>:gold.state==="error"?<p>Historical reporting unavailable: {gold.message}. Run Phase 2.3 local export before viewing analytics.</p>:<><p><strong>Historical snapshot {gold.data?.source_month}</strong> • development-only, not a live source</p><div className="nx-health">
     {([["Validated source trips",gold.data?.validated_source_rows],["Accepted Silver trips",gold.data?.silver_rows],["Quarantined trips",gold.data?.quarantined_rows],["In-month trips",gold.data?.in_month_trip_count],["Outside-month trips",gold.data?.outside_month_trip_count]] as [string,number|undefined][]).map(([name,value])=><div key={name}><small>{name}</small><strong>{value===undefined?"—":value.toLocaleString()}</strong></div>)}
    </div><p>Verified data lineage: {gold.data?.source_sha256.slice(0,16)}… • {gold.data?.in_month_days} January dates / {gold.data?.outside_month_days} out-of-month dates</p>
    {gold.data&&<HistoricalGoldExplorer daily={gold.data.daily} sourceMonth={gold.data.source_month}/>}
    <div className="evidence-rows" role="table" aria-label="Real historical daily Gold aggregates"><div role="row"><strong>Pickup date</strong><span>Trips • trip total (USD) • distance</span></div>{gold.data?.daily.map(d=><div role="row" key={d.date}><strong>{d.date}{d.within_source_month?"":" (outside January)"}</strong><span>{d.trip_count.toLocaleString()} trips • ${d.total_amount_sum.toLocaleString()} • {d.trip_distance_sum.toLocaleString()} mi</span></div>)}</div><small>{gold.data?.caveat}</small></>}
  </article>
  <article className="evidence-card" style={{marginTop:12}}><div className="evidence-title"><Database size={21}/><h3>NYC TLC — local historical acquisition</h3></div>
   {bronze.state==="loading"?<p>Checking local raw-file manifests...</p>:bronze.state==="unauthorized"?<p>Sign in to view locally acquired data.</p>:bronze.state==="error"?<p>Acquisition inventory unavailable: {bronze.message}</p>:<><p>Raw Parquet files found: <strong>{bronze.data?.downloads.length ?? 0}</strong> (Bronze only; no validated trip counts)</p><div className="evidence-rows">{bronze.data?.downloads.map(d=><div key={d.file_name}><strong>{d.period} • {d.file_name}</strong><span>{(d.bytes/1048576).toFixed(1)} MiB • {d.stage} • SHA-256: {d.sha256.slice(0,12)}…</span></div>)}</div>{bronze.data?.downloads.length===0&&<p>No source files acquired yet. Run the documented local NYC TLC collector first.</p>}<small>{bronze.data?.caveat}</small></>}
  </article>
 </section>;
}
