import "server-only";

type NeonPrimitive = string | number | boolean | null;

type NeonErrorShape = {
  message?: string;
};

export type NeonRow = Record<string, unknown>;

export type NeonQueryResult<T extends NeonRow = NeonRow> = {
  rows: T[];
  rowCount: number;
};

function getDatabaseUrl() {
  const databaseUrl = process.env.DATABASE_URL;

  if (!databaseUrl) {
    throw new Error("DATABASE_URL is not configured.");
  }

  return databaseUrl;
}

function getNeonHttpEndpoint(databaseUrl: string) {
  const parsed = new URL(databaseUrl);
  const port = parsed.port ? `:${parsed.port}` : "";
  return `https://${parsed.hostname}${port}/sql`;
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  if (typeof error === "string" && error.trim()) {
    return error;
  }

  if (error && typeof error === "object") {
    const maybeMessage = (error as NeonErrorShape).message;

    if (typeof maybeMessage === "string" && maybeMessage.trim()) {
      return maybeMessage;
    }
  }

  return "Unknown database error.";
}

export async function neonQuery<T extends NeonRow = NeonRow>(
  query: string,
  params: NeonPrimitive[] = []
) {
  const databaseUrl = getDatabaseUrl();
  const endpoint = getNeonHttpEndpoint(databaseUrl);

  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Neon-Connection-String": databaseUrl
    },
    body: JSON.stringify({ query, params }),
    cache: "no-store"
  });

  const payload = (await response.json().catch(() => null)) as
    | (NeonQueryResult<T> & NeonErrorShape)
    | null;

  if (!response.ok) {
    throw new Error(getErrorMessage(payload));
  }

  if (!payload) {
    throw new Error("Empty database response.");
  }

  return {
    rows: Array.isArray(payload.rows) ? payload.rows : [],
    rowCount: typeof payload.rowCount === "number" ? payload.rowCount : 0
  } satisfies NeonQueryResult<T>;
}
