"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "./AuthProvider";
import { apiFetch, formatDate, type CommunityPost } from "../lib/api";

export default function QnaClient() {
  const { token, user } = useAuth();
  const [posts, setPosts] = useState<CommunityPost[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const loadPosts = async () => {
    try {
      const response = await apiFetch<CommunityPost[]>("/api/qna/posts");
      setPosts(response);
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "QnA를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadPosts();
  }, []);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!token) {
      setError("로그인 후 질문을 등록할 수 있습니다.");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      await apiFetch<CommunityPost>(
        "/api/qna/posts",
        {
          method: "POST",
          body: JSON.stringify({ title, content }),
        },
        token,
      );
      setTitle("");
      setContent("");
      await loadPosts();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "질문 등록에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="content-shell pb-20 pt-10">
      <section className="hero-grid">
        <div>
          <p className="hero-kicker">Questions & Answers</p>
          <h1 className="hero-title text-[clamp(2.8rem,6vw,5rem)]">실습 중 막히는 지점을 바로 남기는 QnA</h1>
          <p className="hero-copy">질문을 기록하고 답변 상태를 분리해서, 수업 후에도 맥락이 유지되도록 구성했습니다.</p>
        </div>
        <div className="glass-card p-6">
          <p className="text-sm font-semibold text-slate-500">질문 상태</p>
          <p className="mt-2 text-3xl font-semibold text-slate-950">{posts.filter((post) => post.answer).length}개 답변 완료</p>
          <p className="mt-3 text-sm leading-7 text-slate-600">{user ? `${user.name} 계정으로 질문 등록 가능` : "로그인하면 질문을 등록할 수 있습니다."}</p>
        </div>
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-[420px_1fr]">
        <div className="glass-card p-6">
          <h2 className="text-3xl font-semibold text-slate-950">질문 등록</h2>
          <p className="mt-2 text-sm leading-7 text-slate-600">실습 단계, 오류 메시지, 기대 결과를 함께 적으면 답변 속도가 빨라집니다.</p>
          <form className="form-grid mt-6" onSubmit={handleSubmit}>
            <input className="form-input" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="질문 제목" />
            <textarea className="form-textarea" value={content} onChange={(event) => setContent(event.target.value)} placeholder="어디에서 막혔는지 구체적으로 작성하세요." />
            {error ? <p className="text-sm font-medium text-red-600">{error}</p> : null}
            <button type="submit" className="primary-button font-semibold" disabled={submitting}>
              {submitting ? "등록 중..." : "질문 등록"}
            </button>
          </form>
        </div>

        <div className="space-y-4">
          {loading ? <div className="glass-card p-6">불러오는 중...</div> : null}
          {posts.map((post) => (
            <article key={post.id} className="glass-card p-6">
              <div className="flex flex-wrap items-center gap-3">
                <span className="rounded-full bg-[#dcecf7] px-3 py-2 text-xs font-semibold text-[#215a78]">Q{post.id}</span>
                <span className="text-sm text-slate-500">{formatDate(post.createdAt)}</span>
              </div>
              <h3 className="mt-4 text-3xl font-semibold text-slate-950">{post.title}</h3>
              <p className="mt-4 whitespace-pre-line text-base leading-8 text-slate-700">{post.content}</p>
              <p className="mt-5 text-sm font-medium text-slate-500">{post.author}</p>
              <div className="mt-5 rounded-[22px] bg-[#fff9ef] p-5">
                <p className="text-xs font-bold uppercase tracking-[0.28em] text-[#c66a1a]">Answer</p>
                <p className="mt-3 whitespace-pre-line text-base leading-8 text-slate-700">{post.answer?.trim() ? post.answer : "아직 답변이 등록되지 않았습니다."}</p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
