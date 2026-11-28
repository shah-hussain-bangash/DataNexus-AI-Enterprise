"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";
import base from "../metrics-assistant/assistant.module.css";
import styles from "./review.module.css";

type Brief = {
  assessment: null | { snapshot_sha256: string; assessed_at_utc: string; alerts: { code: string; severity: string }[] };
  review: null | { state: string; resolution_self_reported: boolean };
  recovery: null | { records_restored: number; report_stale: boolean };
  gaps: string[];
  citations: { id: string; reference: string; observed_utc: string }[];
};

type ReviewRequest = {
  request_id: string;
  evidence_sha256: string;
  evidence: Brief;
  submitted_by: string;
  expires_at: number;
  status: "pending" | "expired" | "approved" | "rejected";
  decision: null | { by: string; at: number; choice: "approve" | "reject" };
};

const endpoint = "/api/portal/mta-review/";
const requestIdPattern = /^[a-f0-9]{32}$/;
const gapLabels: Record<string, string> = {
  resolution_requires_independent_verification: "The recorded resolution needs independent verification",
  operator_review_incomplete: "Operator review is incomplete",
  local_restore_report_is_stale: "The local restore report is stale",
  no_verified_local_restore_report: "Verified local restore evidence is unavailable",
  live_provider_health_unverified: "Live MTA provider health is unverified",
  case_specific_kafka_recovery_unverified: "Kafka recovery for this incident is unverified",
  no_actionable_assessment_in_read_window: "No actionable assessment in the available evidence",
};

function words(value: string) {
  return value.replaceAll("_", " ").toLowerCase();
}

function utc(value: string | number) {
  return new Date(typeof value === "number" ? value * 1000 : value).toISOString().slice(0, 16).replace("T", " ") + " UTC";
}

async function requestJson<T>(url: string, body?: object): Promise<T> {
  const response = await fetch(url, {
    cache: "no-store",
    ...(body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {}),
  });
  if (response.status === 401) throw new Error("Your session expired. Sign in again.");
  if (!response.ok) {
    const problem = await response.json() as { error?: string };
    throw new Error(problem.error || "Review evidence is unavailable.");
  }
  return await response.json() as T;
}

export default function ReviewPanel({ initialId }: { initialId: string }) {
  const [role, setRole] = useState<string | null>(null);
  const [id, setId] = useState(initialId);
  const [draft, setDraft] = useState<Brief | null>(null);
  const [review, setReview] = useState<ReviewRequest | null>(null);
  const [busy, setBusy] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function initialize() {
      try {
        const session = await requestJson<{ role: string }>("/api/auth/me");
        if (active) setRole(session.role);
        if (initialId) {
          const existing = await requestJson<ReviewRequest>(endpoint + "requests/" + initialId);
          if (active) setReview(existing);
        }
      } catch (problem) {
        if (active) setError(problem instanceof Error ? problem.message : "Review evidence is unavailable.");
      } finally {
        if (active) setBusy(false);
      }
    }
    void initialize();
    return () => { active = false; };
  }, [initialId]);

  function showRequest(value: ReviewRequest) {
    setReview(value);
    setDraft(null);
    setId(value.request_id);
    window.history.replaceState(null, "", "/mta-review?request=" + value.request_id);
  }

  async function perform(action: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await action();
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : "Review evidence is unavailable.");
    } finally {
      setBusy(false);
    }
  }

  function openRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const requested = id.trim();
    if (!requestIdPattern.test(requested)) return;
    void perform(async () => {
      if (requested !== review?.request_id) {
        setReview(null);
        setDraft(null);
      }
      showRequest(await requestJson<ReviewRequest>(endpoint + "requests/" + requested));
    });
  }

  function loadBrief() {
    void perform(async () => {
      const value = await requestJson<Brief>(endpoint + "investigation");
      setDraft(value);
      setReview(null);
      window.history.replaceState(null, "", "/mta-review");
    });
  }

  function submitBrief(assessment_sha256: string) {
    void perform(async () => {
      const value = await requestJson<ReviewRequest>(endpoint + "requests", { assessment_sha256 });
      showRequest(value);
      setMessage("Review request ready. Share its link or ID with the reviewer.");
    });
  }

  function decide(decision: "approve" | "reject", request: ReviewRequest) {
    void perform(async () => {
      const value = await requestJson<ReviewRequest>(endpoint + "requests/" + request.request_id + "/decision", {
        decision, evidence_sha256: request.evidence_sha256,
      });
      showRequest(value);
      setMessage(value.status === "approved" ? "Brief approved." : "Brief rejected.");
    });
  }

  async function copyLink() {
    if (!review) return;
    try {
      await navigator.clipboard.writeText(window.location.origin + "/mta-review?request=" + review.request_id);
      setMessage("Review link copied.");
    } catch {
      setMessage("Copy the request ID shown below to share the review.");
    }
  }

  const brief = review?.evidence ?? draft;
  const draftAssessment = draft?.assessment?.snapshot_sha256;
  return (
    <div className={styles.workspace}>
      <aside className={base.card} aria-label="Review controls">
        <h2>Review controls</h2>
        {role && <p className={styles.role}>Signed in as {role === "admin" ? "operator" : role === "mta_reviewer" ? "reviewer" : words(role)}</p>}
        {role === "admin" && <button className={base.primary} type="button" disabled={busy} onClick={loadBrief}>Load latest brief</button>}
        <form className={styles.open} onSubmit={openRequest}>
          <label htmlFor="review-id">Review request ID</label>
          <input id="review-id" value={id} onChange={(event) => setId(event.target.value)} maxLength={32} />
          <button className={styles.secondary} type="submit" disabled={busy || !role || !requestIdPattern.test(id.trim())}>Open request</button>
        </form>
        <p className={styles.notice} role="status">{busy ? "Loading review evidence…" : message}</p>
        {error && <p className={styles.error} role="alert">{error} {!role && <Link href="/sign-in">Sign in</Link>}</p>}
      </aside>
      <section className={base.card} aria-label="Investigation brief">
        <div className={styles.heading}>
          <h2>{review ? "Frozen evidence brief" : "Investigation brief"}</h2>
          {review && <span className={styles.status} data-state={review.status}>{review.status}</span>}
        </div>
        {!brief && <p>Load the latest brief as an operator, or open a shared request ID to review it.</p>}
        {brief && (
          <>
            {brief.assessment ? (
              <dl className={styles.facts}>
                <div><dt>Alert assessment</dt><dd>{utc(brief.assessment.assessed_at_utc)}</dd></div>
                <div><dt>Alerts</dt><dd>{brief.assessment.alerts.map((alert) => words(alert.code)).join(", ")}</dd></div>
                <div><dt>Prior operator review</dt><dd>{brief.review?.resolution_self_reported ? "Resolution reported by operator" : brief.review?.state || "Unavailable"}</dd></div>
                <div><dt>Isolated restore</dt><dd>{brief.recovery ? brief.recovery.records_restored + " records" + (brief.recovery.report_stale ? " · stale evidence" : "") : "Unavailable"}</dd></div>
              </dl>
            ) : <p>No actionable assessment is available.</p>}
            <h3>Evidence gaps</h3>
            <ul className={styles.gaps}>{brief.gaps.map((gap) => <li key={gap}>{gapLabels[gap] || words(gap)}</li>)}</ul>
            {brief.citations.length > 0 && (
              <details className={styles.citations}>
                <summary>Cited sources ({brief.citations.length})</summary>
                <ul>{brief.citations.map((cite) => <li key={cite.id}>
                  <strong>{words(cite.id)}</strong> · {utc(cite.observed_utc)}
                  <code>{cite.reference}</code>
                </li>)}</ul>
              </details>
            )}
            {draftAssessment && role === "admin" &&
              <button className={base.primary} type="button" disabled={busy} onClick={() => submitBrief(draftAssessment)}>Submit for review</button>}
          </>
        )}
        {review && (
          <div className={styles.request}>
            <h3>Review request</h3>
            <dl className={styles.facts}>
              <div><dt>Request ID</dt><dd><code>{review.request_id}</code></dd></div>
              <div><dt>Submitted by</dt><dd>{review.submitted_by}</dd></div>
              <div><dt>Expires</dt><dd>{utc(review.expires_at)}</dd></div>
              <div><dt>Evidence SHA-256</dt><dd><code>{review.evidence_sha256}</code></dd></div>
            </dl>
            {review.decision && <p>Decision recorded by <strong>{review.decision.by}</strong> at {utc(review.decision.at)}.</p>}
            <div className={styles.actions}>
              <button className={styles.secondary} type="button" onClick={() => void copyLink()}>Copy review link</button>
              {role === "mta_reviewer" && review.status === "pending" && <>
                <button className={base.primary} type="button" disabled={busy} onClick={() => decide("approve", review)}>Approve brief</button>
                <button className={styles.reject} type="button" disabled={busy} onClick={() => decide("reject", review)}>Reject brief</button>
              </>}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
