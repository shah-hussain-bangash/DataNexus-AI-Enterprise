import { NextResponse } from "next/server";

export const cookieName = "datanexus_session";
const api = () => process.env.API_INTERNAL_URL || "http://api:8000";

export async function portalLogin(username: string, password: string) {
  const response = await fetch(new URL("/auth/login", api()), {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }), cache: "no-store", signal: AbortSignal.timeout(7000),
  });
  if (!response.ok) return { status: response.status === 401 ? 401 : 503 };
  const data = await response.json() as { access_token?: string; expires_in?: number };
  return data.access_token ? { status: 200, token: data.access_token, maxAge: Math.min(data.expires_in || 28800, 28800) }
    : { status: 503 };
}

export async function validPortalSession(token: string): Promise<boolean> {
  const response = await fetch(new URL("/auth/me", api()), {
    headers: { Authorization: `Bearer ${token}` }, cache: "no-store", signal: AbortSignal.timeout(7000),
  });
  return response.ok;
}

export function writePortalSession(response: NextResponse, token: string, maxAge: number): void {
  response.cookies.set(cookieName, token, {
    httpOnly: true, sameSite: "strict", secure: process.env.NODE_ENV === "production", maxAge, path: "/",
  });
}
