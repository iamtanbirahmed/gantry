# Right Panel Detail Viewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a right-side scrollable detail panel for resource descriptions and pod logs on ClusterScreen.

**Architecture:** Replace the bottom-bar Label widget with a VerticalScroll + Static combo in the right sidebar (40% width). Panel is hidden by default, toggled via `d`/`l` keys, and supports arrow-key navigation with auto-focus. Panel navigation cycle becomes sidebar ↔ table ↔ detail (when visible).

**Tech Stack:** Textual (VerticalScroll, Static widgets), existing k8s and state modules

---

## File Structure

**Modified Files:**
- `src/gantry/screens.py` — ClusterScreen layout, navigation, detail panel helpers, CSS
- `tests/test_app.py` — Add tests for detail panel visibility, focus, and Escape handling

**No new files created.**

---

## Task 1: Update ClusterScreen.compose() to move detail panel to right sidebar

**Files:**
- Modify: `src/gantry/screens.py:303-323`

The `compose()` method currently yields `#detail-panel` as a standalone Label at the bottom. Move it into `#main-container` as a right sidebar with VerticalScroll + Static inside.

- [ ] **Step 1: Open `screens.py` and locate the `compose()` method (line 303)**

Current structure at lines 303-323:
```python
def compose(self):
    """Compose the cluster screen."""
    # Main container with sidebar and content
    with Horizontal(id="main-container"):
        yield ListView(...)
        with Vertical(id="content-area"):
            yield ResourceTable(id="resource-table")
            yield SearchInput(id="search-input")

    # Detail panel for descriptions and logs
    yield Label(id="detail-panel")

    # Status bar
    yield StatusBar(id="status-bar")
```

- [ ] **Step 2: Import VerticalScroll at the top of screens.py**

At line 6, add `VerticalScroll` to the imports:

```python
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer, VerticalScroll
```

- [ ] **Step 3: Rewrite compose() to move detail-panel into #main-container**

Replace lines 303-323 with:

```python
def compose(self):
    """Compose the cluster screen."""
    # Main container with sidebar, content, and detail panel
    with Horizontal(id="main-container"):
        yield ListView(
            ListItem(Label("Pods")),
            ListItem(Label("Services")),
            ListItem(Label("Deployments")),
            ListItem(Label("ConfigMaps")),
            id="resource-type-sidebar",
            initial_index=0,
        )
        with Vertical(id="content-area"):
            yield ResourceTable(id="resource-table")
            yield SearchInput(id="search-input")

        # Detail panel for descriptions and logs (right sidebar)
        with VerticalScroll(id="detail-panel"):
            yield Static(id="detail-panel-content")

    # Status bar
    yield StatusBar(id="status-bar")
```

---

## Task 2: Update CSS for the new detail panel layout

**Files:**
- Modify: `src/gantry/screens.py:204-279` (CSS block in ClusterScreen)

The CSS currently styles `#detail-panel` as a bottom bar with `height: auto`. Change it to a right sidebar with fixed 40% width.

- [ ] **Step 1: Locate the CSS block (line 204)**

Current `#detail-panel` CSS at lines 260-273:
```python
#detail-panel {
    height: auto;
    border: solid $accent;
    display: none;
    background: $boost;
    color: $text;
    padding: 1;
    margin: 1 0;
}

#detail-panel.show {
    display: block;
    height: auto;
}
```

- [ ] **Step 2: Add CSS for #detail-panel as a right sidebar and #detail-panel-content**

Replace the `#detail-panel` CSS block (lines 260-273) with:

```python
#detail-panel {
    width: 40%;
    height: 100%;
    border-left: solid $accent;
    background: $panel;
    padding: 0;
    display: none;
}

#detail-panel.show {
    display: block;
}

#detail-panel > Static {
    width: 100%;
    height: 100%;
    padding: 1;
    border: none;
}
```

---

## Task 3: Add reactive state for detail panel visibility

**Files:**
- Modify: `src/gantry/screens.py:284-289` (reactive state block)

Add a new reactive variable to track whether the detail panel is open.

- [ ] **Step 1: Locate the reactive state block (line 284)**

Current state at lines 284-289:
```python
current_resource_type = reactive("Pods", init=False)
current_namespace = reactive("default")
current_context = reactive("N/A")
connection_status = reactive("Disconnected")
# Panel focus state: tracks which panel currently has focus
current_panel = reactive("sidebar")  # "sidebar", "table", or "search"
```

- [ ] **Step 2: Add detail panel visibility state**

Add after line 289:

```python
    detail_panel_open = reactive(False)  # Tracks if detail panel is visible
```

---

## Task 4: Add helper methods to show and close the detail panel

**Files:**
- Modify: `src/gantry/screens.py` (add new methods after `_display_detail_panel()` at line 587)

Add two new methods: `_show_detail_panel()` (displays content, shows panel, updates focus cycle) and `_close_detail_panel()` (hides panel, updates focus cycle, returns focus to table).

- [ ] **Step 1: Locate where to insert new methods**

Find `_display_detail_panel()` at line 578. New methods go after it, around line 587.

- [ ] **Step 2: Add `_show_detail_panel()` method**

Add this method after line 587:

```python
def _show_detail_panel(self, title: str, content: str) -> None:
    """Show the detail panel with the given title and content.
    
    Args:
        title: Panel header (e.g. "DESCRIBE", "LOGS")
        content: Text content to display
    """
    try:
        # Get the detail panel and its content widget
        detail_panel = self.query_one("#detail-panel", VerticalScroll)
        detail_content = self.query_one("#detail-panel-content", Static)
        
        # Format content with title
        formatted = f"{title}\n\n{content}"
        detail_content.update(formatted)
        
        # Show the panel
        detail_panel.add_class("show")
        self.detail_panel_open = True
        
        # Update panel focus cycle to include "detail"
        self.current_panel = "detail"
        detail_panel.focus()
        
        # Update status bar with hint
        self.connection_status = f"Detail: {title} | ESC to close · ↑↓ scroll"
        self._update_status_bar()
        
        logger.debug(f"_show_detail_panel: {title}")
    except Exception as e:
        logger.error(f"Error showing detail panel: {e}")
```

- [ ] **Step 3: Add `_close_detail_panel()` method**

Add this method after `_show_detail_panel()`:

```python
def _close_detail_panel(self) -> None:
    """Close the detail panel and return focus to the table."""
    try:
        detail_panel = self.query_one("#detail-panel", VerticalScroll)
        detail_panel.remove_class("show")
        self.detail_panel_open = False
        
        # Clear the content
        detail_content = self.query_one("#detail-panel-content", Static)
        detail_content.update("")
        
        # Return focus to table
        self.current_panel = "table"
        table = self.query_one("#resource-table", ResourceTable)
        table.focus()
        
        # Restore normal status bar
        self.connection_status = "Connected"
        self._update_status_bar()
        
        logger.debug("_close_detail_panel")
    except Exception as e:
        logger.error(f"Error closing detail panel: {e}")
```

---

## Task 5: Update `_apply_describe_result()` to use the new detail panel helper

**Files:**
- Modify: `src/gantry/screens.py:536-540` (the `_apply_describe_result()` method)

Change the method to call `_show_detail_panel()` instead of `_display_detail_panel()`.

- [ ] **Step 1: Locate `_apply_describe_result()` at line 536**

Current implementation:
```python
def _apply_describe_result(self, description: str, status: str) -> None:
    """Apply describe result on main thread."""
    self._display_detail_panel(description)
    self.connection_status = status
    self._update_status_bar()
```

- [ ] **Step 2: Replace with new implementation**

Replace lines 536-540 with:

```python
def _apply_describe_result(self, description: str, status: str) -> None:
    """Apply describe result on main thread."""
    self._show_detail_panel("DESCRIBE", description)
```

---

## Task 6: Create new `_apply_logs_result()` method for logs handling

**Files:**
- Modify: `src/gantry/screens.py` (add new method after `_show_logs_worker()` at line 619)

Currently, `_show_logs_worker()` calls `_apply_describe_result()` which is confusing. Create a dedicated method for logs and update the worker to call it.

- [ ] **Step 1: Create `_apply_logs_result()` method**

Add this method after `_show_logs_worker()` at line 619:

```python
def _apply_logs_result(self, logs: str, status: str) -> None:
    """Apply logs result on main thread."""
    self._show_detail_panel("LOGS", logs)
```

- [ ] **Step 2: Update `_show_logs_worker()` to call `_apply_logs_result()`**

At line 616, change:
```python
self.app.call_from_thread(self._apply_describe_result, log_display, status)
```

To:
```python
self.app.call_from_thread(self._apply_logs_result, logs, status)
```

Also remove the `log_display` prefix line (613) since we'll format it in `_apply_logs_result()`. Change line 613 from:
```python
log_display = f"=== Logs for {pod_name} ===\n\n{logs}"
```

To just pass `logs` directly.

Full updated `_show_logs_worker()` should be:

```python
@work(thread=True)
def _show_logs_worker(self, pod_name: str, namespace: str) -> None:
    """Worker to fetch and display pod logs."""
    logger.debug(f"_show_logs_worker started for pod {pod_name} in {namespace}")
    logs = k8s.get_pod_logs(pod_name, namespace=namespace)
    if logs:
        status = f"Logs for {pod_name}"
        logger.debug(f"_show_logs_worker completed for pod {pod_name}")
        self.app.call_from_thread(self._apply_logs_result, logs, status)
    else:
        logger.error(f"Failed to retrieve logs for pod {pod_name}")
        self.app.call_from_thread(self._apply_fetch_status, f"Failed to retrieve logs for {pod_name}")
```

---

## Task 7: Update panel navigation cycle to include "detail"

**Files:**
- Modify: `src/gantry/screens.py:629-677` (both `action_focus_next_panel()` and `action_focus_previous_panel()` methods)

The panel cycle currently is: sidebar ↔ table ↔ search. When detail is open, it should be: sidebar ↔ table ↔ detail. Update both methods to check if detail is open.

- [ ] **Step 1: Update `action_focus_next_panel()` (line 629)**

Replace the method with:

```python
def action_focus_next_panel(self) -> None:
    """Move focus to the next panel (right arrow).

    Cycles: sidebar → table → detail (if open) → search → sidebar
    If detail is open, cycles through: sidebar → table → detail → sidebar
    Search is skipped (commented out for now).
    """
    # If detail panel is open, include it in the cycle
    if self.detail_panel_open:
        next_panels = {
            "sidebar": "table",
            "table": "detail",
            "detail": "sidebar",
        }
    else:
        next_panels = {
            "sidebar": "table",
            "table": "sidebar",
        }
    
    next_panel = next_panels.get(self.current_panel, "sidebar")
    self.current_panel = next_panel

    # Move focus to the target panel widget
    try:
        if next_panel == "sidebar":
            self.query_one("#resource-type-sidebar", ListView).focus()
        elif next_panel == "table":
            self.query_one("#resource-table", ResourceTable).focus()
        elif next_panel == "detail":
            self.query_one("#detail-panel", VerticalScroll).focus()
    except Exception as e:
        logger.debug(f"Error focusing panel: {e}")
```

- [ ] **Step 2: Update `action_focus_previous_panel()` (line 654)**

Replace the method with:

```python
def action_focus_previous_panel(self) -> None:
    """Move focus to the previous panel (left arrow).

    Cycles: sidebar ← table ← detail (if open) ← sidebar
    If detail is open, cycles through: sidebar ← detail ← table ← sidebar
    Search is skipped (commented out for now).
    """
    # If detail panel is open, include it in the cycle
    if self.detail_panel_open:
        prev_panels = {
            "sidebar": "detail",
            "table": "sidebar",
            "detail": "table",
        }
    else:
        prev_panels = {
            "sidebar": "table",
            "table": "sidebar",
        }
    
    prev_panel = prev_panels.get(self.current_panel, "sidebar")
    self.current_panel = prev_panel

    # Move focus to the target panel widget
    try:
        if prev_panel == "sidebar":
            self.query_one("#resource-type-sidebar", ListView).focus()
        elif prev_panel == "table":
            self.query_one("#resource-table", ResourceTable).focus()
        elif prev_panel == "detail":
            self.query_one("#detail-panel", VerticalScroll).focus()
    except Exception as e:
        logger.debug(f"Error focusing panel: {e}")
```

---

## Task 8: Add Escape key handler to close the detail panel

**Files:**
- Modify: `src/gantry/screens.py` (add new method or update existing key handler)

Add a handler for the Escape key that closes the detail panel if it's open.

- [ ] **Step 1: Add the `action_close_detail_panel()` action**

Add this method after the panel navigation methods (around line 677):

```python
def action_close_detail_panel(self) -> None:
    """Close the detail panel (Escape key handler)."""
    if self.detail_panel_open:
        self._close_detail_panel()
```

- [ ] **Step 2: Add Escape binding to BINDINGS**

At line 189-202, find the BINDINGS list and add:

```python
("escape", "close_detail_panel", "Close Panel"),
```

Add it after the other panel-related bindings. Full BINDINGS should be:

```python
BINDINGS = [
    # Panel navigation (replaces manual Tab usage for panels)
    ("left", "focus_previous_panel", "Previous Panel"),
    ("right", "focus_next_panel", "Next Panel"),

    # Existing keybindings
    ("escape", "close_detail_panel", "Close Panel"),
    ("tab", "app.action_switch_screen", "Switch to Helm View"),
    ("slash", "focus_search", "Search"),
    ("c", "show_context_picker", "Pick Context"),
    ("d", "describe_resource", "Describe"),
    ("l", "show_logs", "Logs"),
    ("r", "refresh_resources", "Refresh"),
    ("q", "quit", "Quit Gantry"),
]
```

---

## Task 9: Remove the old `_display_detail_panel()` method (cleanup)

**Files:**
- Modify: `src/gantry/screens.py:578-586`

The old `_display_detail_panel()` method is no longer used. Remove it.

- [ ] **Step 1: Locate and delete `_display_detail_panel()`**

Find the method at lines 578-586:

```python
def _display_detail_panel(self, content: str) -> None:
    """Display content in the detail panel."""
    try:
        detail_panel = self.query_one("#detail-panel", Label)
        detail_panel.update(content)
        detail_panel.add_class("show")
    except Exception:
        # If detail panel is not available, just update status bar
        pass
```

Delete this entire method.

---

## Task 10: Write and run tests for detail panel functionality

**Files:**
- Modify: `tests/test_app.py`

Add tests to verify:
1. Detail panel is hidden on mount
2. Pressing `d` opens the detail panel with describe content
3. Pressing `l` on a pod opens the detail panel with logs
4. Pressing `Escape` closes the detail panel
5. Right arrow from table focuses detail panel when open
6. Left arrow from detail panel focuses table

- [ ] **Step 1: Run existing tests to ensure they still pass**

```bash
cd /Users/tanbirsagar/Documents/Personal/Projects/gantry
uv run pytest tests/test_app.py -v
```

Expected: All existing tests pass (or at least, no new failures introduced by layout changes).

- [ ] **Step 2: Add test for detail panel hidden on mount**

Open `tests/test_app.py` and add this test:

```python
async def test_detail_panel_hidden_on_mount(client: Pilot):
    """Detail panel should be hidden by default."""
    screen = client.app.screen
    assert isinstance(screen, ClusterScreen)
    # Check that detail_panel_open is False
    assert screen.detail_panel_open is False
    # Check that detail panel has the hidden class
    detail_panel = screen.query_one("#detail-panel", VerticalScroll)
    assert "show" not in detail_panel.classes
```

- [ ] **Step 3: Add test for detail panel focus cycle**

Add this test:

```python
async def test_panel_navigation_with_detail_open(client: Pilot):
    """Panel cycle should include detail when open."""
    screen = client.app.screen
    assert isinstance(screen, ClusterScreen)
    
    # Open detail panel
    screen.detail_panel_open = True
    screen.query_one("#detail-panel", VerticalScroll).add_class("show")
    
    # Cycle: sidebar -> table -> detail -> sidebar
    screen.action_focus_next_panel()
    assert screen.current_panel == "table"
    
    screen.action_focus_next_panel()
    assert screen.current_panel == "detail"
    
    screen.action_focus_next_panel()
    assert screen.current_panel == "sidebar"
```

- [ ] **Step 4: Add test for Escape closes detail panel**

Add this test:

```python
async def test_escape_closes_detail_panel(client: Pilot):
    """Pressing Escape should close the detail panel."""
    screen = client.app.screen
    assert isinstance(screen, ClusterScreen)
    
    # Manually open the detail panel
    screen.detail_panel_open = True
    screen.query_one("#detail-panel", VerticalScroll).add_class("show")
    
    # Simulate Escape key
    screen.action_close_detail_panel()
    
    # Verify panel is closed
    assert screen.detail_panel_open is False
    detail_panel = screen.query_one("#detail-panel", VerticalScroll)
    assert "show" not in detail_panel.classes
```

- [ ] **Step 5: Run the new tests**

```bash
cd /Users/tanbirsagar/Documents/Personal/Projects/gantry
uv run pytest tests/test_app.py::test_detail_panel_hidden_on_mount -v
uv run pytest tests/test_app.py::test_panel_navigation_with_detail_open -v
uv run pytest tests/test_app.py::test_escape_closes_detail_panel -v
```

Expected: All three tests pass.

---

## Task 11: Commit all changes

**Files:**
- Modified: `src/gantry/screens.py`, `tests/test_app.py`

- [ ] **Step 1: Check git status**

```bash
cd /Users/tanbirsagar/Documents/Personal/Projects/gantry
git status
```

Expected: Shows `src/gantry/screens.py` and `tests/test_app.py` as modified.

- [ ] **Step 2: Review changes**

```bash
git diff src/gantry/screens.py | head -100
```

Verify the layout, helpers, and navigation changes are present.

- [ ] **Step 3: Add files and commit**

```bash
git add src/gantry/screens.py tests/test_app.py
git commit -m "feat: Add right-side scrollable detail panel with focus navigation

- Move detail panel from bottom bar to 40% right sidebar
- Add VerticalScroll + Static widgets for scrollable content
- Implement _show_detail_panel() and _close_detail_panel() helpers
- Update panel navigation cycle to include 'detail' when open
- Add Escape key binding to close detail panel
- Auto-focus detail panel when opened, return focus to table on close
- Update status bar with panel hints when detail is open
- Add tests for detail panel visibility and navigation"
```

---

## Task 12: Manual testing of detail panel functionality

**Files:**
- None (testing only)

Once all code changes are in place, manually test the feature end-to-end.

- [ ] **Step 1: Start Gantry with debug logging**

```bash
cd /Users/tanbirsagar/Documents/Personal/Projects/gantry
uv run python -m gantry --debug
```

- [ ] **Step 2: Navigate to a pod and press `d` to describe**

1. Focus should be on sidebar by default
2. Arrow down or up to navigate to a pod
3. Press `right` twice to move focus to table
4. Press `d` to open detail panel with describe output
5. Verify: Panel appears on right side (40% width), shows "DESCRIBE" header, content is scrollable
6. Verify: Focus automatically moves to detail panel
7. Verify: Status bar shows "Detail: DESCRIBE | ESC to close · ↑↓ scroll"

- [ ] **Step 3: Test panel navigation with detail open**

1. While detail panel is open, press `left` arrow
2. Verify: Focus returns to table
3. Press `right` arrow
4. Verify: Focus returns to detail panel
5. Press `right` arrow again
6. Verify: Focus moves to sidebar (completing the cycle: table → detail → sidebar)

- [ ] **Step 4: Test scrolling in detail panel**

1. With detail panel focused, press `up` and `down` arrows
2. Verify: Content scrolls up and down within the panel
3. Verify: Other widgets don't respond (arrows stay within panel)

- [ ] **Step 5: Test Escape closes panel**

1. With detail panel open and focused, press `Escape`
2. Verify: Panel closes and hides
3. Verify: Focus returns to table
4. Verify: Status bar returns to normal
5. Verify: Panel cycle reverts to sidebar ↔ table (no detail)

- [ ] **Step 6: Test logs panel**

1. Ensure you're viewing Pods (check sidebar)
2. Select a pod with the cursor in the table
3. Press `l` to show logs
4. Verify: Detail panel appears with "LOGS" header and log content
5. Verify: Logs are scrollable and focus is in the panel
6. Press `Escape` to close

- [ ] **Step 7: Test describe on non-pod resources**

1. Navigate sidebar to "Services" or "Deployments"
2. Focus table and select a resource
3. Press `d` to describe
4. Verify: Panel opens with service/deployment description
5. Verify: Content is appropriate for the resource type

---

## Verification & Success Criteria

All of the following should be true:
- [ ] Detail panel is a right sidebar (40% width) when visible
- [ ] Detail panel is scrollable (VerticalScroll + Static)
- [ ] Detail panel is hidden by default (`display: none`)
- [ ] Pressing `d` on a resource opens the detail panel with describe output
- [ ] Pressing `l` on a pod opens the detail panel with logs
- [ ] Detail panel auto-focuses when opened
- [ ] Arrow keys navigate between sidebar, table, and detail panel (when open)
- [ ] `Up`/`Down` arrows scroll content within the detail panel (when focused)
- [ ] `Escape` closes the detail panel and returns focus to table
- [ ] Panel focus cycle is correct: sidebar → table → detail → sidebar (when detail open)
- [ ] Status bar updates with panel hints (e.g., "Detail: DESCRIBE | ESC to close · ↑↓ scroll")
- [ ] All existing tests still pass
- [ ] New tests for detail panel functionality pass
- [ ] Manual testing confirms all above behaviors work as expected
