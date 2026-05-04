import "server-only";
import { cookies } from "next/headers";
import { createHmac, timingSafeEqual } from "node:crypto";
import type { NextResponse } from "next/server";

const ADMIN_SESSION_COOKIE = "iml_admin_session";
const ADMIN_SESSION_MAX_AGE = 60 * 60 * 24 * 7;

type AdminSessionPayload = {
  exp: number;
  role: "admin";
};

function getRequiredSecret(name: "ADMIN_PASSWORD" | "SESSION_SECRET") {
  const value = process.env[name];

  if (!value) {
    throw new Error(`${name} is not configured.`);
  }

  return value;
}

function encodeBase64Url(input: string | Buffer) {
  return Buffer.from(input).toString("base64url");
}

function decodeBase64Url(input: string) {
  return Buffer.from(input, "base64url").toString("utf8");
}

function createSessionSignature(payload: string, secret: string) {
  return createHmac("sha256", secret).update(payload).digest();
}

function createSessionToken() {
  const secret = getRequiredSecret("SESSION_SECRET");
  const payload = encodeBase64Url(
    JSON.stringify({
      exp: Math.floor(Date.now() / 1000) + ADMIN_SESSION_MAX_AGE,
      role: "admin"
    } satisfies AdminSessionPayload)
  );
  const signature = encodeBase64Url(createSessionSignature(payload, secret));
  return `${payload}.${signature}`;
}

function parseSessionToken(token: string | undefined | null) {
  if (!token) {
    return null;
  }

  const [payloadPart, signaturePart] = token.split(".");

  if (!payloadPart || !signaturePart) {
    return null;
  }

  try {
    const secret = getRequiredSecret("SESSION_SECRET");
    const expectedSignature = createSessionSignature(payloadPart, secret);
    const actualSignature = Buffer.from(signaturePart, "base64url");

    if (actualSignature.length !== expectedSignature.length) {
      return null;
    }

    if (!timingSafeEqual(actualSignature, expectedSignature)) {
      return null;
    }

    const payload = JSON.parse(decodeBase64Url(payloadPart)) as Partial<AdminSessionPayload>;

    if (payload.role !== "admin" || typeof payload.exp !== "number") {
      return null;
    }

    if (payload.exp <= Math.floor(Date.now() / 1000)) {
      return null;
    }

    return payload as AdminSessionPayload;
  } catch {
    return null;
  }
}

export function validateAdminPassword(password: string) {
  const expectedPassword = getRequiredSecret("ADMIN_PASSWORD");
  const submitted = Buffer.from(password);
  const expected = Buffer.from(expectedPassword);

  if (submitted.length !== expected.length) {
    return false;
  }

  return timingSafeEqual(submitted, expected);
}

export async function isAdminAuthenticated() {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(ADMIN_SESSION_COOKIE)?.value;
  return Boolean(parseSessionToken(sessionToken));
}

export function setAdminSessionCookie(response: NextResponse) {
  response.cookies.set({
    name: ADMIN_SESSION_COOKIE,
    value: createSessionToken(),
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: ADMIN_SESSION_MAX_AGE
  });
}

export function clearAdminSessionCookie(response: NextResponse) {
  response.cookies.set({
    name: ADMIN_SESSION_COOKIE,
    value: "",
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0
  });
}
