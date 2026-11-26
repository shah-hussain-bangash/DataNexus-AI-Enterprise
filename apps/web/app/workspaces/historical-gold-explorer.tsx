"use client";
import {useMemo,useState} from "react";

export type GoldDay={
 date:string;
 trip_count:number;
 trip_distance_sum:number;
 total_amount_sum:number;
 within_source_month:boolean;
};
type Metric="trip_count"|"trip_distance_sum"|"total_amount_sum";
const METRICS:{key:Metric;label:string;unit:string}[]=[
 {key:"trip_count",label:"Daily trips",unit:"trips"},
 {key:"trip_distance_sum",label:"Trip distance",unit:"miles"},
 {key:"total_amount_sum",label:"Trip total",unit:"USD"}
];
const format=(value:number,unit:string)=>unit==="USD"?new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:2}).format(value):new Intl.NumberFormat("en-US",{maximumFractionDigits:2}).format(value);

export default function HistoricalGoldExplorer({daily,sourceMonth}:{daily:GoldDay[];sourceMonth:string}){
 const [metric,setMetric]=useState<Metric>("trip_count");
 const [start,setStart]=useState(sourceMonth+"-01");
 const [end,setEnd]=useState(sourceMonth+"-31");
 const [includeOutside,setIncludeOutside]=useState(false);
 const [selectedDate,setSelectedDate]=useState<string|null>(null);
 const valid=useMemo(()=>daily.filter(row=>/^\d{4}-\d{2}-\d{2}$/.test(row.date)&&Number.isFinite(row.trip_count)&&Number.isFinite(row.trip_distance_sum)&&Number.isFinite(row.total_amount_sum)&&row.trip_count>=0).sort((a,b)=>a.date.localeCompare(b.date)),[daily]);
 const filtered=useMemo(()=>valid.filter(row=>(includeOutside||row.within_source_month)&&row.date>=start&&row.date<=end),[valid,includeOutside,start,end]);
 const metricDef=METRICS.find(x=>x.key===metric)!;
 const totals=useMemo(()=>filtered.reduce((acc,row)=>({
   trips:acc.trips+row.trip_count,distance:acc.distance+row.trip_distance_sum,amount:acc.amount+row.total_amount_sum
 }),{trips:0,distance:0,amount:0}),[filtered]);
 const max=Math.max(1,...filtered.map(x=>x[metric]));
 const selected=filtered.find(row=>row.date===selectedDate);
 const xPositions=filtered.map((_,i)=>filtered.length===1?320:40+(i*560)/(filtered.length-1));
 const points=filtered.map((row,i)=>xPositions[i]+","+(200-170*row[metric]/max)).join(" ");
 return <div className="tlc-explorer" aria-label="Interactive real historical Gold analytics">
  <div className="tlc-explorer-heading"><div><h4>Historical daily analytics</h4><p>Source: local validated Gold Parquet • {sourceMonth} • not live or production approved</p></div><span>REAL LOCAL DATA</span></div>
  <div className="tlc-controls">
    <label>Metric<select aria-label="Historical metric" value={metric} onChange={e=>{setMetric(e.target.value as Metric);setSelectedDate(null)}}>{METRICS.map(item=><option key={item.key} value={item.key}>{item.label}</option>)}</select></label>
    <label>From<input aria-label="Historical from date" type="date" value={start} onChange={e=>{setStart(e.target.value);setSelectedDate(null)}}/></label>
    <label>To<input aria-label="Historical to date" type="date" value={end} onChange={e=>{setEnd(e.target.value);setSelectedDate(null)}}/></label>
    <label className="tlc-toggle"><input type="checkbox" checked={includeOutside} onChange={e=>{setIncludeOutside(e.target.checked);setSelectedDate(null)}}/> Include outside-month dates</label>
    <button type="button" onClick={()=>{setStart(sourceMonth+"-01");setEnd(sourceMonth+"-31");setIncludeOutside(false);setMetric("trip_count");setSelectedDate(null)}}>Reset filters</button>
  </div>
  {start>end?<p role="alert">Start date is after end date. Adjust the range.</p>:<div>
   <div className="tlc-kpis" aria-live="polite">
    <div><small>Trips in selection</small><strong>{format(totals.trips,"trips")}</strong></div>
    <div><small>Trip distance in selection</small><strong>{format(totals.distance,"miles")} mi</strong></div>
    <div><small>Trip total in selection</small><strong>{format(totals.amount,"USD")}</strong></div>
    <div><small>Selected reporting days</small><strong>{filtered.length}</strong></div>
   </div>
   {filtered.length===0?<p role="status">No real Gold records in the selected date range.</p>:<>
    <div className="tlc-chart" role="img" aria-label={"Verified historical "+metricDef.label.toLowerCase()+" by pickup date. Exact values are listed in the table below."}>
     <svg viewBox="0 0 640 245" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
      {[0,0.5,1].map(f=><g key={f}><line x1="40" x2="610" y1={200-f*170} y2={200-f*170} stroke="#dce8ef" strokeDasharray="4 5"/><text x="8" y={204-f*170} fill="#547185" fontSize="10">{Math.round(max*f).toLocaleString("en-US",{notation:"compact"})}</text></g>)}
      <polyline points={points} fill="none" stroke="#137c98" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round"/>
      {filtered.map((row,i)=><circle key={row.date} cx={xPositions[i]} cy={200-170*row[metric]/max} r={selectedDate===row.date?6:3.5} fill={row.within_source_month?"#087f9a":"#c47e18"}/>)}
      <text x="40" y="225" fill="#547185" fontSize="11">{filtered[0].date}</text><text x="610" y="225" fill="#547185" fontSize="11" textAnchor="end">{filtered[filtered.length-1].date}</text>
     </svg>
    </div>
    <p className="tlc-chart-caption">{metricDef.label} ({metricDef.unit}); aggregated values, not individual taxi records. Orange marks indicate outside-month dates.</p>
    <div className="tlc-detail">Select a day in the table to inspect exact values. {selected?<strong>{selected.date}: {format(selected[metric],metricDef.unit)} {metricDef.unit}</strong>:null}</div>
    <div className="tlc-table-scroll"><table className="tlc-table"><caption>Actual historical daily Gold metrics for the selected dates</caption><thead><tr><th scope="col">Pickup date</th><th scope="col">Trips</th><th scope="col">Distance (miles)</th><th scope="col">Trip total (USD)</th><th scope="col">Period</th></tr></thead><tbody>{filtered.map(row=><tr key={row.date} className={selectedDate===row.date?"tlc-selected":""}><th scope="row"><button onClick={()=>setSelectedDate(row.date)} type="button" aria-pressed={selectedDate===row.date}>{row.date}</button></th><td>{format(row.trip_count,"trips")}</td><td>{format(row.trip_distance_sum,"miles")}</td><td>{format(row.total_amount_sum,"USD")}</td><td>{row.within_source_month?"January":"Outside January"}</td></tr>)}</tbody></table></div>
   </>}
  </div>}
  <p className="tlc-disclaimer">Date and metric filters operate on the authenticated historical reporting snapshot in this browser. They do not query live services, change the dataset, or authorize commercial use. The trip total is not net revenue.</p>
 </div>;
}
