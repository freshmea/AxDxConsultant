# kordoc mcp 설치

- 설치

```text
kordoc 이라고 하는 npm 패키지가 있다. 이것을 전역에서 실행될 수 있게 설치해줘


codex 에서 실행

C:\Users\Administrator\dxAx\docs\2. 블록체인 뱅킹 시스템 프로젝트_교육_한국융합인재교육협회.hwp
이 파일을 md 파일로 변경시켜줘

VsCdoe 에서 실행(copilot)

이 한글 문서를 md 파일로 변환해줘
두 한글파일을 비교해서 결과를 알려줘

```

- kordoc mcp 설정 파일 (.vscode/mcp.json)

```json
{
  "servers": {
    "kordoc": {
      "type": "stdio",
      "command": "cmd",
      "args": ["/c", "npx", "-y", "kordoc@latest", "mcp"]
    }
  }
}
```

- codex mcp 설정 파일 (.codex/config.toml)

```toml
[mcp_servers.kordoc]
command = "cmd"
args = ["/c", "npx", "-y", "kordoc@latest", "mcp"]

```

- 플랜모드 실습

```text

C:\Users\Administrator\dxAx\실습결과물\17\14 Marketing Campaigns.xlsx
이 엑셀 파일을 분석하려고 한다. polars 라이브러리를 써서 스크립트 파일을 만들고 통계 분석을 진행해줘
그다음에 필요한 머신러닝 기법을 skitlearn을 통해서 수행을 하고 seaborn을 통해서 그래프를 여러개 만들어줘
만들어진 자료들을 gpt 의 image 생성 기술을 써서 한장 짜리 infography 를 만들어주고 한페이지 분량의 보고서와 그림을 notion에
페이지를 작성해줘

---
