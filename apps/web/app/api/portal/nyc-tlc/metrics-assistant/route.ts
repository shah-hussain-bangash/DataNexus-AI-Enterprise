import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const reply = (body: unknown, status: number) =>
  NextResponse.json(body, { status, headers: { "Cache-Control": "no-store" } });

async function readQuestion(request: NextRequest): Promise<string | null> {
  const body = request.body?.getReader();
  if (!body) return null;

  const decoder = new TextDecoder("utf-8", { fatal: true });
  let bytes = 0;
  let text = "";
  try {
    while (true) {
      const chunk = await body.read();
      if (chunk.done) break;
      bytes += chunk.value.byteLength;
      if (bytes > 1024) {
        await body.cancel();
        return null;
      }
      text += decoder.decode(chunk.value, { stream: true });
    }
    const json: unknown = JSON.parse(text + decoder.decode());
    if (!json || typeof json !== "object" || Array.isArray(json) || Object.keys(json).length !== 1) {
      return null;
    }
    const { question } = json as { question?: unknown };
    return typeof question === "string" && question.trim() && question.length <= 160
      ? question.trim()
      : null;
  } catch {
    return null;
  } finally {
    body.releaseLock();
  }
}

export async function POST(request: NextRequest) {
  const origin = request.headers.get("origin");
  const expectedOrigin = process.env.DATANEXUS_PUBLIC_ORIGIN || request.nextUrl.origin;
  if (origin && origin !== expectedOrigin) return reply({ error: "Invalid request origin" }, 403);

  const token = request.cookies.get("datanexus_session")?.value;
  if (!token) return reply({ error: "Authentication required" }, 401);

  const question = await readQuestion(request);
  if (question === null) return reply({ error: "Enter a question of up to 160 characters" }, 400);

  try {
    const response = await fetch(
      new URL("/api/v1/nyc-tlc/metrics-assistant", process.env.API_INTERNAL_URL || "http://api:8000"),
      {
        method: "POST",
        headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
        cache: "no-store",
        signal: AbortSignal.timeout(7000),
      },
    );
    if (response.status === 401) {
      const result = reply({ error: "Session expired" }, 401);
      result.cookies.set("datanexus_session", "", { httpOnly: true, sameSite: "strict", path: "/", maxAge: 0 });
      return result;
    }
    if (response.status === 403) return reply({ error: "Catalog access required" }, 403);
    if (!response.ok) return reply({ error: "Reporting evidence unavailable" }, 503);
    return reply(await response.json(), 200);
  } catch {
    return reply({ error: "Portal API unavailable" }, 503);
  }
}
