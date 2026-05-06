from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from crewai import Agent, Crew, LLM, Process, Task


PROJECT_ROOT = Path(__file__).resolve().parents[2]

AGENT_KEYS = {
    "role",
    "goal",
    "backstory",
    "verbose",
    "allow_delegation",
    "max_iter",
    "max_retry_limit",
    "max_execution_time",
    "max_tokens",
    "respect_context_window",
    "reasoning",
    "max_reasoning_attempts",
    "use_system_prompt",
    "system_template",
    "prompt_template",
    "response_template",
    "inject_date",
    "date_format",
    "cache",
    "llm",
}

TASK_KEYS = {
    "name",
    "description",
    "expected_output",
    "agent",
    "context",
    "async_execution",
    "output_file",
    "create_directory",
    "human_input",
    "markdown",
}

CREW_KEYS = {
    "name",
    "process",
    "verbose",
    "memory",
    "output_file",
    "agents",
    "tasks",
}

AGENT_BOOL_KEYS = {
    "verbose",
    "allow_delegation",
    "cache",
    "respect_context_window",
    "reasoning",
    "use_system_prompt",
    "inject_date",
}

TASK_BOOL_KEYS = {
    "async_execution",
    "create_directory",
    "human_input",
    "markdown",
}

CREW_BOOL_KEYS = {
    "verbose",
    "memory",
}

TRUE_VALUES = {"true", "yes", "1", "예", "참", "켜짐", "사용", "사용함"}
FALSE_VALUES = {"false", "no", "0", "아니오", "아님", "거짓", "꺼짐", "미사용", "사용안함"}


class MissingInput(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"YAML config file not found: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def render_inputs(value: Any, inputs: dict[str, str]) -> Any:
    if isinstance(value, str):
        return value.format_map(MissingInput(inputs))
    if isinstance(value, list):
        return [render_inputs(item, inputs) for item in value]
    if isinstance(value, dict):
        return {key: render_inputs(item, inputs) for key, item in value.items()}
    return value


def parse_key_values(items: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Input must use key=value format: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Input key cannot be empty: {item}")
        values[key] = value
    return values


def validate_keys(section: str, name: str, config: dict[str, Any], allowed: set[str]) -> None:
    unknown = sorted(set(config) - allowed)
    if unknown:
        joined = ", ".join(unknown)
        raise ValueError(f"Unsupported {section} key(s) for '{name}': {joined}")


def coerce_bool(value: Any, *, section: str, name: str, key: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in TRUE_VALUES:
            return True
        if normalized in FALSE_VALUES:
            return False
    raise ValueError(f"{section} '{name}' key '{key}' must be a boolean or Korean yes/no value")


def coerce_bool_fields(
    config: dict[str, Any],
    keys: set[str],
    *,
    section: str,
    name: str,
) -> dict[str, Any]:
    coerced = dict(config)
    for key in keys:
        if key in coerced:
            coerced[key] = coerce_bool(coerced[key], section=section, name=name, key=key)
    return coerced


def process_from_name(name: str) -> Process:
    normalized = name.strip().lower()
    if normalized in {"sequential", "순차", "순차실행", "순차 실행"}:
        return Process.sequential
    if normalized in {"hierarchical", "계층", "계층실행", "계층 실행"}:
        return Process.hierarchical
    raise ValueError("crew.process must be 'sequential', 'hierarchical', '순차', or '계층'")


def select_order(
    section_name: str,
    definitions: dict[str, dict[str, Any]],
    requested: list[str] | None,
) -> list[str]:
    if requested is None:
        return list(definitions)

    missing = [name for name in requested if name not in definitions]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Unknown {section_name} reference(s): {joined}")
    return requested


def build_agents(agent_configs: dict[str, Any], local_llm: LLM, agent_order: list[str] | None) -> dict[str, Agent]:
    agents_section = agent_configs.get("agents", agent_configs)
    if not isinstance(agents_section, dict) or not agents_section:
        raise ValueError("agents.yaml must define at least one agent")

    ordered_names = select_order("agent", agents_section, agent_order)
    agents: dict[str, Agent] = {}
    for name in ordered_names:
        raw_config = agents_section[name]
        if not isinstance(raw_config, dict):
            raise ValueError(f"Agent '{name}' must be a mapping")
        validate_keys("agent", name, raw_config, AGENT_KEYS)

        config = coerce_bool_fields(
            raw_config,
            AGENT_BOOL_KEYS,
            section="agent",
            name=name,
        )
        llm_ref = config.pop("llm", "default")
        if llm_ref not in (None, "default", "local"):
            raise ValueError(f"Agent '{name}' only supports llm: default/local in this project")

        agents[name] = Agent(**config, llm=local_llm)
    return agents


def build_tasks(
    task_configs: dict[str, Any],
    agents: dict[str, Agent],
    task_order: list[str] | None,
) -> list[Task]:
    tasks_section = task_configs.get("tasks", task_configs)
    if not isinstance(tasks_section, dict) or not tasks_section:
        raise ValueError("tasks.yaml must define at least one task")

    ordered_names = select_order("task", tasks_section, task_order)
    tasks_by_name: dict[str, Task] = {}
    ordered_tasks: list[Task] = []

    for name in ordered_names:
        raw_config = tasks_section[name]
        if not isinstance(raw_config, dict):
            raise ValueError(f"Task '{name}' must be a mapping")
        validate_keys("task", name, raw_config, TASK_KEYS)

        config = coerce_bool_fields(
            raw_config,
            TASK_BOOL_KEYS,
            section="task",
            name=name,
        )
        agent_name = config.pop("agent", None)
        if agent_name not in agents:
            raise ValueError(f"Task '{name}' references unknown agent: {agent_name}")

        context_names = config.pop("context", None)
        if context_names is not None:
            if not isinstance(context_names, list):
                raise ValueError(f"Task '{name}' context must be a list of task names")
            missing_context = [item for item in context_names if item not in tasks_by_name]
            if missing_context:
                joined = ", ".join(missing_context)
                raise ValueError(
                    f"Task '{name}' context must reference earlier tasks only. Missing: {joined}"
                )
            config["context"] = [tasks_by_name[item] for item in context_names]

        config.setdefault("name", name)
        task = Task(**config, agent=agents[agent_name])
        tasks_by_name[name] = task
        ordered_tasks.append(task)

    return ordered_tasks


def load_crew_config(path: Path, inputs: dict[str, str]) -> dict[str, Any]:
    data = render_inputs(load_yaml(path), inputs)
    crew_config = data.get("crew", data)
    if not isinstance(crew_config, dict):
        raise ValueError("crew.yaml must contain a crew mapping")
    validate_keys("crew", "crew", crew_config, CREW_KEYS)
    return crew_config


def build_crew_from_yaml(
    *,
    agents_path: Path,
    tasks_path: Path,
    crew_path: Path,
    local_llm: LLM,
    inputs: dict[str, str],
) -> tuple[Crew, Path | None]:
    crew_config = load_crew_config(crew_path, inputs)
    agent_configs = render_inputs(load_yaml(agents_path), inputs)
    task_configs = render_inputs(load_yaml(tasks_path), inputs)

    agent_order = crew_config.get("agents")
    task_order = crew_config.get("tasks")
    agents_by_name = build_agents(agent_configs, local_llm, agent_order)
    tasks = build_tasks(task_configs, agents_by_name, task_order)

    process_name = str(crew_config.get("process", "sequential"))
    crew_config = coerce_bool_fields(
        crew_config,
        CREW_BOOL_KEYS,
        section="crew",
        name=str(crew_config.get("name", "crew")),
    )
    output_file = crew_config.pop("output_file", None)
    crew_kwargs = {
        "name": crew_config.get("name", "crew"),
        "agents": list(agents_by_name.values()),
        "tasks": tasks,
        "process": process_from_name(process_name),
        "verbose": bool(crew_config.get("verbose", True)),
        "memory": bool(crew_config.get("memory", False)),
    }

    output_path = PROJECT_ROOT / output_file if output_file else None
    return Crew(**crew_kwargs), output_path
