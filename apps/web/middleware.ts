import { NextRequest, NextResponse } from "next/server";
export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname === "/" && !request.cookies.get("datanexus_session")?.value) {
    return NextResponse.redirect(new URL("/sign-in", request.url));
  }
  // Only token presence here; FastAPI checks signature and expiration.
  // Sign-in remains accessible even if a cookie expires.
  return NextResponse.next();
}
export const config = { matcher: ["/"] };
