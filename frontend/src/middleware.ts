export { default } from "next-auth/middleware";

export const config = {
  // Protect all routes except the sign-in page and NextAuth's own endpoints.
  matcher: ["/((?!auth|api/auth|_next/static|_next/image|favicon.ico).*)"],
};
