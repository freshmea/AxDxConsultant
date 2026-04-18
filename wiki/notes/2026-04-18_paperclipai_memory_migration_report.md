# PaperclipAI 메모리 시스템 이식 보고서

## 1. 점검 범위와 결론

이번 판단은 로컬 `dxAx` 메모리 시스템 구조 확인에 더해, SSH로 `182.229.102.180:30000` 원격 `paperclipai` 런타임의 실제 파일 구조와 heartbeat 운영 상태를 직접 확인한 뒤 정리했다. 결론부터 말하면, **이식은 가능하지만 “현재 각 에이전트 워크스페이스의 파일형 메모리”와 “공유 장기기억”을 분리하는 재설계가 선행되어야 한다.** 지금 구조에 `Mem0/Qdrant`를 각 에이전트별로 덧붙이는 방식은 권장하지 않는다.

## 2. 확인한 대상 시스템 구조

실행 루트는 `/home/aa/vllm`이며, 서비스는 `paperclipai.service`로 올라와 있고 실제 실행 명령은 `/home/aa/.npm-global/bin/paperclipai run --data-dir ./paperclip-data`다. 설정 파일은 `/home/aa/vllm/.env`, `/home/aa/vllm/paperclip-data/instances/default/config.json`에 있다. 데이터베이스는 외부 DB가 아니라 **embedded Postgres**이며 저장 위치는 `/home/aa/vllm/paperclip-data/instances/default/db`, 로그는 `/home/aa/vllm/paperclip-data/instances/default/logs/server.log`, 스토리지는 `/home/aa/vllm/paperclip-data/instances/default/data/storage`, 워크스페이스는 `/home/aa/vllm/paperclip-data/instances/default/workspaces/<agent-id>` 구조다.

실제 확인된 주요 디렉터리는 아래와 같다.

```text
/home/aa/vllm
  .env
  run_paperclipai_service.sh
  paperclipai.service
  paperclip-data/
    instances/default/
      config.json
      db/
      logs/server.log
      data/storage/
      companies/<company-id>/
      workspaces/<agent-id>/
      skills/<company-id>/
      projects/<company-id>/
```

## 3. 에이전트 및 heartbeat 현황

API와 로그 기준으로 현재 회사에는 **7개 에이전트**가 있다.

- CEO
- CTO
- CMO
- UXDesigner
- Robot Research Agent
- ROS2 Expert
- Rust Expert

heartbeat 는 실제로 동작 중이며, 서버 로그에는 `checked:7`이 찍힌다. 간격은 균일하지 않다.

- CEO: `intervalSec=3600`
- CTO: `intervalSec=1800`
- 나머지 다수: `intervalSec=300`

즉 현재 시스템은 이미 “중앙 제어(Paperclip DB/API)”와 “에이전트별 워크스페이스 파일 상태”가 함께 존재하는 구조다.

## 4. 실제 메모리 구조 관찰 결과

가장 중요한 점은, 각 워크스페이스 안에 이미 `memory/`, `life/`, `research/`, `reports/` 같은 폴더가 따로 있다는 것이다. 예를 들어 CEO 워크스페이스에는 `memory/2026-04-16.md`, `memory/2026-04-17.md`, `memory/2026-04-18.md` 같은 일일 메모가 있고, 내용도 “이번 heartbeat 에서 inbox-lite 를 확인했고 할당 이슈가 없어 종료했다”는 식의 실행 기록 중심이다. `HEARTBEAT.md`와 `AGENTS.md`도 **`para-memory-files` 스킬로 memory/life 계층을 사용하라**고 명시한다.

즉 현재 `paperclipai` 쪽은 이미 다음 두 층을 갖고 있다.

- 중앙 상태: 회사/이슈/런/승인/heartbeat 는 Paperclip API + embedded Postgres
- 로컬 파일 기억: 각 에이전트 워크스페이스의 `memory/`, `life/`, `research/` 등

이 상태에서 `dxAx`의 `Mem0 + Qdrant`를 그대로 붙이면, **중앙 DB와 워크스페이스 파일 메모리 사이에 제3의 기억 계층이 추가되어 사실 원천이 3개가 되는 문제**가 생긴다.

## 5. source 시스템과의 매핑 판단

`dxAx` 쪽은 구조가 명확하다.

- 정적 지식: `wiki/system/page_index.json`, `query_cache.json`, `community_summaries.json`, `semantic_index.faiss`
- 변화 사실: `memory_layer/` 아래 `Mem0 + local Qdrant + history.db`
- 질의 흐름: graph-first 라우팅 후 필요한 문서만 읽고, 운영 상태는 `memory-search`

이 패턴을 `paperclipai`에 이식할 때는 아래처럼 역할을 분리하는 것이 가장 맞다.

- `wiki 계층` → 회사 공통 지식베이스로 이식
- `memory_layer 계층` → 공통 운영 사실 저장소로 축소 이식
- 각 워크스페이스의 `memory/` → 에이전트 개인 일지/작업 메모로 유지

핵심은 **워크스페이스 메모리를 없애는 것이 아니라, 장기 공유 기억과 개인 작업 메모리를 분리하는 것**이다.

## 6. 권장 이식안

권장안은 `3계층 + 1개 정리 계층`이다.

1. **공유 지식 계층**
회사 공통 문서, 절차, 설계, 정책은 `dxAx`의 LLM Wiki 패턴처럼 별도 저장한다. 가능하면 `paperclip-data` 바깥의 독립 경로에 두고, JSON 인덱스/링크 그래프/FAISS를 유지한다.

2. **공유 운영 메모리 계층**
사용자 상태, 최근 결정, 승인 결과, 이슈 간 합의, budget 상태, 조직 변경처럼 “모든 에이전트가 알아야 하는 변화 사실”만 저장한다. 이 계층은 로컬 파일형 Qdrant 대신 **서버형 Qdrant 또는 Postgres/pgvector**로 두는 편이 안전하다.

3. **에이전트 로컬 메모리 계층**
현재 워크스페이스의 `memory/YYYY-MM-DD.md`, `life/`, `research/`는 그대로 유지하되, 여기에는 초안/일지/개인 회상만 둔다. 공유 사실의 canonical source 가 되면 안 된다.

4. **Memory Consolidator**
7개 heartbeat 에이전트가 장기기억 DB에 직접 확정 write 하지 말고, `memory candidate`를 남기면 별도 정리기나 후처리 heartbeat 가 dedupe, 최신성 판정, TTL, namespace 분류를 거쳐 저장하도록 한다.

## 7. 왜 direct write 가 위험한가

현재 로그상 heartbeat 는 병렬로 실행되고 있고, interval 도 5분짜리가 많다. 이 상태에서 각 에이전트가 다음을 직접 하면 문제가 생긴다.

- 같은 사실을 여러 표현으로 중복 저장
- 최근 사실을 오래된 사실이 덮어씀
- issue/task 단위 사실과 company 전역 사실이 섞임
- 로컬 워크스페이스 일지와 공유 메모리의 불일치 발생

특히 지금 워크스페이스별 `memory/*.md`가 이미 존재하므로, **에이전트의 사고흐름 메모와 회사의 shared memory 를 분리하지 않으면 운영 복잡도만 늘어난다.**

## 8. 실행 플랜

1. **구조 정리**
공유 메모리의 저장 대상만 먼저 정의한다.
`global`: 정책, 승인, 예산, 전사 사실
`task`: 특정 issue/task 생명주기 사실
`agent`: 개인 선호, 개인 진행 힌트

2. **스키마 정의**
모든 메모리 레코드에 `source_agent`, `run_id`, `task_id`, `timestamp`, `confidence`, `ttl`, `supersedes`를 강제한다.

3. **읽기 우선 통합**
처음에는 write 를 붙이지 말고, CEO/CTO 같은 상위 에이전트만 공통 메모리를 read 하도록 붙여 retrieval 품질부터 검증한다.

4. **후보 저장 방식 도입**
각 agent 는 확정 저장 대신 candidate JSON만 남긴다. consolidator 가 이를 정제해 shared memory 로 승격한다.

5. **wiki 연결**
공유 메모리에서 안정화된 사실만 `wiki/notes` 또는 공통 위키에 반영한다. 반대로 문서성 사실은 shared memory 로 무한 복제하지 않는다.

6. **2주 shadow run**
중복률, stale memory 비율, retrieval recall, 잘못된 최신성 판정 사례를 측정한다.

## 9. 최종 판단

`paperclipai`의 실제 구조를 확인한 결과, 이 시스템은 이미 **중앙 DB 기반 orchestration + 워크스페이스 파일형 메모리**를 동시에 사용 중이다. 따라서 `dxAx`의 메모리 시스템을 이식할 때는 “새 메모리 저장소를 하나 더 추가”하는 접근이 아니라, **공유 지식베이스와 공유 운영 메모리를 별도 계층으로 추가하고, 기존 워크스페이스 메모리는 개인 작업기억으로 격하하는 방식**이 맞다. 가장 좋은 방향은 **shared wiki + shared operational memory + per-agent local memory + consolidator**의 4층 구조다.
