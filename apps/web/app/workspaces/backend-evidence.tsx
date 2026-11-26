"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import HistoricalGoldExplorer from "./historical-gold-explorer";
import {Database,ShieldCheck,RefreshCw,AlertTriangle,LockKeyhole} from "lucide-react";

type Source={id:string;name:string;historical:string;latest:string;historical_state:string;latest_state:string;approved_snapshot:string|null;verified_rows:number|null};
type Catalog={tenant_id:string;environment:string;sources:Source[]};
type Bronze={tenant_id:string;source:string;state:string;downloads:{period:string;file_name:string;bytes:number;sha256:string;stage:string;schema_validated:boolean;row_count:null}[];caveat:string};
type GoldReport={tenant_id:string;source_month:string;source_sha256:string;validated_source_rows:number;silver_rows:number;quarantined_rows:number;in_month_trip_count:number;outside_month_trip_count:number;in_month_days:number;outside_month_days:number;daily:{date:string;trip_count:number;trip_distance_sum:number;total_amount_sum:number;within_source_month:boolean}[];caveat:string};
type Readiness={tenant_id:string;release_status:string;approved_controls:number;required_controls:number;controls:{id:string;status:string}[]};
type Load<T>={state:"loading"|"ready"|"unauthorized"|"error";data?:T;message?:string};
export default function BackendEvidence(){
 const [catalog,setCatalog]=useState<Load<Catalog>>({state:"loading"});
 const [readiness,setReadiness]=useState<Load<Readiness>>({state:"loading"});
 const [bronze,setBronze]=useState<Load<Bronze>>({state:"loading"});
 const [gold,setGold]=useState<Load<GoldReport>>({state:"loading"});
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
  setCatalog({state:"loading"});setReadiness({state:"loading"});setBronze({state:"loading"});setGold({state:"loading"});
  void load<Catalog>("catalog",setCatalog);
  void load<Readiness>("readiness",setReadiness);
  void load<Bronze>("nyc-tlc/bronze",setBronze);
  void load<GoldReport>("nyc-tlc/reporting",setGold);
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
