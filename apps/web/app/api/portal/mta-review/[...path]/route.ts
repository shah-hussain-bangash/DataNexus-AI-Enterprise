import { NextRequest, NextResponse } from "next/server";
import { readBoundedJson } from "../../bounded-json";

export const dynamic = "force-dynamic";

const reviewId = /^[a-f0-9]{32}$/;
const sha256 = /^[a-f0-9]{64}$/;
const reply = (body: unknown, status: number) =>
  NextResponse.json(body, { status, headers: { "Cache-Control": "no-store" } });

function backendPath(path: string[], method: "GET" | "POST"): string | null {
  const [group, id, action] = path;
  if (method === "GET" && group === "investigation" && path.length === 1) return "/api/v1/mta/investigation";
  if (group !== "requests") return null;
  if (method === "POST" && path.length === 1) return "/api/v1/mta/review-requests";
  if (!reviewId.test(id ?? "")) return null;
  if (method === "GET" && path.length === 2) return "/api/v1/mta/review-requests/" + id;
  if (method === "POST" && path.length === 3 && action === "decision") {
    return "/api/v1/mta/review-requests/" + id + "/decision";
  }
  return null;
}

async function relay(request: NextRequest, path: string[], method: "GET" | "POST") {
  const endpoint = backendPath(path, method);
  if (!endpoint) return reply({ error: "Review endpoint not found" }, 404);
  const token = request.cookies.get("datanexus_session")?.value;
  if (!token) return reply({ error: "Sign in to continue." }, 401);

  let body: string | undefined;
  if (method === "POST") {
    const expectedOrigin = process.env.DATANEXUS_PUBLIC_ORIGIN || request.nextUrl.origin;
    if (request.headers.get("origin") !== expectedOrigin) return reply({ error: "Invalid request origin" }, 403);
    const json = await readBoundedJson(request);
    if (!json || typeof json !== "object" || Array.isArray(json)) return reply({ error: "Invalid review request" }, 400);
    const input = json as Record<string, unknown>;
    if (path.length === 1 && Object.keys(input).length === 1 &&
        typeof input.assessment_sha256 === "string" && sha256.test(input.assessment_sha256)) {
      body = JSON.stringify({ assessment_sha256: input.assessment_sha256 });
    } else if (path.length === 3 && Object.keys(input).length === 2 &&
        (input.decision === "approve" || input.decision === "reject") &&
        typeof input.evidence_sha256 === "string" && sha256.test(input.evidence_sha256)) {
      body = JSON.stringify({ decision: input.decision, evidence_sha256: input.evidence_sha256 });
    } else {
      return reply({ error: "Invalid review request" }, 400);
    }
  }

  try {
    const response = await fetch(new URL(endpoint, process.env.API_INTERNAL_URL || "http://api:8000"), {
      method, body, cache: "no-store", signal: AbortSignal.timeout(7000),
      headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
    });
    if (response.ok) return reply(await response.json(), response.status);
    if (response.status === 401) {
      const result = reply({ error: "Your session expired. Sign in again." }, 401);
      result.cookies.set("datanexus_session", "", { httpOnly: true, sameSite: "strict", path: "/", maxAge: 0 });
      return result;
    }
    if (response.status === 403) return reply({ error: "Your account cannot perform this review step." }, 403);
    if (response.status === 404) return reply({ error: "That review request or assessment was not found." }, 404);
    if (response.status === 409) {
      const result = await response.json() as { detail?: string };
      return reply({ error: result.detail || "The request can no longer be decided." }, 409);
    }
    return reply({ error: "Review evidence is unavailable." }, 503);
  } catch {
    return reply({ error: "Review evidence is unavailable." }, 503);
  }
}

export function GET(request: NextRequest, context: { params: { path: string[] } }) {
  return relay(request, context.params.path, "GET");
}

export function POST(request: NextRequest, context: { params: { path: string[] } }) {
  return relay(request, context.params.path, "POST");
}
