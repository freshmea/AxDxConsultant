from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path
from urllib import request


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(url: str) -> dict:
    with request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_workflow(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "prompt" in payload and isinstance(payload["prompt"], dict):
        return payload["prompt"]
    return payload


def wait_for_history(base_url: str, prompt_id: str, timeout_seconds: int) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        history = get_json(f"{base_url}/history/{prompt_id}")
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(2)
    raise TimeoutError(f"Timed out waiting for prompt {prompt_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit a ComfyUI API workflow JSON file")
    parser.add_argument("--workflow", required=True, help="Path to API workflow JSON")
    parser.add_argument("--base-url", help="Full ComfyUI base URL, for example http://bindsoft.ddns.net:30006")
    parser.add_argument("--host", default="127.0.0.1", help="ComfyUI host")
    parser.add_argument("--port", type=int, default=8188, help="ComfyUI port")
    parser.add_argument("--wait", action="store_true", help="Wait for execution and print history payload")
    parser.add_argument("--timeout", type=int, default=600, help="Wait timeout in seconds")
    args = parser.parse_args()

    workflow_path = Path(args.workflow).resolve()
    prompt = load_workflow(workflow_path)
    base_url = (args.base_url or f"http://{args.host}:{args.port}").rstrip("/")
    response = post_json(
        f"{base_url}/prompt",
        {
            "prompt": prompt,
            "client_id": str(uuid.uuid4()),
        },
    )

    prompt_id = response.get("prompt_id")
    if not prompt_id:
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return 1

    result = {
        "workflow": str(workflow_path),
        "prompt_id": prompt_id,
        "queued": True,
    }

    if args.wait:
        result["history"] = wait_for_history(base_url, prompt_id, args.timeout)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
