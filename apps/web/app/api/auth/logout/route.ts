import { NextRequest, NextResponse } from "next/server";
export async function POST(request: NextRequest) {
  const origin = request.headers.get("origin");
  if (origin && origin !== request.nextUrl.origin) return NextResponse.json({ error: "Invalid origin" }, { status: 403 });
  const response = NextResponse.json({ ok: true }, { headers: { "Cache-Control": "no-store" } });
  response.cookies.set("datanexus_session", "", { httpOnly: true, sameSite: "strict", path: "/", maxAge: 0 });
  return response;
}
