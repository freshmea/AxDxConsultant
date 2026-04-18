from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Dict, List


def _make_id(*parts: str) -> str:
    combined = "::".join(part for part in parts if part)
    cleaned = re.sub(r"[^a-zA-Z0-9_:./-]+", "_", combined)
    return cleaned.strip("_")


def _module_node_id(relpath: str) -> str:
    return _make_id("module", relpath)


def _symbol_node_id(relpath: str, qualname: str) -> str:
    return _make_id("symbol", relpath, qualname)


class _PythonExtractor(ast.NodeVisitor):
    def __init__(self, relpath: str) -> None:
        self.relpath = relpath
        self.nodes: List[Dict[str, object]] = []
        self.edges: List[Dict[str, object]] = []
        self.module_id = _module_node_id(relpath)
        self.scope_stack: List[str] = []
        self.local_defs: Dict[str, str] = {}
        self._seen_nodes: set[str] = set()

    def extract(self, source: str) -> Dict[str, object]:
        tree = ast.parse(source)
        self._add_node(
            self.module_id,
            Path(self.relpath).name,
            "module",
            1,
        )
        self.generic_visit(tree)
        return {"nodes": self.nodes, "edges": self.edges}

    def _qualname(self, name: str) -> str:
        return ".".join([*self.scope_stack, name]) if self.scope_stack else name

    def _add_node(self, node_id: str, label: str, kind: str, lineno: int, **extra: object) -> None:
        if node_id in self._seen_nodes:
            return
        self._seen_nodes.add(node_id)
        payload = {
            "id": node_id,
            "label": label,
            "kind": kind,
            "path": self.relpath,
            "source_file": self.relpath,
            "source_location": f"L{lineno}",
            **extra,
        }
        self.nodes.append(payload)

    def _add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        lineno: int,
        *,
        confidence: str = "EXTRACTED",
    ) -> None:
        self.edges.append(
            {
                "source": source,
                "target": target,
                "relation": relation,
                "confidence": confidence,
                "path": self.relpath,
                "source_file": self.relpath,
                "source_location": f"L{lineno}",
            }
        )

    def _register_symbol(self, name: str, kind: str, lineno: int) -> str:
        qualname = self._qualname(name)
        symbol_id = _symbol_node_id(self.relpath, qualname)
        self.local_defs[qualname] = symbol_id
        self.local_defs[name] = symbol_id
        self._add_node(symbol_id, qualname, kind, lineno)
        self._add_edge(self.module_id, symbol_id, "defines", lineno)
        return symbol_id

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            raw = alias.name
            target_id = _make_id("import", raw)
            self._add_node(target_id, raw, "import", node.lineno, external=True)
            self._add_edge(self.module_id, target_id, "imports", node.lineno)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module_name = "." * node.level + (node.module or "")
        if not module_name:
            return
        target_id = _make_id("import", module_name)
        self._add_node(target_id, module_name, "import", node.lineno, external=True)
        self._add_edge(self.module_id, target_id, "imports", node.lineno)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        class_id = self._register_symbol(node.name, "class", node.lineno)
        for base in node.bases:
            base_name = self._expr_name(base)
            if not base_name:
                continue
            base_id = self.local_defs.get(base_name) or _make_id("symbol-ref", base_name)
            self._add_node(base_id, base_name, "symbol_ref", getattr(base, "lineno", node.lineno))
            self._add_edge(class_id, base_id, "inherits", getattr(base, "lineno", node.lineno))
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        fn_id = self._register_symbol(node.name, "function", node.lineno)
        self.scope_stack.append(node.name)
        for child in node.body:
            self.visit(child)
        self.scope_stack.pop()
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        fn_id = self._register_symbol(node.name, "async_function", node.lineno)
        self.scope_stack.append(node.name)
        for child in node.body:
            self.visit(child)
        self.scope_stack.pop()
        return

    def visit_Call(self, node: ast.Call) -> None:
        caller_name = ".".join(self.scope_stack) if self.scope_stack else Path(self.relpath).stem
        caller_id = self.local_defs.get(caller_name, self.module_id)
        callee_name = self._expr_name(node.func)
        if callee_name:
            callee_id = self.local_defs.get(callee_name) or _make_id("symbol-ref", callee_name)
            self._add_node(callee_id, callee_name, "symbol_ref", getattr(node, "lineno", 1))
            self._add_edge(caller_id, callee_id, "calls", getattr(node, "lineno", 1))
        self.generic_visit(node)

    def _expr_name(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            root = self._expr_name(node.value)
            return f"{root}.{node.attr}" if root else node.attr
        if isinstance(node, ast.Call):
            return self._expr_name(node.func)
        return None


def extract_python(path: Path, relpath: str) -> Dict[str, object]:
    source = path.read_text(encoding="utf-8", errors="ignore").lstrip("\ufeff")
    extractor = _PythonExtractor(relpath)
    result = extractor.extract(source)
    result["language"] = "python"
    result["path"] = relpath
    return result


def extract_code_file(path: Path, relpath: str) -> Dict[str, object]:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return extract_python(path, relpath)
    return {"nodes": [], "edges": [], "language": "unsupported", "path": relpath}
