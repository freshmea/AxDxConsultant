"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./AuthProvider";

export default function LoginClient() {
  const router = useRouter();
  const { user, login, logout } = useAuth();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin1234");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await login({ username, password });
      router.push("/board");
      router.refresh();
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "로그인에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="content-shell pb-20 pt-10">
      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="hero-grid">
          <div>
            <p className="hero-kicker">Member Access</p>
            <h1 className="hero-title text-[clamp(2.8rem,6vw,5rem)]">게시판과 QnA를 여는 로그인</h1>
            <p className="hero-copy">간단한 데모 인증을 붙여서 커뮤니티 작성 기능이 로그인 상태와 연결되도록 구성했습니다.</p>
          </div>
          <div className="glass-card p-6">
            <p className="text-sm font-semibold text-slate-500">테스트 계정</p>
            <div className="mt-4 space-y-3 text-sm leading-7 text-slate-700">
              <p>`admin / admin1234`</p>
              <p>`guest / guest1234`</p>
            </div>
          </div>
        </div>

        <div className="glass-card p-6 sm:p-8">
          <h2 className="font-[var(--font-display)] text-5xl font-semibold text-slate-950">Sign In</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">로그인 후 게시판과 QnA에서 글을 작성할 수 있습니다.</p>

          {user ? (
            <div className="mt-8 space-y-4">
              <div className="rounded-[22px] bg-[#eef4f8] p-5">
                <p className="text-sm text-slate-500">현재 로그인</p>
                <p className="mt-2 text-2xl font-semibold text-slate-950">{user.name}</p>
                <p className="mt-1 text-sm text-slate-600">{user.username}</p>
              </div>
              <button type="button" onClick={logout} className="secondary-button w-full font-semibold">
                로그아웃
              </button>
            </div>
          ) : (
            <form className="form-grid mt-8" onSubmit={handleSubmit}>
              <input className="form-input" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="아이디" />
              <input className="form-input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="비밀번호" />
              {error ? <p className="text-sm font-medium text-red-600">{error}</p> : null}
              <button type="submit" className="primary-button w-full font-semibold" disabled={submitting}>
                {submitting ? "로그인 중..." : "로그인"}
              </button>
            </form>
          )}
        </div>
      </section>
    </main>
  );
}
