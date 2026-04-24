from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib import parse, request


def get_json(url: str) -> dict:
    with request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with request.urlopen(url, timeout=300) as resp, dest.open("wb") as out:
        out.write(resp.read())


def main() -> int:
    parser = argparse.ArgumentParser(description="Download image outputs from a ComfyUI history item")
    parser.add_argument("--prompt-id", required=True, help="Prompt id returned by /prompt")
    parser.add_argument("--base-url", default="http://127.0.0.1:8188", help="ComfyUI base URL")
    parser.add_argument("--output-dir", default="downloads", help="Directory to store downloaded files")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    history = get_json(f"{base_url}/history/{args.prompt_id}")
    if args.prompt_id not in history:
        raise SystemExit(f"Prompt id not found in history: {args.prompt_id}")

    item = history[args.prompt_id]
    output_dir = Path(args.output_dir).resolve()
    downloaded = []

    for node_id, node_output in item.get("outputs", {}).items():
        for image in node_output.get("images", []):
            query = parse.urlencode(
                {
                    "filename": image["filename"],
                    "subfolder": image.get("subfolder", ""),
                    "type": image.get("type", "output"),
                }
            )
            url = f"{base_url}/view?{query}"
            filename = Path(image["filename"]).name
            dest = output_dir / f"{args.prompt_id}_{node_id}_{filename}"
            download_file(url, dest)
            downloaded.append(str(dest))

    print(json.dumps({"prompt_id": args.prompt_id, "downloaded": downloaded}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
