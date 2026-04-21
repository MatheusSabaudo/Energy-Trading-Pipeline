import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Solar Decision Platform | Data Engineering Project Walkthrough",
  description:
    "An end-to-end solar decision platform and data engineering project walkthrough with real data context, simulation logic, and a full pipeline architecture."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
