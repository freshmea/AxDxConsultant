from __future__ import annotations

import os
import sys
from argparse import ArgumentParser
from pathlib import Path

from crewai import LLM
from dotenv import load_dotenv

from crewai_local_gemma.config_loader import (
    PROJECT_ROOT,
    build_crew_from_yaml,
    parse_key_values,
)

DEFAULT_AGENTS_PATH = PROJECT_ROOT / "config" / "agents.yaml"
DEFAULT_TASKS_PATH = PROJECT_ROOT / "config" / "tasks.yaml"
DEFAULT_CREW_PATH = PROJECT_ROOT / "config" / "crew.yaml"


def configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def build_llm() -> LLM:
    load_dotenv(PROJECT_ROOT / ".env")
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = os.getenv("LLM_MODEL", "gemma-4-26b-a4b-it")
    if model.startswith(f"{provider}/"):
        model = model.split("/", 1)[1]

    return LLM(
        model=model,
        provider=provider,
        base_url=os.getenv("LLM_BASE_URL", "http://182.229.102.180:30003/v1"),
        api_key=os.getenv("LLM_API_KEY", "llamacpp"),
        temperature=0.2,
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        timeout=120,
    )


def parse_args() -> tuple[Path, Path, Path, dict[str, str]]:
    parser = ArgumentParser(
        description="Run a CrewAI crew from YAML agent/task configuration."
    )
    parser.add_argument("--agents-config", type=Path, default=DEFAULT_AGENTS_PATH)
    parser.add_argument("--tasks-config", type=Path, default=DEFAULT_TASKS_PATH)
    parser.add_argument("--crew-config", type=Path, default=DEFAULT_CREW_PATH)
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Template value for YAML strings. Can be passed multiple times.",
    )
    args = parser.parse_args()
    return args.agents_config, args.tasks_config, args.crew_config, parse_key_values(args.input)


def write_output(output_path: Path | None, content: str) -> None:
    if output_path is None:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content + "\n", encoding="utf-8")


def main() -> None:
    configure_console_encoding()
    agents_path, tasks_path, crew_path, inputs = parse_args()
    crew, output_path = build_crew_from_yaml(
        agents_path=agents_path,
        tasks_path=tasks_path,
        crew_path=crew_path,
        local_llm=build_llm(),
        inputs=inputs,
    )
    result = crew.kickoff(inputs=inputs)
    content = getattr(result, "raw", str(result)).strip()

    if not content:
        raise RuntimeError("CrewAI completed, but the local LLM returned an empty response.")

    write_output(output_path, content)

    print("\n=== CrewAI local Gemma smoke result ===\n")
    print(content)
    if output_path:
        print(f"\nSaved result to: {output_path}")


if __name__ == "__main__":
    main()
