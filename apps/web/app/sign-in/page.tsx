"use client";

import { FormEvent, useState } from "react";
import { ArrowRight, Eye, EyeOff, LockKeyhole, Layers3, ShieldCheck, Activity, Plane, Database, CheckCircle2, Radar, Workflow, Sparkles } from "lucide-react";

export default function SignIn() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [visible, setVisible] = useState(false);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  async function submit(e: FormEvent) {
    e.preventDefault(); setError(""); setWorking(true);
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }), credentials: "same-origin",
      });
      if (!response.ok) { setError(response.status === 401 ? "Incorrect username or password." : "Authentication service unavailable. Check portal.env and API logs."); return; }
      window.location.assign("/");
    } catch { setError("Unable to reach the authentication service."); }
    finally { setWorking(false); }
  }
  return <div className="signin-shell">
    <section className="signin-art" aria-label="DataNexus aviation intelligence platform overview">
      <div className="signin-photo-backdrop" aria-hidden="true"/>
      <div className="signin-brand"><span className="signin-mark"><Plane size={24}/></span><div>Data<span>Nexus</span><sup>AI</sup><small>AVIATION INTELLIGENCE PLATFORM</small></div></div>
      <div className="signin-art-body"><div className="signin-label"><span className="signin-pulse"/> AVIATION INTELLIGENCE PLATFORM</div><h1>Every signal.<br/><em>One intelligent<br/>command center.</em></h1><p>An aviation intelligence workspace connecting flight operations, high-quality data and responsible enterprise AI.</p>
        <div className="signin-infra"><span><Activity size={17}/> EVENT STREAMS</span><span><Database size={17}/> DATA LAKEHOUSE</span><span><Plane size={17}/> AVIATION OPS</span></div>
        <div className="signin-photo-gallery" aria-label="Aviation project imagery">
          <div className="signin-photo-tile signin-photo-aircraft"><span className="signin-photo-kicker">01 / FLEET INTELLIGENCE</span><strong>Aircraft operations</strong><span>Monitoring-ready aviation data foundation</span></div>
          <div className="signin-photo-tile signin-photo-airport"><span className="signin-photo-kicker">02 / AIRPORT OPERATIONS</span><strong>Dubai aviation network</strong><span>Airports · data pipelines · decision support</span></div>
        </div><div className="signin-console"><div className="signin-console-header"><span><span className="signin-console-pulse"/> AVIATION DATA NETWORK</span><span>ENGINEERING PREVIEW / LOCAL</span></div><div className="signin-console-body"><div className="signin-console-path"><span className="signin-console-node"><Radar size={20}/> INGEST</span><span className="signin-console-wire"/><span className="signin-console-node"><Workflow size={20}/> TRANSFORM</span><span className="signin-console-wire"/><span className="signin-console-node"><Database size={20}/> ANALYZE</span></div><div className="signin-console-caption"><Sparkles size={15}/> Streaming → Lakehouse → Operational insights</div></div></div>
      </div>
      <div className="signin-art-footer"><span><ShieldCheck size={16}/> Protected local workspace</span><span>DATANEXUS / AVIATION INTELLIGENCE</span></div>
      <div className="signin-image-credit">Illustrative airport photography: <a target="_blank" rel="noreferrer" href="https://commons.wikimedia.org/wiki/File:A2613-Dubai_Airport-Emirates2.jpg">A2613 (CC BY-SA 4.0)</a> · <a target="_blank" rel="noreferrer" href="https://commons.wikimedia.org/wiki/File:Dubai_Airport_overview.jpg">Umair Shaikh (CC BY-SA 2.0)</a> · No airline affiliation</div>
      <div className="signin-orbit one"/><div className="signin-orbit two"/><div className="signin-orbit three"/>
    </section>
    <section className="signin-form-side">
      <div className="signin-top"><span className="signin-local"><span/> LOCAL DEVELOPMENT</span><span>Phase 3A.2</span></div>
      <div className="signin-card"><div className="signin-secure"><LockKeyhole size={23}/></div><div className="signin-heading-label">WELCOME BACK · LOCAL DEVELOPMENT</div><h2>Sign in to DataNexus</h2><p>Access your aviation intelligence command center.</p>
      <form onSubmit={submit}>
        <label htmlFor="user-name">Username</label>
        <input id="user-name" name="username" autoComplete="username" placeholder="Your administrator username" required value={username} onChange={e => setUsername(e.target.value)}/>
        <div className="signin-password-heading"><label htmlFor="user-password">Password</label><span>Private workspace</span></div>
        <div className="signin-password"><input id="user-password" type={visible ? "text" : "password"} autoComplete="current-password" placeholder="Enter your password" required value={password} onChange={e => setPassword(e.target.value)}/><button type="button" aria-label={visible ? "Hide password" : "Show password"} onClick={() => setVisible(!visible)}>{visible ? <EyeOff size={18}/> : <Eye size={18}/>}</button></div>
        {error && <p className="signin-error" role="alert">{error}</p>}
        <button className="signin-submit" disabled={working} type="submit">{working ? "Signing in…" : "Enter the workspace"}<ArrowRight size={17}/></button>
      </form>
      <div className="signin-notice"><CheckCircle2 size={17}/><span>Protected local session with PostgreSQL authentication auditing when enabled. Enterprise SSO, MFA and RBAC are not yet implemented.</span></div></div>
      <div className="signin-help">Need to configure access? Run <code>python scripts/create_portal_env.py</code> from the repository.</div>
    </section>
  </div>;
}
