from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path
from urllib import parse, request


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(url: str) -> dict:
    with request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wait_for_history(base_url: str, prompt_id: str, timeout_seconds: int) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        history = get_json(f"{base_url}/history/{prompt_id}")
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(2)
    raise TimeoutError(f"Timed out waiting for prompt {prompt_id}")


def download_outputs(base_url: str, prompt_id: str, history_item: dict, output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[str] = []
    for node_id, node_output in history_item.get("outputs", {}).items():
        for image in node_output.get("images", []):
            query = parse.urlencode(
                {
                    "filename": image["filename"],
                    "subfolder": image.get("subfolder", ""),
                    "type": image.get("type", "output"),
                }
            )
            url = f"{base_url}/view?{query}"
            dest = output_dir / f"{prompt_id}_{node_id}_{Path(image['filename']).name}"
            with request.urlopen(url, timeout=300) as resp, dest.open("wb") as out:
                out.write(resp.read())
            downloaded.append(str(dest))
    return downloaded


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the remote Z-Image workflow against ComfyUI")
    parser.add_argument("prompt", help="Prompt text")
    parser.add_argument("--base-url", default="http://bindsoft.ddns.net:30006", help="ComfyUI base URL")
    parser.add_argument(
        "--workflow",
        default=str(Path(__file__).resolve().parents[2] / "workflows" / "zimage-turbo-api.json"),
        help="Path to the Z-Image API workflow JSON",
    )
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--cfg", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--shift", type=float, default=3.0)
    parser.add_argument("--prefix", default="ZIMAGE_TURBO")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--download-dir", help="If set, download completed images to this directory")
    args = parser.parse_args()

    workflow = json.loads(Path(args.workflow).read_text(encoding="utf-8"))
    prompt = workflow["prompt"]
    prompt["4"]["inputs"]["text"] = args.prompt
    prompt["6"]["inputs"]["width"] = args.width
    prompt["6"]["inputs"]["height"] = args.height
    prompt["7"]["inputs"]["shift"] = args.shift
    prompt["8"]["inputs"]["seed"] = args.seed
    prompt["8"]["inputs"]["steps"] = args.steps
    prompt["8"]["inputs"]["cfg"] = args.cfg
    prompt["10"]["inputs"]["filename_prefix"] = args.prefix

    base_url = args.base_url.rstrip("/")
    response = post_json(
        f"{base_url}/prompt",
        {
            "prompt": prompt,
            "client_id": str(uuid.uuid4()),
        },
    )
    prompt_id = response["prompt_id"]
    history_item = wait_for_history(base_url, prompt_id, args.timeout)

    result = {
        "prompt_id": prompt_id,
        "status": history_item.get("status", {}),
        "outputs": history_item.get("outputs", {}),
    }

    if args.download_dir:
        result["downloaded"] = download_outputs(base_url, prompt_id, history_item, Path(args.download_dir).resolve())

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
