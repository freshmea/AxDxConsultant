"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "./AuthProvider";
import { apiFetch, formatDate, type CommunityPost } from "../lib/api";

export default function BoardClient() {
  const { token, user, ready } = useAuth();
  const [posts, setPosts] = useState<CommunityPost[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const loadPosts = async () => {
    try {
      const response = await apiFetch<CommunityPost[]>("/api/board/posts");
      setPosts(response);
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "게시글을 불러오지 못했습니다.");
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
      setError("로그인 후 게시글을 작성할 수 있습니다.");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      await apiFetch<CommunityPost>(
        "/api/board/posts",
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
      setError(submitError instanceof Error ? submitError.message : "게시글 작성에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="content-shell pb-20 pt-10">
      <section className="hero-grid">
        <div>
          <p className="hero-kicker">Community Board</p>
          <h1 className="hero-title text-[clamp(2.8rem,6vw,5rem)]">공지와 실습 후기를 쌓는 게시판</h1>
          <p className="hero-copy">운영 공지, 수업 후기, 자동화 실험 기록을 한곳에서 관리할 수 있도록 구성했습니다.</p>
        </div>
        <div className="glass-card p-6">
          <p className="text-sm font-semibold text-slate-500">작성 권한</p>
          <p className="mt-2 text-3xl font-semibold text-slate-950">{user ? `${user.name} 로그인 중` : "로그인 필요"}</p>
          <p className="mt-3 text-sm leading-7 text-slate-600">기본 계정은 `admin / admin1234`, `guest / guest1234` 입니다.</p>
        </div>
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-[420px_1fr]">
        <div className="glass-card p-6">
          <h2 className="text-3xl font-semibold text-slate-950">새 글 작성</h2>
          <p className="mt-2 text-sm leading-7 text-slate-600">로그인 사용자는 바로 커뮤니티 글을 올릴 수 있습니다.</p>
          <form className="form-grid mt-6" onSubmit={handleSubmit}>
            <input className="form-input" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="제목" />
            <textarea className="form-textarea" value={content} onChange={(event) => setContent(event.target.value)} placeholder="내용" />
            {error ? <p className="text-sm font-medium text-red-600">{error}</p> : null}
            <button type="submit" className="primary-button font-semibold" disabled={!ready || submitting}>
              {submitting ? "등록 중..." : "게시글 등록"}
            </button>
          </form>
        </div>

        <div className="space-y-4">
          {loading ? <div className="glass-card p-6">불러오는 중...</div> : null}
          {posts.map((post) => (
            <article key={post.id} className="glass-card p-6">
              <div className="flex flex-wrap items-center gap-3">
                <span className="rounded-full bg-[#fff2cf] px-3 py-2 text-xs font-semibold text-[#9f5a17]">#{post.id}</span>
                <span className="text-sm text-slate-500">{formatDate(post.createdAt)}</span>
              </div>
              <h3 className="mt-4 text-3xl font-semibold text-slate-950">{post.title}</h3>
              <p className="mt-4 whitespace-pre-line text-base leading-8 text-slate-700">{post.content}</p>
              <p className="mt-5 text-sm font-medium text-slate-500">{post.author}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
