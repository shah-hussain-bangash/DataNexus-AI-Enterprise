import type { Metadata } from "next";
import Link from "next/link";
import { cookies } from "next/headers";
import Assistant from "./assistant";
import styles from "./assistant.module.css";

export const metadata: Metadata = { title: "Taxi Metrics Assistant | DataNexus" };

export default function MetricsAssistantPage() {
  const signedIn = Boolean(cookies().get("datanexus_session")?.value);

  return (
    <main className={styles.page}>
      <div className={styles.frame}>
        <nav className={styles.nav} aria-label="Breadcrumb">
          <Link href="/workspaces?domain=mobility&view=historical">Urban Mobility</Link>
          <span aria-hidden="true">/</span>
          <span aria-current="page">Taxi Metrics Assistant</span>
        </nav>
        <header className={styles.hero}>
          <div>
            <p className={styles.source}>NYC TLC · Yellow Taxi</p>
            <h1>Taxi Metrics Assistant</h1>
            <p>Ask about the January 2024 report. Each answer cites the reporting snapshot and fields used.</p>
          </div>
        </header>
        {signedIn ? (
          <Assistant />
        ) : (
          <section className={styles.card} aria-labelledby="sign-in-title">
            <h2 id="sign-in-title">Sign in to ask a question</h2>
            <p>The assistant uses your existing DataNexus portal session.</p>
            <Link className={styles.primary} href="/sign-in">Sign in</Link>
          </section>
        )}
      </div>
    </main>
  );
}
