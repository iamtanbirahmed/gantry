# Vim-Style Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace always-visible `ctrl+f` search with vim-style `/`-triggered search that hides by default, shows on `/`, confirms with Enter, and cancels with Escape.

**Architecture:** SearchInput gains show/hide state via a CSS `show` class. Both ClusterScreen and HelmScreen switch their binding back to `slash` and update `action_focus_search` to add the `show` class before focusing. The SearchInput widget handles Enter (hide + keep filter) and Escape (hide + clear filter) entirely.

**Tech Stack:** Python, Textual TUI framework, pytest

---

### Task 1: Update SearchInput to support hide/show and vim key handling

**Files:**
- Modify: `src/gantry/widgets.py:125-185`

- [ ] **Step 1: Update SearchInput CSS to be hidden by default and add `.show` rule**

In `src/gantry/widgets.py`, replace the `SearchInput` CSS block (lines 139-156):

```python
    CSS = """
    SearchInput {
        height: 1;
        width: 100%;
        border: solid $accent;
        padding: 0 1;
        margin: 1 0;
        display: none;
    }

    SearchInput.show {
        display: block;
    }

    SearchInput:focus {
        border: double $accent;
        background: $boost;
    }

    SearchInput Input {
        border: none;
    }
    """
```

- [ ] **Step 2: Update `_on_key` to handle Enter (confirm) and Escape (cancel) with hide logic**

Replace the `_on_key` method (lines 167-185):

```python
    def _on_key(self, event: Key) -> None:
        """Handle key events for search input."""
        if event.key == "escape":
            event.stop()
            self.value = ""
            self.post_message(self.SearchChanged(""))
            self.remove_class("show")
            try:
                table = self.screen.query_one(ResourceTable)
                table.focus()
            except Exception:
                pass
        elif event.key == "enter":
            event.stop()
            self.remove_class("show")
            try:
                table = self.screen.query_one(ResourceTable)
                table.focus()
            except Exception:
                pass
        elif event.key == "right":
            event.stop()
            self.screen.action_focus_next_panel()
        elif event.key == "left":
            event.stop()
            self.screen.action_focus_previous_panel()
        else:
            super()._on_key(event)
```

- [ ] **Step 3: Commit widget changes**

```bash
git add src/gantry/widgets.py
git commit -m "feat: SearchInput hidden by default, Enter confirms, Escape hides+clears"
```

---

### Task 2: Update ClusterScreen binding and action

**Files:**
- Modify: `src/gantry/screens.py:197,249-254,516-519`

- [ ] **Step 1: Change ClusterScreen binding from `ctrl+f` to `slash`**

In `src/gantry/screens.py` line 197, replace:

```python
        Binding("ctrl+f", "focus_search", "Search", priority=True),
```

with:

```python
        Binding("slash", "focus_search", "Search", priority=True),
```

- [ ] **Step 2: Add `display: none` to ClusterScreen SearchInput CSS**

In `src/gantry/screens.py`, the ClusterScreen CSS block has (lines 249-254):

```css
    SearchInput {
        height: 1;
        width: 100%;
        border: solid $accent;
        padding: 0 1;
    }
```

Replace with:

```css
    SearchInput {
        height: 1;
        width: 100%;
        border: solid $accent;
        padding: 0 1;
        display: none;
    }

    SearchInput.show {
        display: block;
    }
```

- [ ] **Step 3: Update ClusterScreen `action_focus_search` to show then focus**

In `src/gantry/screens.py` lines 516-519, replace:

```python
    def action_focus_search(self) -> None:
        """Focus on the search input."""
        search_input: SearchInput = self.query_one("#search-input", SearchInput)
        search_input.focus()
```

with:

```python
    def action_focus_search(self) -> None:
        """Show and focus the search input (vim-style)."""
        search_input: SearchInput = self.query_one("#search-input", SearchInput)
        search_input.add_class("show")
        search_input.focus()
```

- [ ] **Step 4: Run tests to check nothing is broken**

```bash
uv run pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit ClusterScreen changes**

```bash
git add src/gantry/screens.py
git commit -m "feat: ClusterScreen uses slash binding and show/hide for search"
```

---

### Task 3: Update HelmScreen binding and action

**Files:**
- Modify: `src/gantry/screens.py:852,905-910,1113-1116`

- [ ] **Step 1: Change HelmScreen binding from `ctrl+f` to `slash`**

In `src/gantry/screens.py` line 852, replace:

```python
        Binding("ctrl+f", "focus_search", "Search", priority=True),
```

with:

```python
        Binding("slash", "focus_search", "Search", priority=True),
```

- [ ] **Step 2: Add `display: none` to HelmScreen SearchInput CSS**

In `src/gantry/screens.py`, the HelmScreen CSS block has (lines 905-910):

```css
    SearchInput {
        height: 1;
        width: 100%;
        border: solid $accent;
        padding: 0 1;
    }
```

Replace with:

```css
    SearchInput {
        height: 1;
        width: 100%;
        border: solid $accent;
        padding: 0 1;
        display: none;
    }

    SearchInput.show {
        display: block;
    }
```

- [ ] **Step 3: Update HelmScreen `action_focus_search` to show then focus**

In `src/gantry/screens.py` lines 1113-1116, replace:

```python
    def action_focus_search(self) -> None:
        """Focus on the search input."""
        search_input: SearchInput = self.query_one("#search-input", SearchInput)
        search_input.focus()
```

with:

```python
    def action_focus_search(self) -> None:
        """Show and focus the search input (vim-style)."""
        search_input: SearchInput = self.query_one("#search-input", SearchInput)
        search_input.add_class("show")
        search_input.focus()
```

- [ ] **Step 4: Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit HelmScreen changes**

```bash
git add src/gantry/screens.py
git commit -m "feat: HelmScreen uses slash binding and show/hide for search"
```

---

### Task 4: Update test for search_active keybindings hint

**Files:**
- Modify: `tests/test_app.py:299-302`

The `test_keybindings_bar_search_active` test asserts `"↵ Select"` which matches Enter-to-confirm. Verify no test assertions need updating for the new binding (`slash` was already expected in the `"/ Search"` hints).

- [ ] **Step 1: Run the full test suite to confirm all pass**

```bash
uv run pytest tests/ -v
```

Expected: all 81+ tests pass with no failures.

- [ ] **Step 2: Commit if any test fixes were needed**

Only commit if tests required changes. If all pass, skip this step.

```bash
git add tests/
git commit -m "test: update tests for vim-style search"
```
