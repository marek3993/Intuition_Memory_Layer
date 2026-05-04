import { NextResponse } from "next/server";
import { setAdminSessionCookie, validateAdminPassword } from "@/lib/admin-auth";

function redirectTo(request: Request, path: string) {
  return NextResponse.redirect(new URL(path, request.url), { status: 303 });
}

export async function POST(request: Request) {
  let formData: FormData;

  try {
    formData = await request.formData();
  } catch {
    return redirectTo(request, "/admin/login?error=missing");
  }

  const password = formData.get("password");

  if (typeof password !== "string" || !password.trim()) {
    return redirectTo(request, "/admin/login?error=missing");
  }

  try {
    if (!validateAdminPassword(password)) {
      return redirectTo(request, "/admin/login?error=invalid");
    }

    const response = redirectTo(request, "/admin");
    setAdminSessionCookie(response);
    return response;
  } catch (error) {
    console.error("Admin login error:", error);
    return redirectTo(request, "/admin/login?error=server");
  }
}
