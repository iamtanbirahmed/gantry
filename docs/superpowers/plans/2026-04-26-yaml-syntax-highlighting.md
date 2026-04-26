# YAML Syntax Highlighting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable YAML syntax highlighting with monokai theme in the read-only TextArea that displays Kubernetes resource manifests.

**Architecture:** Textual's TextArea uses tree-sitter (via the `textual[syntax]` optional extra) for syntax highlighting. The extra is not installed, so `language="yaml"` is currently inert. Adding the extra activates highlighting. Two small code changes follow: add `theme="monokai"` to the TextArea constructor, and defensively re-set `language = "yaml"` after `load_text()` on mode toggle.

**Tech Stack:** Textual 8.2.3 + `textual[syntax]` (tree-sitter + tree-sitter-languages), pytest-asyncio for tests.

---

## Files

| File | Change |
|------|--------|
| `pyproject.toml` | `textual` → `textual[syntax]` |
| `src/gantry/screens.py` | Add `theme="monokai"` in `_show_yaml_panel()`; add `language = "yaml"` in `action_toggle_yaml_mode()` |
| `tests/test_app.py` | Add 3 tests: theme, language on open, language after toggle |

---

### Task 1: Install `textual[syntax]`

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Edit `pyproject.toml`**

Change line 12 from:
```
    "textual>=0.40.0",
```
to:
```
    "textual[syntax]>=0.40.0",
```

- [ ] **Step 2: Sync dependencies**

```bash
uv sync
```

Expected output contains a line like:
```
+ tree-sitter ...
+ tree-sitter-languages ...
```

(Exact package names may differ; what matters is tree-sitter appears in the install output.)

- [ ] **Step 3: Run existing tests to confirm no regression**

```bash
uv run pytest tests/ -v
```

Expected: all 68 tests pass.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add textual[syntax] for YAML syntax highlighting"
```

---

### Task 2: TDD — TextArea theme

**Files:**
- Modify: `tests/test_app.py`
- Modify: `src/gantry/screens.py`

- [ ] **Step 1: Write the failing test**

In `tests/test_app.py`, append after the last test (after line 612):

```python
@pytest.mark.asyncio
async def test_yaml_text_area_uses_monokai_theme():
    """TextArea for YAML should be created with the monokai theme."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._apply_yaml_result(("apiVersion: v1\nkind: Pod\n", "apiVersion: v1\n"))
        await pilot.pause()

        text_area = screen.query_one("#yaml-content", TextArea)
        assert text_area.theme == "monokai"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_app.py::test_yaml_text_area_uses_monokai_theme -v
```

Expected: FAIL — `AssertionError: assert 'css' == 'monokai'` (default theme is "css")

- [ ] **Step 3: Add `theme="monokai"` to `_show_yaml_panel()` in `screens.py`**

In `src/gantry/screens.py`, locate `_show_yaml_panel()` (around line 737). Change:

```python
        text_area = TextArea(
            yaml_content,
            language="yaml",
            read_only=True,
            id="yaml-content",
        )
```

to:

```python
        text_area = TextArea(
            yaml_content,
            language="yaml",
            theme="monokai",
            read_only=True,
            id="yaml-content",
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_app.py::test_yaml_text_area_uses_monokai_theme -v
```

Expected: PASS

- [ ] **Step 5: Run full test suite**

```bash
uv run pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/test_app.py src/gantry/screens.py
git commit -m "feat: use monokai theme in YAML TextArea"
```

---

### Task 3: TDD — language attribute on open and after toggle

**Files:**
- Modify: `tests/test_app.py`
- Modify: `src/gantry/screens.py`

- [ ] **Step 1: Write two failing tests**

In `tests/test_app.py`, append after `test_yaml_text_area_uses_monokai_theme`:

```python
@pytest.mark.asyncio
async def test_yaml_text_area_uses_yaml_language():
    """TextArea for YAML should be created with language='yaml'."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._apply_yaml_result(("apiVersion: v1\nkind: Pod\n", "apiVersion: v1\n"))
        await pilot.pause()

        text_area = screen.query_one("#yaml-content", TextArea)
        assert text_area.language == "yaml"


@pytest.mark.asyncio
async def test_yaml_language_preserved_after_toggle():
    """TextArea language must remain 'yaml' after toggling between full and spec mode."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        full = "apiVersion: v1\nkind: Pod\nstatus:\n  phase: Running\n"
        spec = "apiVersion: v1\nkind: Pod\nspec: {}\n"
        screen._apply_yaml_result((full, spec))
        await pilot.pause()

        # Initial state: spec mode
        text_area = screen.query_one("#yaml-content", TextArea)
        assert text_area.language == "yaml"

        # Toggle to full
        screen.action_toggle_yaml_mode()
        await pilot.pause()
        text_area = screen.query_one("#yaml-content", TextArea)
        assert text_area.language == "yaml"

        # Toggle back to spec
        screen.action_toggle_yaml_mode()
        await pilot.pause()
        text_area = screen.query_one("#yaml-content", TextArea)
        assert text_area.language == "yaml"
```

- [ ] **Step 2: Run tests to check their current state**

```bash
uv run pytest tests/test_app.py::test_yaml_text_area_uses_yaml_language tests/test_app.py::test_yaml_language_preserved_after_toggle -v
```

Note the results. `test_yaml_text_area_uses_yaml_language` may already pass (language is set in the constructor). `test_yaml_language_preserved_after_toggle` may or may not pass depending on whether Textual 8.x preserves language through `load_text()`. Either way, proceed with the next step.

- [ ] **Step 3: Add defensive language re-set in `action_toggle_yaml_mode()` in `screens.py`**

In `src/gantry/screens.py`, locate `action_toggle_yaml_mode()` (around line 766). Change:

```python
        if self._yaml_text_area is not None:
            self._yaml_text_area.load_text(yaml_content)
```

to:

```python
        if self._yaml_text_area is not None:
            self._yaml_text_area.load_text(yaml_content)
            self._yaml_text_area.language = "yaml"
```

- [ ] **Step 4: Run all three new tests**

```bash
uv run pytest tests/test_app.py::test_yaml_text_area_uses_yaml_language tests/test_app.py::test_yaml_text_area_uses_monokai_theme tests/test_app.py::test_yaml_language_preserved_after_toggle -v
```

Expected: all 3 PASS.

- [ ] **Step 5: Run full test suite**

```bash
uv run pytest tests/ -v
```

Expected: all 71 tests pass (68 original + 3 new).

- [ ] **Step 6: Commit**

```bash
git add tests/test_app.py src/gantry/screens.py
git commit -m "feat: preserve yaml language after mode toggle"
```

---

## Verification

1. `uv run pytest tests/ -v` → 71 tests pass
2. `uv run python -m gantry` → select any K8s resource → press `y` → YAML panel shows colored keys/strings/values in monokai palette
3. Press `m` to toggle full ↔ spec → colors remain after toggle
4. Press `Escape` to close panel → no errors
