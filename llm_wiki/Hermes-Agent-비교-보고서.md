# Hermes Agent 조사 및 현재 시스템 비교 보고서

- 작성일: 2026-04-21
- 비교 대상 1: [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)
- 비교 대상 2: 현재 저장소의 `LLM Wiki + FAISS + GraphRAG-lite + Smart Connections bridge + Mem0 + local Whisper` 스택

## 1. 조사 요약

Hermes Agent는 Nous Research가 공개한 범용 에이전트 런타임이다. 2026-04-21 기준 GitHub 저장소는 약 `105k` stars, latest release는 `v0.10.0 (2026-04-16)`로 표시된다. 공식 설명의 핵심은 "self-improving AI agent"이며, 기술적으로는 단순 코딩 도우미가 아니라 `도구 호출 + 세션 저장 + 메모리 + 스킬 + 게이트웨이 + 스케줄러 + 서브에이전트`를 하나의 런타임으로 묶은 제품에 가깝다. 출처: [GitHub README](https://github.com/NousResearch/hermes-agent), [Docs 홈](https://hermes-agent.nousresearch.com/docs/).

Hermes가 내세우는 차별점은 네 가지다.

1. 스킬이 정적 문서가 아니라 에이전트의 절차 기억으로 관리된다.
2. 메모리가 세션을 넘어 누적되며, 사용자 프로필과 에이전트 메모리를 분리한다.
3. CLI만이 아니라 Telegram, Discord, Slack, WhatsApp, Signal 등 다중 플랫폼에서 같은 에이전트를 계속 쓴다.
4. 장기 실행, 크론, delegation, tool RPC, plugin, MCP까지 포함한 운영 런타임을 제공한다.

출처: [README](https://github.com/NousResearch/hermes-agent), [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills), [Persistent Memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory/), [Architecture](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture/).

## 2. Hermes Agent 구조

### 2.1 실행 환경

Hermes는 공식적으로 Linux, macOS, WSL2를 지원하고, Windows 네이티브는 지원하지 않는다. 현재 문서상 Windows 사용자는 WSL2 설치가 권장된다. 출처: [README Quick Install](https://github.com/NousResearch/hermes-agent).

### 2.2 인터페이스와 운영 모델

Hermes는 두 가지 진입점을 가진다.

- `hermes`: 터미널 UI
- `hermes gateway`: 메신저 게이트웨이

공식 문서상 하나의 에이전트가 CLI와 메신저 플랫폼을 함께 커버한다. 세션은 SQLite 기반으로 저장되고, FTS5 검색과 lineage 추적을 가진다. 출처: [README Getting Started](https://github.com/NousResearch/hermes-agent), [Architecture](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture/).

### 2.3 메모리

Hermes의 기본 persistent memory는 `~/.hermes/memories/` 아래의 두 파일로 설명된다.

- `MEMORY.md`: 환경 사실, 학습 내용
- `USER.md`: 사용자 선호, 커뮤니케이션 스타일

이 메모리는 bounded memory로 설계되어 있고, 세션 시작 시 시스템 프롬프트에 고정 snapshot으로 들어간다. 즉 세션 중 디스크에는 즉시 반영되지만, 같은 세션 내 시스템 프롬프트는 자동 갱신되지 않는다. 출처: [Persistent Memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory/), [Tips](https://hermes-agent.nousresearch.com/docs/guides/tips/).

### 2.4 스킬

Hermes의 스킬은 `~/.hermes/skills/`가 source of truth다. 공식 문서는 스킬을 "on-demand knowledge documents"이자 "procedural memory"로 정의한다. 중요한 점은 agent가 `skill_manage` 도구로 스킬을 직접 생성, 패치, 삭제할 수 있다는 점이다. 출처: [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/).

### 2.5 컨텍스트 파일

Hermes는 프로젝트 컨텍스트 파일도 읽는다. 우선순위는 다음과 같다.

- `.hermes.md` / `HERMES.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.cursorrules`

또한 `SOUL.md`는 전역 personality 파일로 별도 로드된다. `AGENTS.md`는 하위 디렉터리까지 점진적으로 발견된다. 출처: [Context Files](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files), [Configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuration/).

### 2.6 토큰 관리

Hermes는 컨텍스트 압축을 내장한다. 문서상 두 층이 있다.

- gateway hygiene: 대략 85% 근처에서 안전 압축
- agent context compressor: 기본 50% 근처에서 인루프 압축

또한 Anthropic prompt caching과 pluggable context engine 구조를 지원한다. 출처: [Context Compression and Caching](https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching).

### 2.7 확장성

Hermes는 다음을 공식 지원한다.

- plugin system
- memory provider plugin
- context engine plugin
- MCP integration
- cron
- delegation
- ACP editor integration

출처: [Architecture](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture/), [Docs 홈](https://hermes-agent.nousresearch.com/docs/).

## 3. 현재 내 시스템 구조

현재 이 저장소에서 실제 확인되는 시스템은 범용 agent runtime이 아니라 `문서 중심 지식 체계`다.

핵심 구성:

- `AGENTS.md` 기반 프로젝트 규칙
- `llm_wiki` 인덱서와 CLI
- `sentence-transformers + FAISS` 페이지 임베딩 검색
- `GraphRAG-lite` 커뮤니티 요약
- `Obsidian Smart Connections` 브리지
- `Mem0 + Ollama + local Qdrant` 변화 사실 계층
- `local_whisper` GPU STT

확인된 현재 상태:

- markdown pages: `95`
- resolved edges: `89`
- unresolved links: `0`
- total token estimate: `83,110`
- community count: `40`
- Smart Connections bridge embedded pages: `95`
- Smart Connections related edges: `1,140`

로컬 근거:

- [AGENTS.md](/C:/Users/Administrator/dxAx/AGENTS.md)
- [llm_wiki/README.md](/C:/Users/Administrator/dxAx/llm_wiki/README.md)
- [memory_layer/README.md](/C:/Users/Administrator/dxAx/memory_layer/README.md)
- [wiki/system/link_graph.json](/C:/Users/Administrator/dxAx/wiki/system/link_graph.json)
- [wiki/system/obsidian_semantic_cache.json](/C:/Users/Administrator/dxAx/wiki/system/obsidian_semantic_cache.json)

## 4. 직접 비교

| 항목 | Hermes Agent | 현재 시스템 |
|---|---|---|
| 제품 성격 | 범용 agent runtime | 문서 중심 지식 시스템 |
| 1차 목표 | 장기 운영, 멀티플랫폼, 툴 실행, 메모리, 스킬 | 토큰 절약형 문서 검색, 요약, 지식 축적 |
| 운영 인터페이스 | CLI + 게이트웨이 + 다중 메신저 | Codex + Obsidian + 로컬 스크립트 |
| 메모리 기본 설계 | bounded `MEMORY.md` + `USER.md` snapshot | `wiki/` 인덱스 + `Mem0` fact layer + Smart Connections bridge |
| 스킬 설계 | agent-managed procedural memory | 사람이 작성한 Codex skill 문서 중심 |
| 문서 검색 | 일반 agent 문맥 + 검색/세션/도구 중심 | graph-first + FAISS + Smart Connections + community summaries |
| 그래프 구조 | 범용 memory/runtime 쪽이 중심 | markdown link graph와 community graph가 중심 |
| 토큰 최적화 방식 | session compression, prompt caching, delegation | 사전 인덱싱, 후보 축소, graph-first read plan |
| 플랫폼 범위 | 매우 넓음 | 좁지만 현재 워크플로우에 밀착 |
| Windows 적합성 | WSL2 필요 | 현재 환경에서 바로 동작 |
| STT/Obsidian 결합 | 문서상 범용 voice 있음, Obsidian 결합은 기본 아님 | Whisper GPU와 Obsidian가 이미 직접 연결됨 |

## 5. 장단점 비교

### 5.1 Hermes가 더 강한 부분

Hermes가 더 강한 쪽은 "운영체제 위의 살아있는 에이전트"다.

- 다중 플랫폼 게이트웨이
- 세션 저장과 검색
- built-in cron
- profile isolation
- plugin / MCP / delegation
- 절차 기억으로서의 스킬 자동 생성

즉 Hermes는 문서 검색 시스템이라기보다 `운영 가능한 개인/팀 에이전트 OS`에 가깝다.

### 5.2 현재 시스템이 더 강한 부분

현재 시스템이 더 강한 쪽은 `내 자료를 적은 토큰으로 정확히 읽는 것`이다.

- markdown를 source-of-truth로 유지
- `page_index.json`, `query_cache.json`, `community_summaries.json` 선조회
- 전체 코퍼스를 매번 읽지 않음
- Obsidian Smart Connections 임베딩을 다시 Codex 질의 랭킹에 반영
- 한국어 노트와 Obsidian vault 구조에 직접 최적화

즉 지금 시스템은 Hermes보다 범위는 좁지만, 현재 사용 목적에는 더 효율적이다.

## 6. 핵심 차이: 메모리 철학

Hermes의 메모리는 `작고 curated 된 운영 메모리`다. 메모리를 bounded 하게 유지해서 에이전트가 계속 동일한 identity와 user understanding을 유지하도록 설계한다.

현재 시스템의 메모리는 둘로 나뉜다.

- `wiki/`: 정적 또는 반정적 문서 지식
- `Mem0`: 바뀌는 사실, 설정 상태, 운영 facts

이 구조는 Hermes보다 지식 평면이 더 명시적이다. 대신 Hermes처럼 전체 agent runtime 내부에 자연스럽게 녹아 있지는 않다.

정리하면:

- Hermes: "에이전트가 사람과 오래 살기 위한 메모리"
- 현재 시스템: "문서 코퍼스를 싸게 읽고, 바뀌는 사실은 별도 계층에 넣는 메모리"

## 7. 토큰 효율 비교

토큰 효율은 현재 시스템이 더 직접적이다.

Hermes는 대화가 길어질 때 압축하고, 세션을 재개하고, prompt caching과 delegation으로 비용을 낮춘다. 즉 `운영 중 압축` 전략이다. 출처: [Context Compression and Caching](https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching), [Tips](https://hermes-agent.nousresearch.com/docs/guides/tips/).

현재 시스템은 질문 전에 아예 문서를 graph/JSON/semantic cache로 좁힌다. 즉 `사전 인덱싱 후 선택 읽기` 전략이다. 이 방식은 지금 목적이 "내 vault를 묻는 질문"일 때 더 유리하다.

따라서 토큰 절약 관점에서:

- 범용 agent 운영: Hermes 방식이 강함
- 로컬 vault 검색/요약: 현재 시스템 방식이 강함

## 8. 내 시스템에 Hermes를 도입한다면

전면 교체는 권장하지 않는다.

이유:

1. 현재 시스템은 Obsidian, 한국어 md, Smart Connections, Whisper, wiki artifact에 이미 맞춰져 있다.
2. Hermes는 이보다 훨씬 큰 런타임이라 운영 복잡도가 올라간다.
3. Windows 환경에서는 WSL2가 추가로 필요하다.
4. 현재 목적은 "지식 체계"가 중심이지 "멀티플랫폼 agent 운영"이 중심은 아니다.

다만 부분적으로는 많이 배울 수 있다.

### 가져오면 좋은 요소

1. 세션 저장 + FTS5 검색 계층
2. bounded 운영 메모리 스냅샷
3. cron/automation 레이어
4. multi-profile 분리
5. procedural skill 자동 생성 규칙
6. context engine 플러그인 구조

### 그대로 두는 게 좋은 요소

1. `wiki/` 중심 graph-first retrieval
2. Smart Connections 브리지
3. 문서/그래프/메모리의 분리
4. Whisper 로컬 GPU STT

## 9. 최종 판단

Hermes Agent는 현재 시스템보다 "더 큰 시스템"이지, "바로 상위호환"은 아니다.

비교 결론:

- 범용 개인 에이전트 런타임을 원하면 Hermes가 더 강하다.
- 내 자료를 로컬에서 싸게, 안정적으로, 구조적으로 읽는 지식 체계를 원하면 현재 시스템이 더 맞다.
- 가장 좋은 방향은 교체가 아니라 흡수다.

실무 권장안:

1. 현재 `wiki LLM`을 유지한다.
2. Hermes에서 `session search`, `bounded memory snapshot`, `cron`, `profile isolation` 개념만 가져온다.
3. Hermes 전체 런타임은 별도 WSL2 인스턴스에서 실험용으로 분리 검증한다.

## 10. 참고 링크

- [NousResearch/hermes-agent GitHub](https://github.com/NousResearch/hermes-agent)
- [Hermes Docs 홈](https://hermes-agent.nousresearch.com/docs/)
- [Hermes Architecture](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture/)
- [Hermes Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/)
- [Hermes Persistent Memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory/)
- [Hermes Context Files](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files)
- [Hermes Context Compression and Caching](https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching)
