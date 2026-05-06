from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from crewai.tools import tool
from firecrawl import FirecrawlApp


DEFAULT_CONFIG = {
	"limit": 5,
	"location": "South Korea",
	"timeout": 60000,
}


@tool("firecrawl_search")
def firecrawl_search(
	query: str,
	output_path: str = "firecrawl_search_result.md",
) -> str:
	"""Search the web with Firecrawl and save the results to a markdown file."""
	api_key = os.getenv("FIRECRAWL_API_KEY")
	if not api_key:
		raise ValueError("FIRECRAWL_API_KEY environment variable is required")

	app = FirecrawlApp(api_key=api_key)
	result = app.search(query=query, **DEFAULT_CONFIG)

	target_path = Path(output_path)
	markdown = _build_markdown(query=query, result=result)
	target_path.write_text(markdown, encoding="utf-8")

	return f"Saved Firecrawl search results to {target_path.resolve()}"


def _build_markdown(query: str, result: Any) -> str:
	serialized_result = _serialize_result(result)
	lines = [f"# Firecrawl Search Results", "", f"- Query: {query}", ""]

	entries = _extract_entries(serialized_result)
	if entries:
		lines.append("## Results")
		lines.append("")
		for index, entry in enumerate(entries, start=1):
			title = entry.get("title") or f"Result {index}"
			url = entry.get("url") or entry.get("sourceURL") or ""
			snippet = entry.get("markdown") or entry.get("description") or entry.get("snippet") or ""

			lines.append(f"### {index}. {title}")
			lines.append("")
			if url:
				lines.append(f"- URL: {url}")
				lines.append("")
			if snippet:
				lines.append(snippet if isinstance(snippet, str) else json.dumps(snippet, ensure_ascii=False, indent=2))
				lines.append("")

	lines.append("## Raw Response")
	lines.append("")
	lines.append("```json")
	lines.append(json.dumps(serialized_result, ensure_ascii=False, indent=2, default=str))
	lines.append("```")
	lines.append("")
	return "\n".join(lines)


def _serialize_result(result: Any) -> Any:
	if hasattr(result, "model_dump"):
		return result.model_dump()
	if hasattr(result, "dict"):
		return result.dict()
	return result


def _extract_entries(result: Any) -> list[dict[str, Any]]:
	if isinstance(result, dict):
		for key in ("data", "results", "web", "items"):
			value = result.get(key)
			if isinstance(value, list):
				return [item for item in value if isinstance(item, dict)]
	if isinstance(result, list):
		return [item for item in result if isinstance(item, dict)]
	return []


def main() -> None:
	parser = argparse.ArgumentParser(description="Run Firecrawl search and save the results as markdown.")
	parser.add_argument("query", help="Search query to send to Firecrawl")
	parser.add_argument(
		"--output",
		default="firecrawl_search_result.md",
		help="Path to the markdown file to write",
	)
	args = parser.parse_args()

	print(firecrawl_search.run(query=args.query, output_path=args.output))


if __name__ == "__main__":
	main()