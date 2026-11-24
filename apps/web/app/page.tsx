"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity, ArrowDownRight, ArrowRight, ArrowUpRight, Bell, Boxes, CheckCheck,
  ChevronDown, ChevronLeft, ChevronRight, CircleHelp, ClipboardCheck, Cloud,
  Command, Database, Download, ExternalLink, Filter, Gauge, Layers3, LayoutDashboard,
  LockKeyhole, Menu, Plane, Radar, RefreshCw, Search, Server, Settings2, ShieldCheck,
  Sparkles, Workflow, X, LogOut,
} from "lucide-react";

type EventRow = {
  event_id: string; source_time: string; tenant_id: string; icao24: string;
  latitude: number | null; longitude: number | null; callsign: string | null;
  velocity_mps: number | null; altitude_m: number | null; on_ground: boolean | null; source: string;
};
type Summary = {
  configured: boolean; sample_size: number; total_events: number; aircraft_in_sample: number;
  positions_in_sample: number; tenants_in_sample: number; duplicate_ids_in_sample: number;
  last_source_event_at: string | null; message: string | null;
};
type Overview = {
  events: Summary; environment: string;
  workspace?: { username: string; role: string; tenant_id: string };
  systems: { name: string; key: string; status: string }[];
  limitations: string[];
};
type EventResponse = { configured: boolean; events: EventRow[]; total: number; message: string | null };
type View = "overview" | "aviation" | "pipelines" | "quality" | "intelligence" | "settings";

const nav: { heading: string; items: { id: View; label: string; icon: typeof Activity; hint?: string }[] }[] = [
  { heading: "WORKSPACE", items: [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "aviation", label: "Aviation Intelligence", icon: Plane },
    { id: "pipelines", label: "Data Pipelines", icon: Workflow },
    { id: "quality", label: "Data Quality", icon: ShieldCheck },
  ] },
  { heading: "INTELLIGENCE", items: [
    { id: "intelligence", label: "AI & Model Ops", icon: Sparkles, hint: "Soon" },
    { id: "settings", label: "Workspace Settings", icon: Settings2 },
  ] },
];

const pages: Record<View, { name: string; eyebrow: string; subtitle: string }> = {
  overview: { name: "Command Overview", eyebrow: "OPERATIONS / OVERVIEW", subtitle: "Your aviation data platform, at a glance." },
  aviation: { name: "Aviation Intelligence", eyebrow: "OPERATIONS / AVIATION", subtitle: "Inspect aircraft state events and source observations." },
  pipelines: { name: "Pipeline Observatory", eyebrow: "OPERATIONS / PIPELINES", subtitle: "Data flow architecture and integration visibility." },
  quality: { name: "Data Quality Center", eyebrow: "GOVERNANCE / QUALITY", subtitle: "Inspect available consistency checks and their coverage." },
  intelligence: { name: "AI & Model Operations", eyebrow: "INTELLIGENCE / LAB", subtitle: "The next generation of aviation decision intelligence." },
  settings: { name: "Workspace Settings", eyebrow: "ADMINISTRATION / ENVIRONMENT", subtitle: "Service information, limitations and configuration." },
};

function fmt(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("en-US").format(value);
}
function dateLabel(value?: string | null) {
  if (!value) return "No observations yet";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" }) + " UTC";
}
function downloadJson(data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "datanexus-events.json"; a.click();
  URL.revokeObjectURL(url);
}

function MiniBars() {
  return <div className="mini-bars" aria-hidden="true">{[27,48,36,59,44,72,51,64,81,60,86,74,95,78,88,100,83,96].map((height, i) =>
    <span key={i} style={{ height: height + "%" }} />)}</div>;
}
function Sparkline({ variant = "blue" }: { variant?: "blue" | "green" | "purple" }) {
  return <svg className={"sparkline " + variant} viewBox="0 0 118 38" role="img" aria-label="Decorative trend illustration, not historical metrics">
    <path d="M1 32L16 25L29 28L43 17L55 22L68 11L81 17L94 7L106 12L117 3" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round" />
  </svg>;
}
function FlightMap({ events }: { events: EventRow[] }) {
  const markers = events.filter(e => e.latitude != null && e.longitude != null && e.latitude >= -90 && e.latitude <= 90 && e.longitude >= -180 && e.longitude <= 180).slice(0, 24);
  return <div className="map-panel">
    <div className="map-grid" />
    <svg className="map-vector" viewBox="0 0 820 340" preserveAspectRatio="xMidYMid slice" aria-label="Stylized global map illustration">
      <defs><pattern id="mapdots" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r=".8" fill="#4d819e" opacity=".3"/></pattern></defs>
      <path fill="url(#mapdots)" stroke="#386680" strokeWidth="1" strokeOpacity=".3" d="M36 81L84 62 143 72 162 92 208 87 236 115 217 140 192 139 171 167 150 155 143 200 116 187 109 151 78 147 61 116ZM204 209L252 208 280 234 271 268 254 297 230 316 219 285 209 257ZM351 85L376 73 413 78 427 101 451 109 439 135 415 130 406 153 381 154 369 128ZM396 169L447 158 473 185 469 235 441 279 409 264 396 210ZM462 74L543 61 603 74 647 93 689 84 742 119 718 151 667 151 638 187 603 178 583 144 540 150 513 122 480 135ZM639 249L697 237 741 262 730 296 684 293 655 279Z"/>
      <path d="M58 236L756 236M58 117L756 117M207 31L207 308M410 31L410 308M614 31L614 308" stroke="#30607a" strokeWidth=".8" strokeDasharray="4 6" opacity=".4"/>
      {markers.map((e, index) => {
        const x = ((e.longitude! + 180) / 360) * 820, y = ((90 - e.latitude!) / 180) * 340;
        return <g key={e.event_id + index} transform={"translate(" + x + " " + y + ")"}>
          <circle r="11" fill="#10c2df" opacity=".14"/><circle r="4" fill="#4cdbef" stroke="#fff" strokeWidth="1"/>
          <title>{e.callsign || e.icao24} + " / " + e.latitude + ", " + e.longitude</title>
        </g>;
      })}
    </svg>
    <div className="map-top"><span className="map-live"><span className="status-dot"/> RECORDED POSITIONS</span><span>WGS84 / GLOBAL VIEW</span></div>
    <div className="map-bottom"><span><Radar size={15}/> {markers.length} plotted observations</span><span>Map schematic • coordinates positioned geographically</span></div>
  </div>;
}
function MetricCard({ label, value, change, icon: Icon, color, hint }: { label: string; value: string; change: string; icon: typeof Activity; color: string; hint?: string }) {
  return <div className="metric-card">
    <div className="metric-head"><span>{label}</span><div className={"metric-icon " + color}><Icon size={18}/></div></div>
    <div className="metric-body"><strong>{value}</strong><span className={"metric-accent metric-accent-"+color} aria-hidden="true"><span/><span/><span/><span/><span/></span></div>
    <div className="metric-footer"><span className="metric-pill">{change}</span><span>{hint || "Local data sample"}</span></div>
  </div>;
}
export default function Home() {
  const [view, setView] = useState<View>("overview");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [events, setEvents] = useState<EventResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sortNew, setSortNew] = useState(true);
  const [selected, setSelected] = useState<EventRow | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const refresh = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [o, e] = await Promise.all([
        fetch("/api/portal/overview", { cache: "no-store" }),
        fetch("/api/portal/events", { cache: "no-store" }),
      ]);
      if (o.status === 401 || e.status === 401) { window.location.assign("/sign-in"); return; }
      if (!o.ok || !e.ok) throw new Error("The local API is unreachable. Check the backend service.");
      setOverview(await o.json()); setEvents(await e.json());
      setLastRefresh(new Date());
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to load data."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  const list = useMemo(() => {
    const q = query.toLowerCase().trim();
    const filtered = (events?.events || []).filter(x => !q || [x.icao24, x.callsign, x.tenant_id, x.event_id].some(v => v?.toLowerCase().includes(q)));
    return [...filtered].sort((a,b) => sortNew ? b.source_time.localeCompare(a.source_time) : a.source_time.localeCompare(b.source_time));
  }, [events, query, sortNew]);
  const summary = overview?.events;
  const setPage = (id: View) => { setView(id); setMobileOpen(false); setSelected(null); };
  const signOut = async () => { await fetch("/api/auth/logout", { method: "POST" }); window.location.assign("/sign-in"); };
  return <div className="shell">
    {mobileOpen && <button className="mobile-backdrop" onClick={() => setMobileOpen(false)} aria-label="Close menu"/>}
    <aside className={"sidebar " + (mobileOpen ? "sidebar-open" : "")}>
      <div className="brand"><div className="brand-mark"><Plane size={23} strokeWidth={2.2}/></div><div><div className="brand-name">Data<span>Nexus</span><sup>AI</sup></div><div className="brand-sub">ENTERPRISE INTELLIGENCE</div></div></div>
      <div className="workspace-switch"><div className="workspace-avatar"><Command size={18}/></div><div className="workspace-info"><strong>Aviation Workspace</strong><span>Tenant {overview?.workspace?.tenant_id || "local"} · Development</span></div><ChevronDown size={15}/></div>
      <div className="nav-area">{nav.map(group => <div className="nav-group" key={group.heading}><div className="nav-heading">{group.heading}</div>{group.items.map(item =>
        <button key={item.id} className={"nav-item " + (view === item.id ? "active" : "")} onClick={() => setPage(item.id)}>
          <item.icon size={18} strokeWidth={1.85}/><span>{item.label}</span>{item.hint && <small>{item.hint}</small>}{view === item.id && <span className="nav-indicator"/>}
        </button>)}</div>)}</div>
      <div className="sidebar-bottom">
        <div className="platform-note"><div className="platform-note-icon"><Gauge size={19}/></div><strong>Platform foundation</strong><p>Streaming, lakehouse and object storage are implemented. Observability integration is next.</p><button onClick={() => setPage("pipelines")}>Explore architecture <ArrowRight size={14}/></button></div>
        <div className="profile"><div className="profile-avatar">DN</div><div><strong>{overview?.workspace?.username || "Local operator"}</strong><span>{overview?.workspace?.role || "admin"} · Local session</span></div><button className="profile-signout" title="Sign out" aria-label="Sign out" onClick={() => void signOut()}><LogOut size={17}/></button></div>
      </div>
    </aside>
    <main className="main">
      <header className="topbar">
        <div className="breadcrumb"><button className="mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={21}/></button><span>Workspace</span><ChevronRight size={15}/><strong>{pages[view].name}</strong></div>
        <div className="top-actions"><span className="environment-badge"><span className="status-dot"/> LOCAL DEVELOPMENT</span><button className="top-icon" onClick={() => setPage("quality")} aria-label="Open data quality"><Bell size={19}/></button><button className="top-icon" onClick={() => setPage("settings")} aria-label="Open settings"><CircleHelp size={19}/></button><button className="top-avatar top-avatar-button" title="Sign out" aria-label="Sign out" onClick={() => void signOut()}>DN</button></div>
      </header>
      <div className="content">
        <div className="page-heading"><div><div className="eyebrow">{pages[view].eyebrow} <span className="eyebrow-sep">/</span> TENANT {overview?.workspace?.tenant_id || "—"}</div><h1>{pages[view].name}<span className="heading-dot">.</span></h1><p>{pages[view].subtitle}</p></div><div className="heading-actions"><button className="button button-quiet" disabled={!events?.events?.length} onClick={() => downloadJson({ exported_at: new Date().toISOString(), data_source: "local_sqlite", events: list })}><Download size={16}/> Export events</button><button className="button button-primary" disabled={loading} onClick={() => void refresh()}><RefreshCw size={16} className={loading ? "spin" : ""}/> Refresh data</button></div></div>
        {error && <div className="warning"><CircleHelp size={18}/><span>{error} Existing pipeline data has not been modified.</span><button onClick={() => void refresh()}>Retry</button></div>}
        {!error && !loading && summary && !summary.configured && <div className="warning"><Database size={18}/><span>{summary.message} The portal does not invent event metrics.</span></div>}
        {view === "overview" && <>
          <section className="hero">
            <div className="hero-content">
              <div className="hero-tag"><span className="hero-tag-dot"/> DATA OPERATIONS / AVIATION INTELLIGENCE <span className="hero-tag-separator">•</span> LOCAL WORKSPACE</div>
              <h2>Aviation intelligence<br/><em>command center.</em></h2>
              <p>Explore aviation events, validate data quality, and navigate your enterprise lakehouse architecture from one workspace.</p>
              <div className="hero-actions"><button onClick={() => setPage("aviation")} className="hero-link">Explore aviation intelligence <ArrowUpRight size={16}/></button><button className="hero-secondary" onClick={() => setPage("pipelines")}>View data architecture <ArrowRight size={16}/></button></div>
            </div>
            <div className="hero-visual">
              <div className="hero-radar-rings"/><div className="hero-route route-a"/><div className="hero-route route-b"/>
              <div className="hero-center"><Plane size={38} strokeWidth={1.3}/><span>DATA / NEXUS</span></div>
              <div className="hero-satellite satellite-one"><span className="satellite-icon"><Database size={17}/></span><span>EVENT INGESTION<strong>{summary?.configured ? fmt(summary.total_events) + " recorded" : "Not connected"}</strong></span></div>
              <div className="hero-satellite satellite-two"><span className="satellite-icon"><ShieldCheck size={17}/></span><span>DATA INTEGRITY<strong>{summary?.configured ? fmt(summary.duplicate_ids_in_sample) + " sample duplicates" : "Not measured"}</strong></span></div>
              <div className="hero-orbit-dot"/>
            </div>
          </section>
          <div className="section-head"><div><span className="section-overline">AT A GLANCE</span><h3>Operational aviation data</h3><p>Read-only observations from your local event store</p></div><span className="section-note"><span className="status-dot"/> {lastRefresh ? "Updated " + lastRefresh.toLocaleTimeString() : "Loading"}</span></div>
          <div className="metrics"><MetricCard label="Stored events" value={summary?.configured ? fmt(summary.total_events) : "—"} change="SQLite source" icon={Database} color="blue"/><MetricCard label="Distinct aircraft" value={summary?.configured ? fmt(summary.aircraft_in_sample) : "—"} change="Sample scope" icon={Plane} color="mint"/><MetricCard label="Position records" value={summary?.configured ? fmt(summary.positions_in_sample) : "—"} change="Sample scope" icon={Radar} color="violet"/><MetricCard label="Data tenants" value={summary?.configured ? fmt(summary.tenants_in_sample) : "—"} change="Sample scope" icon={Layers3} color="orange"/></div>
          <section className="aviation-feature-strip" aria-label="Explore DataNexus platform domains">
            <button className="aviation-feature aviation-feature-flight" onClick={() => setPage("aviation")}>
              <span className="aviation-feature-category"><Plane size={15}/> AVIATION OPERATIONS</span>
              <strong>Aircraft intelligence</strong><span>Inspect real recorded flight positions</span><ArrowUpRight className="aviation-feature-arrow" size={19}/>
            </button>
            <button className="aviation-feature aviation-feature-engine" onClick={() => setPage("intelligence")}>
              <span className="aviation-feature-category"><Sparkles size={15}/> AI & MODEL OPS</span>
              <strong>Predictive maintenance</strong><span>Planned capability · not yet operational</span><ArrowUpRight className="aviation-feature-arrow" size={19}/>
            </button>
            <button className="aviation-feature aviation-feature-data" onClick={() => setPage("pipelines")}>
              <span className="aviation-feature-category"><Workflow size={15}/> DATA ENGINEERING</span>
              <strong>Lakehouse & streaming</strong><span>Explore pipeline architecture and status</span><ArrowUpRight className="aviation-feature-arrow" size={19}/>
            </button>
          </section>
          <div className="dashboard-grid"><div className="card map-card"><div className="card-header"><div><h3>Aircraft position overview</h3><p>Location observations from your local dataset</p></div><button className="card-action" onClick={() => setPage("aviation")}>Explore <ArrowUpRight size={15}/></button></div><FlightMap events={events?.events || []}/></div>
          <div className="card health-card"><div className="card-header"><div><h3>Platform integrations</h3><p>Monitoring connection status</p></div><Server size={18} className="muted-icon"/></div><div className="health-list">{(overview?.systems || []).map((system, i) => <div className="health-row" key={system.key}><div className={"health-icon health-" + i}>{i === 0 ? <Activity size={17}/> : i === 1 ? <Workflow size={17}/> : i === 2 ? <Layers3 size={17}/> : <Cloud size={17}/>}</div><span>{system.name}</span><span className="status-neutral">Not monitored</span></div>)}</div><div className="health-foot"><ShieldCheck size={15}/><span>Infrastructure health telemetry is not yet connected.</span></div></div></div>
          <section className="datanexus-gallery" aria-label="Aviation platform project areas">
            <button className="datanexus-gallery-panel gallery-aviation" onClick={() => setPage("aviation")}><span><Plane size={16}/> AVIATION INTELLIGENCE</span><strong>Aircraft Operations</strong><small>Explore real locally stored aviation events</small><ArrowUpRight size={18}/></button>
            <button className="datanexus-gallery-panel gallery-ai" onClick={() => setPage("intelligence")}><span><Sparkles size={16}/> MODEL OPERATIONS</span><strong>Predictive Engineering</strong><small>Planned AI capability — not deployed</small><ArrowUpRight size={18}/></button>
            <button className="datanexus-gallery-panel gallery-streaming" onClick={() => setPage("pipelines")}><span><Workflow size={16}/> DATA ENGINEERING</span><strong>Lakehouse & Streaming</strong><small>Pipeline architecture and integration roadmap</small><ArrowUpRight size={18}/></button>
          </section>
          <div className="dashboard-grid lower-grid"><div className="card"><div className="card-header"><div><h3>Latest aircraft events</h3><p>Most recent source observations</p></div><button className="card-action" onClick={() => setPage("aviation")}>View all <ArrowUpRight size={15}/></button></div><EventTable rows={list.slice(0, 5)} onSelect={setSelected} compact/></div><div className="card insight-card"><div className="insight-icon"><CheckCheck size={22}/></div><h3>Engineering confidence</h3><p>Quality checks must reflect the actual data scope. This dashboard distinguishes test evidence from live monitoring.</p><div className="insight-divider"/><div className="insight-stat"><span>Duplicate event IDs (sample)</span><strong>{summary?.configured ? fmt(summary.duplicate_ids_in_sample) : "—"}</strong></div><div className="insight-stat"><span>Last event timestamp</span><strong className="small-stat">{dateLabel(summary?.last_source_event_at)}</strong></div><button className="insight-link" onClick={() => setPage("quality")}>Inspect quality evidence <ArrowRight size={15}/></button></div></div>
          <section className="datanexus-pipeline-ribbon" aria-label="Data and AI pipeline architecture">
            <div className="ribbon-heading"><Layers3 size={24}/><div><strong>Data &amp; AI Pipeline</strong><small>Development architecture · telemetry not connected</small></div></div>
            <div className="ribbon-stages">{["Ingest","Process","Lakehouse","AI models","Serve"].map((stage,i)=><div className="ribbon-stage" key={stage}><span>{String(i+1).padStart(2,"0")}</span><strong>{stage}</strong><small>{i<3?"Not monitored":"Not operational"}</small></div>)}</div>
            <span className="ribbon-state">Monitoring pending</span>
          </section>
        </>}
        {view === "aviation" && <><div className="metrics metrics-three"><MetricCard label="Total stored events" value={summary?.configured ? fmt(summary.total_events) : "—"} change="SQLite source" icon={Database} color="blue"/><MetricCard label="Aircraft in sample" value={summary?.configured ? fmt(summary.aircraft_in_sample) : "—"} change="Latest 500" icon={Plane} color="mint"/><MetricCard label="Located records" value={summary?.configured ? fmt(summary.positions_in_sample) : "—"} change="Latest 500" icon={Radar} color="violet"/></div><div className="card full-map-card"><div className="card-header"><div><h3>Geospatial observation view</h3><p>Recorded coordinates • not live aircraft tracking</p></div><span className="tag-outline">SOURCE: LOCAL SQLITE</span></div><FlightMap events={events?.events || []}/></div><div className="card events-card"><div className="card-header"><div><h3>Aircraft event explorer</h3><p>Search and inspect source events</p></div><span className="record-count">{list.length} visible / {fmt(events?.total)}</span></div><div className="table-tools"><div className="search-field"><Search size={17}/><input aria-label="Search aircraft events" placeholder="Search aircraft, callsign or tenant..." value={query} onChange={e => setQuery(e.target.value)}/>{query && <button onClick={() => setQuery("")} aria-label="Clear search"><X size={15}/></button>}</div><button className="button button-quiet" onClick={() => setSortNew(s => !s)}><Filter size={16}/>{sortNew ? "Newest first" : "Oldest first"}</button></div><EventTable rows={list} onSelect={setSelected}/></div></>}
        {view === "pipelines" && <><div className="warning info"><Activity size={18}/><span>Pipeline stages were tested separately in Phase 2. This view represents the architecture; it does not claim live service health.</span></div><div className="card pipeline-card"><div className="card-header"><div><h3>Data platform architecture</h3><p>Event processing to analytical storage</p></div><span className="tag-outline">DESIGN + LOCAL TESTS</span></div><div className="pipeline-flow">{[{title:"Event capture",sub:"OpenSky → Kafka",icon:Radar},{title:"Stream processing",sub:"Apache Spark",icon:Workflow},{title:"Lakehouse tables",sub:"Apache Iceberg",icon:Layers3},{title:"Object storage",sub:"S3-compatible",icon:Cloud}].map((step,i) => <div className="flow-wrap" key={step.title}><div className="pipeline-node"><div className="flow-icon"><step.icon size={23}/></div><strong>{step.title}</strong><span>{step.sub}</span><small>Telemetry pending</small></div>{i < 3 && <ArrowRight className="flow-arrow" size={24}/>}</div>)}</div></div><div className="dashboard-grid"><div className="card"><div className="card-header"><div><h3>Monitoring coverage</h3><p>Services awaiting runtime integration</p></div><Gauge size={19}/></div><div className="health-list">{(overview?.systems || []).map(s => <div className="health-row" key={s.key}><div className="health-icon health-0"><Server size={17}/></div><span>{s.name}</span><span className="status-neutral">Pending</span></div>)}</div></div><div className="card next-card"><div className="next-icon"><Boxes size={25}/></div><h3>Next engineering milestone</h3><p>Connect authenticated service health checks, lag, Spark job runs, Iceberg snapshot audit metrics, and storage capacity to versioned API contracts.</p><div className="next-list"><span><CheckCheck size={15}/> Reuse existing pipeline components</span><span><CheckCheck size={15}/> Add real telemetry adapters</span><span><CheckCheck size={15}/> Test failure and recovery</span></div></div></div></>}
        {view === "quality" && <><div className="metrics metrics-three"><MetricCard label="Sampled events" value={summary?.configured ? fmt(summary.sample_size) : "—"} change="At most 500" icon={Database} color="blue"/><MetricCard label="Duplicate IDs" value={summary?.configured ? fmt(summary.duplicate_ids_in_sample) : "—"} change="Sample only" icon={ShieldCheck} color="mint"/><MetricCard label="Located observations" value={summary?.configured ? fmt(summary.positions_in_sample) : "—"} change="Sample only" icon={Radar} color="violet"/></div><div className="card"><div className="card-header"><div><h3>Evidence-based data quality</h3><p>Defined scope and limitations for each check</p></div><ClipboardCheck size={19}/></div><div className="quality-check">{[{n:"Event identity uniqueness",d:"Count duplicate event identifiers across up to 500 recent SQLite events.",s:"Measured in sample"},{n:"Coordinate completeness",d:"Count records with both latitude and longitude present in the same sample.",s:"Measured in sample"},{n:"Iceberg snapshot integrity",d:"The separate Phase 2G Spark audit is not yet connected to this API.",s:"Not integrated"},{n:"Kafka delivery quality",d:"No broker lag or delivery telemetry endpoint is connected.",s:"Not integrated"}].map((c,i)=><div className="quality-row" key={c.n}><span className={"quality-symbol " + (i < 2 ? "quality-ok" : "quality-idle")}>{i < 2 ? <CheckCheck size={18}/> : <LockKeyhole size={18}/>}</span><div><strong>{c.n}</strong><p>{c.d}</p></div><span className={i < 2 ? "quality-tag" : "status-neutral"}>{c.s}</span></div>)}</div></div></>}
        {view === "intelligence" && <div className="coming-soon"><div className="coming-icon"><Sparkles size={36}/></div><span className="eyebrow">COMING IN NEXT DEVELOPMENT PHASE</span><h2>Operational AI, with evidence.</h2><p>Disruption forecasting, interpretable predictions, evidence-grounded retrieval and approval-controlled agents are planned. No simulated model accuracy or fabricated AI output is shown here.</p><div className="coming-steps"><span><Gauge size={17}/> Prediction models</span><span><Database size={17}/> Evidence-backed RAG</span><span><ShieldCheck size={17}/> Governed agents</span></div></div>}
        {view === "settings" && <div className="dashboard-grid settings-grid"><div className="card"><div className="card-header"><div><h3>Environment information</h3><p>Current development configuration</p></div><Settings2 size={19}/></div><div className="settings-line"><span>Deployment tier</span><strong>Local development</strong></div><div className="settings-line"><span>API access</span><strong>Internal Next.js proxy</strong></div><div className="settings-line"><span>Data source</span><strong>SQLite event sink</strong></div><div className="settings-line"><span>Authentication</span><strong>Local signed sessions (not SSO)</strong></div><div className="settings-line"><span>Storage telemetry</span><strong>Not connected</strong></div></div><div className="card next-card"><div className="next-icon"><LockKeyhole size={25}/></div><h3>Security first</h3><p>This portal uses a single local administrator with signed sessions and tenant-filtered SQLite queries. It is not enterprise SSO or multi-user RBAC. Do not publish it until MFA, centralized identity and production security controls are validated.</p></div></div>}
        <footer className="footer"><span>© DataNexus AI Enterprise • Engineering preview</span><span>LOCAL DEVELOPMENT <span className="footer-sep">/</span> PHASE 3A.1</span></footer>
      </div>
    </main>
    {selected && <div className="drawer-overlay" onClick={() => setSelected(null)}><aside className="detail-drawer" onClick={e => e.stopPropagation()}><div className="drawer-header"><div><span className="eyebrow">AIRCRAFT OBSERVATION</span><h2>{selected.callsign || selected.icao24}</h2></div><button className="top-icon" onClick={() => setSelected(null)} aria-label="Close details"><X size={19}/></button></div><p>Event details sourced from your local SQLite ingestion sink.</p>{Object.entries({ "Event ID": selected.event_id, "Aircraft ICAO24": selected.icao24, "Source timestamp": dateLabel(selected.source_time), "Tenant": selected.tenant_id, "Latitude": selected.latitude ?? "—", "Longitude": selected.longitude ?? "—", "Altitude (m)": selected.altitude_m ?? "—", "Velocity (m/s)": selected.velocity_mps ?? "—", "On ground": String(selected.on_ground ?? "unknown"), "Source": selected.source }).map(([name,value]) => <div className="drawer-field" key={name}><span>{name}</span><strong>{value}</strong></div>)}<button className="button button-primary" onClick={() => { navigator.clipboard?.writeText(selected.event_id); }}>Copy event ID</button></aside></div>}
  </div>;
}
function EventTable({ rows, compact = false, onSelect }: { rows: EventRow[]; compact?: boolean; onSelect: (e: EventRow) => void }) {
  return <div className="table-wrap"><table><thead><tr><th>Aircraft</th><th>Event time (UTC)</th><th>Coordinates</th>{!compact && <th>Tenant</th>}<th>Action</th></tr></thead><tbody>{rows.length ? rows.map(e => <tr key={e.event_id}><td><div className="aircraft-cell"><div className="aircraft-icon"><Plane size={16}/></div><div><strong>{e.callsign || e.icao24}</strong><span>{e.icao24}</span></div></div></td><td>{dateLabel(e.source_time)}</td><td>{e.latitude == null || e.longitude == null ? <span className="muted">Unavailable</span> : <span>{e.latitude.toFixed(2)}°, {e.longitude.toFixed(2)}°</span>}</td>{!compact && <td>{e.tenant_id}</td>}<td><button className="table-action" onClick={() => onSelect(e)} aria-label={"View " + e.icao24}><ArrowUpRight size={17}/></button></td></tr>) : <tr><td colSpan={compact ? 4 : 5} className="empty-row">No matching observations. Check your source ingestion or search criteria.</td></tr>}</tbody></table></div>;
}
