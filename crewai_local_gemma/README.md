# crewai-local-gemma

Minimal CrewAI smoke test that calls a llama.cpp OpenAI-compatible endpoint running Gemma.

## Run

```powershell
uv run crewai-local-gemma
```

The run writes the final Korean response to `output/smoke_result.md`.

You can also provide template inputs used by YAML strings:

```powershell
uv run crewai-local-gemma --input topic="로컬 LLM 점검"
```

## YAML Structure

Default config files live under `config/`:

- `agents.yaml` defines reusable agents.
- `tasks.yaml` defines tasks and maps each task to an agent by name.
- `crew.yaml` selects the process, execution order, and final output file.

Minimal shape:

```yaml
# config/agents.yaml
agents:
  analyst:
    role: Analyst
    goal: Analyze {topic}
    backstory: Works with the local Gemma model.
    verbose: true
    allow_delegation: false
    max_iter: 1
```

```yaml
# config/tasks.yaml
tasks:
  report:
    description: Write a Korean report about {topic}.
    expected_output: Korean markdown.
    agent: analyst
    markdown: true
```

```yaml
# config/crew.yaml
crew:
  name: local_gemma_crew
  process: sequential
  verbose: true
  memory: false
  output_file: output/smoke_result.md
  agents:
    - analyst
  tasks:
    - report
```

Custom config paths:

```powershell
uv run crewai-local-gemma `
  --agents-config config/agents.yaml `
  --tasks-config config/tasks.yaml `
  --crew-config config/crew.yaml
```

## Local LLM Configuration

The project reads `.env` from the project root:

```text
LLM_BASE_URL=http://182.229.102.180:30003/v1
LLM_PROVIDER=openai
LLM_MODEL=gemma-4-26b-a4b-it
LLM_API_KEY=llamacpp
```

Current CrewAI native OpenAI routing accepts the custom llama.cpp model when the
provider is set separately as `openai`. The code also tolerates an
`openai/gemma-4-26b-a4b-it` value by stripping that prefix before constructing
the LLM.
