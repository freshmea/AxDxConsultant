# Remote ComfyUI Z-Image Setup

Remote endpoint:

- `http://bindsoft.ddns.net:30006`

Remote model files installed on the server:

- `/home/aa/vllm/comfyui/models/diffusion_models/z_image_turbo_bf16.safetensors`
- `/home/aa/vllm/comfyui/models/text_encoders/qwen_3_4b.safetensors`
- `/home/aa/vllm/comfyui/models/vae/ae.safetensors`

Local API workflow:

- `C:\Users\Administrator\dxAx\workflows\zimage-turbo-api.json`

Submit a prompt:

```powershell
.\.venv-comfyui\Scripts\python.exe .\scripts\comfyui\submit_workflow.py `
  --workflow .\workflows\zimage-turbo-api.json `
  --base-url http://bindsoft.ddns.net:30006 `
  --wait
```

Prompt-only wrapper:

```powershell
.\.venv-comfyui\Scripts\python.exe .\scripts\comfyui\run_remote_zimage.py `
  "portrait photo of a woman under neon city lights, moody cinematic atmosphere" `
  --download-dir .\downloads\zimage
```

Download generated images from a finished prompt:

```powershell
.\.venv-comfyui\Scripts\python.exe .\scripts\comfyui\download_history_outputs.py `
  --prompt-id <prompt_id> `
  --base-url http://bindsoft.ddns.net:30006 `
  --output-dir .\downloads\zimage
```

Workflow defaults:

- sampler: `res_multistep`
- scheduler: `simple`
- steps: `4`
- cfg: `1`
- size: `1024x1024`
- shift: `3`

To change the prompt, edit node `4` in `zimage-turbo-api.json`.
