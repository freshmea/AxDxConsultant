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
