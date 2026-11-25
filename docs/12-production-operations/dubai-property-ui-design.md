# Dubai Property - Premium Dashboard UI (design preview)

## Scope and source

This is the **visual/UI milestone only** for the Dubai Property workspace in DataNexus AI Enterprise.

Reference: user-approved side-by-side Dubai investment dashboard screenshot (25 November 2026), with a light ivory content area, dark-navy sidebar, teal active navigation, gold action buttons, marina/Burj Khalifa imagery, four metric cards, an investment chart, donut distribution, market snapshot, property cards, and quick actions.

**Route:** \`/dubai-property\` (reachable from existing Aviation overview).

**Critical:** The entire page is a **design fixture**. Portfolio values (AED 24.8M), appreciation, yield, market averages, opportunity counts, chart points and properties are NOT sourced from real Dubai Land Department, live listings or any user's financial records. Do not remove the on-screen fixture warning. Do not enable fictitious login/SAML/Microsoft buttons in this preview. It uses the existing portal's sign-in/session protection only.

## Implementation

- Responsive Next.js React route with locally scoped CSS, desktop navigation, mobile menu, image-backed Dubai marina hero and cards.
- Search filters three explicitly illustrative property cards.
- Save/unsave favorites is transient in-page state, no persistent portfolio write.
- Chart period controls change visual fixture series; not financial returns.
- Property detail modal explains fixtures.
- ROI calculator does simple client-side gross-rent arithmetic for *user-entered hypothetical values*, not investment advice.
- Existing navigation provides a link back to the aviation dashboard.
- Photos are external illustrative images; they may need licensed first-party replacement before release.

## Must not change

- Aviation routes, flight observations and SQLite source.
- FastAPI routes, tenant policies and P0.3 authorization behavior.
- Existing sign-in, logout, credentials, audit PostgreSQL.
- Kafka, Iceberg, Spark, Docker environments or production release gates.

## UI QA / acceptance

1. Existing login continues to reach aviation Overview and flight/event tabs.
2. Aviation Overview has a link to Dubai Property preview.
3. Route /dubai-property currently contains only public illustrative UI; do not place private data in it. Before integrating real data, add and validate server-side authentication/authorization on this route and all data APIs.
4. The Dubai preview matches reference layout and responsive layout across desktop/tablet/mobile.
5. Search, period selector, save, property details, quick actions, modal close and calculator work.
6. Fixture warning visible on desktop and mobile; no fake feed status or unsourced financial results represented as real.
7. Existing Python tests, Next.js TypeScript check and production build remain successful.

## Next milestones (only after UI approval)

- Finalize data contracts and licensed Dubai DLD data sources.
- Implement source-based data metrics with coverage, currency, timestamp and publication state.
- Implement verified property catalog, entitlement filtering and portfolio features.
- Keep the independent 16-control production gate unchanged.
