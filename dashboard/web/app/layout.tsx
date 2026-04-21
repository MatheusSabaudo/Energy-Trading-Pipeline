import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Solar Energy Data Pipeline | Project Portfolio",
  description:
    "A portfolio website for an end-to-end solar energy data pipeline, structured for data engineering, cloud engineering, and AWS architecture interview walkthroughs."
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
