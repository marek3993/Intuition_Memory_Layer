import "server-only";
import { neonQuery } from "@/lib/neon";

export const submissionStatuses = ["new", "read", "archived"] as const;

export type SubmissionStatus = (typeof submissionStatuses)[number];

export type ContactSubmissionInsert = {
  name: string;
  email: string;
  company: string | null;
  message: string;
  locale: string | null;
  sourcePage: string | null;
  ip: string | null;
  userAgent: string | null;
};

export type ContactSubmissionRecord = {
  id: string;
  created_at: string;
  name: string;
  email: string;
  company: string | null;
  message: string;
  locale: string | null;
  source_page: string | null;
  status: SubmissionStatus;
  notes: string | null;
  ip: string | null;
  user_agent: string | null;
};

type InsertRow = {
  id: string;
};

export async function insertContactSubmission(input: ContactSubmissionInsert) {
  const result = await neonQuery<InsertRow>(
    `
      INSERT INTO contact_submissions (
        name,
        email,
        company,
        message,
        locale,
        source_page,
        status,
        notes,
        ip,
        user_agent
      )
      VALUES ($1, $2, $3, $4, $5, $6, 'new', NULL, $7, $8)
      RETURNING id
    `,
    [
      input.name,
      input.email,
      input.company,
      input.message,
      input.locale,
      input.sourcePage,
      input.ip,
      input.userAgent
    ]
  );

  return result.rows[0]?.id ?? null;
}

export async function listContactSubmissions() {
  const result = await neonQuery<ContactSubmissionRecord>(
    `
      SELECT
        id,
        created_at,
        name,
        email,
        company,
        message,
        locale,
        source_page,
        status,
        notes,
        ip,
        user_agent
      FROM contact_submissions
      ORDER BY created_at DESC
    `
  );

  return result.rows;
}

export async function updateSubmissionStatus(id: string, status: SubmissionStatus) {
  await neonQuery(
    `
      UPDATE contact_submissions
      SET status = $2
      WHERE id = $1
    `,
    [id, status]
  );
}

export async function updateSubmissionNotes(id: string, notes: string | null) {
  await neonQuery(
    `
      UPDATE contact_submissions
      SET notes = $2
      WHERE id = $1
    `,
    [id, notes]
  );
}
