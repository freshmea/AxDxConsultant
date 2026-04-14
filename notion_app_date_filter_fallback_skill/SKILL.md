# Notion App Date Filter Fallback Skill

## 목적
Notion 앱 연동에서 데이터소스 SQL 도구(`notion-query-data-sources`)가 비활성일 때,
`기간` 같은 날짜 속성 기준으로 업무를 정확하게 추출한다.

## 사용 시점
- 사용자가 "특정 날짜(예: 2026-03-31) 업무 리스트"를 요청함
- 대상이 Notion 데이터베이스/데이터소스 기반 업무 테이블임
- SQL 쿼리 도구가 에러(`Tool ... not found`) 또는 비활성 상태임

## 입력값
- `target_date`: 조회 기준일 (`YYYY-MM-DD`)
- `database_id` 또는 데이터베이스 URL
- `date_property_name`: 기본 `기간`
- (선택) 담당자/키워드 힌트

## 핵심 전략
1. 데이터베이스에서 데이터소스 URL(`collection://...`)을 먼저 확보한다.
2. 검색 API로 후보 페이지를 넓게 수집한다.
3. 후보 페이지를 개별 `fetch`로 열어 `date:{속성}:start/end`를 직접 확인한다.
4. 날짜 일치 규칙으로 최종 결과만 남긴다.

## 날짜 일치 규칙
- 단일 날짜: `date:start == target_date`
- 기간 범위: `date:start <= target_date <= date:end`
- `date:end`가 없으면 단일 날짜로 처리

## 표준 절차
### 1) 데이터소스 찾기
- `notion_fetch(database_id)` 실행
- `<data-source url="collection://...">` 값 저장

### 2) 후보 검색 (병렬 권장)
아래 쿼리를 데이터소스 범위로 실행:
- `YYYY-MM-DD` (예: `2026-03-31`)
- `M월 D일` (예: `3월 31`)
- 업무 키워드 (예: `sojt`, `ICT`, `DX/AX`, `업무`)

중복 페이지 ID는 하나로 합친다.

### 3) 후보 페이지 속성 검증
- 각 페이지에 `notion_fetch(page_id)` 실행
- `<properties>`에서 아래 키 추출:
  - `date:{date_property_name}:start`
  - `date:{date_property_name}:end` (있으면)
  - `Done`
  - `시간`
  - `이름`
  - `url`

### 4) 필터 적용
- 날짜 일치 규칙으로 포함/제외 결정
- 포함된 결과를 제목 기준 정렬

### 5) 응답 포맷
각 항목을 다음 형식으로 출력:
- 이름
- 기간(start~end)
- 시간(있으면)
- 완료 여부(Done)
- 링크(url)

## 실패/예외 처리
- SQL 도구 호출 시 `Tool ... not found`면 즉시 fallback 절차로 전환
- 검색 결과가 0건이어도 "후보 0건"과 사용한 검색 조건을 명시
- 후보는 있으나 날짜 불일치면 "검증 결과 불일치"로 명확히 안내
- 시간대 혼선 방지를 위해 날짜는 항상 `YYYY-MM-DD`로 고정

## 품질 체크리스트
- 데이터소스 URL 확인 완료
- 후보 검색 쿼리 최소 3종 실행
- 후보 페이지 속성 직접 검증 완료
- 중복 제거 완료
- 날짜 일치 규칙 적용 완료
- 최종 건수와 항목 링크 제공 완료

## 예시 요약 문장
- "SQL 도구가 비활성이라 검색 기반 후보 수집 후 페이지 속성(`date:기간:start/end`)을 직접 검증해 결과를 확정했습니다."

## 주의사항
- 검색 결과의 `timestamp`(생성/수정 시각)를 기간 속성으로 오해하지 않는다.
- 본문 텍스트 매칭만으로 확정하지 않는다. 반드시 `<properties>`의 날짜 속성으로 검증한다.
- 민감정보(토큰/비밀번호/카드/연락처)는 출력하지 않는다.
