import { NextRequest, NextResponse } from "next/server";
export const dynamic = "force-dynamic";
export async function GET(request: NextRequest) {
  const token = request.cookies.get("datanexus_session")?.value;
  if (!token) return NextResponse.json({ error: "Authentication required" }, { status: 401 });
  try {
    const response = await fetch(new URL("/auth/me", process.env.API_INTERNAL_URL || "http://api:8000"), {
      headers: { Authorization: "Bearer " + token }, cache: "no-store", signal: AbortSignal.timeout(7000),
    });
    return NextResponse.json(await response.json(), { status: response.status, headers: { "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json({ error: "Authentication unavailable" }, { status: 503 });
  }
}
