"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";
import styles from "./assistant.module.css";

const examples = [
  "How many accepted taxi trips were there in January 2024?",
  "Which day had the most taxi trips in January 2024?",
  "What was the average daily taxi trip count in January 2024?",
  "What dates does the taxi report cover?",
];

type Citation = {
  source_id: string;
  start: string;
  end: string;
  fields: string[];
  gold_sha256: string;
};

type Answer = {
  status: "answered" | "unsupported";
  answer: string;
  citations: Citation[];
};

export default function Assistant() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [error, setError] = useState<"sign-in" | "permission" | "unavailable" | null>(null);
  const [busy, setBusy] = useState(false);

  async function ask(value: string) {
    const prompt = value.trim();
    if (!prompt || busy) return;
    setQuestion(prompt);
    setAnswer(null);
    setError(null);
    setBusy(true);
    try {
      const response = await fetch("/api/portal/nyc-tlc/metrics-assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: prompt }),
        cache: "no-store",
      });
      if (response.status === 401) setError("sign-in");
      else if (response.status === 403) setError("permission");
      else if (!response.ok) setError("unavailable");
      else setAnswer((await response.json()) as Answer);
    } catch {
      setError("unavailable");
    } finally {
      setBusy(false);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void ask(question);
  }

  return (
    <div className={styles.grid}>
      <section className={styles.card} aria-labelledby="question-title">
        <h2 id="question-title">Ask a question</h2>
        <form onSubmit={submit} className={styles.form}>
          <label htmlFor="taxi-question">Your question</label>
          <input id="taxi-question" value={question} onChange={(event) => setQuestion(event.target.value)}
            placeholder="Which day had the most trips?" maxLength={160} required />
          <button type="submit" className={styles.primary} disabled={busy || !question.trim()}>
            {busy ? "Checking evidence…" : "Ask"}
          </button>
        </form>
        <div className={styles.result} aria-live="polite" aria-busy={busy}>
          {error === "sign-in" && <p>Your session has expired. <Link href="/sign-in">Sign in again</Link>.</p>}
          {error === "permission" && <p>Your account needs catalog access to read this report.</p>}
          {error === "unavailable" && <p>The reporting evidence could not be loaded. Try again later.</p>}
          {answer && (
            <div className={styles.answer}>
              <h3>{answer.status === "answered" ? "Answer" : "Outside this report’s scope"}</h3>
              <p>{answer.answer}</p>
              {answer.citations.map((cite) => (
                <section key={cite.source_id + cite.gold_sha256} className={styles.citation} aria-label="Source citation">
                  <h4>Source citation</h4>
                  <Link href="/workspaces?domain=mobility&view=historical">NYC Yellow Taxi Gold reporting</Link>
                  <dl>
                    <div><dt>Date range</dt><dd>{cite.start} to {cite.end}</dd></div>
                    <div><dt>Fields</dt><dd>{cite.fields.join(", ")}</dd></div>
                  </dl>
                  <details>
                    <summary>Gold snapshot fingerprint</summary>
                    <code>{cite.gold_sha256}</code>
                  </details>
                </section>
              ))}
            </div>
          )}
        </div>
      </section>
      <aside className={styles.card} aria-labelledby="examples-title">
        <h2 id="examples-title">Supported questions</h2>
        <ul className={styles.examples}>
          {examples.map((example) => (
            <li key={example}>
              <button type="button" disabled={busy} onClick={() => void ask(example)}>{example}</button>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
