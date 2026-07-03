import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const DEMO_USERNAME = process.env.DEMO_USERNAME || "demo";
const DEMO_PASSWORD = process.env.DEMO_PASSWORD || "demo123";
const DEMO_ACCESS_CODE = process.env.DEMO_ACCESS_CODE || "";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" },
        accessCode: { label: "Access Code", type: "text" },
      },
      async authorize(credentials) {
        const validUser =
          credentials?.username === DEMO_USERNAME &&
          credentials?.password === DEMO_PASSWORD;
        const validCode =
          DEMO_ACCESS_CODE === "" ||
          credentials?.accessCode === DEMO_ACCESS_CODE;
        if (validUser && validCode) {
          return {
            id: "1",
            name: "Demo User",
            email: "demo@hybrid-ai.demo",
          };
        }
        return null;
      },
    }),
  ],
  pages: {
    signIn: "/auth/signin",
  },
  session: {
    strategy: "jwt",
    maxAge: 24 * 60 * 60,
  },
  secret: process.env.NEXTAUTH_SECRET,
};
