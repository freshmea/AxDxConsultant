export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type LoginUser = {
  username: string;
  name: string;
  role: string;
};

export type LoginResponse = {
  token: string;
  user: LoginUser;
};

export type CommunityPost = {
  id: number;
  title: string;
  content: string;
  author: string;
  username: string;
  createdAt: string;
  answer?: string;
};

export async function apiFetch<T>(path: string, init?: RequestInit, token?: string | null): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? "요청 처리에 실패했습니다.");
  }

  return (await response.json()) as T;
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
