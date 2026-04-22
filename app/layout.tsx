import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "imLayer | Decision-Memory Infrastructure for Workflow AI",
  description:
    "imLayer is decision-memory infrastructure for workflow AI. support_v1 is the first product, first applied workflow, and first pilot wedge built on the layer."
};

export default function RootLayout({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
