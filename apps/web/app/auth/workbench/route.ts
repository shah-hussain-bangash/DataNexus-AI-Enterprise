import { NextRequest, NextResponse } from "next/server";
import { cookieName, portalLogin, validPortalSession, writePortalSession } from "../../../lib/portal-session";

export const dynamic = "force-dynamic";

function isLoopback(url: URL): boolean {
  return url.protocol === "http:" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
}

function isWorkbenchLaunch(request: NextRequest): boolean {
  if (process.env.NODE_ENV !== "development") return false;
  try {
    const origin = process.env.DATANEXUS_WORKBENCH_DEMO_ORIGIN ?? "";
    const workbench = new URL(origin);
    const referer = new URL(request.headers.get("referer") ?? "");
    return isLoopback(request.nextUrl) && isLoopback(workbench) &&
      workbench.origin === origin && referer.origin === origin;
  } catch {
    return false;
  }
}

export async function GET(request: NextRequest) {
  const result = new NextResponse(null, { status: 303, headers: { Location: "/", "Cache-Control": "no-store" } });
  if (!isWorkbenchLaunch(request)) return result;
  const username = process.env.DATANEXUS_WORKBENCH_DEMO_USERNAME;
  const password = process.env.DATANEXUS_WORKBENCH_DEMO_PASSWORD;
  if (!username || !password) return result;
  try {
    const current = request.cookies.get(cookieName)?.value;
    if (current && await validPortalSession(current)) {
      result.headers.set("Location", "/workspaces");
      return result;
    }
    const login = await portalLogin(username, password);
    if (login.token) {
      writePortalSession(result, login.token, login.maxAge);
      result.headers.set("Location", "/workspaces");
    }
  } catch {
    // The portal continues through its normal sign-in flow when local auth is unavailable.
  }
  return result;
}
