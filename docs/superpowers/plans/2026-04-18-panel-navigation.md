# Panel Navigation & Live Sidebar Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Tab/Shift+Tab panel navigation with left/right arrow keys, and implement live resource preview when browsing the sidebar with up/down arrows (no Enter needed).

**Architecture:** Add a `current_panel` reactive variable to track focus state (sidebar/table/search). Left/right arrow handlers cycle through panels and manage focus transitions. Change sidebar event handler from `on_list_view_selected` (Enter-based) to `on_list_view_highlighted` (arrow-based) to trigger resource updates on every keystroke. Tab key remains unchanged for screen switching.

**Tech Stack:** Textual (ListView, focus management), Python reactive variables, pytest for testing.

---

## File Structure

- **src/gantry/screens.py** — Modify `ClusterScreen` and `HelmScreen` classes
  - Add `current_panel` reactive variable (tracks which panel has focus)
  - Add left/right arrow keybindings
  - Implement `action_focus_next_panel()` and `action_focus_previous_panel()` handlers
  - Change sidebar event from `on_list_view_selected()` to `on_list_view_highlighted()`
  - Add focus management via `query_one()` and `.focus()`

- **tests/test_app.py** — Add panel navigation and live preview tests
  - Test left arrow cycles panels backward
  - Test right arrow cycles panels forward
  - Test sidebar up/down immediately updates resources
  - Test focus transitions to correct panel

---

## Task 1: Add current_panel Reactive Variable to ClusterScreen

**Files:**
- Modify: `src/gantry/screens.py` (ClusterScreen class, around line 283 where `_RESOURCE_TYPES` is defined)

- [ ] **Step 1: Locate ClusterScreen class definition and reactive imports**

Read lines 1-50 of `src/gantry/screens.py` to verify `from textual.reactive import reactive` is imported.

Expected: Should see `from textual.reactive import reactive` near the top.

- [ ] **Step 2: Add current_panel reactive variable to ClusterScreen**

Find the line with `_RESOURCE_TYPES = ["Pods", "Services", "Deployments", "ConfigMaps"]` (around line 283).

Add right after it:

```python
# Panel focus state: tracks which panel currently has focus
current_panel = reactive("sidebar")  # "sidebar", "table", or "search"
```

- [ ] **Step 3: Verify the edit**

Read lines 280-290 of `src/gantry/screens.py` to confirm `current_panel` reactive variable is added.

Expected: Should see both `_RESOURCE_TYPES` and `current_panel` defined as class attributes.

- [ ] **Step 4: Commit**

```bash
git add src/gantry/screens.py
git commit -m "feat: Add current_panel reactive variable to ClusterScreen"
```

---

## Task 2: Add Left/Right Arrow Keybindings to ClusterScreen

**Files:**
- Modify: `src/gantry/screens.py` (ClusterScreen BINDINGS list, around line 288-300)

- [ ] **Step 1: Locate ClusterScreen BINDINGS list**

Search for `BINDINGS = [` in ClusterScreen (around line 288).

Expected: Should find a list with entries like `("tab", "app.action_switch_screen", "Switch to Helm View")`.

- [ ] **Step 2: Add left/right arrow bindings**

Add two new bindings at the START of the BINDINGS list (before "tab"):

```python
BINDINGS = [
    # Panel navigation (replaces manual Tab usage for panels)
    ("left", "focus_previous_panel", "Previous Panel"),
    ("right", "focus_next_panel", "Next Panel"),
    
    # Existing keybindings continue...
    ("tab", "app.action_switch_screen", "Switch to Helm View"),
    # ... rest of bindings
]
```

- [ ] **Step 3: Verify the edit**

Read the BINDINGS section to confirm left/right are added.

Expected: Should see left and right as first two entries.

- [ ] **Step 4: Commit**

```bash
git add src/gantry/screens.py
git commit -m "feat: Add left/right arrow keybindings to ClusterScreen"
```

---

## Task 3: Implement action_focus_next_panel in ClusterScreen

**Files:**
- Modify: `src/gantry/screens.py` (ClusterScreen, add new action handler method)

- [ ] **Step 1: Find where to add the action handler**

Search for `def action_show_logs(self)` in ClusterScreen (around line 500-600).

This is near other action handlers. We'll add our new handlers nearby.

- [ ] **Step 2: Add action_focus_next_panel method**

Add this method right after `on_list_view_selected()` handler (after the resource fetching handlers):

```python
def action_focus_next_panel(self) -> None:
    """Move focus to the next panel (right arrow).
    
    Cycles: sidebar → table → search → sidebar
    """
    # Map current panel to next panel
    next_panels = {
        "sidebar": "table",
        "table": "search",
        "search": "sidebar",
    }
    next_panel = next_panels.get(self.current_panel, "sidebar")
    self.current_panel = next_panel
    
    # Move focus to the target panel widget
    try:
        if next_panel == "sidebar":
            self.query_one("#resource-type-sidebar", ListView).focus()
        elif next_panel == "table":
            self.query_one("#resource-table", ResourceTable).focus()
        elif next_panel == "search":
            self.query_one("#search-input", SearchInput).focus()
    except Exception as e:
        logger.debug(f"Error focusing panel: {e}")
```

- [ ] **Step 3: Verify the edit**

Read the method you just added to confirm it's correct.

Expected: Should see the method with clear panel cycling logic and focus calls.

- [ ] **Step 4: Commit**

```bash
git add src/gantry/screens.py
git commit -m "feat: Implement action_focus_next_panel in ClusterScreen"
```

---

## Task 4: Implement action_focus_previous_panel in ClusterScreen

**Files:**
- Modify: `src/gantry/screens.py` (ClusterScreen, add new action handler method)

- [ ] **Step 1: Add action_focus_previous_panel method**

Add this method right after `action_focus_next_panel()`:

```python
def action_focus_previous_panel(self) -> None:
    """Move focus to the previous panel (left arrow).
    
    Cycles: search ← table ← sidebar ← search
    """
    # Map current panel to previous panel
    prev_panels = {
        "sidebar": "search",
        "table": "sidebar",
        "search": "table",
    }
    prev_panel = prev_panels.get(self.current_panel, "sidebar")
    self.current_panel = prev_panel
    
    # Move focus to the target panel widget
    try:
        if prev_panel == "sidebar":
            self.query_one("#resource-type-sidebar", ListView).focus()
        elif prev_panel == "table":
            self.query_one("#resource-table", ResourceTable).focus()
        elif prev_panel == "search":
            self.query_one("#search-input", SearchInput).focus()
    except Exception as e:
        logger.debug(f"Error focusing panel: {e}")
```

- [ ] **Step 2: Verify the edit**

Read both `action_focus_next_panel()` and `action_focus_previous_panel()` to confirm they are opposites.

Expected: Previous should reverse the mapping of next.

- [ ] **Step 3: Commit**

```bash
git add src/gantry/screens.py
git commit -m "feat: Implement action_focus_previous_panel in ClusterScreen"
```

---

## Task 5: Change Sidebar Event Handler from on_list_view_selected to on_list_view_highlighted

**Files:**
- Modify: `src/gantry/screens.py` (ClusterScreen, replace event handler)

- [ ] **Step 1: Locate on_list_view_selected handler**

Search for `def on_list_view_selected(self, event: ListView.Selected)` in ClusterScreen (around line 470-490).

Expected: Should find a method that sets `self.current_resource_type = self._RESOURCE_TYPES[event.index]`.

- [ ] **Step 2: Replace with on_list_view_highlighted**

Replace the entire method signature and implementation:

**OLD:**
```python
def on_list_view_selected(self, event: ListView.Selected) -> None:
    if event.list_view.id == "resource-type-sidebar":
        self.current_resource_type = self._RESOURCE_TYPES[event.index]
```

**NEW:**
```python
def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
    """Handle sidebar up/down navigation - immediately update resource type.
    
    This replaces on_list_view_selected (Enter-based) to trigger on every
    up/down arrow press, providing live preview of resource types.
    """
    if event.list_view.id == "resource-type-sidebar":
        self.current_resource_type = self._RESOURCE_TYPES[event.index]
```

- [ ] **Step 3: Verify the edit**

Read the new `on_list_view_highlighted()` method.

Expected: Should see method name changed and event type changed to `ListView.Highlighted`.

- [ ] **Step 4: Run a quick test to verify sidebar still works**

```bash
uv run pytest tests/test_app.py::test_sidebar_selection_changes_resource_type -v
```

Expected: PASS (sidebar arrow navigation should still trigger resource updates).

- [ ] **Step 5: Commit**

```bash
git add src/gantry/screens.py
git commit -m "feat: Change sidebar handler to on_list_view_highlighted for live preview"
```

---

## Task 6: Add Current Panel Tracking to ClusterScreen on_mount

**Files:**
- Modify: `src/gantry/screens.py` (ClusterScreen.on_mount method)

- [ ] **Step 1: Locate on_mount method**

Search for `def on_mount(self) -> None:` in ClusterScreen (around line 318).

Expected: Should find the method with `_load_context_info()` call.

- [ ] **Step 2: Add panel initialization**

At the END of `on_mount()`, just before the final closing or after all other setup, add:

```python
# Initialize panel focus to sidebar
self.current_panel = "sidebar"
```

- [ ] **Step 3: Verify the edit**

Read the on_mount method to confirm current_panel is initialized.

Expected: Should see `self.current_panel = "sidebar"` near the end.

- [ ] **Step 4: Commit**

```bash
git add src/gantry/screens.py
git commit -m "feat: Initialize current_panel on ClusterScreen mount"
```

---

## Task 7: Apply Panel Navigation to HelmScreen (Same Pattern)

**Files:**
- Modify: `src/gantry/screens.py` (HelmScreen class)

- [ ] **Step 1: Locate HelmScreen class and add current_panel reactive**

Find `class HelmScreen` definition (around line 850-900).

Find where `_RESOURCE_TYPES` or class attributes are defined in HelmScreen, or find the first method after class declaration.

Add right after class declaration or near other reactive variables:

```python
# Panel focus state: tracks which panel currently has focus
current_panel = reactive("sidebar")  # "sidebar", "table", or "search"
```

- [ ] **Step 2: Add left/right keybindings to HelmScreen BINDINGS**

Find `BINDINGS = [` in HelmScreen (around line 900-920).

Add at the START:

```python
BINDINGS = [
    # Panel navigation (replaces manual Tab usage for panels)
    ("left", "focus_previous_panel", "Previous Panel"),
    ("right", "focus_next_panel", "Next Panel"),
    
    # Existing keybindings continue...
    ("tab", "app.action_switch_screen", "Switch to Cluster View"),
    # ... rest of bindings
]
```

- [ ] **Step 3: Add action_focus_next_panel and action_focus_previous_panel to HelmScreen**

Copy the same two methods from ClusterScreen and add them to HelmScreen. The logic is identical:

```python
def action_focus_next_panel(self) -> None:
    """Move focus to the next panel (right arrow).
    
    Cycles: sidebar → table → search → sidebar
    """
    # Map current panel to next panel
    next_panels = {
        "sidebar": "table",
        "table": "search",
        "search": "sidebar",
    }
    next_panel = next_panels.get(self.current_panel, "sidebar")
    self.current_panel = next_panel
    
    # Move focus to the target panel widget
    try:
        if next_panel == "sidebar":
            self.query_one("#chart-repo-sidebar", ListView).focus()
        elif next_panel == "table":
            self.query_one("#chart-table", DataTable).focus()
        elif next_panel == "search":
            self.query_one("#search-input", SearchInput).focus()
    except Exception as e:
        logger.debug(f"Error focusing panel: {e}")

def action_focus_previous_panel(self) -> None:
    """Move focus to the previous panel (left arrow).
    
    Cycles: search ← table ← sidebar ← search
    """
    # Map current panel to previous panel
    prev_panels = {
        "sidebar": "search",
        "table": "sidebar",
        "search": "table",
    }
    prev_panel = prev_panels.get(self.current_panel, "sidebar")
    self.current_panel = prev_panel
    
    # Move focus to the target panel widget
    try:
        if prev_panel == "sidebar":
            self.query_one("#chart-repo-sidebar", ListView).focus()
        elif prev_panel == "table":
            self.query_one("#chart-table", DataTable).focus()
        elif prev_panel == "search":
            self.query_one("#search-input", SearchInput).focus()
    except Exception as e:
        logger.debug(f"Error focusing panel: {e}")
```

- [ ] **Step 4: Initialize current_panel in HelmScreen on_mount**

Find `def on_mount(self)` in HelmScreen.

Add `self.current_panel = "sidebar"` at the end, similar to ClusterScreen.

- [ ] **Step 5: Verify HelmScreen edits**

Read the HelmScreen class to confirm:
- current_panel reactive variable added
- left/right keybindings added
- action_focus_next_panel and action_focus_previous_panel methods added
- on_mount initializes current_panel

Expected: All four changes should be visible.

- [ ] **Step 6: Commit**

```bash
git add src/gantry/screens.py
git commit -m "feat: Add panel navigation to HelmScreen"
```

---

## Task 8: Write Test for Left Arrow Panel Cycling

**Files:**
- Modify: `tests/test_app.py` (add new test)

- [ ] **Step 1: Add test after existing sidebar tests**

Find the end of `test_sidebar_selection_changes_resource_type()` (around line 143).

Add right after it:

```python
@pytest.mark.asyncio
async def test_panel_navigation_right_arrow():
    """Test that pressing right arrow cycles panels forward."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)
        
        # Start on sidebar
        assert screen.current_panel == "sidebar"
        
        # Right arrow → table
        await pilot.press("right")
        await pilot.pause()
        assert screen.current_panel == "table"
        
        # Right arrow → search
        await pilot.press("right")
        await pilot.pause()
        assert screen.current_panel == "search"
        
        # Right arrow → sidebar (wraps)
        await pilot.press("right")
        await pilot.pause()
        assert screen.current_panel == "sidebar"
```

- [ ] **Step 2: Run the test to verify it passes**

```bash
uv run pytest tests/test_app.py::test_panel_navigation_right_arrow -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_app.py
git commit -m "test: Add test for right arrow panel navigation"
```

---

## Task 9: Write Test for Right Arrow Panel Cycling

**Files:**
- Modify: `tests/test_app.py` (add new test)

- [ ] **Step 1: Add test after right arrow test**

Add right after `test_panel_navigation_right_arrow()`:

```python
@pytest.mark.asyncio
async def test_panel_navigation_left_arrow():
    """Test that pressing left arrow cycles panels backward."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)
        
        # Start on sidebar, move to search first
        await pilot.press("right")
        await pilot.press("right")
        await pilot.pause()
        assert screen.current_panel == "search"
        
        # Left arrow → table
        await pilot.press("left")
        await pilot.pause()
        assert screen.current_panel == "table"
        
        # Left arrow → sidebar
        await pilot.press("left")
        await pilot.pause()
        assert screen.current_panel == "sidebar"
        
        # Left arrow → search (wraps)
        await pilot.press("left")
        await pilot.pause()
        assert screen.current_panel == "search"
```

- [ ] **Step 2: Run the test to verify it passes**

```bash
uv run pytest tests/test_app.py::test_panel_navigation_left_arrow -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_app.py
git commit -m "test: Add test for left arrow panel navigation"
```

---

## Task 10: Write Test for Live Sidebar Preview (Up/Down Updates Resources)

**Files:**
- Modify: `tests/test_app.py` (add new test)

- [ ] **Step 1: Add test after left arrow test**

Add after `test_panel_navigation_left_arrow()`:

```python
@pytest.mark.asyncio
async def test_sidebar_up_down_updates_resources():
    """Test that navigating sidebar with arrows immediately updates resource type.
    
    Previously, Enter was required to apply the selection. Now up/down
    navigation immediately triggers a resource type change and fetch.
    """
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)
        
        # Start on Pods
        assert screen.current_resource_type == "Pods"
        
        # Down arrow to Services
        await pilot.press("down")
        await pilot.pause()
        assert screen.current_resource_type == "Services"
        
        # Down arrow to Deployments
        await pilot.press("down")
        await pilot.pause()
        assert screen.current_resource_type == "Deployments"
        
        # Up arrow back to Services
        await pilot.press("up")
        await pilot.pause()
        assert screen.current_resource_type == "Services"
```

- [ ] **Step 2: Run the test to verify it passes**

```bash
uv run pytest tests/test_app.py::test_sidebar_up_down_updates_resources -v
```

Expected: PASS (this test relies on on_list_view_highlighted being triggered by arrow keys)

- [ ] **Step 3: Commit**

```bash
git add tests/test_app.py
git commit -m "test: Add test for live sidebar preview via arrow navigation"
```

---

## Task 11: Run Full Test Suite and Verify No Regressions

**Files:**
- No files modified, validation only

- [ ] **Step 1: Run full test suite**

```bash
uv run pytest tests/ -v
```

Expected: All tests pass (at least 74+ tests, including 3 new panel navigation tests).

- [ ] **Step 2: Check for any failures**

If any tests fail:
- Note the failing test name and error message
- Read the test to understand what it expects
- Check the implementation in screens.py for the corresponding behavior
- Fix the issue and re-run

Expected outcome: All tests pass with no failures or skips.

- [ ] **Step 3: Run with coverage if desired (optional)**

```bash
uv run pytest tests/ --cov=src/gantry --cov-report=term-missing
```

Expected: Coverage should be at or above previous baseline (looking for no regressions).

- [ ] **Step 4: Commit**

```bash
git add tests/test_app.py src/gantry/screens.py
git commit -m "test: Verify all tests pass with panel navigation implementation"
```

---

## Task 12: Manual Testing and UI Verification

**Files:**
- No files modified, manual verification only

- [ ] **Step 1: Start the app in cluster view**

```bash
uv run python -m gantry
```

Expected: App starts on ClusterScreen with Pods selected, sidebar has focus.

- [ ] **Step 2: Test right arrow panel cycling**

- Press right arrow → focus should move to resource table (table should highlight)
- Press right arrow again → focus should move to search input (input should be active, cursor visible)
- Press right arrow again → focus should wrap back to sidebar (sidebar highlight visible)

Expected: Smooth focus transitions, visual feedback from borders/colors changing.

- [ ] **Step 3: Test left arrow panel cycling**

- Press left arrow → focus should move backwards through panels
- Verify reverse cycling works as expected

Expected: Same smooth transitions as right arrow, but in reverse.

- [ ] **Step 4: Test live sidebar preview**

- Navigate sidebar with up/down arrows (don't press Enter)
- Verify resource table updates immediately on each arrow press
- Example: Down arrow → Services, resource table shows services; Down again → Deployments, table updates to show deployments

Expected: No need to press Enter; resources update as you navigate.

- [ ] **Step 5: Test Tab still switches screens**

- Press Tab from Cluster view → should switch to Helm view
- Press Tab from Helm view → should switch back to Cluster view
- Existing Tab functionality unchanged

Expected: Tab continues to work for screen switching.

- [ ] **Step 6: Test search still works**

- From Cluster view, press "/" → search input should activate
- Type a search term → resource table should filter
- Escape to close search

Expected: Search functionality unchanged.

- [ ] **Step 7: Quit the app**

```
Press 'q' to quit
```

Expected: App closes cleanly.

- [ ] **Step 8: Final commit summary**

```bash
git log --oneline -10
```

Expected: Should see approximately 12 commits related to panel navigation (Tasks 1-12).

---

## Verification Against Spec

**Panel Navigation (Left/Right Arrows):**
- ✅ Task 2: Added left/right keybindings
- ✅ Task 3-4: Implemented action_focus_next_panel and action_focus_previous_panel
- ✅ Task 1: current_panel reactive variable for state tracking
- ✅ Task 8-9: Tests for left/right cycling

**Live Sidebar Preview (Up/Down Arrows):**
- ✅ Task 5: Changed on_list_view_selected to on_list_view_highlighted
- ✅ Task 10: Test for immediate resource updates on arrow navigation
- ✅ Task 12: Manual verification of live preview

**Focus Management:**
- ✅ Task 3-4: Focus transitions via query_one().focus()
- ✅ Task 6, 7: current_panel initialization on mount
- ✅ Task 12: Manual verification of focus transitions

**HelmScreen Consistency:**
- ✅ Task 7: Applied same pattern to HelmScreen

**Testing:**
- ✅ Task 8-11: Comprehensive test coverage with no regressions

---

## Plan complete and saved to `docs/superpowers/plans/2026-04-18-panel-navigation.md`.

Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
