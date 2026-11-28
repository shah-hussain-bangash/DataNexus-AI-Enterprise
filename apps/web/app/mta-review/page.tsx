import type { Metadata } from "next";
import Link from "next/link";
import { cookies } from "next/headers";
import ReviewPanel from "./review-panel";
import styles from "../metrics-assistant/assistant.module.css";

export const metadata: Metadata = { title: "MTA Incident Review | DataNexus" };

export default function MtaReviewPage({ searchParams }: { searchParams: { request?: string | string[] } }) {
  const signedIn = Boolean(cookies().get("datanexus_session")?.value);
  const initialId = typeof searchParams.request === "string" && /^[a-f0-9]{32}$/.test(searchParams.request)
    ? searchParams.request : "";

  return (
    <main className={styles.page}>
      <div className={styles.frame}>
        <nav className={styles.nav} aria-label="Breadcrumb">
          <Link href="/workspaces?domain=mobility&view=historical">Urban Mobility</Link>
          <span aria-hidden="true">/</span>
          <span aria-current="page">MTA Incident Review</span>
        </nav>
        <header className={styles.hero}>
          <p className={styles.source}>MTA · Local investigation evidence</p>
          <h1>MTA Incident Review</h1>
          <p>Submit a brief, share its request ID, and record a separate reviewer’s decision on that evidence.</p>
        </header>
        {signedIn ? (
          <ReviewPanel initialId={initialId} />
        ) : (
          <section className={styles.card}>
            <h2>Sign in to review MTA evidence</h2>
            <Link className={styles.primary} href="/sign-in">Sign in</Link>
          </section>
        )}
      </div>
    </main>
  );
}
