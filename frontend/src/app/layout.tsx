import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "LLM Reference Registry",
  description: "Admin UI for LLM Reference Registry",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="bg-gray-50 text-gray-800 text-sm antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
