# Graphify와 현재 dxAx 시스템 비교 분석

## 분석 기준

이 문서는 다음 두 대상을 코드와 라이브러리 수준에서 비교한다.

- Graphify 공식 저장소: `https://github.com/safishamsi/graphify`
- 현재 저장소의 지식 시스템: `llm_wiki/`, `wiki/system/`, `memory_layer/`

Graphify는 로컬에 클론해 `pyproject.toml`, `ARCHITECTURE.md`, `graphify/*.py`를 직접 읽고 비교했다.

## 결론 요약

현재 시스템은 **markdown 중심 LLM Wiki + GraphRAG-lite + FAISS 의미검색 + Mem0/Qdrant 메모리** 구조다. Graphify는 **결정적 AST 추출 + 멀티모달 semantic extraction + NetworkX 그래프 분석 + Leiden/Louvain 커뮤니티 탐지 + 파일 단위 SHA256 캐시** 구조다.

핵심 차이는 다음이다.

- Graphify는 **구조 추출기**가 강하다.
- 현재 시스템은 **문서 라우터와 장기 메모리 계층**이 강하다.
- Graphify는 **코드베이스/멀티모달 그래프 생성 도구**에 가깝다.
- 현재 시스템은 **지식 위키와 질문 라우팅 시스템**에 가깝다.

따라서 가장 좋은 방향은 둘 중 하나를 버리는 것이 아니라, **현재 시스템 앞단에 Graphify식 extractor와 graph query를 붙이는 것**이다.

## 1. Graphify의 실제 코드 구조

`ARCHITECTURE.md` 기준 파이프라인은 아래와 같다.

```text
detect() -> extract() -> build_graph() -> cluster() -> analyze() -> report() -> export()
```

실제 모듈은 다음처럼 분리되어 있다.

- `graphify/detect.py`
- `graphify/extract.py`
- `graphify/build.py`
- `graphify/cluster.py`
- `graphify/analyze.py`
- `graphify/report.py`
- `graphify/export.py`
- `graphify/cache.py`
- `graphify/transcribe.py`
- `graphify/wiki.py`
- `graphify/benchmark.py`
- `graphify/serve.py`
- `graphify/__main__.py`

이 구조는 비교적 명확하다. 각 단계가 독립 함수/독립 파일로 나뉘어 있고, 공유 상태 없이 dict와 NetworkX graph로 넘긴다.

## 2. Graphify의 주요 라이브러리

`pyproject.toml` 기준 핵심 의존성은 다음이다.

### 기본 의존성

- `networkx`
- `tree-sitter>=0.23.0`
- `tree-sitter-python`
- `tree-sitter-javascript`
- `tree-sitter-typescript`
- `tree-sitter-go`
- `tree-sitter-rust`
- `tree-sitter-java`
- `tree-sitter-c`
- `tree-sitter-cpp`
- `tree-sitter-ruby`
- `tree-sitter-c-sharp`
- `tree-sitter-kotlin`
- `tree-sitter-scala`
- `tree-sitter-php`
- `tree-sitter-swift`
- `tree-sitter-lua`
- `tree-sitter-zig`
- `tree-sitter-powershell`
- `tree-sitter-elixir`
- `tree-sitter-objc`
- `tree-sitter-julia`
- `tree-sitter-verilog`

### 선택 의존성

- `graspologic` 또는 NetworkX Louvain fallback
- `pypdf`, `html2text`
- `python-docx`, `openpyxl`
- `faster-whisper`, `yt-dlp`
- `watchdog`
- `matplotlib`
- `neo4j`
- `mcp`

즉 Graphify는 **AST 파싱 + 그래프 분석 + 멀티모달 변환 + 시각화 + MCP 서빙**까지 한 패키지에 넣은 형태다.

## 3. 현재 시스템의 실제 코드 구조

현재 시스템은 Graphify처럼 extractor 중심이 아니라 wiki builder 중심이다.

핵심 파일은 다음과 같다.

- `llm_wiki/indexer.py`
- `llm_wiki/community.py`
- `llm_wiki/semantic.py`
- `llm_wiki/obsidian_bridge.py`
- `llm_wiki/memory_layer.py`
- `llm_wiki/cli.py`

역할은 다음과 같이 나뉜다.

- `indexer.py`: markdown 수집, 제목/요약/헤딩/태그/토픽/엔터티 추출, 링크 그래프 생성
- `community.py`: community graph, summaries 생성
- `semantic.py`: `sentence-transformers + faiss` 기반 의미검색 인덱스 생성
- `memory_layer.py`: `Mem0 + Ollama + Qdrant` 기반 운영 사실 메모리
- `cli.py`: build / ask / route / memory-* 워크플로우

즉 현재 시스템은 **문서에서 구조화된 메타데이터를 뽑아 검색 가능한 위키 계층을 만드는 코드**다.

## 4. Graphify의 추출 방식 vs 현재 시스템의 추출 방식

### Graphify

Graphify의 `extract.py`는 구조적으로 강하다.

- `LanguageConfig`로 언어별 tree-sitter 파서 설정
- import/call/inherit/use 관계를 AST에서 직접 추출
- `EXTRACTED`, `INFERRED`, `AMBIGUOUS` confidence 라벨 부여
- JS, Python, Java, C/C++, C#, Kotlin, Scala, PHP 등 언어별 import handler 구현
- 함수 이름 정규화와 stable node id 생성

즉 Graphify는 **코드 구조를 결정적으로 파싱**한다. 이 부분은 LLM을 안 쓴다.

### 현재 시스템

현재 `indexer.py`는 markdown 기반 메타데이터 추출이다.

- `WIKI_LINK_RE`, `MD_LINK_RE`로 링크 파싱
- 제목/요약/헤딩/태그/토픽/엔터티를 규칙 기반 추출
- `normalize_page_id()`로 문서 ID 생성
- `extract_summary()`, `extract_topics()`, `extract_entities()`로 검색용 요약 필드 생성

즉 현재 시스템은 **코드 AST 추출기**가 아니라 **문서 인덱서**다.

### 비교 판단

- 코드 구조 이해: Graphify 우세
- markdown corpus 탐색: 현재 시스템 우세
- “왜 이런 구조인가”를 문서+코드+이미지 섞어서 그래프로 보는 것: Graphify 우세
- markdown 지식베이스를 지속적으로 운영하는 것: 현재 시스템 우세

## 5. Graphify의 캐시 전략 vs 현재 시스템의 캐시 전략

### Graphify

`cache.py` 기준:

- 파일 단위 SHA256 캐시
- markdown는 YAML frontmatter를 해시에서 제외
- `graphify-out/cache/{hash}.json` 저장
- semantic extraction 결과도 `source_file` 기준으로 파일별 캐시
- 변경되지 않은 파일은 재처리 생략

이 구조는 **증분 업데이트**에 강하다.

### 현재 시스템

현재 시스템도 결과물 캐시는 있다.

- `wiki/system/page_index.json`
- `query_cache.json`
- `community_summaries.json`
- `semantic_index.faiss`
- `obsidian_semantic_cache.json`

하지만 현재 구현은 Graphify처럼 **개별 파일 hash 기반 증분 빌드**는 약하다. 빌드 단위는 상대적으로 더 거칠고, “변경된 파일만 재추출”보다는 전체 위키 재생성에 가깝다.

### 비교 판단

- 증분 리빌드 정교함: Graphify 우세
- 장기 검색 아티팩트 축적: 현재 시스템 우세

## 6. Graphify의 그래프 분석 vs 현재 시스템의 그래프 분석

### Graphify

`analyze.py`는 다음 개념을 명시적으로 계산한다.

- `god_nodes()`
- `surprising_connections()`
- cross-file surprise scoring
- cross-community surprising edges
- confidence-aware surprise ranking

즉 단순 연결 수뿐 아니라, “왜 이 연결이 놀라운가”를 설명한다.

`cluster.py`는 다음을 수행한다.

- `graspologic.partition.leiden()` 우선
- 없으면 `networkx.community.louvain_communities()` fallback
- oversized community split
- cohesion score 계산

즉 Graphify는 **그래프 분석 자체가 1급 기능**이다.

### 현재 시스템

현재 시스템의 `community.py`는 비교적 단순하다.

- `networkx.algorithms.community.greedy_modularity_communities()` 또는 fallback
- representative page 선정
- top_tags / top_topics / top_entities 계산
- community summary 문장 생성

즉 현재 시스템도 community를 만들지만, Graphify처럼:

- god node
- surprising connection
- confidence-based relation analysis
- graph-query-first explanation

까지는 가지 않는다.

### 비교 판단

- topology 분석 깊이: Graphify 우세
- community-level human summary: 현재 시스템 우세

## 7. Graphify의 의미 처리 vs 현재 시스템의 의미 처리

### Graphify

Graphify는 README 기준으로 semantic similarity도 그래프 엣지로 넣는다. 중요한 점은:

- 별도 embedding/vector DB가 필수 아님
- semantic edge 자체를 그래프에 넣고
- Leiden이 그 topology를 기반으로 군집화

즉 “embedding retrieval”보다 “semantic relation을 graph edge로 편입”하는 접근이다.

### 현재 시스템

현재 시스템은 `semantic.py`에서 명시적으로 embedding 기반 검색을 쓴다.

- `sentence-transformers/all-MiniLM-L6-v2`
- `faiss.IndexFlatIP`
- page 단위 normalized embedding 저장
- 질의시 semantic bonus를 score에 합산

즉 현재 시스템은 전형적인 **vector retrieval + graph reranking 하이브리드**다.

### 비교 판단

- semantic edge를 그래프 자체로 녹여내는 방식: Graphify 우세
- 범용 semantic retrieval 안정성: 현재 시스템 우세

## 8. Graphify의 멀티모달 처리 vs 현재 시스템의 멀티모달 처리

### Graphify

`detect.py`와 `transcribe.py` 기준:

- PDF: `pypdf`
- DOCX: `python-docx`
- XLSX: `openpyxl`
- Video/Audio: `faster-whisper`
- URL media download: `yt-dlp`
- 이미지도 semantic extraction 대상으로 포함

즉 Graphify는 멀티모달을 기본 설계에 넣었다.

### 현재 시스템

현재 시스템은 사실상 markdown 중심이다.

- markdown 파일 위키화
- Obsidian Smart Connections cache 연동
- 별도 PDF/영상/이미지 ingest 파이프라인은 없음

다만 skill 목록에 `pdf`, `doc` 스킬은 있지만, 이 시스템 자체의 자동 인덱서에는 아직 깊게 결합되지 않았다.

### 비교 판단

- 멀티모달 ingest: Graphify 우세
- markdown wiki 운영: 현재 시스템 우세

## 9. Graphify의 질의 인터페이스 vs 현재 시스템의 질의 인터페이스

### Graphify

README와 `serve.py`/`benchmark.py` 구조상 Graphify는 다음 질의를 전제로 한다.

- query
- path
- explain
- shortest path
- get neighbors
- MCP server exposing graph access
- BFS depth-based subgraph token estimation

특히 `benchmark.py`는 질의 토큰을 이렇게 계산한다.

- 질문 terms로 node label 스코어링
- top start nodes 선택
- BFS depth 3 확장
- visited nodes + traversed edges를 작은 context block으로 구성
- 그 토큰 수를 전체 corpus 토큰과 비교

즉 Graphify의 토큰 절감 주장은 **“LLM이 읽을 context를 BFS subgraph로 축소한다”**는 구조에서 나온다.

### 현재 시스템

현재 시스템의 `cli.py`는 다음 흐름이다.

- `route`
- `ask`
- `memory-search`

`score_pages()`는 다음 신호를 혼합한다.

- lexical
- title/headings/tags/topics/entities
- semantic bonus
- community bonus
- inbound bonus
- obsidian-related bonus

즉 현재 시스템은 **랭킹 기반 read plan 생성기**다. Graphify처럼 path query나 graph traversal query가 전면에 있지는 않다.

### 비교 판단

- precise graph traversal UX: Graphify 우세
- ranked document routing: 현재 시스템 우세

## 10. Graphify의 위키 export vs 현재 시스템의 위키 export

### Graphify

`wiki.py`는 graph에서 wiki를 만든다.

- `index.md`
- community article
- god node article
- cross-community links
- audit trail

즉 그래프가 원천이고, 위키는 그래프에서 파생된다.

### 현재 시스템

현재 시스템은 반대다.

- raw markdown가 원천
- 위키/인덱스/그래프는 raw markdown에서 파생

즉 두 시스템은 방향이 반대다.

- Graphify: `corpus -> graph -> wiki`
- 현재 시스템: `markdown corpus -> wiki metadata + graph + semantic index`

이 차이는 매우 중요하다.

## 11. 메모리 계층 비교

### Graphify

Graphify 자체는 persistent graph는 있지만, 현재 저장소 기준으로 Mem0/Qdrant 같은 long-term operational memory 계층은 없다. persistent artifact는 주로:

- `graph.json`
- `GRAPH_REPORT.md`
- `graph.html`
- `cache/`

이다.

### 현재 시스템

현재 시스템은 `memory_layer.py`와 `memory_layer/README.md` 기준으로:

- `Mem0`
- `Ollama`
- `local Qdrant`
- `history.db`

를 쓰고, setup state / tool install state / recent operational changes를 따로 저장한다.

### 비교 판단

- 장기 운영 기억: 현재 시스템 우세
- 구조화된 지식 그래프 persistence: Graphify 우세

## 12. 토큰 절감 주장에 대한 코드 수준 평가

Graphify README는 71.5x 감소를 전면에 둔다. 코드 기준으로 보면 이 수치는 **보장치**가 아니라 `benchmark.py`의 근사 계산에 가깝다.

Graphify의 benchmark는:

- corpus_words -> corpus_tokens 근사
- query subgraph tokens BFS로 근사
- 샘플 질문 기준 reduction ratio 계산

즉 마케팅 문구로 보는 것이 안전하고, “항상 71.5배”로 받아들이면 안 된다.

반면 현재 시스템은 `cli.py`의 `token_budget`에서:

- full corpus estimate
- targeted read estimate
- saved_estimate
- savings_ratio

를 직접 남긴다. 이 값도 근사치지만, 실제 read plan 기반이라 현재 저장소 상황에 더 밀착되어 있다.

따라서 토큰 절감 측정의 성격은 다음과 같다.

- Graphify: BFS subgraph 중심의 구조 기반 절감 추정
- 현재 시스템: reranked page subset 중심의 문서 기반 절감 추정

## 13. 현재 시스템에 Graphify를 도입한다면

가장 좋은 결합 방식은 아래와 같다.

### 도입 가치가 큰 부분

1. `tree-sitter` 기반 코드 extractor
2. `EXTRACTED / INFERRED / AMBIGUOUS` confidence 태그
3. `god nodes`, `surprising connections`
4. `graph query / path / explain`
5. 파일 hash 기반 증분 업데이트
6. `faster-whisper` 기반 영상 transcript ingest

### 그대로 가져오지 않는 것이 좋은 부분

1. Graphify의 semantic layer를 현재 시스템의 FAISS 대신 완전히 대체하는 것
2. 현재 Mem0/Qdrant 메모리 계층을 없애는 것
3. markdown-first 위키 운영을 포기하는 것

즉 Graphify는 **extractor/graph-query front-end**로 들여오고, 현재 시스템은 **wiki/memory/search back-end**로 유지하는 게 좋다.

## 14. 최종 판단

Graphify는 코드상으로 보면 단순 “그래프 시각화 도구”가 아니다. 실제로는:

- `tree-sitter` 기반 구조 추출기
- `NetworkX` 기반 그래프 조립기
- `Leiden/Louvain` 기반 군집화기
- `faster-whisper` 기반 전사기
- `pypdf/python-docx/openpyxl` 기반 문서 변환기
- `MCP` 서버와 wiki exporter를 가진 graph runtime

에 가깝다.

반면 현재 `dxAx` 시스템은:

- markdown corpus 인덱서
- GraphRAG-lite community summarizer
- `sentence-transformers + FAISS` retrieval layer
- `Mem0 + Qdrant` operational memory layer
- query routing CLI

를 가진 지식 운영 시스템이다.

그래서 두 시스템의 위치는 다르다.

- Graphify: **구조를 만들어 주는 엔진**
- 현재 시스템: **지식을 운영하고 질의 라우팅하는 엔진**

가장 합리적인 결론은 다음 한 줄로 정리된다.

**현재 시스템은 Graphify로 대체할 대상이 아니라, Graphify식 extractor와 graph query를 흡수해 더 강해질 수 있는 기반 시스템이다.**
