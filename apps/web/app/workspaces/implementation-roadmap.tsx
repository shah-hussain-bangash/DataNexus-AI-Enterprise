"use client";
import {useMemo,useState} from "react";
import {ArrowRight,CheckCircle2,ClipboardCheck,Filter,Search,ShieldAlert} from "lucide-react";
import {implementationRoadmap} from "./implementation-roadmap-data";

type TaskStatus="not_verified"|"in_progress"|"needs_review";
type ReviewRecord={status:TaskStatus;note:string};
const reviewStates:{value:TaskStatus;label:string}[]=[
 {value:"not_verified",label:"Not verified"},
 {value:"in_progress",label:"In progress (local note)"},
 {value:"needs_review",label:"Needs review (local note)"}
];
const all=implementationRoadmap.flatMap(group=>group.items.map(task=>({...task,group:group.name})));
const total=all.length;

export default function ImplementationRoadmap(){
 const [category,setCategory]=useState("All workstreams");
 const [search,setSearch]=useState("");
 const [selected,setSelected]=useState(1);
 const [statusFilter,setStatusFilter]=useState("All review notes");
 const [reviews,setReviews]=useState<Record<number,ReviewRecord>>({});
 const [draft,setDraft]=useState("");
 const [copyMessage,setCopyMessage]=useState("");
 const current=all.find(t=>t.id===selected) ?? all[0];
 const review=reviews[selected] ?? {status:"not_verified",note:""};
 const filtered=useMemo(()=>all.filter(t=>(category==="All workstreams"||t.group===category)&&(t.title+" "+t.group+" "+String(t.id)).toLowerCase().includes(search.toLowerCase().trim())&&(statusFilter==="All review notes"||((reviews[t.id]?.status??"not_verified")===statusFilter))),[category,search,statusFilter,reviews]);
 const changeSelected=(id:number)=>{setSelected(id);setDraft(reviews[id]?.note??"");setCopyMessage("")};
 const changeReview=(next:Partial<ReviewRecord>)=>setReviews(prev=>({...prev,[selected]:{...review,...next}}));
 const noteCount=Object.keys(reviews).filter(key=>reviews[Number(key)].status!=="not_verified"||reviews[Number(key)].note.trim()).length;
 const copy=()=>{const text=all.map(t=>{const r=reviews[t.id];return [String(t.id).padStart(2,"0"),t.group,t.title,r?.status??"not_verified",JSON.stringify(r?.note??"")].join(" | ")}).join("\n");if(typeof navigator!=="undefined"&&navigator.clipboard){void navigator.clipboard.writeText("DataNexus implementation review notes — LOCAL ONLY\n"+text).then(()=>setCopyMessage("Review notes copied. Not submitted to GitHub."),()=>setCopyMessage("Copy unavailable: check browser clipboard permissions."))}else setCopyMessage("Clipboard API unavailable.")};
 return <section className="ir-root" aria-label="76-task enterprise implementation roadmap">
   <div className="ir-hero"><div><small>DATANEXUS / DELIVERY & VERIFICATION ROADMAP</small><h2>76 implementation and verification tasks</h2><p>Everything in the expanded implementation list is tracked here. These are development obligations, not completed production features. The original 72-item acceptance register remains separate.</p></div><span>ROADMAP ONLY</span></div>
   <div className="ir-warning"><ShieldAlert size={19}/><div><strong>Not a production implementation status report.</strong> Every task is pending independent verification until tested code, real source evidence, security review and deployment approval exist. Local review notes never change production readiness or the repository.</div></div>
   <div className="ir-kpis"><article><small>Roadmap items</small><strong>{total}/76</strong><span>Requirements catalogued</span></article><article><small>Delivery workstreams</small><strong>{implementationRoadmap.length}</strong><span>Categories</span></article><article><small>Local review annotations</small><strong>{noteCount}</strong><span>Not audited evidence</span></article><article><small>Release controls</small><strong>0/16</strong><span>Approvals verified</span></article></div>
   <div className="ir-filters"><label><Search size={16}/><input aria-label="Search the 76 implementation tasks" placeholder="Search task ID, name, or workstream" value={search} onChange={e=>setSearch(e.target.value)}/></label><label>Workstream<select aria-label="Filter by workstream" value={category} onChange={e=>setCategory(e.target.value)}><option>All workstreams</option>{implementationRoadmap.map(g=><option key={g.name}>{g.name}</option>)}</select></label><label>Review notes<select aria-label="Filter local review notes" value={statusFilter} onChange={e=>setStatusFilter(e.target.value)}><option>All review notes</option>{reviewStates.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select></label></div>
   <div className="ir-work"><aside className="ir-list" aria-label="Remaining tasks"><div className="ir-list-heading">{filtered.length} tasks match</div>{filtered.length?filtered.map(t=><button key={t.id} className={selected===t.id?"selected":""} onClick={()=>changeSelected(t.id)} aria-current={selected===t.id?"true":undefined}><span className="ir-index">{String(t.id).padStart(2,"0")}</span><span className="ir-task-title">{t.title}<small>{t.group}</small></span><ArrowRight size={15}/></button>):<p className="ir-empty">No matching tasks. Clear or change the filters.</p>}</aside>
    <article className="ir-detail" key={selected}><div className="ir-detail-top"><span>TASK {String(current.id).padStart(2,"0")} / 76</span><span className="ir-pending">No production verification</span></div><h3>{current.title}</h3><p>{current.group} · Track implementation requirements, evidence and independent review before marking this task production-complete.</p>
     <div className="ir-steps"><h4>Acceptance workflow</h4>{["Implement and document actual behavior","Validate authorized data, quality, and security","Run automated and end-to-end tests","Verify logs, resilience and deployment","Attach independent reviewer sign-off"].map((step,i)=><div key={step}><span>{i+1}</span><strong>{step}</strong><small>Evidence required</small></div>)}</div>
     <div className="ir-review"><h4>Personal review notes <span>(browser session only)</span></h4><label>Local work status<select value={review.status} onChange={e=>changeReview({status:e.target.value as TaskStatus})}>{reviewStates.map(s=><option key={s.value} value={s.value}>{s.label}</option>)}</select></label><label>Notes<textarea rows={3} maxLength={1000} placeholder="Write a review note. This will not update GitHub or approve the task." value={draft} onChange={e=>{setDraft(e.target.value);changeReview({note:e.target.value})}}/></label><p>Review notes are not persisted to GitHub or backend services. They reset when you reload this page.</p></div>
     <div className="ir-evidence"><ClipboardCheck size={17}/><div><strong>Production acceptance: pending</strong><p>No approval is inferred from UI state, review notes, local tests, or design coverage.</p></div></div>
    </article>
   </div>
   <div className="ir-bottom"><div><h3>Roadmap coverage by workstream</h3><p>Every one of the 76 items is present. Categories are deliberately distinct from the preexisting 72-item acceptance ledger.</p><div className="ir-groups">{implementationRoadmap.map(g=><button key={g.name} onClick={()=>{setCategory(g.name);setStatusFilter("All review notes");setSearch("")}}>{g.name}<strong>{g.items.length}</strong></button>)}</div></div><div className="ir-export"><button onClick={copy}><ClipboardCheck size={17}/> Copy 76-task register and local notes</button>{copyMessage&&<p role="status">{copyMessage}</p>}</div></div>
  </section>;
}
