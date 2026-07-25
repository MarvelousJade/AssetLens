import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "AssetLens — Portfolio Research Workbench",
  description: "Grounded portfolio analytics, attribution, risk, and deterministic scenarios.",
  icons: { icon: "/mark.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
