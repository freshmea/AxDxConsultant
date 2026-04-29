import ClassShowcase, { type ClassSummary, type Highlights } from "./ClassShowcase";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const dynamic = "force-dynamic";

const fallbackHighlights: Highlights = {
  headline: "DXAX는 AI를 연결해 실무 자동화, 콘텐츠 생산, 지식 운영까지 이어지는 실행형 수업입니다.",
  topics: ["자동화 설계", "JSON 구조화", "팀 운영 AX", "콘텐츠 생성", "지식 시스템"],
  latestMessages: [
    "좋은 자동화는 좋은 시스템 설계에서 시작합니다.",
    "AI는 단순 실행보다 작업 조정자로 쓸 때 강해집니다.",
    "툴 연결 능력이 실무 생산성을 크게 바꿉니다.",
  ],
  classCount: 0,
};

const fallbackClasses: ClassSummary[] = [
  {
    date: "2026-04-28",
    title: "MCP 연동 기초와 AI 워크플로 연결",
    summary: "도구 연결 구조를 이해하고 실무에서 바로 사용할 자동화 루프를 설계하는 수업입니다.",
    lessons: ["클라이언트와 서버 구조", "JSON 기반 도구 연결", "업무 자동화 시나리오 작성"],
    messages: ["AI는 기능보다 연결 구조에서 차이를 만듭니다."],
    allLessons: ["클라이언트와 서버 구조", "JSON 기반 도구 연결", "업무 자동화 시나리오 작성"],
    allMessages: ["AI는 기능보다 연결 구조에서 차이를 만듭니다."],
    details: ["실제 클래스 노트는 백엔드 API와 연결되면 최신 내용으로 갱신됩니다."],
    conclusion: "서버 연결 시 전체 클래스 요약과 이미지가 자동으로 반영됩니다.",
    sections: {
      "수업 전체 요약": "도구 연결 구조를 이해하고 실무에서 바로 사용할 자동화 루프를 설계하는 수업입니다.",
      결론: "서버 연결 시 전체 클래스 요약과 이미지가 자동으로 반영됩니다.",
    },
    coverImage: null,
  },
];

async function fetchJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
    if (!response.ok) {
      return fallback;
    }
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export default async function HomePage() {
  const [highlights, classes] = await Promise.all([
    fetchJson<Highlights>("/api/highlights", fallbackHighlights),
    fetchJson<ClassSummary[]>("/api/classes", fallbackClasses),
  ]);

  return <ClassShowcase apiBase={API_BASE} highlights={highlights} classes={classes} />;
}
