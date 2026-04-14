import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Intuition Memory Layer | Decision-Memory Technology",
  description:
    "Intuition Memory Layer is a decision-memory layer between memory and decisioning. support_v1 is the first pilot-ready proving ground."
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
