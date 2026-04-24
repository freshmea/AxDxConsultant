# ComfyUI Local Setup

이 작업 공간에는 ComfyUI를 별도 가상환경으로 설치했다.

## 경로

- 가상환경: `C:\Users\Administrator\dxAx\.venv-comfyui`
- ComfyUI 체크아웃: `C:\Users\Administrator\dxAx\comfyui\ComfyUI`
- 제어 스크립트: `C:\Users\Administrator\dxAx\scripts\comfyui`
- 런타임 로그와 PID: `C:\Users\Administrator\dxAx\tmp\comfyui`

## 시작

```powershell
.\scripts\comfyui\start.ps1
```

LAN에서 열려야 하면:

```powershell
.\scripts\comfyui\start.ps1 -AllowLan
```

기본 주소는 `http://127.0.0.1:8188` 이다.

## 상태 확인

```powershell
.\scripts\comfyui\status.ps1
```

## 중지

```powershell
.\scripts\comfyui\stop.ps1
```

## API 워크플로 제출

ComfyUI에서 `Save (API Format)`으로 저장한 워크플로 JSON을 사용한다.

```powershell
.\.venv-comfyui\Scripts\python.exe .\scripts\comfyui\submit_workflow.py --workflow .\path\to\workflow_api.json --wait
```

기본 예제로 SD 1.5 + LCM LoRA 워크플로를 넣어두었다.

```powershell
.\.venv-comfyui\Scripts\python.exe .\scripts\comfyui\submit_workflow.py --workflow .\workflows\sd15-lcm-txt2img-api.json --wait
```

## 입력 이미지 업로드

```powershell
.\.venv-comfyui\Scripts\python.exe .\scripts\comfyui\upload_input.py --file C:\path\to\image.png --target input --overwrite
```

## 모델 배치

기본 모델 경로는 ComfyUI 표준 구조를 따른다.

- 체크포인트: `comfyui\ComfyUI\models\checkpoints`
- VAE: `comfyui\ComfyUI\models\vae`
- LoRA: `comfyui\ComfyUI\models\loras`
- ControlNet: `comfyui\ComfyUI\models\controlnet`
- 업스케일러: `comfyui\ComfyUI\models\upscale_models`

아직 기본 체크포인트는 자동 다운로드하지 않았다. 원하는 모델 파일을 직접 넣거나, 기존 모델 저장소가 있으면 이후 `extra_model_paths.yaml`로 연결하면 된다.

## Codex에서 제어하는 방법

Codex 세션에서 아래 패턴으로 바로 다룰 수 있다.

```powershell
.\scripts\comfyui\start.ps1
.\scripts\comfyui\status.ps1
.\.venv-comfyui\Scripts\python.exe .\scripts\comfyui\submit_workflow.py --workflow .\workflow_api.json --wait
.\scripts\comfyui\stop.ps1
```
