type ClassSummary = {
  date: string;
  title: string;
  summary: string;
  lessons: string[];
  messages: string[];
};

type Highlights = {
  headline: string;
  topics: string[];
  latestMessages: string[];
  classCount: number;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const fallbackHighlights: Highlights = {
  headline: "AI를 답변 도구에서 업무 실행 시스템으로 확장하는 DXAX 클래스",
  topics: ["업무 자동화", "JSON 데이터 구조", "협업형 AX", "이미지·영상 생성", "MCP 도구 연결"],
  latestMessages: [
    "좋은 자동화는 좋은 프롬프트보다 좋은 프로세스 설계에서 시작된다.",
    "AI는 단순 실행 도구를 넘어 협업 조정자 역할로 확장될 수 있다.",
    "이미지와 영상 생성은 마케팅과 내부 커뮤니케이션의 실무 도구다.",
  ],
  classCount: 0,
};

const fallbackClasses: ClassSummary[] = [
  {
    date: "2026-04-28",
    title: "MCP 서버 구축 기초와 AI 도구 연결",
    summary:
      "AI가 파일, 문서, 데이터베이스, 외부 서비스와 연결되는 표준 계층을 이해하고 JSON-RPC 기반 실행 구조를 익히는 수업입니다.",
    lessons: ["MCP 클라이언트와 서버 구분", "설정 파일과 인증 구조", "트리거 기반 자동화 연결"],
    messages: ["AI를 잘 쓰는 것에서 실제 도구를 표준 방식으로 다루게 만드는 단계로 확장합니다."],
  },
  {
    date: "2026-04-24",
    title: "워크플로우 자동화와 이미지 생성 실무",
    summary:
      "n8n 자동화 흐름과 이미지 생성 AI를 연결해 발표자료, 홍보 이미지, 업무 산출물을 만드는 실습 중심 수업입니다.",
    lessons: ["Trigger-Action 구조", "이미지 프롬프트 설계", "업무형 시각 자산 제작"],
    messages: ["텍스트, 메시지, 이미지 생성까지 하나의 업무 흐름 안에서 연결합니다."],
  },
];

async function fetchJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, { next: { revalidate: 30 } });
    if (!response.ok) {
      return fallback;
    }
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export default async function Home() {
  const [highlights, classes] = await Promise.all([
    fetchJson<Highlights>("/api/highlights", fallbackHighlights),
    fetchJson<ClassSummary[]>("/api/classes", fallbackClasses),
  ]);

  const featuredClasses = classes.slice(0, 9);
  const classCount = highlights.classCount || classes.length;

  return (
    <main className="min-h-screen overflow-hidden bg-ink text-slate-100">
      <section className="relative px-6 pb-20 pt-8 sm:px-10 lg:px-16">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_20%_20%,rgba(94,234,212,0.22),transparent_28%),radial-gradient(circle_at_80%_0%,rgba(167,139,250,0.2),transparent_30%),linear-gradient(135deg,#080b13_0%,#0f172a_52%,#111827_100%)]" />
        <nav className="mx-auto flex max-w-7xl items-center justify-between rounded-full border border-white/10 bg-white/5 px-5 py-3 backdrop-blur">
          <span className="text-sm font-semibold tracking-[0.3em] text-cyanline">DXAX CLASS</span>
          <span className="hidden text-sm text-slate-300 sm:block">AI 업무 자동화 실전 랜딩</span>
        </nav>

        <div className="mx-auto grid max-w-7xl gap-12 pt-20 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div>
            <p className="mb-5 inline-flex rounded-full border border-cyanline/40 bg-cyanline/10 px-4 py-2 text-sm font-medium text-cyanline">
              n8n, JSON, 생성형 미디어, MCP를 하나의 업무 흐름으로
            </p>
            <h1 className="max-w-4xl text-5xl font-black leading-tight tracking-tight text-white sm:text-6xl lg:text-7xl">
              실무 AX를 자동화 시스템으로 바꾸는 클래스
            </h1>
            <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-300 sm:text-xl">{highlights.headline}</p>
            <div className="mt-10 flex flex-wrap gap-4">
              <a
                href="#curriculum"
                className="rounded-full bg-cyanline px-7 py-4 text-sm font-bold text-slate-950 shadow-glow transition hover:-translate-y-0.5"
              >
                커리큘럼 보기
              </a>
              <a
                href="#outcomes"
                className="rounded-full border border-white/15 px-7 py-4 text-sm font-bold text-white transition hover:border-cyanline/60 hover:bg-white/10"
              >
                결과물 확인
              </a>
            </div>
          </div>

          <div className="rounded-[2rem] border border-white/10 bg-white/[0.07] p-5 shadow-2xl backdrop-blur-xl">
            <div className="rounded-[1.5rem] bg-panel p-6">
              <p className="text-sm font-semibold text-violetline">Live class intelligence</p>
              <div className="mt-6 grid grid-cols-2 gap-4">
                <Metric label="수업 요약" value={`${classCount}`} />
                <Metric label="핵심 축" value="5" />
                <Metric label="운영 방식" value="API" />
                <Metric label="프론트" value="Next" />
              </div>
              <div className="mt-6 space-y-3">
                {highlights.latestMessages.slice(0, 4).map((message) => (
                  <div key={message} className="rounded-2xl border border-white/10 bg-white/[0.04] p-4 text-sm leading-6 text-slate-300">
                    {message}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="px-6 py-16 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-7xl">
          <SectionTitle eyebrow="Why DXAX" title="프롬프트 사용법이 아니라, 업무가 굴러가는 구조를 배웁니다." />
          <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-5">
            {highlights.topics.map((topic, index) => (
              <div key={topic} className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 transition hover:-translate-y-1 hover:border-cyanline/50">
                <span className="text-sm font-black text-cyanline">0{index + 1}</span>
                <h3 className="mt-5 text-xl font-bold text-white">{topic}</h3>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="curriculum" className="px-6 py-16 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-7xl">
          <SectionTitle eyebrow="Dynamic Curriculum" title="FastAPI가 수업 노트를 읽어 최신 커리큘럼을 보여줍니다." />
          <div className="mt-10 grid gap-5 lg:grid-cols-3">
            {featuredClasses.map((item) => (
              <article key={item.date} className="group rounded-[1.75rem] border border-white/10 bg-slate-900/70 p-6 transition hover:-translate-y-1 hover:border-violetline/60">
                <time className="text-sm font-bold text-cyanline">{item.date}</time>
                <h3 className="mt-4 text-2xl font-black leading-snug text-white">{item.title.replace(/^\d{4}-\d{2}-\d{2}\s*/, "")}</h3>
                <p className="mt-4 line-clamp-5 text-sm leading-7 text-slate-300">{item.summary}</p>
                <div className="mt-6 space-y-2">
                  {[...item.messages, ...item.lessons].slice(0, 3).map((line) => (
                    <p key={line} className="rounded-2xl bg-white/[0.04] px-4 py-3 text-sm text-slate-300">
                      {line}
                    </p>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="outcomes" className="px-6 py-16 sm:px-10 lg:px-16">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[0.8fr_1.2fr] lg:items-start">
          <SectionTitle eyebrow="Outcomes" title="수업 후 남는 것은 데모가 아니라 운영 가능한 업무 자산입니다." />
          <div className="grid gap-4 sm:grid-cols-2">
            {[
              ["Workflow", "Trigger, Action, Condition으로 반복 업무를 실행 가능한 흐름으로 설계합니다."],
              ["Data", "JSON 구조, 출력 스키마, 로그 추적으로 자동화를 디버깅합니다."],
              ["Media", "이미지와 영상 생성으로 발표자료와 홍보 자산을 빠르게 제작합니다."],
              ["Integration", "Notion, Slack, MCP 서버를 연결해 AI가 실제 도구를 다루게 합니다."],
            ].map(([title, text]) => (
              <div key={title} className="rounded-3xl border border-white/10 bg-white/[0.05] p-7">
                <h3 className="text-2xl font-black text-white">{title}</h3>
                <p className="mt-4 leading-7 text-slate-300">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-6 py-20 sm:px-10 lg:px-16">
        <div className="mx-auto max-w-5xl rounded-[2rem] border border-cyanline/30 bg-gradient-to-br from-cyanline/20 via-white/[0.06] to-violetline/20 p-10 text-center shadow-glow">
          <p className="text-sm font-bold uppercase tracking-[0.35em] text-cyanline">Start building AX</p>
          <h2 className="mt-5 text-4xl font-black text-white sm:text-5xl">AI를 쓰는 사람에서, AI 업무 시스템을 설계하는 사람으로</h2>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-300">
            DXAX 클래스는 프롬프트, 데이터, 자동화, 협업 도구, 생성형 미디어를 하나의 실무 워크플로우로 묶는 방법을 다룹니다.
          </p>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-black text-white">{value}</p>
    </div>
  );
}

function SectionTitle({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div>
      <p className="text-sm font-bold uppercase tracking-[0.35em] text-violetline">{eyebrow}</p>
      <h2 className="mt-4 max-w-3xl text-3xl font-black leading-tight text-white sm:text-5xl">{title}</h2>
    </div>
  );
}
