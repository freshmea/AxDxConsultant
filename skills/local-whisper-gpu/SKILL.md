---
name: local-whisper-gpu
description: "Set up or repair Windows GPU speech-to-text with faster-whisper in this repository pattern, including dedicated venv, ffmpeg, CUDA runtime DLLs on PATH, strict CUDA validation, and 30-minute chunk transcription for long recordings. Use when Codex needs to install, verify, or run local Whisper STT without CPU fallback."
---

# Local Whisper GPU

Set up the STT stack in this order.

## 1. Confirm the required layout

Expect these files and folders:

- `.venv-whisper/`
- `local_whisper/transcribe.py`
- `local_whisper/chunk_transcribe.py`
- `local_whisper/requirements.txt`
- `local_whisper/vendor/cuda12/`

If the scripts exist but `vendor/cuda12/` is empty, CUDA loading will likely fail.

## 2. Install the environment

Create the dedicated venv and install dependencies:

```powershell
python -m venv .venv-whisper
.\.venv-whisper\Scripts\python.exe -m pip install -r local_whisper\requirements.txt
winget install -e --id Gyan.FFmpeg
```

Keep Whisper isolated from the main repo Python environment.

## 3. Provide CUDA runtime DLLs

Place extracted CUDA/cuDNN DLLs under:

- `local_whisper/vendor/cuda12/`

The transcription scripts should prepend this directory to `PATH` before loading `WhisperModel`.

## 4. Validate GPU visibility

Check CUDA device visibility:

```powershell
.\.venv-whisper\Scripts\python.exe -c "import ctranslate2; print(ctranslate2.get_cuda_device_count())"
```

Check actual model load:

```powershell
.\.venv-whisper\Scripts\python.exe -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cuda', compute_type='int8_float16'); print('cuda-ok')"
```

Treat CPU fallback as a failure.

## 5. Run long recordings in chunks

Do not transcribe very long files in one pass.

Use:

```powershell
.\.venv-whisper\Scripts\python.exe local_whisper\chunk_transcribe.py `
  --input "C:\path\to\recording.m4a" `
  --model small `
  --language ko `
  --chunk-minutes 30 `
  --compute-type int8_float16 `
  --output-dir local_whisper\outputs
```

Expected outputs:

- `local_whisper/outputs/chunk_text/*.txt`
- `local_whisper/outputs/*.json`
- `local_whisper/outputs/*.srt`
- `local_whisper/outputs/manifest.json`

## 6. Verify results after each run

Confirm:

1. chunk files were created
2. `manifest.json` exists
3. the script did not silently switch to CPU
4. the output count matches the expected chunk count

For failure cases, read `../troubleshooting.md`.
