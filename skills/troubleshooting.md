# Troubleshooting

This note covers setup problems already encountered in this workspace while building the wiki LLM, semantic retrieval, Mem0 memory, and the local Whisper stack.

## Wiki LLM

### Unresolved links caused by `%20`

Symptom:

- markdown links such as `./file%20name.md` appear unresolved

Cause:

- the indexer treated the href as a raw path instead of a URL-decoded local file path

Fix:

- decode markdown hrefs before resolving local files
- rebuild with `.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli build --root . --render-graph`

### Unresolved links to `wiki/` generated files

Symptom:

- links to `../../wiki/index.md` or `../../wiki/log.md` remain unresolved

Cause:

- `wiki/` is intentionally excluded by `.llmwikiignore`, so generated files are not part of the corpus graph

Fix:

- keep those references as plain-text guidance instead of graph links
- or remove `wiki/` from `.llmwikiignore` if you intentionally want generated files indexed

### Obsidian graph still shows excluded folders

Symptom:

- folders hidden by `.llmwikiignore` still appear in Obsidian graph view

Cause:

- `.llmwikiignore` only affects the custom wiki builder, not Obsidian

Fix:

- update `.obsidian/graph.json`
- set `search` with negative `path:` filters
- reload Obsidian after saving

### Semantic search artifacts are missing

Symptom:

- `ask` works, but `semantic_hits` is empty and `wiki/system/semantic_index.faiss` does not exist

Cause:

- `sentence-transformers` or `faiss-cpu` is missing in `.venv-knowledge`

Fix:

```powershell
.\.venv-knowledge\Scripts\python.exe -m pip install sentence-transformers faiss-cpu
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli build --root . --render-graph
```

### Community summaries are missing

Symptom:

- `wiki/system/community_summaries.json` is absent or `community_count` is `0`

Cause:

- `networkx` is missing or the build did not complete

Fix:

```powershell
.\.venv-knowledge\Scripts\python.exe -m pip install networkx
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli build --root . --render-graph
```

### PowerShell shows broken Korean text

Symptom:

- Korean text appears as mojibake in terminal output

Cause:

- PowerShell is using a legacy code page such as `cp949`

Fix:

- prefer reading files as UTF-8 in Python
- set `$env:PYTHONUTF8='1'` before validation scripts when needed
- treat terminal display corruption separately from actual file corruption

## Mem0 And Local Memory

### `memory-check` cannot see Ollama models

Symptom:

- `memory-check` fails or returns an empty model list

Cause:

- Ollama is not running
- the required models were not pulled

Fix:

```powershell
ollama serve
ollama pull nomic-embed-text
ollama pull qwen2.5:1.5b
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli memory-check --root .
```

### `memory-add` fails with embedding dimension mismatch

Symptom:

- error similar to `shapes (0,1536) and (768,) not aligned`

Cause:

- the local Qdrant collection was created with the wrong embedding dimension

Fix:

- set `"embedding_model_dims": 768` in `memory_layer/mem0_config.json`
- delete stale local memory data
- bootstrap again

Typical reset targets:

- `memory_layer/qdrant/`
- `memory_layer/history.db`
- `memory_layer/memory_state.json`

### `memory-search` fails because `user_id` is not accepted

Symptom:

- Mem0 rejects search arguments when `user_id` is passed directly

Cause:

- current Mem0 search expects `filters={"user_id": ...}` instead of a top-level `user_id`

Fix:

- keep `llm_wiki/memory_layer.py` on the workspace version that wraps `user_id` in `filters`

### Memory bootstrap locks or stalls

Symptom:

- `memory-bootstrap` appears stuck or local Qdrant reports file locking

Cause:

- another bootstrap or search process is still holding the local Qdrant store

Fix:

- stop stale Python processes running `memory-bootstrap`
- rerun in small sequential batches with `--offset` and `--limit`
- avoid running multiple Mem0 commands in parallel against local Qdrant

### Local Qdrant warns that payload indexes have no effect

Symptom:

- warning about payload indexes appears during search or bootstrap

Cause:

- this is a limitation of local embedded Qdrant mode

Fix:

- ignore it for local single-user use
- move to server Qdrant only if payload indexes or multi-process access are required

## Skill Docs

### `quick_validate.py` fails with `UnicodeDecodeError`

Symptom:

- validation fails while reading `SKILL.md`

Cause:

- the validator inherits a non-UTF-8 default encoding from the shell

Fix:

```powershell
$env:PYTHONUTF8='1'
python C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\wiki-llm-setup
python C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\local-whisper-gpu
```

### `quick_validate.py` fails with invalid YAML

Symptom:

- frontmatter parsing fails on the `description` line

Cause:

- YAML scalar contains `:` and is not quoted

Fix:

- wrap long `description` values in double quotes

## Local Whisper GPU

### CUDA device count is `0`

Symptom:

- `ctranslate2.get_cuda_device_count()` returns `0`

Cause:

- CUDA runtime DLLs are missing from `PATH`
- the wrong runtime version was installed
- the GPU driver or CUDA runtime is unavailable

Fix:

- confirm `local_whisper/vendor/cuda12/` contains the required DLLs
- ensure the transcription scripts prepend that folder to `PATH`
- rerun the CUDA visibility check

### Model loads on CPU instead of GPU

Symptom:

- transcription runs, but not on CUDA

Cause:

- the model was created without `device='cuda'`
- the environment silently fell back due to missing DLLs

Fix:

- force `WhisperModel(..., device='cuda', compute_type='int8_float16')`
- treat fallback as failure and stop the run

### Long recording fails or is too slow

Symptom:

- a multi-hour recording stalls, consumes too much memory, or is difficult to review

Cause:

- the input was transcribed as one job instead of chunked

Fix:

- use `local_whisper/chunk_transcribe.py`
- keep `--chunk-minutes 30`
- review `manifest.json` and chunk text outputs after the run
