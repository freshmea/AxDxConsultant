---
name: local-llm-stack-setup
description: "Bring up or repair the local AI workspace stack in this repository. Use when Codex needs to verify the knowledge wiki environment, Mem0 and Ollama prerequisites, ComfyUI local setup, or the local Whisper GPU path before practical work starts."
---

# Local LLM Stack Setup

Use this skill to get the repository into a runnable local-AI state before task work starts.

## Scope

This skill is the entry point for the combined local stack in this workspace:

- wiki and retrieval in `.venv-knowledge`
- Mem0 and Ollama prerequisites for change-aware memory
- local Whisper GPU speech-to-text in `.venv-whisper`
- ComfyUI local image workflow in `.venv-comfyui`

For deeper repairs, hand off to the more specific docs:

- `../wiki-llm-setup/SKILL.md`
- `../local-whisper-gpu/SKILL.md`
- `../troubleshooting.md`
- `../../docs/comfyui-setup.md`

## 1. Confirm the expected layout

Expect these paths to exist:

- `.venv-knowledge/`
- `.venv-whisper/`
- `.venv-comfyui/`
- `llm_wiki/README.md`
- `memory_layer/mem0_config.json`
- `local_whisper/`
- `scripts/comfyui/`
- `docs/comfyui-setup.md`

If one of these is missing, do not assume the stack is healthy.

## 2. Verify the wiki environment first

Run:

```powershell
.\.venv-knowledge\Scripts\python.exe -V
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli build --root . --render-graph
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli ask "workspace setup status" --root . --limit 5
```

If build or ask fails, use `../wiki-llm-setup/SKILL.md` as the primary repair workflow.

## 3. Verify the memory prerequisites

Run:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-check --root .
```

Healthy local model expectations:

- `nomic-embed-text`
- `qwen2.5:1.5b`

If local Qdrant or Ollama is unstable, consult `../troubleshooting.md` before running bootstrap commands repeatedly.

## 4. Verify Whisper only with GPU intent

Run:

```powershell
.\.venv-whisper\Scripts\python.exe -c "import ctranslate2; print(ctranslate2.get_cuda_device_count())"
```

If CUDA is not visible or the scripts fall back to CPU, switch to `../local-whisper-gpu/SKILL.md` and repair that stack directly.

## 5. Verify ComfyUI control scripts

Use the repository scripts, not ad hoc commands:

```powershell
.\scripts\comfyui\status.ps1
```

If ComfyUI setup or model paths need repair, read `../../docs/comfyui-setup.md` before changing scripts.

## 6. Startup order

When the user says they want to "start" or "bring up the local stack", prefer this order:

1. verify `.venv-knowledge`
2. verify wiki build and `ask`
3. verify `memory-check`
4. verify Whisper GPU only if STT work is needed
5. verify ComfyUI only if image workflow is needed

## 7. Repair rule

Do not make broad environment claims from one successful command.

Treat the stack as healthy only when the relevant subsystem command actually passes for the requested workflow.
