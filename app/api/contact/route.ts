import { NextResponse } from "next/server";
import { Resend } from "resend";

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type ContactPayload = {
  name?: unknown;
  email?: unknown;
  company?: unknown;
  message?: unknown;
};

function normalizeString(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function validateContactPayload(payload: ContactPayload) {
  const name = normalizeString(payload.name);
  const email = normalizeString(payload.email);
  const company = normalizeString(payload.company);
  const message = normalizeString(payload.message);

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
    message.length > 5000
  ) {
    return { error: "Submitted fields exceed allowed length." as const };
  }

  return { name, email, company, message };
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

export async function POST(request: Request) {
  const resendApiKey = process.env.RESEND_API_KEY;
  const contactEmail = process.env.CONTACT_EMAIL;
  const resendFrom = process.env.RESEND_FROM;

  if (!resendApiKey || !contactEmail || !resendFrom) {
    console.error("Contact form config missing:", {
      hasResendApiKey: !!resendApiKey,
      hasContactEmail: !!contactEmail,
      hasResendFrom: !!resendFrom
    });

    return NextResponse.json(
      { success: false, error: "Contact form is not configured correctly." },
      { status: 500 }
    );
  }

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

  const resend = new Resend(resendApiKey);

  const submittedAt = new Date().toISOString();
  const { name, email, company, message } = validated;
  const companyLine = company || "Not provided";
  const subject = `[imLayer] New pilot inquiry from ${name}`;

  const text = [
    "Source: imLayer website contact form",
    `Timestamp: ${submittedAt}`,
    `Name: ${name}`,
    `Work email: ${email}`,
    `Company: ${companyLine}`,
    "",
    "Message:",
    message
  ].join("\n");

  const html = `
    <h2>New pilot inquiry</h2>
    <p><strong>Source:</strong> imLayer website contact form</p>
    <p><strong>Timestamp:</strong> ${submittedAt}</p>
    <p><strong>Name:</strong> ${escapeHtml(name)}</p>
    <p><strong>Work email:</strong> ${escapeHtml(email)}</p>
    <p><strong>Company:</strong> ${escapeHtml(companyLine)}</p>
    <p><strong>Message:</strong></p>
    <p>${escapeHtml(message).replace(/\n/g, "<br />")}</p>
  `;

  try {
    const result = await resend.emails.send({
      from: resendFrom,
      to: [contactEmail],
      replyTo: email,
      subject,
      text,
      html
    });

    if (result.error) {
      const resendMessage = getErrorMessage(result.error);
      console.error("Resend API error:", result.error);

      return NextResponse.json(
        { success: false, error: `Resend error: ${resendMessage}` },
        { status: 500 }
      );
    }

    return NextResponse.json({ success: true, id: result.data?.id ?? null });
  } catch (error) {
    const message = getErrorMessage(error);
    console.error("Unexpected server error in /api/contact:", error);

    return NextResponse.json(
      { success: false, error: `Server error: ${message}` },
      { status: 500 }
    );
  }
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
