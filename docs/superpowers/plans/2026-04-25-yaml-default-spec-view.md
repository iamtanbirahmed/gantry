# YAML Default Spec View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change the YAML panel to open in spec mode by default when the user presses `y`.

**Architecture:** One-line change in `_apply_yaml_result` sets `yaml_mode = "spec"` instead of `"full"`. Reactive default on `ClusterScreen` updated to match. Tests updated to reflect new initial state and toggling order.

**Tech Stack:** Python, Textual, pytest, pytest-asyncio

---

### Task 1: Update `_apply_yaml_result` and reactive default

**Files:**
- Modify: `src/gantry/screens.py:329` (reactive default)
- Modify: `src/gantry/screens.py:717` (`_apply_yaml_result`)

- [ ] **Step 1: Update the reactive default**

In `src/gantry/screens.py` line 329, change:
```python
yaml_mode: reactive[str] = reactive("full")
```
to:
```python
yaml_mode: reactive[str] = reactive("spec")
```

- [ ] **Step 2: Update `_apply_yaml_result` to default to spec**

In `src/gantry/screens.py` line 717, change:
```python
self.yaml_mode = "full"
```
to:
```python
self.yaml_mode = "spec"
```

- [ ] **Step 3: Run existing tests to see failures**

```bash
uv run pytest tests/test_app.py -v -k "yaml"
```

Expected: multiple FAIL — tests asserting `yaml_mode == "full"` initially and wrong toggle order.

---

### Task 2: Fix unit tests to reflect new default

**Files:**
- Modify: `tests/test_app.py`

- [ ] **Step 1: Fix `test_cluster_screen_has_yaml_reactives` (line 362)**

Change:
```python
assert screen.yaml_mode == "full"
```
to:
```python
assert screen.yaml_mode == "spec"
```

- [ ] **Step 2: Fix `test_toggle_yaml_mode_switches_content` (lines 433–450)**

The test opens YAML (now defaults to spec), then toggles twice. Update the assertions:

```python
full = "apiVersion: v1\nkind: Pod\nstatus:\n  phase: Running\n"
spec = "apiVersion: v1\nkind: Pod\nspec: {}\n"
screen._apply_yaml_result((full, spec))
await pilot.pause()

# Now opens in spec
assert screen.yaml_mode == "spec"
text_area = screen.query_one("#yaml-content", TextArea)
assert "status:" not in text_area.text
assert "spec:" in text_area.text

# First toggle → full
screen.action_toggle_yaml_mode()
await pilot.pause()

assert screen.yaml_mode == "full"
text_area = screen.query_one("#yaml-content", TextArea)
assert "status:" in text_area.text

# Second toggle → back to spec
screen.action_toggle_yaml_mode()
await pilot.pause()

assert screen.yaml_mode == "spec"
text_area = screen.query_one("#yaml-content", TextArea)
assert "status:" not in text_area.text
assert "spec:" in text_area.text
```

- [ ] **Step 3: Fix `test_toggle_yaml_mode_no_op_when_panel_closed` (line 465)**

Change:
```python
assert screen.yaml_mode == "full"
```
to:
```python
assert screen.yaml_mode == "spec"
```

- [ ] **Step 4: Fix `test_status_bar_shows_yaml_mode_hint` (lines 482–486)**

`_show_yaml_panel()` is called directly here without `_apply_yaml_result`. The reactive default is now `"spec"`, so the status bar will show `"spec"` first, then toggle to `"full"`.

Change:
```python
assert "full" in screen.connection_status

screen.action_toggle_yaml_mode()
assert "spec" in screen.connection_status
```
to:
```python
assert "spec" in screen.connection_status

screen.action_toggle_yaml_mode()
assert "full" in screen.connection_status
```

- [ ] **Step 5: Fix integration test (lines 592–601)**

Find the test that calls `_apply_yaml_result((full, spec))` then checks `yaml_mode == "full"` and `"status:" in text_area.text`, then presses `m`.

Change:
```python
assert screen.yaml_view_open is True
assert screen.yaml_mode == "full"
text_area = screen.query_one("#yaml-content", TextArea)
assert "status:" in text_area.text

await pilot.press("m")
await pilot.pause()

assert screen.yaml_mode == "spec"
text_area = screen.query_one("#yaml-content", TextArea)
assert "status:" not in text_area.text
```
to:
```python
assert screen.yaml_view_open is True
assert screen.yaml_mode == "spec"
text_area = screen.query_one("#yaml-content", TextArea)
assert "status:" not in text_area.text

await pilot.press("m")
await pilot.pause()

assert screen.yaml_mode == "full"
text_area = screen.query_one("#yaml-content", TextArea)
assert "status:" in text_area.text
```

- [ ] **Step 6: Run yaml tests — expect all pass**

```bash
uv run pytest tests/test_app.py -v -k "yaml"
```

Expected: all PASS.

- [ ] **Step 7: Run full test suite**

```bash
uv run pytest tests/ -v
```

Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add src/gantry/screens.py tests/test_app.py
git commit -m "feat(yaml): default YAML panel to spec view on open"
```
