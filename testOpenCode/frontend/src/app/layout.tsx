import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Cormorant_Garamond, IBM_Plex_Sans_KR } from "next/font/google";
import AuthProvider from "../components/AuthProvider";
import TopNav from "../components/TopNav";
import "./globals.css";

const displayFont = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
});

const bodyFont = IBM_Plex_Sans_KR({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "DXAX Campus",
  description: "DXAX 클래스 소개, 커뮤니티 게시판, QnA, 로그인 기능이 연결된 클래스 허브",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ko">
      <body className={`${displayFont.variable} ${bodyFont.variable}`}>
        <AuthProvider>
          <div className="site-shell">
            <TopNav />
            {children}
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
