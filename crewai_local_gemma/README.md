# crewai-local-gemma

CrewAI에서 로컬 llama.cpp Gemma 엔드포인트를 호출하는 YAML 기반 실습 프로젝트입니다.
기본 시나리오는 두 에이전트가 순차로 협업합니다.

1. `코드작성자`가 할인 가격 계산 함수를 작성합니다.
2. `코드검증자`가 작성된 코드를 테스트 관점으로 검토합니다.

## 실행

```powershell
uv run crewai-local-gemma
```

실행 결과는 `출력/위임_코드_테스트_결과.md`에 저장됩니다.
중간 산출물은 `출력/작성된_코드.md`, `출력/테스트_검토_보고서.md`에 저장됩니다.

템플릿 입력이 필요한 YAML을 만들면 다음처럼 값을 넘길 수 있습니다.

```powershell
uv run crewai-local-gemma --input 주제="로컬 엘엘엠 점검"
```

## YAML 구조

기본 설정 파일은 `config/` 아래에 있습니다.

- `agents.yaml`: 재사용할 에이전트 정의
- `tasks.yaml`: 각 작업과 담당 에이전트 연결
- `crew.yaml`: 실행 순서, 프로세스, 최종 출력 파일 정의

이 프로젝트의 YAML 로더는 값으로 `예`, `아니오`, `순차`, `계층`을 사용할 수 있습니다.
그래서 설정값도 한국어 중심으로 작성할 수 있습니다.

```yaml
agents:
  코드작성자:
    role: 파이썬 코드 작성 에이전트
    goal: 할인 가격 계산 함수를 안전한 파이썬 코드로 작성한다.
    backstory: 작은 업무 자동화 함수를 명확하게 작성하는 개발자다.
    verbose: 예
    allow_delegation: 예
```

```yaml
tasks:
  코드작성:
    description: 할인 가격을 계산하는 파이썬 함수를 작성하라.
    expected_output: 한국어 마크다운 문서.
    agent: 코드작성자
    markdown: 예
```

```yaml
crew:
  name: 코드_작성_검증_위임_시나리오
  process: 순차
  verbose: 예
  memory: 아니오
  agents:
    - 코드작성자
  tasks:
    - 코드작성
```

다른 YAML 파일을 사용할 수도 있습니다.

```powershell
uv run crewai-local-gemma `
  --agents-config config/agents.yaml `
  --tasks-config config/tasks.yaml `
  --crew-config config/crew.yaml
```

## 로컬 엘엘엠 설정

프로젝트 루트의 `.env`를 읽습니다. 예시는 `.env.example`에 있습니다.

```text
LLM_BASE_URL=http://182.229.102.180:30003/v1
LLM_PROVIDER=openai
LLM_MODEL=gemma-4-26b-a4b-it
LLM_API_KEY=llamacpp
LLM_MAX_TOKENS=4096
```

현재 CrewAI에서는 사용자 지정 llama.cpp 모델을 `LLM_PROVIDER=openai`와
`LLM_MODEL=gemma-4-26b-a4b-it`처럼 provider와 model을 분리해 넘깁니다.
