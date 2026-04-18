# Graphify 통합 실행안

## 목표

현재 `dxAx` 시스템을 유지하면서, Graphify의 강점인 다음 4가지를 흡수한다.

- `tree-sitter` 기반 코드 구조 추출
- confidence 라벨(`EXTRACTED`, `INFERRED`, `AMBIGUOUS`)
- graph query / path / explain 류의 탐색
- 파일 해시 기반 증분 업데이트

즉 최종 목표는 **기존 wiki/memory/search 시스템 위에 Graphify식 구조 추출 계층을 추가하는 것**이다.

## 최종 구조

통합 후 구조는 아래 5층으로 본다.

1. `raw corpus`
   - markdown
   - code
   - pdf/docx/xlsx
   - 필요 시 transcript

2. `deterministic graph layer`
   - 코드 AST 추출
   - 링크/참조/호출/상속 관계
   - confidence 라벨

3. `wiki knowledge layer`
   - page index
   - link graph
   - structure index
   - community summaries

4. `semantic + routing layer`
   - FAISS
   - query reranking
   - graph-first read plan

5. `change-aware memory layer`
   - Mem0
   - Qdrant
   - 운영 사실

## 구현 원칙

- 기존 `llm_wiki/indexer.py`는 유지한다.
- Graphify 전체를 그대로 이식하지 않고, 필요한 기능만 흡수한다.
- 현재 산출물 체계(`wiki/system/*.json`, `wiki/index.md`, `wiki/log.md`)를 깨지 않는다.
- 새 구조 추출 결과는 처음에는 별도 파일로 저장하고, 안정화 후 기존 query 흐름에 합친다.

## 1단계: 구조 추출 계층 추가

### 추가할 파일

- `llm_wiki/code_graph.py`
- `llm_wiki/code_extractors.py`
- `llm_wiki/code_cache.py`

### 역할

`code_graph.py`
- 코드 파일 수집
- tree-sitter 디스패치
- 노드/엣지 병합
- `wiki/system/code_graph.json` 출력

`code_extractors.py`
- 언어별 extractor
- 최소 지원 언어:
  - Python
  - JavaScript / TypeScript
  - PowerShell
- 추출 관계:
  - `defines`
  - `imports`
  - `calls`
  - `inherits`

`code_cache.py`
- 파일별 SHA256 해시 캐시
- 변경되지 않은 파일은 재추출 생략

### 1단계 산출물

- `wiki/system/code_graph.json`
- `wiki/system/code_graph_meta.json`

## 2단계: confidence 라벨 도입

현재 시스템은 링크와 community는 있지만 relation confidence 개념이 없다. 이를 추가한다.

### 규칙

- `EXTRACTED`
  - 코드 AST에서 직접 확인된 관계
  - markdown 링크에서 직접 확인된 관계

- `INFERRED`
  - path token / 공존 / neighborhood 확장으로 추정된 관계

- `AMBIGUOUS`
  - 이름이 겹치거나 대상 결정이 불안정한 관계

### 적용 위치

- `code_graph.json`의 edge
- 필요 시 `link_graph.json` 확장판

## 3단계: graph query CLI 추가

### `llm_wiki/cli.py`에 추가할 명령

- `graph-query`
- `graph-path`
- `graph-neighbors`
- `graph-explain`

### 기능

`graph-query`
- 키워드로 node 후보 검색

`graph-path`
- 두 node 간 shortest path 또는 bounded path 탐색

`graph-neighbors`
- 특정 node 주변 edge/neighbor 출력

`graph-explain`
- 특정 node의 source, relation, community, confidence를 설명

### 이유

현재 `ask`는 문서 reranking에는 좋지만, “A와 B가 어떻게 연결되는가” 같은 구조 질문에는 약하다. 이 부분을 Graphify식 query로 보완한다.

## 4단계: query routing에 code graph 반영

현재 `score_pages()`는 문서 메타데이터 중심이다. 여기에 code graph 신호를 넣는다.

### 추가 신호

- node label match
- code neighbor bonus
- call path bonus
- shared community bonus

### 기대 효과

- 코드 질문일 때 markdown 문서보다 실제 코드 구조를 우선 제시
- 문서 질문일 때 기존 wiki 흐름 유지

## 5단계: 리포트 확장

기존 `graph_report.md`에 아래 항목을 추가한다.

- God Nodes
- Surprising Connections
- Code Communities
- Confidence Breakdown
- Suggested Questions

즉 현재 human-readable report를 Graphify 수준으로 확장한다.

## 6단계: 멀티모달은 별도 2차 확장

PDF/영상/이미지 ingest는 당장 1차 구현 범위에 넣지 않는다. 이유는 현재 시스템의 핵심 병목이 먼저 코드 구조 추출 부재이기 때문이다.

우선순위는 아래와 같다.

1. 코드 AST
2. graph query
3. 증분 캐시
4. 리포트 확장
5. 이후 transcript / pdf/docx/xlsx

## 권장 라이브러리

### 즉시 도입

- `networkx`
- `tree-sitter`
- `tree-sitter-python`
- `tree-sitter-javascript`
- `tree-sitter-typescript`
- `tree-sitter-powershell`

### 선택 도입

- `graspologic`
  - Leiden 필요 시
- `watchdog`
  - watch/update 모드 필요 시

### 유지

- `sentence-transformers`
- `faiss-cpu`
- `mem0ai[nlp]`
- `ollama`
- `requests`

## 구현 순서

### Phase 1

- `code_graph.py`
- Python extractor
- `code_graph.json` 생성

### Phase 2

- JS/TS/PowerShell extractor
- confidence 라벨
- file hash cache

### Phase 3

- `graph-query`, `graph-path`, `graph-neighbors`, `graph-explain`
- `graph_report.md` 확장

### Phase 4

- `ask`에 code graph signal 결합
- `query_cache.json` 확장

## 완료 기준

다음이 되면 통합 성공으로 본다.

- 코드 질문 시 `ask`가 관련 코드 구조와 문서를 함께 제시
- `graph-path`로 함수/모듈 간 연결 경로를 보여줄 수 있음
- 변경 없는 파일은 재추출하지 않음
- `graph_report.md`에 god nodes / surprising connections가 포함됨
- 기존 `memory-search`와 semantic retrieval는 그대로 동작함

## 최종 판단의 실행 의미

`14. 최종 판단`을 실제 작업으로 바꾸면, 해야 할 일은 “Graphify로 갈아타기”가 아니다. 정확히는 다음이다.

**현재 시스템을 유지한 채, Graphify의 extractor/graph-query/cache 레이어만 흡수해 `문서형 지식 시스템 + 구조형 코드 그래프 시스템`으로 업그레이드한다.**
