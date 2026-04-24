# Paperclip Shared Memory Handover

작성일: 2026-04-24  
목적: 다른 agent가 현재 Paperclip 운영 상태, shared-memory 적용 상태, instruction 자동 반영 구조, agent별 지식 계층 현황을 바로 이어서 점검/수정할 수 있도록 핵심 사실과 경로를 정리한다.

## 1. 작업 목적과 현재 판단

이번 작업의 핵심 목표는 다음 두 가지였다.

1. `paperclipai`에 `para-memory-files`만으로는 부족한 운영 공유 기억 계층을 추가한다.
2. 새로 추가된 shared-memory recall 규칙이 실제 agent runtime instruction에 자동 반영되도록 만든다.

현재 판단은 다음과 같다.

- `PARA(local memory/life)`는 유지하는 것이 맞다.
- `dxAx`식 메모리 계층은 전체 이식보다 `공유 운영 메모리 + 검색 회수 계층`만 부분 이식하는 것이 맞다.
- 현재 Paperclip는 agent별 워크스페이스 분리는 되어 있으나, agent별 지식 축적의 밀도는 크게 다르다.
- shared-memory와 `qmd` 기반 회수 경로는 실운영에 붙었다.
- instruction 자동 반영은 "다음 run/heartbeat부터 적용" 기준으로는 동작한다.
- 다만 "신규 agent 생성 직후 즉시 patch"는 아직 없다. 현재는 다음 shared-memory cycle에서 반영된다.

## 2. 원격 접속 정보

- 호스트: `182.229.102.180`
- 포트: `30000`
- 사용자: `aa`
- 키: `C:/Users/Administrator/.ssh/id_rsa`
- 원격 루트 작업 디렉토리: `/home/aa/vllm`

SSH 예시:

```bash
ssh -i C:/Users/Administrator/.ssh/id_rsa -p 30000 -o PubkeyAcceptedAlgorithms=+ssh-rsa -o HostkeyAlgorithms=+ssh-rsa aa@182.229.102.180
```

## 3. 원격에 반영된 핵심 파일

### 3.1 설계/운영 문서

- `/home/aa/vllm/docs/paperclip_shared_memory_migration_plan.md`
- `/home/aa/vllm/docs/paperclip_agent_memory_runtime_guide.md`

### 3.2 shared-memory 스크립트

- `/home/aa/vllm/scripts/paperclip_shared_memory/bootstrap_qmd.sh`
- `/home/aa/vllm/scripts/paperclip_shared_memory/collect_candidates.py`
- `/home/aa/vllm/scripts/paperclip_shared_memory/consolidate_shared_memory.py`
- `/home/aa/vllm/scripts/paperclip_shared_memory/patch_agent_instructions.py`
- `/home/aa/vllm/scripts/paperclip_shared_memory/run_shared_memory_cycle.sh`
- `/home/aa/vllm/scripts/paperclip_shared_memory/scheduled_shared_memory_cycle.sh`
- `/home/aa/vllm/scripts/paperclip_shared_memory/install_cron.sh`

### 3.3 shared-memory 산출물

- `/home/aa/vllm/paperclip-data/instances/default/shared-memory/candidates/`
- `/home/aa/vllm/paperclip-data/instances/default/shared-memory/facts/operational_facts.jsonl`
- `/home/aa/vllm/paperclip-data/instances/default/shared-memory/facts/operational_summary.md`
- `/home/aa/vllm/paperclip-data/instances/default/shared-memory/logs/scheduled_cycle.log`

## 4. 현재 shared-memory 동작 방식

### 4.1 검색/회수 계층

- `qmd`를 원격에 설치했다.
- shared-memory는 `paperclip-shared-memory` 컬렉션을 직접 만드는 구조가 아니라, 현재는:
  - `paperclip-workspaces` 인덱스 검색
  - shared-memory 파일 직접 읽기
  - candidate/fact 정리 파이프라인
  조합으로 운용 중이다.

### 4.2 배치 파이프라인

현재 주기 작업은 다음 흐름이다.

1. `qmd update`
2. `qmd embed`
3. `patch_agent_instructions.py`
4. `collect_candidates.py`
5. `consolidate_shared_memory.py`
6. 오래된 candidate 파일 정리

즉 shared-memory 갱신과 instruction 보정이 같은 cycle 안에서 함께 돈다.

### 4.3 스케줄

cron 등록:

```cron
*/30 * * * * /bin/bash /home/aa/vllm/scripts/paperclip_shared_memory/scheduled_shared_memory_cycle.sh
```

의미:

- 최대 30분마다 instruction과 shared-memory가 다시 동기화된다.
- 신규 agent가 회사 트리 아래 추가되면 다음 cycle에서 patch된다.

## 5. instruction 자동 반영 구조

### 5.1 실제 진입점

중요: 실제 runtime 진입점은 워크스페이스 루트의 `AGENTS.md`가 아니라 agent adapter 설정이 가리키는 managed instruction 파일이다.

주요 경로:

- 일반 agent:
  - `/home/aa/vllm/paperclip-data/instances/default/companies/<company-id>/agents/<agent-id>/instructions/AGENTS.md`
- CEO:
  - managed instruction:
    `/home/aa/vllm/paperclip-data/instances/default/companies/facae2e1-4110-4373-b4f2-3cbf7bd666ac/agents/c73df5fb-9c81-4be2-9e3c-81696ae46ac9/instructions/AGENTS.md`
  - workspace copy:
    `/home/aa/vllm/paperclip-data/instances/default/workspaces/c73df5fb-9c81-4be2-9e3c-81696ae46ac9/AGENTS.md`
  - workspace heartbeat copy:
    `/home/aa/vllm/paperclip-data/instances/default/workspaces/c73df5fb-9c81-4be2-9e3c-81696ae46ac9/HEARTBEAT.md`

### 5.2 patch_agent_instructions.py가 하는 일

이 스크립트는 다음을 수행한다.

- 각 agent `instructions/AGENTS.md`에 `## Shared Memory Runtime` 블록 삽입 또는 정규화
- CEO `instructions/HEARTBEAT.md`에 `## 5.5. Shared Memory Recall`과 `Fact Extraction` 규칙 반영
- CEO workspace `AGENTS.md`, `HEARTBEAT.md`도 같이 patch
- 이전에 들어간 구형 `5.5. Shared memory recall` 블록 제거 후 최신 블록으로 정규화

즉, 지금은 단순 삽입기가 아니라 "정규화형 patcher"다.

### 5.3 현재 자동 반영의 의미

현재는 다음이 참이다.

- 기존 agent: 다음 heartbeat/run부터 새 instruction 사용 가능
- CEO workspace copy: 동기화됨
- 신규 agent: 다음 30분 cycle에서 patch됨

현재는 다음이 아직 아니다.

- agent 생성 직후 즉시 patch
- Paperclip server의 native hook에 연결된 실시간 instruction 보정

## 6. 검증 완료 상태

다음 사항을 실제로 확인했다.

1. `scheduled_shared_memory_cycle.sh`에 `patch_agent_instructions.py` 호출이 포함되어 있다.
2. `run_shared_memory_cycle.sh`에도 instruction patch가 포함되어 있다.
3. CEO workspace `AGENTS.md`에 `## Shared Memory Runtime`이 들어갔다.
4. CEO workspace `HEARTBEAT.md`에 `## 5.5. Shared Memory Recall`과 shared-memory 승격 규칙이 들어갔다.
5. managed CEO `instructions/HEARTBEAT.md`도 동일하게 정리됐다.
6. shared-memory cycle 수동 실행 시 candidate/fact 생성이 정상 완료됐다.

확인에 사용한 대표 파일:

- `/home/aa/vllm/paperclip-data/instances/default/workspaces/c73df5fb-9c81-4be2-9e3c-81696ae46ac9/AGENTS.md`
- `/home/aa/vllm/paperclip-data/instances/default/workspaces/c73df5fb-9c81-4be2-9e3c-81696ae46ac9/HEARTBEAT.md`
- `/home/aa/vllm/paperclip-data/instances/default/companies/facae2e1-4110-4373-b4f2-3cbf7bd666ac/agents/c73df5fb-9c81-4be2-9e3c-81696ae46ac9/instructions/HEARTBEAT.md`
- `/home/aa/vllm/paperclip-data/instances/default/shared-memory/logs/scheduled_cycle.log`

## 7. 현재 남아 있는 한계와 리스크

### 7.1 신규 agent 즉시 반영 부재

지금은 cron cycle 기반이다.  
새 agent 채용 직후 즉시 patch되지는 않는다.

후속 작업 후보:

- agent 생성 API 이후 hook 추가
- hiring workflow 마지막 단계에서 patcher 직접 호출

### 7.2 agent별 지식 밀도 편차

agent 워크스페이스는 독립되어 있지만, 지식 밀도는 agent마다 많이 다르다.

예시:

- ROS2 Expert:
  - `memory/`는 존재
  - `life/`와 `docs/`는 최소 수준
  - `2026-04-24.md`는 거의 idle heartbeat 로그 위주
- Robot Research Agent:
  - `robot/research/` 트리가 두껍고
  - `summaries/`, `topics/`, `findings/`, `sources/`, `reports/`가 풍부함
  - 내부 markdown 링크도 존재해 Obsidian graph에 적합

즉 "독립 workspace"는 되어 있지만, "전문가별 충분한 지식 베이스"는 아직 아니다.

### 7.3 heartbeat noise

shared-memory 쪽은 어느 정도 noise filtering을 넣었지만, agent local `memory/YYYY-MM-DD.md`는 아직 idle heartbeat 반복이 많다.

특히 ROS2 Expert, Robot Research Agent는 idle/no-task 로그 비중이 높다.

## 8. agent별 지식 계층 현재 상태

### 8.1 ROS2 Expert

워크스페이스:

- `/home/aa/vllm/paperclip-data/instances/default/workspaces/b1805ca8-e756-4886-acac-140ff41ec116`

대표 파일:

- `memory/2026-04-23.md`
- `memory/2026-04-24.md`
- `life/resources/ros2/summary.md`
- `docs/research/ros2_versions/comparison.md`

판단:

- 독립 workspace는 존재
- 검색 가능
- 수정 가능
- 그러나 축적된 전문 문서량은 적음
- Obsidian graph를 띄울 수는 있지만 노드 수가 적어 분석 효용은 낮음

### 8.2 Robot Research Agent

워크스페이스:

- `/home/aa/vllm/paperclip-data/instances/default/workspaces/4d34f025-076d-4bc1-9776-c3da7646b44b`

대표 파일:

- `robot/research/plan.md`
- `robot/research/summaries/ros2_educational_overview.md`
- `robot/research/topics/robot_operating_system/ros_vs_ros2.md`
- `robot/research/findings/ros2/educational_use_cases/ros2_educational_benefits.md`
- `robot/research/sources/robotics_educational_resources_2026/sources_list.md`

판단:

- 가장 구조화된 지식 계층 보유
- 내부 markdown 링크가 실제로 연결돼 있음
- Obsidian graph/백링크 분석에 적합
- ROS2 관련 탐색은 실제로 이 agent 자료가 더 풍부함

### 8.3 CTO

워크스페이스:

- `/home/aa/vllm/paperclip-data/instances/default/workspaces/1a708d66-d586-4d88-81ca-f773c24115be`

특징:

- 메모리에는 운영 의사결정과 감독 로그가 많이 들어 있음
- agent 운영, hiring, fallback, blocking 분석 문서가 실무상 중요함
- 기술 지식 자체보다 orchestration 지식이 강함

## 9. Obsidian 시각화 가능성

가능하다. 다만 범위를 나눠서 보는 것이 좋다.

### 9.1 agent별 vault

예:

- ROS2 Expert workspace만 vault로 열기
- Robot Research Agent workspace만 vault로 열기

장점:

- 개별 전문가 지식 구조 파악이 쉬움

단점:

- cross-agent 연결은 약하게 보임

### 9.2 회사 전체 vault

권장 경로:

- `/home/aa/vllm/paperclip-data/instances/default/workspaces`

장점:

- 전체 agent 산출물과 cross-agent 검색이 쉬움
- shared-memory와 local memory의 관계를 함께 볼 수 있음

단점:

- link 규칙이 통일되지 않아 graph가 다소 지저분할 수 있음

현재 상태 요약:

- Robot Research Agent는 Obsidian 분석 가치 높음
- ROS2 Expert는 구조는 있으나 graph 밀도가 낮음

## 10. 이어서 할 일 우선순위

### 우선순위 1

신규 agent 생성 직후 즉시 patch되게 만들 것

후보:

- hiring workflow 후단에 `patch_agent_instructions.py` 직접 호출
- server/API hook 연결

### 우선순위 2

ROS2 Expert 지식 계층 강화

필수:

- `life/resources/ros2/summary.md` 확장
- `research/` 구조 생성
- `docs/`와 `life/`를 연결하는 링크 추가
- idle heartbeat 노이즈 정리

### 우선순위 3

Obsidian graph 친화적 링크 규칙 정리

권장:

- summary -> topic -> finding -> source 구조로 링크 통일
- agent별 `index.md` 추가
- 주요 디렉토리마다 landing note 생성

### 우선순위 4

shared-memory read path를 더 명확히 만들기

후보:

- `paperclip-shared-memory`를 별도 qmd collection으로 인덱싱
- shared-memory facts 요약 파일 간 링크 추가

## 11. 바로 재진입할 때 쓸 명령

### 11.1 원격 접속

```bash
ssh -i C:/Users/Administrator/.ssh/id_rsa -p 30000 -o PubkeyAcceptedAlgorithms=+ssh-rsa -o HostkeyAlgorithms=+ssh-rsa aa@182.229.102.180
```

### 11.2 shared-memory cycle 수동 실행

```bash
cd /home/aa/vllm
/bin/bash ./scripts/paperclip_shared_memory/run_shared_memory_cycle.sh
```

### 11.3 스케줄러 로그 확인

```bash
tail -n 40 /home/aa/vllm/paperclip-data/instances/default/shared-memory/logs/scheduled_cycle.log
```

### 11.4 instruction 반영 확인

```bash
grep -n "Shared Memory Runtime" /home/aa/vllm/paperclip-data/instances/default/workspaces/c73df5fb-9c81-4be2-9e3c-81696ae46ac9/AGENTS.md
grep -n "Shared Memory Recall" /home/aa/vllm/paperclip-data/instances/default/workspaces/c73df5fb-9c81-4be2-9e3c-81696ae46ac9/HEARTBEAT.md
```

### 11.5 ROS2 Expert 상태 확인

```bash
find /home/aa/vllm/paperclip-data/instances/default/workspaces/b1805ca8-e756-4886-acac-140ff41ec116 -maxdepth 3 -type f | sort
```

### 11.6 Robot Research Agent 지식 구조 확인

```bash
find /home/aa/vllm/paperclip-data/instances/default/workspaces/4d34f025-076d-4bc1-9776-c3da7646b44b/robot/research -maxdepth 3 -type f | sort
```

## 12. 핵심 결론

현재 상태를 한 줄로 요약하면 다음과 같다.

`shared-memory 인프라와 instruction 자동 재반영은 운영에 붙었고, agent workspace는 독립적이지만 전문가별 지식 밀도는 불균형하다.`

특히 후속 agent는 아래를 기억하면 된다.

- 메모리 계층 추가 자체는 끝났다.
- instruction 자동 반영도 cron 기준으로는 끝났다.
- 다음 병목은 "새 agent 즉시 반영"과 "얕은 전문가 지식 계층 보강"이다.
- ROS2 Expert보다 Robot Research Agent가 현재 ROS2/로보틱스 문서 자산이 더 풍부하다.
