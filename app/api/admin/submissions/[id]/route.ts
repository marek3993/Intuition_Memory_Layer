import { NextResponse } from "next/server";
import { redirect } from "next/navigation";
import { isAdminAuthenticated } from "@/lib/admin-auth";
import {
  updateSubmissionNotes,
  updateSubmissionStatus
} from "@/lib/contact-submissions";

type Params = Promise<{
  id: string;
}>;

export async function POST(
  request: Request,
  { params }: { params: Params }
) {
  if (!(await isAdminAuthenticated())) {
    redirect("/admin/login");
  }

  const { id } = await params;
  const formData = await request.formData();
  const action = formData.get("action");

  try {
    if (action === "mark_read") {
      await updateSubmissionStatus(id, "read");
    } else if (action === "archive") {
      await updateSubmissionStatus(id, "archived");
    } else if (action === "save_note") {
      const notes = formData.get("notes");
      const normalizedNotes =
        typeof notes === "string" && notes.trim() ? notes.trim() : null;
      await updateSubmissionNotes(id, normalizedNotes);
    }
  } catch (error) {
    console.error(`Admin submission update failed for ${id}:`, error);
    return NextResponse.redirect(new URL("/admin?error=update", request.url), {
      status: 303
    });
  }

  return NextResponse.redirect(new URL("/admin", request.url), { status: 303 });
}
