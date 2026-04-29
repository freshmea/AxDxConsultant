"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";

export type ClassSummary = {
  date: string;
  title: string;
  summary: string;
  lessons: string[];
  messages: string[];
  allLessons?: string[];
  allMessages?: string[];
  details?: string[];
  conclusion?: string;
  sections?: Record<string, string>;
  coverImage: string | null;
};

export type Highlights = {
  headline: string;
  topics: string[];
  latestMessages: string[];
  classCount: number;
};

type Props = {
  highlights: Highlights;
  classes: ClassSummary[];
  apiBase: string;
};

export default function ClassShowcase({ highlights, classes, apiBase }: Props) {
  const [selected, setSelected] = useState<ClassSummary | null>(null);
  const featuredClasses = classes.slice(0, 12);
  const classCount = highlights.classCount || classes.length;

  useEffect(() => {
    document.body.style.overflow = selected ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [selected]);

  return (
    <main className="pb-20">
      <RightDateMenu classes={featuredClasses} />

      <section className="hero-panel">
        <div className="hero-grid">
          <div>
            <p className="hero-kicker">AI Systems Class Hub</p>
            <h1 className="hero-title">수업, 커뮤니티, 질문을 한 화면의 흐름으로 묶은 DXAX 클래스 허브</h1>
            <p className="hero-copy">{highlights.headline}</p>

            <div className="hero-metrics">
              <Metric label="클래스" value={`${classCount}`} />
              <Metric label="주요 토픽" value={`${highlights.topics.length}`} />
              <Metric label="최근 메시지" value={`${highlights.latestMessages.length}`} />
            </div>
          </div>

          <div className="hero-card">
            <CoverImage item={featuredClasses[0]} apiBase={apiBase} className="h-[380px] rounded-[28px] sm:h-[500px]" />
          </div>
        </div>
      </section>

      <section className="content-shell">
        <SectionTitle eyebrow="Program" title="이번 클래스에서 반복해서 다루는 실전 테마" />
        <div className="topic-grid">
          {highlights.topics.map((topic, index) => (
            <div key={topic} className="glass-card p-6">
              <span className="text-xs font-bold uppercase tracking-[0.3em] text-[#c66a1a]">Track {String(index + 1).padStart(2, "0")}</span>
              <h3 className="mt-4 text-2xl font-semibold text-slate-950">{topic}</h3>
            </div>
          ))}
        </div>
      </section>

      <section id="classes" className="content-shell">
        <SectionTitle eyebrow="Classes" title="날짜별 클래스를 열어 세부 요약과 핵심 메시지를 확인할 수 있습니다." />
        <div className="mt-10 space-y-7">
          {featuredClasses.map((item, index) => (
            <article
              id={`class-${item.date}`}
              key={item.date}
              role="button"
              tabIndex={0}
              onClick={() => setSelected(item)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  setSelected(item);
                }
              }}
              className="glass-card grid cursor-pointer gap-6 p-4 transition duration-200 hover:-translate-y-1 hover:shadow-[0_28px_80px_rgba(15,23,42,0.12)] focus:outline-none focus:ring-4 focus:ring-[#f5a623]/35 lg:grid-cols-[360px_1fr]"
            >
              <CoverImage item={item} apiBase={apiBase} className="h-72 rounded-[24px] lg:h-full" />
              <div className="p-3 sm:p-5">
                <div className="flex flex-wrap gap-3">
                  <span className="rounded-full bg-[#fff2cf] px-4 py-2 text-sm font-semibold text-[#9f5a17]">{item.date}</span>
                  <span className="rounded-full bg-[#dcecf7] px-4 py-2 text-sm font-semibold text-[#215a78]">Class {String(index + 1).padStart(2, "0")}</span>
                </div>
                <h3 className="mt-5 text-4xl font-semibold leading-tight text-slate-950">{cleanTitle(item.title)}</h3>
                <p className="mt-5 max-w-3xl text-base leading-8 text-slate-700">{item.summary}</p>
                <div className="mt-6 grid gap-3 md:grid-cols-2">
                  {[...item.messages, ...item.lessons].slice(0, 4).map((line) => (
                    <p key={line} className="rounded-[20px] bg-white/70 px-4 py-4 text-sm leading-6 text-slate-700">
                      {line}
                    </p>
                  ))}
                </div>
                <p className="mt-7 inline-flex rounded-full bg-[#172033] px-5 py-3 text-sm font-semibold text-white">클릭해서 전체 수업 노트 보기</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="content-shell">
        <SectionTitle eyebrow="Messages" title="최근 수업에서 강조한 문장" />
        <div className="topic-grid">
          {highlights.latestMessages.map((message) => (
            <div key={message} className="glass-card p-6">
              <p className="text-lg leading-8 text-slate-800">{message}</p>
            </div>
          ))}
        </div>
      </section>

      <SummaryModal item={selected} apiBase={apiBase} onClose={() => setSelected(null)} />
    </main>
  );
}

function RightDateMenu({ classes }: { classes: ClassSummary[] }) {
  return (
    <aside className="fixed right-4 top-1/2 z-30 hidden max-h-[78vh] -translate-y-1/2 rounded-[24px] border border-white/70 bg-white/75 p-3 shadow-[0_24px_60px_rgba(15,23,42,0.15)] backdrop-blur lg:block">
      <p className="px-3 pb-2 text-xs font-bold uppercase tracking-[0.3em] text-[#c66a1a]">Dates</p>
      <nav className="no-scrollbar flex max-h-[68vh] flex-col gap-2 overflow-y-auto">
        {classes.map((item) => (
          <a key={item.date} href={`#class-${item.date}`} className="rounded-2xl px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-[#fff2cf] hover:text-[#9f5a17]">
            {item.date.slice(5)}
          </a>
        ))}
      </nav>
    </aside>
  );
}

function SummaryModal({ item, apiBase, onClose }: { item: ClassSummary | null; apiBase: string; onClose: () => void }) {
  if (!item) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#172033]/65 p-4 backdrop-blur-sm" role="dialog" aria-modal="true">
      <div className="max-h-[92vh] w-full max-w-6xl overflow-hidden rounded-[32px] bg-[#fffaf1] shadow-[0_34px_120px_rgba(15,23,42,0.4)]">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <time className="text-sm font-semibold text-[#c66a1a]">{item.date}</time>
            <h2 className="mt-1 text-3xl font-semibold text-slate-950">{cleanTitle(item.title)}</h2>
          </div>
          <button type="button" onClick={onClose} className="rounded-full bg-[#172033] px-5 py-3 text-sm font-semibold text-white">
            닫기
          </button>
        </div>
        <div className="max-h-[calc(92vh-96px)] overflow-y-auto">
          <div className="bg-[#f6ead6] p-5 sm:p-6">
            <CoverImage item={item} apiBase={apiBase} className="h-[62vh] max-h-[760px] min-h-[360px] rounded-[28px] bg-white" fit="contain" />
          </div>
          <div className="space-y-8 p-6 sm:p-8 lg:p-10">
            {modalSections(item).map(([title, body]) => (
              <ModalSection key={title} title={title}>
                <p className="whitespace-pre-line text-base leading-8 text-slate-700">{body}</p>
              </ModalSection>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function CoverImage({
  item,
  apiBase,
  className,
  fit = "cover",
}: {
  item: ClassSummary | undefined;
  apiBase: string;
  className: string;
  fit?: "cover" | "contain";
}) {
  if (!item) {
    return <div className={`bg-[linear-gradient(135deg,#fff2cf_0%,#f3dac2_38%,#dcecf7_100%)] ${className}`} />;
  }

  const src = imageUrl(item.coverImage, apiBase);

  if (!src) {
    return (
      <div className={`flex items-center justify-center bg-[linear-gradient(135deg,#fff2cf_0%,#f3dac2_38%,#dcecf7_100%)] ${className}`}>
        <div className="px-8 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.35em] text-[#9f5a17]">DXAX Class</p>
          <p className="mt-4 text-4xl font-semibold text-slate-950">{item.date}</p>
        </div>
      </div>
    );
  }

  return <img src={src} alt={`${item.date} 클래스 커버 이미지`} className={`w-full ${fit === "contain" ? "object-contain" : "object-cover"} ${className}`} loading="lazy" />;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[22px] border border-white/70 bg-white/80 p-4 shadow-[0_10px_30px_rgba(15,23,42,0.08)]">
      <p className="text-xs font-bold uppercase tracking-[0.3em] text-slate-500">{label}</p>
      <p className="mt-2 text-4xl font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function SectionTitle({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-[0.32em] text-[#c66a1a]">{eyebrow}</p>
      <h2 className="mt-4 max-w-4xl text-4xl font-semibold leading-tight text-slate-950 sm:text-5xl">{title}</h2>
    </div>
  );
}

function ModalSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h3 className="mb-4 text-2xl font-semibold text-slate-950">{title}</h3>
      {children}
    </section>
  );
}

function imageUrl(path: string | null, apiBase: string): string | null {
  if (!path) {
    return null;
  }
  return path.startsWith("http") ? path : `${apiBase}${path}`;
}

function cleanTitle(title: string): string {
  return title.replace(/^\d{4}-\d{2}-\d{2}\s*/, "");
}

function modalSections(item: ClassSummary): Array<[string, string]> {
  const sections = Object.entries(item.sections ?? {}).filter(([title, body]) => title !== "intro" && body.trim());

  if (sections.length) {
    return sections;
  }

  const fallbackSections: Array<[string, string]> = [
    ["수업 전체 요약", item.summary],
    ["무엇을 배웠나", (item.allLessons?.length ? item.allLessons : item.lessons).join("\n")],
    ["전달 메시지", (item.allMessages?.length ? item.allMessages : item.messages).join("\n")],
    ["기억해야 할 디테일", (item.details ?? []).join("\n")],
    ["결론", item.conclusion ?? ""],
  ];

  return fallbackSections.filter(([, body]) => body.trim());
}
