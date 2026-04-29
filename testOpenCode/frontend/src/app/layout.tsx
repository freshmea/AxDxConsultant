import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "DXAX Class | AI 업무 자동화 실전 과정",
  description: "n8n, JSON, 협업 AX, 생성형 미디어, MCP를 실무 워크플로우로 연결하는 DXAX 수업 홍보 페이지",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
