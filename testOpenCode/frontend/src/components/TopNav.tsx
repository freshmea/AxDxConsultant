"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "./AuthProvider";

const navItems = [
  { href: "/", label: "홈" },
  { href: "/board", label: "게시판" },
  { href: "/qna", label: "QnA" },
  { href: "/login", label: "로그인" },
];

export default function TopNav() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-40 px-4 pt-4 sm:px-6">
      <div className="mx-auto flex max-w-[1320px] items-center justify-between rounded-[26px] border border-white/75 bg-white/70 px-4 py-3 shadow-[0_18px_40px_rgba(15,23,42,0.08)] backdrop-blur">
        <Link href="/" className="flex items-center gap-3">
          <span className="rounded-full bg-[#fff2cf] px-3 py-2 text-xs font-bold uppercase tracking-[0.35em] text-[#c66a1a]">DXAX</span>
          <span className="font-[var(--font-display)] text-3xl font-semibold text-slate-950">Campus</span>
        </Link>

        <nav className="flex items-center gap-2 overflow-x-auto no-scrollbar">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                  active ? "bg-[#172033] text-white" : "text-slate-700 hover:bg-[#fff2cf] hover:text-[#9f5a17]"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          {user ? (
            <>
              <div className="hidden rounded-full bg-[#eef4f8] px-4 py-2 text-sm font-medium text-slate-700 sm:block">{user.name}</div>
              <button type="button" onClick={logout} className="secondary-button text-sm font-semibold">
                로그아웃
              </button>
            </>
          ) : (
            <Link href="/login" className="primary-button text-sm font-semibold">
              로그인
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
