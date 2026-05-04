import { NextResponse } from "next/server";
import { insertContactSubmission } from "@/lib/contact-submissions";

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type ContactPayload = {
  name?: unknown;
  email?: unknown;
  company?: unknown;
  message?: unknown;
  locale?: unknown;
  source_page?: unknown;
};

function normalizeString(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function validateContactPayload(payload: ContactPayload) {
  const name = normalizeString(payload.name);
  const email = normalizeString(payload.email);
  const company = normalizeString(payload.company);
  const message = normalizeString(payload.message);
  const locale = normalizeString(payload.locale);
  const sourcePage = normalizeString(payload.source_page);

  if (!name || !email || !message) {
    return { error: "Missing required fields." as const };
  }

  if (!emailPattern.test(email)) {
    return { error: "Invalid email address." as const };
  }

  if (
    name.length > 120 ||
    email.length > 320 ||
    company.length > 160 ||
    message.length > 5000 ||
    locale.length > 24 ||
    sourcePage.length > 240
  ) {
    return { error: "Submitted fields exceed allowed length." as const };
  }

  return {
    name,
    email,
    company,
    message,
    locale: locale || null,
    sourcePage: sourcePage || null
  };
}

function getErrorMessage(error: unknown) {
  if (!error) return "Unknown error.";
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;

  if (typeof error === "object") {
    const maybeMessage = (error as { message?: unknown }).message;
    const maybeName = (error as { name?: unknown }).name;

    if (typeof maybeMessage === "string" && maybeMessage.trim()) {
      return maybeMessage;
    }

    if (typeof maybeName === "string" && maybeName.trim()) {
      return maybeName;
    }

    try {
      return JSON.stringify(error);
    } catch {
      return "Unknown object error.";
    }
  }

  return "Unknown error.";
}

function getClientIp(request: Request) {
  const forwardedFor = request.headers.get("x-forwarded-for");

  if (forwardedFor) {
    return forwardedFor.split(",")[0]?.trim() || null;
  }

  return request.headers.get("x-real-ip")?.trim() || null;
}

export async function POST(request: Request) {
  let payload: ContactPayload;

  try {
    payload = (await request.json()) as ContactPayload;
  } catch (error) {
    console.error("Invalid JSON payload:", error);

    return NextResponse.json(
      { success: false, error: "Invalid JSON payload." },
      { status: 400 }
    );
  }

  const validated = validateContactPayload(payload);

  if ("error" in validated) {
    return NextResponse.json(
      { success: false, error: validated.error },
      { status: 400 }
    );
  }

  try {
    const id = await insertContactSubmission({
      name: validated.name,
      email: validated.email,
      company: validated.company || null,
      message: validated.message,
      locale: validated.locale,
      sourcePage: validated.sourcePage,
      ip: getClientIp(request),
      userAgent: request.headers.get("user-agent")?.trim() || null
    });

    return NextResponse.json({ success: true, id });
  } catch (error) {
    const message = getErrorMessage(error);
    console.error("Unexpected server error in /api/contact:", error);

    return NextResponse.json(
      { success: false, error: `Server error: ${message}` },
      { status: 500 }
    );
  }
}
