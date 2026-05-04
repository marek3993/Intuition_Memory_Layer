import { redirect } from "next/navigation";
import {
  listContactSubmissions,
  type ContactSubmissionRecord
} from "@/lib/contact-submissions";
import { isAdminAuthenticated } from "@/lib/admin-auth";

export const dynamic = "force-dynamic";

const statusClasses: Record<ContactSubmissionRecord["status"], string> = {
  new: "border-accent/30 bg-accent/[0.12] text-accent",
  read: "border-emerald-400/25 bg-emerald-400/[0.12] text-emerald-200",
  archived: "border-white/12 bg-white/[0.06] text-white/56"
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Bratislava"
  }).format(new Date(value));
}

function createPreview(message: string) {
  const flattened = message.replace(/\s+/g, " ").trim();
  return flattened.length > 160 ? `${flattened.slice(0, 157)}...` : flattened;
}

export default async function AdminInboxPage() {
  if (!(await isAdminAuthenticated())) {
    redirect("/admin/login");
  }

  const submissions = await listContactSubmissions();
  const newCount = submissions.filter((submission) => submission.status === "new").length;
  const readCount = submissions.filter((submission) => submission.status === "read").length;
  const archivedCount = submissions.filter(
    (submission) => submission.status === "archived"
  ).length;

  return (
    <main className="relative min-h-screen overflow-hidden bg-ink px-4 py-6 text-white sm:px-6">
      <div className="pointer-events-none absolute left-[-10rem] top-10 h-80 w-80 rounded-full bg-accent/[0.12] blur-3xl" />
      <div className="pointer-events-none absolute right-[-8rem] top-32 h-72 w-72 rounded-full bg-accent-strong/[0.09] blur-3xl" />

      <div className="relative mx-auto max-w-7xl">
        <header className="surface-strong panel-rim p-6 sm:p-7">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="eyebrow">Protected Inbox</div>
              <h1 className="balanced-heading mt-5 text-[2.4rem] font-semibold tracking-[-0.055em] text-white">
                Contact submissions
              </h1>
              <p className="pretty-copy mt-3 max-w-3xl text-sm leading-7 text-white/62">
                Newest entries first. Expand any row to review the full message, add notes,
                or move the submission through the inbox.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="surface flex items-center gap-3 px-4 py-3 text-sm text-white/70">
                <span className="text-accent">{newCount}</span>
                <span>new</span>
                <span className="text-white/20">/</span>
                <span>{readCount} read</span>
                <span className="text-white/20">/</span>
                <span>{archivedCount} archived</span>
              </div>

              <form action="/api/admin/logout" method="post">
                <button
                  type="submit"
                  className="inline-flex min-h-12 items-center justify-center rounded-full border border-white/10 bg-white/[0.03] px-5 py-3 text-sm font-medium text-white transition duration-300 hover:border-accent/20 hover:bg-accent/[0.08]"
                >
                  Log out
                </button>
              </form>
            </div>
          </div>
        </header>

        <section className="mt-6">
          {submissions.length === 0 ? (
            <div className="surface p-8 text-sm text-white/62">
              No contact submissions have been stored yet.
            </div>
          ) : (
            <div className="grid gap-4">
              {submissions.map((submission) => (
                <details
                  key={submission.id}
                  className="surface overflow-hidden open:border-accent/20"
                >
                  <summary className="list-none cursor-pointer px-5 py-5 sm:px-6">
                    <div className="flex flex-col gap-4 xl:grid xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.1fr)_auto] xl:items-start">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-3">
                          <span
                            className={`rounded-full border px-3 py-1 text-[10px] font-medium uppercase tracking-[0.22em] ${statusClasses[submission.status]}`}
                          >
                            {submission.status}
                          </span>
                          <span className="text-xs text-white/40">{formatDate(submission.created_at)}</span>
                        </div>
                        <div className="mt-3 text-lg font-semibold text-white">
                          {submission.name}
                        </div>
                        <div className="mt-1 text-sm text-white/60">{submission.email}</div>
                        <div className="mt-1 text-sm text-white/40">
                          {submission.company || "No company provided"}
                        </div>
                      </div>

                      <div className="min-w-0">
                        <div className="text-xs uppercase tracking-[0.22em] text-white/34">
                          Message preview
                        </div>
                        <p className="pretty-copy mt-3 text-sm leading-7 text-white/70">
                          {createPreview(submission.message)}
                        </p>
                      </div>

                      <div className="text-sm text-accent xl:pt-8">Expand</div>
                    </div>
                  </summary>

                  <div className="border-t border-white/10 px-5 py-5 sm:px-6">
                    <div className="grid gap-5 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
                      <div className="grid gap-5">
                        <section className="rounded-[24px] border border-white/10 bg-white/[0.03] p-5">
                          <div className="text-[11px] uppercase tracking-[0.22em] text-accent/72">
                            Full message
                          </div>
                          <p className="pretty-copy mt-4 whitespace-pre-wrap text-sm leading-7 text-white/78">
                            {submission.message}
                          </p>
                        </section>

                        <section className="rounded-[24px] border border-white/10 bg-white/[0.03] p-5">
                          <div className="text-[11px] uppercase tracking-[0.22em] text-accent/72">
                            Internal note
                          </div>
                          <form
                            action={`/api/admin/submissions/${submission.id}`}
                            method="post"
                            className="mt-4 grid gap-3"
                          >
                            <input type="hidden" name="action" value="save_note" />
                            <textarea
                              name="notes"
                              defaultValue={submission.notes || ""}
                              rows={5}
                              className="min-h-36 rounded-[18px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white"
                              placeholder="Add context, follow-up timing, or qualification notes."
                            />
                            <div>
                              <button
                                type="submit"
                                className="inline-flex min-h-11 items-center justify-center rounded-full border border-accent/25 bg-accent px-5 py-2.5 text-sm font-medium text-ink shadow-[0_12px_30px_rgba(79,140,255,0.24)] transition duration-300 hover:-translate-y-0.5 hover:bg-[#9fc2ff]"
                              >
                                Save note
                              </button>
                            </div>
                          </form>
                        </section>
                      </div>

                      <aside className="grid gap-4">
                        <section className="rounded-[24px] border border-white/10 bg-white/[0.03] p-5">
                          <div className="text-[11px] uppercase tracking-[0.22em] text-accent/72">
                            Submission metadata
                          </div>
                          <dl className="mt-4 grid gap-3 text-sm">
                            <MetaRow label="Locale" value={submission.locale || "Not provided"} />
                            <MetaRow
                              label="Source page"
                              value={submission.source_page || "Not provided"}
                            />
                            <MetaRow label="IP" value={submission.ip || "Not captured"} />
                            <MetaRow
                              label="User agent"
                              value={submission.user_agent || "Not captured"}
                              wrap
                            />
                            <MetaRow label="Submission ID" value={submission.id} wrap />
                          </dl>
                        </section>

                        <section className="rounded-[24px] border border-white/10 bg-white/[0.03] p-5">
                          <div className="text-[11px] uppercase tracking-[0.22em] text-accent/72">
                            Inbox actions
                          </div>
                          <div className="mt-4 flex flex-wrap gap-3">
                            {submission.status !== "read" ? (
                              <ActionForm
                                action={`/api/admin/submissions/${submission.id}`}
                                name="action"
                                value="mark_read"
                                label="Mark as read"
                              />
                            ) : null}
                            {submission.status !== "archived" ? (
                              <ActionForm
                                action={`/api/admin/submissions/${submission.id}`}
                                name="action"
                                value="archive"
                                label="Archive"
                                subtle
                              />
                            ) : null}
                          </div>
                        </section>
                      </aside>
                    </div>
                  </div>
                </details>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

function MetaRow({
  label,
  value,
  wrap = false
}: {
  label: string;
  value: string;
  wrap?: boolean;
}) {
  return (
    <div className="grid gap-1">
      <dt className="text-xs uppercase tracking-[0.22em] text-white/34">{label}</dt>
      <dd className={wrap ? "break-all text-white/72" : "text-white/72"}>{value}</dd>
    </div>
  );
}

function ActionForm({
  action,
  name,
  value,
  label,
  subtle = false
}: {
  action: string;
  name: string;
  value: string;
  label: string;
  subtle?: boolean;
}) {
  return (
    <form action={action} method="post">
      <input type="hidden" name={name} value={value} />
      <button
        type="submit"
        className={
          subtle
            ? "inline-flex min-h-11 items-center justify-center rounded-full border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm font-medium text-white transition duration-300 hover:border-accent/20 hover:bg-accent/[0.08]"
            : "inline-flex min-h-11 items-center justify-center rounded-full border border-accent/25 bg-accent px-4 py-2.5 text-sm font-medium text-ink shadow-[0_12px_30px_rgba(79,140,255,0.24)] transition duration-300 hover:-translate-y-0.5 hover:bg-[#9fc2ff]"
        }
      >
        {label}
      </button>
    </form>
  );
}
