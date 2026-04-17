# Obsidian Smart Connections Setup

This workspace already uses Obsidian for graph navigation and `llm_wiki` for graph-first indexing. Smart Connections should be treated as the semantic front-end inside Obsidian, not as a replacement for the wiki build.

## Goal

Use this split:

- `llm_wiki`: build JSON graph, semantic cache, community summaries, token-saving route
- Obsidian Graph View: human link navigation
- Smart Connections: semantic note lookup inside the vault

## Preconditions

1. Open the vault at `C:\Users\Administrator\dxAx`
2. Keep `.obsidian/graph.json` filtering enabled for `나의업무분석`, `tmp`, `wiki`, and `output`
3. Rebuild the wiki before expecting Smart Connections to reflect large structure changes:

```powershell
.\.venv-knowledge\Scripts\python.exe -m llm_wiki.cli build --root . --render-graph
```

## Community Plugin Install

1. In Obsidian, open `Settings -> Community plugins`
2. Disable safe mode if required
3. Search for `Smart Connections`
4. Install and enable the plugin

If multiple similarly named plugins appear, pick the Smart Connections plugin intended for semantic note retrieval in Obsidian.

## Recommended Plugin Settings

Use local-first defaults where possible.

- Vault scope: current vault only
- Excluded folders:
  - `wiki/`
  - `output/`
  - `tmp/`
  - `나의업무분석/`
  - `.venv-whisper/`
  - `local_whisper/`
  - `.venv-knowledge/`
- Preferred note targets:
  - `실습결과물/`
  - `llm_wiki/`
  - `skills/`

## Operating Pattern

1. Use `llm_wiki.cli ask` first for graph-first routing
2. Open the suggested pages
3. Use Smart Connections only when you want nearby semantic notes from inside Obsidian
4. Keep generated `wiki/` files excluded from plugin indexing unless you explicitly want generated artifacts mixed into semantic suggestions

## Maintenance

After adding many new notes or hub pages:

1. rebuild the wiki
2. reopen Obsidian or reload the plugin index
3. verify graph and Smart Connections suggestions are both updated

## Troubleshooting

If semantic results look noisy:

- exclude generated folders again
- make sure same-day notes have explicit links or hub pages
- keep `wiki/` generated outputs out of Smart Connections indexing unless they are intentionally part of the knowledge corpus
