import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
async function forward(_request: NextRequest, context: { params: { path: string[] } }) {
  const allowed = new Set(["overview", "events", "quality"]);
  const key = context.params.path.join("/");
  if (!allowed.has(key)) return NextResponse.json({ error: "Not found" }, { status: 404 });
  const base = process.env.API_INTERNAL_URL || "http://127.0.0.1:8000";
  const url = new URL("/api/v1/" + key, base);
  if (key === "events") {
    const requestUrl = new URL(_request.url);
    const q = (requestUrl.searchParams.get("q") || "").slice(0, 80);
    url.searchParams.set("q", q);
    url.searchParams.set("limit", "100");
  }
  try {
    const response = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(7000) });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status, headers: { "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json({ error: "API is unavailable. Start the datanexus-portal-api service." }, { status: 503 });
  }
}
export const GET = forward;
