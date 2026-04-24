from __future__ import annotations

import argparse
import json
import mimetypes
import uuid
from pathlib import Path
from urllib import request


def build_multipart(field_name: str, file_path: Path, overwrite: bool, subfolder: str) -> tuple[bytes, str]:
    boundary = f"----CodexComfyUI{uuid.uuid4().hex}"
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"

    parts = [
        f"--{boundary}\r\n".encode("utf-8"),
        (
            f'Content-Disposition: form-data; name="{field_name}"; filename="{file_path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8"),
        file_path.read_bytes(),
        b"\r\n",
        f"--{boundary}\r\n".encode("utf-8"),
        f'Content-Disposition: form-data; name="overwrite"\r\n\r\n{"true" if overwrite else "false"}\r\n'.encode("utf-8"),
        f"--{boundary}\r\n".encode("utf-8"),
        f'Content-Disposition: form-data; name="subfolder"\r\n\r\n{subfolder}\r\n'.encode("utf-8"),
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    return b"".join(parts), boundary


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload an image into ComfyUI input/temp/output storage")
    parser.add_argument("--file", required=True, help="Local image file")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8188)
    parser.add_argument("--target", default="input", choices=["input", "temp", "output"])
    parser.add_argument("--subfolder", default="")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    file_path = Path(args.file).resolve()
    body, boundary = build_multipart("image", file_path, args.overwrite, args.subfolder)
    req = request.Request(
        f"http://{args.host}:{args.port}/upload/{args.target}",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
