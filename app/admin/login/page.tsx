import Link from "next/link";
import { redirect } from "next/navigation";
import { isAdminAuthenticated } from "@/lib/admin-auth";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function getErrorMessage(error: string | string[] | undefined) {
  const code = Array.isArray(error) ? error[0] : error;

  switch (code) {
    case "invalid":
      return "Incorrect admin password.";
    case "missing":
      return "Enter the admin password.";
    case "server":
      return "Admin login is not configured correctly.";
    default:
      return "";
  }
}

export default async function AdminLoginPage({
  searchParams
}: {
  searchParams: SearchParams;
}) {
  if (await isAdminAuthenticated()) {
    redirect("/admin");
  }

  const params = await searchParams;
  const errorMessage = getErrorMessage(params.error);

  return (
    <main className="relative min-h-screen overflow-hidden bg-ink px-5 py-10 text-white sm:px-6">
      <div className="pointer-events-none absolute left-[-8rem] top-8 h-72 w-72 rounded-full bg-accent/[0.16] blur-3xl" />
      <div className="pointer-events-none absolute right-[-6rem] top-28 h-64 w-64 rounded-full bg-accent-strong/[0.12] blur-3xl" />

      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-5xl items-center justify-center">
        <section className="surface-strong panel-rim w-full max-w-md p-8 sm:p-10">
          <div className="eyebrow">Admin Access</div>
          <h1 className="balanced-heading mt-6 text-[2.3rem] font-semibold tracking-[-0.05em] text-white">
            imLayer inbox login
          </h1>
          <p className="pretty-copy mt-4 text-sm leading-7 text-white/62">
            This route is protected by a server-side password and a signed session cookie.
          </p>

          <form action="/api/admin/login" method="post" className="mt-8 grid gap-4">
            <label className="grid gap-2">
              <span className="text-sm font-medium text-white/78">Admin password</span>
              <input
                type="password"
                name="password"
                required
                className="min-h-12 rounded-[18px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white"
              />
            </label>

            <button
              type="submit"
              className="inline-flex min-h-12 items-center justify-center rounded-full border border-accent/25 bg-accent px-6 py-3 text-sm font-medium text-ink shadow-[0_12px_30px_rgba(79,140,255,0.24)] transition duration-300 hover:-translate-y-0.5 hover:bg-[#9fc2ff]"
            >
              Enter inbox
            </button>

            <p
              aria-live="polite"
              className={errorMessage ? "min-h-5 text-sm text-[#ffb0b0]" : "min-h-5 text-sm text-white/0"}
            >
              {errorMessage || "."}
            </p>
          </form>

          <div className="mt-8 border-t border-white/10 pt-5 text-sm text-white/48">
            <Link href="/support-v1" className="transition duration-300 hover:text-accent">
              Return to site
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
