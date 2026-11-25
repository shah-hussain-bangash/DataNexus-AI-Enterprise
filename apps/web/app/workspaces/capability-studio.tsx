"use client";
import {useMemo,useState} from "react";
import {Activity,ArrowRight,BarChart3,Bell,CheckCircle2,ClipboardCheck,Database,Download,Filter,GitBranch,LockKeyhole,Search,ShieldCheck,Sparkles,Workflow,X} from "lucide-react";
import {capabilityGroups} from "./capability-data";
type Panel="overview"|"data"|"stream"|"report"|"ai"|"security"|"operations";
const titles:Record<Panel,string>={overview:"Enterprise solution overview",data:"Historical data & quality",stream:"Streaming & live operations",report:"Power BI report studio",ai:"ML, GenAI & Agent operations",security:"Identity, security & governance",operations:"Production operations control center"};
const badgeLabels=["Design only","External source not connected","No production approval"];
const panels:Record<Panel,string[]> = {
 overview:["Workstream scope","Scope and acceptance","Required permissions","Source/dependency health","Evidence and approvals"],
 data:["Source acquisition","Publisher and license review","Bronze manifest","Silver validation and quarantine","Gold snapshot/version","Query and export control"],
 stream:["Collector inventory","Event stream topology","Partition and consumer lag","Replay and checkpoint","Freshness and last-good policy","Incident timeline"],
 report:["Report canvas","Semantic model","DAX validation","Refresh and reconciliation","Dataset lineage","Row-level security"],
 ai:["Feature and model registry","Evaluation and drift","Grounded question assistant","Sources and abstention","Read-only agent investigations","Human approval queue"],
 security:["OIDC / MFA identity","Roles and permissions","Tenant isolation tests","Secrets and encryption","Retention and privacy","Security audit trail"],
 operations:["Service health","Observability signals","Alerts and incidents","Disaster recovery","CI/CD and rollout","16-control release gate"]
};
function panelFor(group:number):Panel{return group===0?"overview":group<=2?"data":group===3?"stream":group===4?"report":group===5?"ai":group===6?"security":"operations"}
function Detail({group,item}:{group:number;item:{id:number;name:string}}){
 const kind=panelFor(group);
 const [tab,setTab]=useState("Design");
 const [note,setNote]=useState("");
 const suggestions=panels[kind];
 return <div className="cap-detail" key={item.id}>
  <div className="cap-detail-header"><span>CAPABILITY {String(item.id).padStart(2,"0")} / 72</span><span className="cap-pill">CONCEPT UI — NOT LIVE</span></div>
  <h3>{item.name}</h3><p>{titles[kind]} — this screen documents the intended UI journey. Real data, access decisions and approvals must come from independently tested services.</p>
  <div className="cap-tabs" role="tablist" aria-label="Capability design panels">{["Design","Workflow","Acceptance"].map(t=><button role="tab" aria-selected={tab===t} className={tab===t?"selected":""} key={t} onClick={()=>setTab(t)}>{t}</button>)}</div>
  {tab==="Design"&&<div className="cap-wire">
   <div className="cap-wire-top"><div><small>PRODUCT DESIGN / {titles[kind]}</small><h4>{item.name}</h4></div><span>DATA UNAVAILABLE</span></div>
   <div className="cap-wire-metrics">{["Observed total","Data freshness","Quality status","Last approval"].map(k=><div key={k}><small>{k}</small><strong>—</strong><span>No verified source</span></div>)}</div>
   <div className="cap-wire-grid"><div><h4>{suggestions[0]}</h4><div className="cap-bars" aria-label="Illustrative chart with no actual values">{[58,85,49,95,64,73,51,89,43,70].map((v,i)=><i key={i} style={{height:v+"%"}}/>)}</div><small>Illustrative layout only; no measurements</small></div><div><h4>Scope and controls</h4>{suggestions.slice(1,5).map(s=><div className="cap-control" key={s}><span>{s}</span><strong>Pending</strong></div>)}</div></div>
   <div className="cap-footer-note"><LockKeyhole size={15}/> Actions affecting data or production are unavailable until source, authorization and audit checks are implemented.</div>
  </div>}
  {tab==="Workflow"&&<div className="cap-flow">{["Identify source and requirements","Validate access and lineage","Execute reviewed service workflow","Verify outcomes and telemetry","Approve evidence and release"].map((s,i)=><div key={s}><span>{i+1}</span><strong>{s}</strong><small>{i===0?"Requirements documented":"Not implemented in this design"}</small></div>)}</div>}
  {tab==="Acceptance"&&<div className="cap-checks">{["UI flow visually reviewed on desktop and mobile","Keyboard and screen-reader behavior tested","Data evidence and source licensing reviewed","Permission and tenant-isolation tested","Failure, stale and unauthorized states verified","Real end-to-end tests and independent signoff"].map(c=><label key={c}><input type="checkbox" disabled readOnly/><span>{c} <small>Not verified</small></span></label>)}</div>}
  <div className="cap-detail-bottom"><small>Acceptance status: pending independent verification</small><button type="button" onClick={()=>{void navigator.clipboard?.writeText("#"+String(item.id).padStart(2,"0")+" "+item.name);setNote("Capability reference copied, where browser permission allows.")}}><ClipboardCheck size={15}/> Copy reference</button></div>{note&&<p className="cap-note" role="status">{note}</p>}
 </div>;
}
export default function CapabilityStudio(){
 const [term,setTerm]=useState("");
 const [group,setGroup]=useState(0);
 const [selected,setSelected]=useState(1);
 const [only,setOnly]=useState(false);
 const [drawer,setDrawer]=useState(false);
 const items=capabilityGroups[group].items;
 const matching=useMemo(()=>items.filter(c=>(c.name+" "+String(c.id)).toLowerCase().includes(term.toLowerCase().trim())),[group,term,items]);
 const all=capabilityGroups.flatMap(g=>g.items);
 const current=all.find(i=>i.id===selected)||items[0];
 const chooseGroup=(n:number)=>{setGroup(n);setSelected(capabilityGroups[n].items[0].id);setTerm("");setDrawer(false)};
 return <section className="cap-studio" aria-label="Enterprise capability UX studio">
  <div className="cap-hero"><div><small>DATA NEXUS / ENTERPRISE DESIGN SYSTEM</small><h2>All 72 enterprise capabilities</h2><p>One integrated design workspace for eight workstreams. Navigate requirements, preview the intended interface and inspect acceptance criteria. Live systems and production actions are not connected.</p></div><span className="cap-pill">UI/UX PROTOTYPE</span></div>
  <div className="cap-stats">{[["72","Tracked requirements"],["8","Enterprise workstreams"],["7","Planned domain adapters"],["0/16","Production approvals"]].map(([n,label])=><div key={label}><strong>{n}</strong><span>{label}</span></div>)}</div>
  <div className="cap-layout">
   <aside className={"cap-menu "+(drawer?"open":"")}>
    <div className="cap-menu-title"><strong>Functional areas</strong><button onClick={()=>setDrawer(false)} aria-label="Close categories"><X size={16}/></button></div>
    {capabilityGroups.map((g,i)=><button key={g.name} onClick={()=>chooseGroup(i)} className={group===i?"selected":""}><span>{g.name}</span><em>{g.items.length}</em></button>)}
   </aside>
   <div className="cap-work"><div className="cap-toolbar"><button className="cap-menu-toggle" onClick={()=>setDrawer(!drawer)}><Filter size={16}/> Workstreams</button><label><Search size={15}/><input value={term} onChange={e=>setTerm(e.target.value)} placeholder="Search current workstream" aria-label="Search capabilities"/></label><span>{matching.length} of {items.length} capabilities</span></div>
   <div className="cap-work-grid"><div className="cap-list" role="list" aria-label="Capability selection">{matching.length?matching.map(c=><button key={c.id} className={selected===c.id?"selected":""} onClick={()=>setSelected(c.id)}><span className="cap-list-number">{String(c.id).padStart(2,"0")}</span><span>{c.name}<small>UI specification · awaiting acceptance</small></span><ArrowRight size={14}/></button>):<p>No matching capabilities in this workstream.</p>}</div>
   <Detail key={current.id} group={group} item={current}/></div></div>
  </div>
  <div className="cap-roadmap"><h3>Full product interface map</h3><p>All domains share the same governance, incident, reporting, security, agent and operations UI pattern.</p><div>{["Data ingestion","Lakehouse & quality","Streaming operations","Power BI reporting","Predictive ML","GenAI assistant","Human-approved agents","Security & governance","SRE and release"].map((s,i)=><span key={s}><span>{i+1}</span>{s}</span>)}</div></div>
 </section>;
}
