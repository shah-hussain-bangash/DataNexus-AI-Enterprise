"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import {Database,ShieldCheck,RefreshCw,AlertTriangle,LockKeyhole} from "lucide-react";

type Source={id:string;name:string;historical:string;latest:string;historical_state:string;latest_state:string;approved_snapshot:string|null;verified_rows:number|null};
type Catalog={tenant_id:string;environment:string;sources:Source[]};
type Readiness={tenant_id:string;release_status:string;approved_controls:number;required_controls:number;controls:{id:string;status:string}[]};
type Load<T>={state:"loading"|"ready"|"unauthorized"|"error";data?:T;message?:string};
export default function BackendEvidence(){
 const [catalog,setCatalog]=useState<Load<Catalog>>({state:"loading"});
 const [readiness,setReadiness]=useState<Load<Readiness>>({state:"loading"});
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
  setCatalog({state:"loading"});setReadiness({state:"loading"});
  void load<Catalog>("catalog",setCatalog);
  void load<Readiness>("readiness",setReadiness);
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
 </section>;
}
