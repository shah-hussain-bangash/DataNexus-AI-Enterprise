"use client";
import {useEffect,useMemo,useState} from "react";
import {Bell,BookOpen,Check,ChevronRight,Command,Download,Filter,Layers3,LayoutDashboard,Link2,Moon,Palette,Search,ShieldCheck,Sun,UserCog,X} from "lucide-react";
import {capabilityGroups} from "./capability-data";

const areas=["Workspace layout","Notification center","Design system","Cross-filter studio","Lineage explorer","User administration","Guided onboarding","Context help","Accessibility lab"] as const;
type Area=typeof areas[number];
type Props={domain:string;onGo:(mode:string,domain?:string)=>void};
type Message={id:number;title:string;detail:string;read:boolean};
const messages:Message[]=[
 {id:1,title:"Data availability",detail:"Some domain dashboards contain design fixtures only.",read:false},
 {id:2,title:"Release evidence",detail:"Production release remains blocked pending 16 control approvals.",read:false},
 {id:3,title:"User access",detail:"Enterprise SSO, MFA and multiuser authorization are not connected.",read:false}
];
const starterWidgets=["Source coverage","Data quality","Historical trend","Latest observations","AI insight","Operations health"];
const designTokens=[["Brand navy","#073654"],["Teal accent","#049c9e"],["Gold alert","#d79b35"],["Surface","#f3f8fc"],["Border","#d8e7f1"]];
const steps=["Choose an industry domain","Inspect historical and live panels","Explore the verified source catalog","Review Power BI concept screens","Open AI and agent design previews","Examine access and release readiness"];
const routes:[string,string][]=[["Overview","overview"],["Data Catalog","catalog"],["Historical Analytics","historical"],["Live Operations","live"],["Power BI Studio","powerbi-studio"],["AI & Agents","ai-studio"],["Security Center","security-studio"],["Operations Center","operations-studio"],["72 Capabilities","capabilities"],["Design Extensions","experience"]];
const domainNames=["mobility","weather","seismic","coastal","river","property","energy"];
const services=["Source publisher","Raw Bronze storage","Validation and quarantine","Silver tables","Gold analytics","Reporting semantic model","Dashboard / AI consumption"];

function Surface({title,children}:{title:string;children:React.ReactNode}){return <section className="ex-card"><h3>{title}</h3>{children}</section>}
function Missing(){return <span className="ex-pending">Design-only • Not connected</span>}
function Pill({children}:{children:React.ReactNode}){return <span className="ex-pill">{children}</span>}
export default function ExperienceExtensions({domain,onGo}:Props){
 const [area,setArea]=useState<Area>("Workspace layout");
 const [widgets,setWidgets]=useState(starterWidgets);
 const [edited,setEdited]=useState(false);
 const [saved,setSaved]=useState(false);
 const [alerts,setAlerts]=useState(messages);
 const [theme,setTheme]=useState<"light"|"dark">("light");
 const [filters,setFilters]=useState({domain,period:"12 months",metric:"Volume"});
 const [selectedNode,setSelectedNode]=useState(services[0]);
 const [role,setRole]=useState("Data analyst");
 const [query,setQuery]=useState("");
 const [onboard,setOnboard]=useState(0);
 const [help,setHelp]=useState("Evidence and availability");
 const [commandOpen,setCommandOpen]=useState(false);
 const [cmd,setCmd]=useState("");
 const [focusMode,setFocusMode]=useState(false);
 const commands=useMemo(()=>routes.filter(([title])=>title.toLowerCase().includes(cmd.toLowerCase().trim())).slice(0,9),[cmd]);
 useEffect(()=>{
   try{
    const raw=window.localStorage.getItem("datanexus.layout.preview.v1");
    if(raw){const value=JSON.parse(raw);if(Array.isArray(value)&&value.length<=starterWidgets.length&&value.every((x:unknown)=>typeof x==="string"&&starterWidgets.includes(x as string)))setWidgets(value);}
   }catch{}
 },[]);
 useEffect(()=>{
  const keyboard=(event:KeyboardEvent)=>{
   if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==="k"){event.preventDefault();setCommandOpen(v=>!v)}
   if(event.key==="Escape")setCommandOpen(false);
  };
  window.addEventListener("keydown",keyboard);return()=>window.removeEventListener("keydown",keyboard);
 },[]);
 const toggleWidget=(name:string)=>{setEdited(true);setSaved(false);setWidgets(w=>w.includes(name)?w.filter(x=>x!==name):[...w,name])};
 const saveLayout=()=>{try{window.localStorage.setItem("datanexus.layout.preview.v1",JSON.stringify(widgets));setSaved(true);setEdited(false);}catch{setSaved(false)}};
 const reset=()=>{setWidgets(starterWidgets);setEdited(true);setSaved(false)};
 const selectRoute=(mode:string)=>{setCommandOpen(false);onGo(mode)};
 const marked=alerts.filter(x=>!x.read).length;
 return <section className={"ex-root "+(theme==="dark"?"ex-dark":"")} aria-label="Enterprise UI and UX enhancement studio">
  <div className="ex-hero"><div><small>ENTERPRISE PRODUCT EXPERIENCE • PROTOTYPE</small><h2>Dashboard experience studio</h2><p>Interactive designs for global search, personal layouts, notifications, visual systems, drill-down, lineage, user administration, onboarding and accessibility. Existing application services remain unchanged.</p></div><Pill>9 UI enhancements</Pill></div>
  <div className="ex-actionbar"><button onClick={()=>setCommandOpen(true)}><Command size={15}/> Command palette <kbd>Ctrl K</kbd></button><button onClick={()=>setArea("Notification center")}><Bell size={15}/> Notifications ({marked})</button><button onClick={()=>{setTheme(t=>t==="light"?"dark":"light");setArea("Design system")}}>{theme==="light"?<Moon size={15}/>:<Sun size={15}/>} {theme==="light"?"Dark preview":"Light preview"}</button><button onClick={()=>setFocusMode(v=>!v)}><LayoutDashboard size={15}/> {focusMode?"Show sections":"Focus mode"}</button></div>
  <div className="ex-layout">
   {!focusMode&&<nav className="ex-menu" aria-label="Experience enhancements">{areas.map((x,i)=><button key={x} className={area===x?"selected":""} onClick={()=>setArea(x)}><span>{i+1}</span>{x}<ChevronRight size={13}/></button>)}</nav>}
   <div className="ex-main">
    <div className="ex-section-head"><h3>{area}</h3><Missing/></div>
    {area==="Workspace layout"&&<><Surface title="Personalizable dashboard cards"><p>Choose which cards to display in your local concept workspace. Your selection is stored only in this browser, not on the server.</p><div className="ex-switches">{starterWidgets.map(x=><label key={x}><input type="checkbox" checked={widgets.includes(x)} onChange={()=>toggleWidget(x)}/>{x}</label>)}</div><div className="ex-widget-grid">{widgets.length?widgets.map(x=><div className="ex-widget" key={x}><small>{x}</small><strong>—</strong><span>Evidence not available</span></div>):<p>No cards selected</p>}</div><div className="ex-actions"><button onClick={saveLayout} disabled={!edited}>Save browser layout</button><button onClick={reset}>Reset widgets</button>{saved&&<span role="status">Saved on this device</span>}</div></Surface></>}
    {area==="Notification center"&&<><Surface title="Preview notification inbox"><p>Demo notifications are local and informational. They are not real alerts or incident events.</p><div className="ex-list">{alerts.map(a=><div key={a.id}><div><strong>{a.title}</strong><p>{a.detail}</p></div><button onClick={()=>setAlerts(prev=>prev.map(x=>x.id===a.id?{...x,read:!x.read}:x))}>{a.read?"Mark unread":"Mark read"}</button></div>)}</div><div className="ex-actions"><button onClick={()=>setAlerts(prev=>prev.map(x=>({...x,read:true})))}>Mark all read</button><Pill>{marked} unread samples</Pill></div></Surface></>}
    {area==="Design system"&&<><div className="ex-cols"><Surface title="Color and typography tokens"><div className="ex-tokens">{designTokens.map(([name,color])=><div key={name}><i style={{backgroundColor:color}}/><strong>{name}</strong><code>{color}</code></div>)}</div><p>Tokens demonstrate visual consistency; the theme control affects this prototype panel only.</p></Surface><Surface title="Component states"><div className="ex-actions"><button>Primary action</button><button disabled>Unavailable action</button><Pill>Preview badge</Pill></div><div className="ex-widget-grid"><div className="ex-widget">Empty data<br/><strong>—</strong></div><div className="ex-widget">Approval<br/><strong>Pending</strong></div></div><p>Check contrast, focus rings and reduced-motion preferences before approval.</p></Surface></div></>}
    {area==="Cross-filter studio"&&<><Surface title="Linked filtering preview"><p>Selections update this local concept immediately. They do not filter authenticated production data.</p><div className="ex-filters"><label>Domain<select value={filters.domain} onChange={e=>setFilters(v=>({...v,domain:e.target.value}))}>{domainNames.map(x=><option key={x}>{x}</option>)}</select></label><label>Period<select value={filters.period} onChange={e=>setFilters(v=>({...v,period:e.target.value}))}>{["7 days","30 days","12 months"].map(x=><option key={x}>{x}</option>)}</select></label><label>Metric<select value={filters.metric} onChange={e=>setFilters(v=>({...v,metric:e.target.value}))}>{["Volume","Quality","Freshness"].map(x=><option key={x}>{x}</option>)}</select></label></div><div className="ex-widget-grid">{["Overview card","Trend chart","Station drill-down","Data table"].map(x=><div key={x} className="ex-widget"><small>{x}</small><strong>—</strong><span>{filters.domain} · {filters.period} · {filters.metric}</span></div>)}</div><div className="ex-actions"><button onClick={()=>onGo("station")}>Open station detail view</button><button onClick={()=>onGo("historical")}>Open historical analytics</button></div></Surface></>}
    {area==="Lineage explorer"&&<><Surface title="Proposed data lineage and governance"><p>Select a step to inspect its intended validation and evidence contract. No actual lineage graph is connected.</p><div className="ex-lineage">{services.map((x,i)=><button key={x} className={selectedNode===x?"selected":""} onClick={()=>setSelectedNode(x)}><span>{i+1}</span>{x}</button>)}</div><div className="ex-feature"><strong>{selectedNode}</strong><p>Provenance, version, ownership, privacy classification, freshness and reconciliation evidence will be displayed when approved sources are connected.</p><Missing/></div></Surface></>}
    {area==="User administration"&&<div className="ex-cols"><Surface title="Users and access request design"><label className="ex-field">Proposed role<select value={role} onChange={e=>setRole(e.target.value)}>{["Data analyst","Data engineer","Security reviewer","Operations lead","Administrator"].map(x=><option key={x}>{x}</option>)}</select></label><div className="ex-feature"><strong>{role}</strong><p>Access requests, invitations, provisioning and revocation require a real identity provider and policy engine.</p></div><button disabled>Create user — unavailable</button></Surface><Surface title="Permission matrix design">{["View datasets","Publish reports","Investigate incidents","Approve agent actions","Manage secrets"].map(x=><div className="ex-permission" key={x}><span>{x}</span><Pill>Not evaluated</Pill></div>)}<p>Changing the displayed role does not grant any permissions.</p></Surface></div>}
    {area==="Guided onboarding"&&<><Surface title="Six-step dashboard walkthrough"><div className="ex-steps">{steps.map((s,i)=><button className={onboard===i?"active":""} key={s} onClick={()=>setOnboard(i)}><span>{i+1}</span>{s}</button>)}</div><div className="ex-feature"><small>STEP {onboard+1} / {steps.length}</small><h4>{steps[onboard]}</h4><p>Guided design preview. No data connectors or production workflows are started automatically.</p></div><div className="ex-actions"><button onClick={()=>setOnboard(i=>Math.max(0,i-1))} disabled={onboard===0}>Previous</button><button onClick={()=>setOnboard(i=>Math.min(steps.length-1,i+1))} disabled={onboard===steps.length-1}>Next step</button></div></Surface></>}
    {area==="Context help"&&<div className="ex-cols"><Surface title="Help topics">{["Evidence and availability","Source licensing","Reporting and exports","Agents and human approval","Production readiness"].map(x=><button className={"ex-help "+(x===help?"selected":"")} key={x} onClick={()=>setHelp(x)}>{x}<ChevronRight size={14}/></button>)}</Surface><Surface title={help}><p>{help==="Evidence and availability"?"A dash means the measurement has not been verified by an approved source. Charts in design studios are illustrative.":help==="Source licensing"?"Provider records require licensing, privacy and source approval before operational reuse.":help==="Reporting and exports"?"Published reports, semantic models and data exports must be scoped to verified permissions and source snapshots.":help==="Agents and human approval"?"Proposed agent actions cannot execute without a real policy gate and auditable reviewer approval.":"All sixteen production controls must pass independent evidence review before release."}</p><div className="ex-actions"><button onClick={()=>onGo("capabilities")}>View all 72 requirements</button></div></Surface></div>}
    {area==="Accessibility lab"&&<><Surface title="Accessibility design checklist"><p>These checks are UI review targets, not completed accessibility certifications.</p>{["Keyboard-only navigation and predictable focus","Screen-reader landmarks, roles and names","Text resizing and responsive reflow","Contrast ratios and visible error messaging","Reduced-motion and non-color status cues","Accessible tables, forms, dialogs and empty states"].map(x=><div className="ex-permission" key={x}><span>{x}</span><Pill>Unverified</Pill></div>)}<div className="ex-actions"><button onClick={()=>setCommandOpen(true)}>Test keyboard command interface</button></div></Surface></>}
   </div>
  </div>
  {commandOpen&&<div className="ex-overlay" role="presentation" onMouseDown={e=>{if(e.target===e.currentTarget)setCommandOpen(false)}}><div role="dialog" aria-modal="true" aria-label="Dashboard command palette" className="ex-command"><div className="ex-command-header"><Command size={18}/><input autoFocus aria-label="Search dashboard destinations" value={cmd} onChange={e=>setCmd(e.target.value)} placeholder="Search dashboard destinations..."/><button onClick={()=>setCommandOpen(false)} aria-label="Close command palette"><X size={16}/></button></div><div className="ex-command-results">{commands.length?commands.map(([label,mode])=><button key={mode} onClick={()=>selectRoute(mode)}><Search size={15}/>{label}<ChevronRight size={14}/></button>):<p>No destinations found</p>}</div><p>Keyboard: Ctrl/Cmd + K to open · Esc to close</p></div></div>}
 </section>;
}
