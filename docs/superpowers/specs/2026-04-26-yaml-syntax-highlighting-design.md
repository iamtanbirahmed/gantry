# YAML Syntax Highlighting Design

**Date:** 2026-04-26  
**Status:** Approved

## Context

The YAML panel in ClusterScreen displays Kubernetes resource manifests in a `TextArea`
widget already configured with `language="yaml"`. However, syntax highlighting does not
render because Textual's TextArea relies on tree-sitter (via the `textual[syntax]`
optional extra) for language-aware coloring — and that extra is not currently installed.
Pygments is present (as a Textual transitive dep) but does not drive TextArea highlighting
in Textual 8.x.

## Goal

Enable YAML syntax highlighting in the read-only TextArea that shows K8s resource
manifests, using the monokai color theme.

## Scope

Two files change. No new top-level libraries. No behavioral changes to the YAML panel
(read-only, two-mode toggle via `m`, keyboard scrolling all unchanged).

## Changes

### 1. `pyproject.toml` — install tree-sitter via Textual syntax extra

```diff
-    "textual>=0.40.0",
+    "textual[syntax]>=0.40.0",
```

After editing, run `uv sync` to lock and install tree-sitter + compiled YAML grammar.

### 2. `src/gantry/screens.py` — `_show_yaml_panel()` (line ~737)

Add `theme="monokai"` to the TextArea constructor:

```python
text_area = TextArea(
    yaml_content,
    language="yaml",
    theme="monokai",   # enables monokai color scheme
    read_only=True,
    id="yaml-content",
)
```

### 3. `src/gantry/screens.py` — `action_toggle_yaml_mode()` (line ~767)

After `load_text()`, explicitly restore the language attribute. Textual preserves
`language` on `load_text()` in 8.x but this guards against version regressions:

```python
self._yaml_text_area.load_text(yaml_content)
self._yaml_text_area.language = "yaml"  # defensive: ensure highlight survives reload
```

## Files Modified

| File | Change |
|------|--------|
| `pyproject.toml` | `textual` → `textual[syntax]` in dependencies |
| `src/gantry/screens.py` | `theme="monokai"` in `_show_yaml_panel()`; `language = "yaml"` in `action_toggle_yaml_mode()` |

## What `textual[syntax]` Installs

- `tree-sitter` — incremental parser
- `tree-sitter-languages` — compiled grammars including YAML
- Enables Textual's `TextArea` to parse and highlight language tokens in real time

## Verification

1. `uv sync` — confirm tree-sitter appears in output
2. `uv run python -m gantry` — open a K8s resource, press `y`
3. YAML panel must show colored keys, values, strings, comments
4. Press `m` to toggle full ↔ spec — colors must persist after toggle
5. `uv run pytest tests/ -v` — all 68 tests pass (no behavioral regression)
