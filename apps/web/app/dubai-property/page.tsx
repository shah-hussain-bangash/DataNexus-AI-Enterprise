"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  Activity, ArrowRight, BarChart3, Bell, Building2, Calculator,
  CheckCircle2, ChevronDown, Database, FileBarChart, Heart,
  Home, KeyRound, Layers3, MapPin, Menu, Search, Settings2,
  ShieldCheck, Sparkles, TrendingUp, X, Zap
} from "lucide-react";
import "./dubai-property.css";

type Tab = "dashboard" | "offers" | "analytics" | "portfolio" | "insights" | "reports" | "ai" | "alerts" | "documents" | "settings";
type Property = { name: string; place: string; price: string; detail: string; tag: string; image: string; yieldText: string; };
const properties: Property[] = [
  {name:"Downtown Dubai Residences",place:"Downtown Dubai",price:"AED 2,350,000",detail:"2 beds · 1,245 sq.ft",tag:"High Yield",image:"dubai-property-downtown",yieldText:"7.5%"},
  {name:"Dubai Marina Waterfront",place:"Dubai Marina",price:"AED 3,900,000",detail:"3 beds · 1,760 sq.ft",tag:"Off-plan",image:"dubai-property-marina",yieldText:"8.1%"},
  {name:"Palm Jumeirah Villa",place:"Palm Jumeirah",price:"AED 18,500,000",detail:"5 beds · 6,200 sq.ft",tag:"Luxury Villa",image:"dubai-property-palm",yieldText:"6.8%"},
];
const menu: {id:Tab;name:string;icon:typeof Home}[] = [
 {id:"dashboard",name:"Dashboard",icon:Home},{id:"offers",name:"Property Offers",icon:Building2},
 {id:"analytics",name:"Investment Analytics",icon:BarChart3},{id:"portfolio",name:"My Portfolio",icon:Layers3},
 {id:"insights",name:"Market Insights",icon:TrendingUp},{id:"reports",name:"Reports & Power BI",icon:FileBarChart},
 {id:"ai",name:"Data & AI Studio",icon:Sparkles},{id:"alerts",name:"Alerts & Watchlist",icon:Bell},
 {id:"documents",name:"Documents",icon:FileBarChart},{id:"settings",name:"Settings",icon:Settings2}
];
const sampleSeries=[36,39,46,49,49,52,55,55,58,61,60,65];
const formatCurrency=(n:number)=>"AED "+new Intl.NumberFormat("en-AE",{maximumFractionDigits:0}).format(n);

function TrendGraph({period}:{period:string}){
 const values=period==="1M"?sampleSeries.slice(-4):period==="3M"?sampleSeries.slice(-6):period==="6M"?sampleSeries.slice(-9):sampleSeries;
 const left=values.map((v,i)=>[22+i*(415/(values.length-1)),176-(v-30)*3.4] as const);
 const poly=left.map(p=>p.join(",")).join(" ");
 const line=left.map((p,i)=>(i?"L":"M")+p[0]+" "+p[1]).join(" ");
 return <svg className="dp-chart" viewBox="0 0 480 215" role="img" aria-label={"Illustrative portfolio trend for "+period}>
   {[35,75,115,155,195].map(y=><line key={y} x1="20" x2="464" y1={y} y2={y} stroke="#dfeaf3"/>)}
   <defs><linearGradient id="dp-fill" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#08b7a4" stopOpacity=".33"/><stop offset="1" stopColor="#08b7a4" stopOpacity="0"/></linearGradient></defs>
   <path d={line+" L"+left[left.length-1][0]+" 195 L22 195 Z"} fill="url(#dp-fill)"/>
   <polyline points={poly} fill="none" stroke="#008e9b" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
   {left.map(([x,y],i)=><circle key={i} cx={x} cy={y} r="3.5" fill="#fff" stroke="#e6a92e" strokeWidth="2.5"/>)}
   {["Jan","Mar","May","Jul","Sep","Dec"].map((m,i)=><text key={m} x={22+i*82} y="209" fill="#68849c" fontSize="10">{m}</text>)}
 </svg>;
}
function Stat({name,value,sub,icon:Icon,tone}:{name:string;value:string;sub:string;icon:typeof Home;tone:string}) {
 return <article className="dp-stat"><span className={"dp-stat-icon "+tone}><Icon size={23}/></span><div className="dp-stat-copy"><span>{name}</span><strong>{value}</strong><small>{sub}</small><svg viewBox="0 0 150 22" aria-hidden="true"><path d="M0 19L18 15L32 17L46 10L60 13L73 8L88 11L103 4L120 7L136 2L150 4" fill="none" stroke={tone==="gold"?"#e6a92e":tone==="blue"?"#149bdc":"#08bca0"} strokeWidth="2"/></svg></div></article>;
}
export default function DubaiPropertyPreview(){
 const [tab,setTab]=useState<Tab>("dashboard");
 const [query,setQuery]=useState("");
 const [period,setPeriod]=useState("1Y");
 const [saved,setSaved]=useState<string[]>([]);
 const [detail,setDetail]=useState<Property|null>(null);
 const [menuOpen,setMenuOpen]=useState(false);
 const [calculator,setCalculator]=useState(false);
 const [investment,setInvestment]=useState("2350000");
 const [yieldRate,setYieldRate]=useState("7.5");
 const matching=useMemo(()=>properties.filter(p=>(p.name+" "+p.place+" "+p.tag).toLowerCase().includes(query.trim().toLowerCase())),[query]);
 const toggleSaved=(name:string)=>setSaved(s=>s.includes(name)?s.filter(x=>x!==name):[...s,name]);
 const explore=()=>{setTab("offers");document.getElementById("dp-opportunities")?.scrollIntoView({behavior:"smooth",block:"center"});};
 return <div className="dp-root">
   <aside className={"dp-sidebar "+(menuOpen?"dp-sidebar-open":"")}>
     <div className="dp-brand"><span className="dp-brand-mark"><BarChart3 size={25}/></span><div><strong>DataNexus</strong><span>AI Enterprise</span></div></div>
     <div className="dp-menu-label">DUBAI PROPERTY WORKSPACE</div>
     <nav aria-label="Dubai property navigation">{menu.map(m=><button key={m.id} className={"dp-nav "+(tab===m.id?"active":"")} onClick={()=>{setTab(m.id);setMenuOpen(false)}}><m.icon size={18}/><span>{m.name}</span></button>)}</nav>
     <div className="dp-sidebar-bottom"><div className="dp-sidebar-image"><strong>Dubai Real Estate Intelligence</strong><p>Visual exploration and future reporting</p></div><Link href="/" className="dp-return"><ArrowRight size={16}/> Return to Aviation Portal</Link></div>
   </aside>
   {menuOpen&&<button className="dp-mobile-scrim" onClick={()=>setMenuOpen(false)} aria-label="Close menu"/>}
   <main className="dp-main">
     <header className="dp-topbar"><button className="dp-mobile-menu" onClick={()=>setMenuOpen(s=>!s)} aria-label="Toggle menu"><Menu size={20}/></button>
       <div className="dp-search"><Search size={17}/><input value={query} onChange={e=>setQuery(e.target.value)} aria-label="Search illustrative properties" placeholder="Search properties, areas, developers..." /></div>
       <div className="dp-top-actions"><span className="dp-preview-dot"/> DESIGN PREVIEW <Bell size={19}/><span className="dp-avatar">LA</span><span className="dp-username">Local Admin</span></div>
     </header>
     <div className="dp-content">
       <div className="dp-preview-banner"><ShieldCheck size={15}/> DESIGN FIXTURES ONLY — property values, yields, graphs and listings below are illustrative, not verified DLD or personal portfolio data.</div>
       <section className="dp-hero"><div className="dp-hero-inner"><span>DUBAI REAL ESTATE INVESTMENT PORTAL</span><h1>Premium Investment<br/>Property Offers in Dubai</h1><p>Explore a vibrant property analytics experience with future data-driven opportunities and portfolio intelligence.</p><button onClick={explore}>Explore Property Offers <ArrowRight size={17}/></button></div><div className="dp-hero-types"><span>▥ &nbsp; Residential <small>Apartments &amp; villas</small></span><span>▥ &nbsp; Commercial <small>Office &amp; retail</small></span><span>▣ &nbsp; Off-plan <small>New developments</small></span><span>↗ &nbsp; High Yield <small>Investment opportunities</small></span></div></section>
       {tab!=="dashboard"&&<div className="dp-mode-note"><strong>{menu.find(m=>m.id===tab)?.name}</strong><p>{tab==="offers"?"Explore the example listings below.":"This workspace is a UI design preview. Real data and features will be integrated after design approval."}</p><button onClick={()=>setTab("dashboard")}>Back to dashboard</button></div>}
       <section className="dp-stat-grid" aria-label="Illustrative portfolio metrics">
         <Stat name="Total Portfolio Value" value="AED 24.8M" sub="▲ 12.4% · illustration" icon={Building2} tone="teal"/>
         <Stat name="Average Rental Yield" value="7.2%" sub="▲ 0.8 pp · illustration" icon={Database} tone="teal"/>
         <Stat name="Capital Appreciation" value="+14.6%" sub="▲ 3.9 pp · illustration" icon={TrendingUp} tone="blue"/>
         <Stat name="Active Opportunities" value="36" sub="+5 new · illustration" icon={KeyRound} tone="gold"/>
       </section>
       <section className="dp-analytics">
        <article className="dp-panel dp-performance"><div className="dp-panel-head"><h2>Portfolio Performance</h2><div className="dp-period">{["1M","3M","6M","1Y","3Y"].map(t=><button key={t} className={period===t?"selected":""} onClick={()=>setPeriod(t)}>{t}</button>)}</div></div><TrendGraph period={period}/><div className="dp-legend"><span>● Portfolio Value (illustrative)</span><span>● Rental Yield (illustrative)</span></div></article>
        <article className="dp-panel dp-allocation"><h2>Investment by Property Type</h2><div className="dp-donut-wrap"><div className="dp-donut"><div>AED<strong>24.8M</strong><small>Illustrative</small></div></div><div className="dp-donut-key">{[["Apartments","45%","#008e98"],["Villas","25%","#d69e25"],["Commercial","15%","#49c3f7"],["Off-plan","10%","#735be6"],["Other","5%","#b8c6d5"]].map(([name,value,color])=><span key={name}><i style={{background:color}}/>{name}<b>{value}</b></span>)}</div></div></article>
        <article className="dp-panel dp-market"><h2><BarChart3 size={19}/> Market Snapshot – Dubai</h2>{[["Avg. Price (Residential)","AED 1,726 / sq.ft"],["Avg. Rental Yield","7.2%"],["Transactions (30 days)","9,842"],["Price Index (YoY)","+14.6%"]].map(([k,v])=><div key={k}><span>{k}</span><strong>{v}</strong></div>)}<small>Illustrative reference values · data source not integrated</small></article>
       </section>
       <section className="dp-bottom-grid"><article className="dp-panel dp-opportunities" id="dp-opportunities"><div className="dp-panel-head"><h2>Featured Investment Property Offers</h2><span>{matching.length} design examples</span></div><div className="dp-property-grid">{matching.length?matching.map(p=><div className="dp-property" key={p.name}><div className={"dp-property-photo "+p.image}><span>{p.tag}</span><button className={saved.includes(p.name)?"liked":""} onClick={()=>toggleSaved(p.name)} aria-label={saved.includes(p.name)?"Remove saved property":"Save property"}><Heart size={18} fill={saved.includes(p.name)?"currentColor":"none"}/></button></div><div className="dp-property-body"><strong>{p.name}</strong><span><MapPin size={13}/>{p.place}</span><b>{p.price}</b><div><small>{p.detail} · example yield {p.yieldText}</small><button onClick={()=>setDetail(p)} aria-label={"View "+p.name}><ArrowRight size={16}/></button></div></div></div>):<p className="dp-empty">No example properties match your search. Clear the search to restore all listings.</p>}</div></article>
       <div className="dp-side-cards"><article className="dp-launch"><h2>New Launches<br/>&amp; Off-plan Deals</h2><p>Explore how upcoming Dubai developments will appear in this workspace.</p><button onClick={explore}>View Example Offers <ArrowRight size={16}/></button></article><article className="dp-panel dp-quick"><h2><Zap size={18}/> Quick Actions</h2><div><button onClick={()=>{document.getElementById("dp-opportunities")?.scrollIntoView({behavior:"smooth"})}}><Search size={23}/>Find Property</button><button onClick={()=>setCalculator(true)}><Calculator size={23}/>ROI Calculator</button><button onClick={()=>setTab("insights")}><TrendingUp size={23}/>Market Insights</button></div></article></div></section>
       <footer className="dp-footer">DataNexus AI Enterprise · Dubai Property UI concept · Not investment advice · <Link href="/">Existing Aviation Dashboard</Link></footer>
     </div>
   </main>
   {detail&&<div className="dp-modal-backdrop" onClick={()=>setDetail(null)}><section className="dp-modal" role="dialog" aria-modal="true" aria-label="Property details" onClick={e=>e.stopPropagation()}><button className="dp-modal-close" onClick={()=>setDetail(null)} aria-label="Close"><X size={20}/></button><span className="dp-modal-label">ILLUSTRATIVE PROPERTY</span><h2>{detail.name}</h2><p><MapPin size={16}/> {detail.place}</p><h3>{detail.price}</h3><p>{detail.detail} · Example yield {detail.yieldText}</p><p>Concept listing only. No live property inventory, price verification or enquiry service is connected.</p><button className="dp-modal-primary" onClick={()=>setDetail(null)}>Close details</button></section></div>}
   {calculator&&<div className="dp-modal-backdrop" onClick={()=>setCalculator(false)}><section className="dp-modal" role="dialog" aria-modal="true" aria-label="Illustrative ROI calculator" onClick={e=>e.stopPropagation()}><button className="dp-modal-close" onClick={()=>setCalculator(false)} aria-label="Close"><X size={20}/></button><span className="dp-modal-label">ILLUSTRATIVE PLANNING TOOL</span><h2>Rental Yield Calculator</h2><label>Property purchase price (AED)<input inputMode="decimal" type="number" min="0" value={investment} onChange={e=>setInvestment(e.target.value)}/></label><label>Annual gross rental yield (%)<input inputMode="decimal" type="number" min="0" max="100" value={yieldRate} onChange={e=>setYieldRate(e.target.value)}/></label><div className="dp-calc-result"><span>Estimated annual gross rent</span><strong>{formatCurrency((Number(investment)||0)*(Number(yieldRate)||0)/100)}</strong></div><p>Illustrative gross figure before vacancy, service charges, financing, fees or taxes.</p></section></div>}
 </div>;
}
