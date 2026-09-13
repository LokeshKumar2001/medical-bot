import type { Metadata } from "next";
import "./globals.css";


export const metadata: Metadata = {
  title: "MedBot - Medical Encyclopedia AI",
  description: "AI-powered medical assistant builton the Gale Encyclopedia of Medicine",
};

export default function RootLayout({ children }: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
    >
      <body className="bg-[#0a0f1e] text-slate-200 h-screen overflow-hidden">{children}</body>
    </html>
  );
}
