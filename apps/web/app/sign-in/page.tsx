"use client";

import { FormEvent, useState } from "react";
import { ArrowRight, Eye, EyeOff, LockKeyhole, Layers3, ShieldCheck, Activity, Plane, Database, CheckCircle2 } from "lucide-react";

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
    <section className="signin-art" aria-label="DataNexus platform overview">
      <div className="signin-brand"><span className="signin-mark"><Layers3 size={24}/></span><div>Data<span>Nexus</span><sup>AI</sup><small>ENTERPRISE INTELLIGENCE</small></div></div>
      <div className="signin-art-body"><div className="signin-label"><span className="signin-pulse"/> AVIATION INTELLIGENCE PLATFORM</div><h1>Every signal.<br/>One intelligent<br/><em>command center.</em></h1><p>Where streaming data, operational visibility and governed intelligence come together in one workspace.</p>
        <div className="signin-infra"><span><Activity size={17}/> EVENT STREAMS</span><span><Database size={17}/> DATA LAKEHOUSE</span><span><Plane size={17}/> AVIATION OPS</span></div>
      </div>
      <div className="signin-art-footer"><span><ShieldCheck size={16}/> Protected local workspace</span><span>DATANEXUS / 3A.2</span></div>
      <div className="signin-orbit one"/><div className="signin-orbit two"/><div className="signin-orbit three"/>
    </section>
    <section className="signin-form-side">
      <div className="signin-top"><span className="signin-local"><span/> LOCAL DEVELOPMENT</span><span>Phase 3A.2</span></div>
      <div className="signin-card"><div className="signin-secure"><LockKeyhole size={23}/></div><div className="signin-heading-label">WELCOME BACK</div><h2>Sign in to DataNexus</h2><p>Enter your local administrator credentials to access the intelligence workspace.</p>
      <form onSubmit={submit}>
        <label htmlFor="user-name">Username</label>
        <input id="user-name" name="username" autoComplete="username" placeholder="Your administrator username" required value={username} onChange={e => setUsername(e.target.value)}/>
        <div className="signin-password-heading"><label htmlFor="user-password">Password</label><span>Private workspace</span></div>
        <div className="signin-password"><input id="user-password" type={visible ? "text" : "password"} autoComplete="current-password" placeholder="Enter your password" required value={password} onChange={e => setPassword(e.target.value)}/><button type="button" aria-label={visible ? "Hide password" : "Show password"} onClick={() => setVisible(!visible)}>{visible ? <EyeOff size={18}/> : <Eye size={18}/>}</button></div>
        {error && <p className="signin-error" role="alert">{error}</p>}
        <button className="signin-submit" disabled={working} type="submit">{working ? "Signing in…" : "Access workspace"}<ArrowRight size={17}/></button>
      </form>
      <div className="signin-notice"><CheckCircle2 size={17}/><span>Session tokens are stored in an HttpOnly browser cookie. This local milestone is not enterprise SSO.</span></div></div>
      <div className="signin-help">Need to configure access? Run <code>python scripts/create_portal_env.py</code> from the repository.</div>
    </section>
  </div>;
}
