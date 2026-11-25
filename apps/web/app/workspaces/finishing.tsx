"use client";

import { useState } from "react";
import { AlertTriangle, ArrowRight, Check, ChevronLeft, ChevronRight, Clock3, Database, Download, Eye, Filter, MapPin, RefreshCcw, Search, ShieldCheck, X } from "lucide-react";

export type Domain = "mobility"|"weather"|"seismic"|"coastal"|"river"|"property"|"energy";
export type PreviewState = "ready"|"loading"|"empty"|"error"|"stale"|"unauthorized";
type Props = {
  domain: Domain;
  station: string;
  period: string;
  region: string;
  selectedState: PreviewState;
  setSelectedState: (state: PreviewState) => void;
  onStationChange: (station: string) => void;
};

const mapNodes=[
  {id:"Station A",name:"Station A",region:"North",x:24,y:30},
  {id:"Station B",name:"Station B",region:"Central",x:54,y:50},
  {id:"Station C",name:"Station C",region:"South",x:76,y:77},
  {id:"Station D",name:"Station D",region:"West",x:35,y:70}
];
const chartValues=[20,28,24,36,32,46,38,52,49,60,53,65,58,71,62,76];
const previewRows=Array.from({length:16},(_,i)=>({
 id:"FIXTURE-"+String(i+1).padStart(3,"0"),period:["2025 Q1","2025 Q2","2025 Q3","2025 Q4"][i%4],
 station:mapNodes[i%mapNodes.length].name, historical:"—",latest:"—",status:"Not connected"
}));

function EmptyState({state}:{state:PreviewState}){
 const content:Record<PreviewState,[string,string]>={
  ready:["Source not connected","No provider samples or approved historical snapshots are available. The map is a layout mockup only."],
  loading:["Loading demonstration","The UI skeleton is a simulated loading state. No network request or data fetch has started."],
  empty:["No matching observations","The selected scope has no design fixtures; adjust the view or reset the preview."],
  error:["Simulated service error","The UI demonstrates a service failure without interrupting the real aviation backend."],
  stale:["Simulated stale feed","A provider has not delivered a newer approved observation; source time remains unknown."],
  unauthorized:["Access denied preview","This represents a forbidden scope. No real identity or API permission was changed."]
 };
 return <div className={"finish-state finish-state-"+state} role="status" aria-live="polite"><AlertTriangle size={19}/><div><strong>{content[state][0]}</strong><p>{content[state][1]}</p></div></div>
}

function SignalEditor({period}:{period:string}){
 const [point,setPoint]=useState(5);
 const entry=chartValues[point];
 return <div className="finish-signal">
  <div className="finish-panel-header"><div><strong>Interactive historical pattern</strong><p>Sample positions only • no real dataset connected</p></div><span>Selected index {point+1}/16</span></div>
  <svg viewBox="0 0 660 174" role="img" aria-label="Decorative data trend. Use the controls below to inspect sample positions.">
   {[29,66,103,140].map(y=><line key={y} x1="20" x2="645" y1={y} y2={y} stroke="#deebf3" strokeDasharray="4 7"/>)}
   <polyline points={chartValues.map((value,i)=>[24+i*40,155-value*1.65].join(",")).join(" ")} fill="none" stroke="#1888d1" strokeWidth="3" strokeLinejoin="round"/>
   <circle cx={24+point*40} cy={155-entry*1.65} r="8" fill="#00a89a" stroke="white" strokeWidth="3"/>
  </svg>
  <div className="finish-chart-controller">
   <button onClick={()=>setPoint(x=>Math.max(0,x-1))} disabled={point===0} aria-label="Previous chart position"><ChevronLeft size={18}/></button>
   <span>Preview position {point+1} • period {period} • actual value <strong>Unavailable</strong></span>
   <button onClick={()=>setPoint(x=>Math.min(chartValues.length-1,x+1))} disabled={point===chartValues.length-1} aria-label="Next chart position"><ChevronRight size={18}/></button>
  </div>
 </div>;
}

export function FinishingExperience({domain,station,period,region,selectedState,setSelectedState,onStationChange}:Props){
 const [rowsPage,setRowsPage]=useState(0);
 const [rowQuery,setRowQuery]=useState("");
 const [selectedRow,setSelectedRow]=useState<string|null>(null);
 const filtered=previewRows.filter(r=>(station==="Sample station"||r.station===station)&&(!rowQuery||[r.id,r.station,r.period].join(" ").toLowerCase().includes(rowQuery.toLowerCase())));
 const pageCount=Math.max(1,Math.ceil(filtered.length/5));
 const currentPage=Math.min(rowsPage,pageCount-1);
 const rows=filtered.slice(currentPage*5,currentPage*5+5);
 const exportDisabled=true;
 return <section className="finish-experience" aria-label="Advanced interactive domain design">
  <div className="finish-section-heading"><div><span className="finish-kicker">DESIGN VALIDATION SUITE</span><h2>Interactive Domain Explorer</h2><p>Inspect a schematic location view, chart selection, accessible table and all non-happy-path UI states.</p></div><span className="finish-preview-tag"><ShieldCheck size={15}/> FIXTURES ONLY</span></div>
  <div className="finish-split">
   <article className="finish-panel">
    <div className="finish-panel-header"><div><h3>Geographic Explorer</h3><p>Conceptual node layout; not a real map or station coordinates</p></div><MapPin size={20}/></div>
    <div className="finish-map"><div className="finish-map-grid"/><div className="finish-map-line" />
     {mapNodes.map(p=><button key={p.id} style={{left:p.x+"%",top:p.y+"%"}} className={"finish-map-node "+(station===p.id?"active":"")} onClick={()=>onStationChange(p.id)} title={"Select "+p.name} aria-label={"Select conceptual "+p.name} aria-pressed={station===p.id}><MapPin size={17}/></button>)}
     <div className="finish-map-watermark">ILLUSTRATIVE LOCATION SCHEMATIC</div>
    </div>
    <div className="finish-locations">{mapNodes.map(p=><button key={p.id} className={station===p.id?"selected":""} onClick={()=>onStationChange(p.id)}>{p.name}<small>{p.region} • no actual coordinates</small></button>)}</div>
    <p className="finish-muted">Domain: {domain} • Region filter: {region} • Source geometry and licensed map tiles are pending.</p>
   </article>
   <article className="finish-panel">
    <SignalEditor period={period}/>
    <h3 className="finish-state-heading">Preview every application state</h3>
    <div className="finish-state-select" role="group" aria-label="Simulate dashboard state">{(["ready","loading","empty","error","stale","unauthorized"] as PreviewState[]).map(s=><button key={s} onClick={()=>setSelectedState(s)} aria-pressed={selectedState===s} className={selectedState===s?"selected":""}>{s==="ready"?"Unavailable":s}</button>)}</div>
    {selectedState==="loading"&&<div className="finish-skeleton" aria-hidden="true"><i/><i/><i/></div>}
    <EmptyState state={selectedState}/>
   </article>
  </div>
  <article className="finish-panel finish-table-panel">
   <div className="finish-panel-header"><div><h3>Data Table & Drillthrough</h3><p>Accessible, searchable table demonstrating record selection and pagination. All records are design fixtures.</p></div><div className="finish-table-tools"><label><Search size={15}/><input value={rowQuery} onChange={e=>{setRowQuery(e.target.value);setRowsPage(0)}} placeholder="Find fixture records" aria-label="Filter fixture records"/></label><button disabled={exportDisabled} title="Real data export requires source, authorization and audit" aria-label="Real data export unavailable"><Download size={16}/> Export data</button></div></div>
   <div className="finish-table-scroll"><table><thead><tr><th>Fixture ID</th><th>Reference period</th><th>Station</th><th>Historical</th><th>Latest</th><th>Status</th><th>Detail</th></tr></thead><tbody>{rows.length?rows.map(row=><tr key={row.id}><td>{row.id}</td><td>{row.period}</td><td>{row.station}</td><td>{row.historical}</td><td>{row.latest}</td><td>{row.status}</td><td><button onClick={()=>setSelectedRow(row.id)} aria-label={"Open "+row.id}><Eye size={17}/></button></td></tr>):<tr><td colSpan={7}>No fixture rows match your filter.</td></tr>}</tbody></table></div>
   <div className="finish-pagination"><span>Showing {rows.length} of {filtered.length} fixtures</span><div><button disabled={currentPage===0} onClick={()=>setRowsPage(x=>Math.max(0,x-1))}>Previous</button><span>Page {currentPage+1} of {pageCount}</span><button disabled={currentPage>=pageCount-1} onClick={()=>setRowsPage(x=>Math.min(pageCount-1,x+1))}>Next</button></div></div>
  </article>
  {selectedRow&&<div className="finish-modal-backdrop" onClick={()=>setSelectedRow(null)}><section className="finish-modal" role="dialog" aria-modal="true" aria-label="Fixture record detail" onClick={e=>e.stopPropagation()}><button className="finish-close" onClick={()=>setSelectedRow(null)} aria-label="Close detail"><X size={19}/></button><span className="finish-kicker">SAMPLE RECORD</span><h3>{selectedRow}</h3><p>This record is entirely illustrative. No live provider event, verified measurement, tenancy, or source timestamp is attached.</p><div className="finish-modal-meta"><span>Actual historical value</span><strong>Unavailable</strong><span>Provider timestamp</span><strong>Unavailable</strong><span>Source lineage</span><strong>Not connected</strong></div><button onClick={()=>setSelectedRow(null)} className="finish-primary">Close details <Check size={16}/></button></section></div>}
 </section>;
}
