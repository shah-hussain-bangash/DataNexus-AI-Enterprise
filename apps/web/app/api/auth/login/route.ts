import { NextRequest, NextResponse } from "next/server";
import { portalLogin, writePortalSession } from "../../../../lib/portal-session";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const origin = request.headers.get("origin");
  if (origin && origin !== process.env.DATANEXUS_PUBLIC_ORIGIN) {
    return NextResponse.json({ error: "Invalid request origin" }, { status: 403 });
  }
  let body: unknown;
  try { body = await request.json(); } catch { return NextResponse.json({ error: "Invalid request" }, { status: 400 }); }
  if (!body || typeof body !== "object") return NextResponse.json({ error: "Invalid credentials" }, { status: 400 });
  const { username, password } = body as { username?: unknown; password?: unknown };
  if (typeof username !== "string" || typeof password !== "string" || username.length > 100 || password.length > 1024) {
    return NextResponse.json({ error: "Invalid credentials" }, { status: 400 });
  }
  try {
    const login = await portalLogin(username, password);
    if (!login.token) return NextResponse.json({ error: "Invalid credentials or authentication unavailable" }, { status: login.status });
    const result = NextResponse.json({ ok: true }, { headers: { "Cache-Control": "no-store" } });
    writePortalSession(result, login.token, login.maxAge);
    return result;
  } catch {
    return NextResponse.json({ error: "Authentication service unavailable" }, { status: 503 });
  }
}
