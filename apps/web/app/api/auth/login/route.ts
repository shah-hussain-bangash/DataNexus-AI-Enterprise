import { NextRequest, NextResponse } from "next/server";

const cookieName = "datanexus_session";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const origin = request.headers.get("origin");
  if (origin && origin !== request.nextUrl.origin) {
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
    const response = await fetch(new URL("/auth/login", process.env.API_INTERNAL_URL || "http://api:8000"), {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }), cache: "no-store", signal: AbortSignal.timeout(7000),
    });
    if (!response.ok) return NextResponse.json({ error: "Invalid credentials or authentication unavailable" }, { status: response.status === 401 ? 401 : 503 });
    const data = await response.json() as { access_token?: string; expires_in?: number };
    if (!data.access_token) return NextResponse.json({ error: "Invalid authentication response" }, { status: 503 });
    const result = NextResponse.json({ ok: true }, { headers: { "Cache-Control": "no-store" } });
    result.cookies.set(cookieName, data.access_token, {
      httpOnly: true, sameSite: "strict", secure: process.env.NODE_ENV === "production",
      maxAge: Math.min(data.expires_in || 28800, 28800), path: "/",
    });
    return result;
  } catch {
    return NextResponse.json({ error: "Authentication service unavailable" }, { status: 503 });
  }
}
