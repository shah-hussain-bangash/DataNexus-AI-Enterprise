import { NextRequest, NextResponse } from "next/server";
export const dynamic = "force-dynamic";
export async function GET(request: NextRequest, context: { params: { path: string[] } }) {
  const key = context.params.path.join("/");
  if (!new Set(["overview", "events", "quality", "catalog", "readiness", "nyc-tlc/bronze", "nyc-tlc/reporting"]).has(key)) return NextResponse.json({error:"Not found"},{status:404});
  const token = request.cookies.get("datanexus_session")?.value;
  if (!token) return NextResponse.json({ error: "Authentication required" }, { status: 401 });
  const url = new URL("/api/v1/" + key, process.env.API_INTERNAL_URL || "http://api:8000");
  if (key === "events") {
    url.searchParams.set("q", (new URL(request.url).searchParams.get("q") || "").slice(0,80));
    url.searchParams.set("limit", "100");
  }
  try {
    const response = await fetch(url, {
      headers: { Authorization: "Bearer " + token },
      cache: "no-store", signal: AbortSignal.timeout(7000)
    });
    const result = NextResponse.json(await response.json(), {
      status: response.status, headers: { "Cache-Control": "no-store" }
    });
    if (response.status === 401) result.cookies.set("datanexus_session","",{httpOnly:true,sameSite:"strict",path:"/",maxAge:0});
    return result;
  } catch {
    return NextResponse.json({error:"Portal API unavailable"},{status:503});
  }
}
