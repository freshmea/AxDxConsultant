# Troubleshooting

This note covers setup problems already encountered in this workspace while building the wiki LLM and local Whisper stack.

## Wiki LLM

### Unresolved links caused by `%20`

Symptom:

- markdown links such as `./5가지단계로%20나누기.md` appear unresolved

Cause:

- the indexer treats the href as a raw path instead of a URL-decoded local file path

Fix:

- decode markdown hrefs before resolving local files
- rebuild with `python -m llm_wiki.cli build --root . --render-graph`

### Unresolved links to `wiki/` generated files

Symptom:

- links to `../../wiki/index.md` or `../../wiki/log.md` remain unresolved

Cause:

- `wiki/` is intentionally excluded by `.llmwikiignore`, so generated files are not part of the corpus graph

Fix:

- keep those references as plain text guidance instead of graph links
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

### PowerShell shows broken Korean text

Symptom:

- Korean text appears as mojibake in terminal output

Cause:

- PowerShell is using a legacy code page such as `cp949`

Fix:

- prefer reading files as UTF-8 in Python
- set `$env:PYTHONUTF8='1'` before validation scripts when needed
- treat terminal display corruption separately from actual file corruption

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
