# KeybindingsBar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a context-aware keybindings bar that displays abbreviated bindings in the footer, updating based on screen, panel focus, detail panel state, and search state.

**Architecture:** New `KeybindingsBar` static widget in widgets.py with context-aware render() logic. Both ClusterScreen and HelmScreen yield it after StatusBar. State changes (panel focus, detail panel open/close, search active) trigger bar updates via watchers.

**Tech Stack:** Textual (Static widget), existing reactive properties (current_panel, detail_panel_open)

---

## File Structure

**Modified Files:**
- `src/gantry/widgets.py` — Add KeybindingsBar class (~80 lines)
- `src/gantry/screens.py` — Update ClusterScreen and HelmScreen to yield bar, add watchers, update CSS
- `tests/test_app.py` — Add tests for KeybindingsBar render logic (optional but recommended)

**No new files created.**

---

## Task 1: Create KeybindingsBar class with __init__ and state management

**Files:**
- Modify: `src/gantry/widgets.py` (add new class at end of file, after StatusBar)

**Context:**
The KeybindingsBar widget needs to store state and provide an update method. Start with the basic class structure.

- [ ] **Step 1: Open widgets.py and find where StatusBar ends**

StatusBar is defined at lines 182-262 in widgets.py. You'll add KeybindingsBar after it.

- [ ] **Step 2: Add KeybindingsBar class definition**

Add this at the end of `src/gantry/widgets.py` after the StatusBar class:

```python
class KeybindingsBar(Static):
    """Context-aware keybindings bar displaying abbreviated key hints."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the keybindings bar with default state."""
        super().__init__(*args, **kwargs)
        self.screen_type = "cluster"  # "cluster" or "helm"
        self.current_panel = "sidebar"  # "sidebar", "table", "detail", "search"
        self.detail_panel_open = False
        self.search_active = False
    
    def update_context(self, screen_type: str, current_panel: str, detail_open: bool, search_active: bool) -> None:
        """Update the context state and refresh the display.
        
        Args:
            screen_type: "cluster" or "helm"
            current_panel: "sidebar", "table", "detail", or "search"
            detail_open: whether detail panel is open
            search_active: whether search is active
        """
        self.screen_type = screen_type
        self.current_panel = current_panel
        self.detail_panel_open = detail_open
        self.search_active = search_active
        self.refresh()
    
    def render(self) -> str:
        """Render abbreviated keybindings based on current context."""
        # Case 1: Detail panel open
        if self.detail_panel_open:
            return "← Back | → Fwd | Esc Close | ↑↓ Scroll"
        
        # Case 2: Search active
        if self.search_active:
            return "Esc Cancel | ↵ Select"
        
        # Case 3 & 4: Normal state (depends on screen type)
        if self.screen_type == "cluster":
            return "←→ Nav | d Desc | l Logs | r Refr | c Ctx | / Srch | Tab Helm | q Quit"
        elif self.screen_type == "helm":
            return "←→ Nav | ↵ Deploy | r Refr | c Ctx | / Srch | Tab Cluster | q Quit"
        
        # Fallback (should not reach here)
        return ""
```

- [ ] **Step 3: Verify indentation and syntax**

The class should be properly indented as a top-level class in the file. Check that all methods are indented correctly and the file has valid Python syntax.

- [ ] **Step 4: Run Python syntax check**

```bash
cd /Users/tanbirsagar/Documents/Personal/Projects/gantry
python -m py_compile src/gantry/widgets.py
```

Expected: No errors (clean exit).

- [ ] **Step 5: Commit**

```bash
git add src/gantry/widgets.py
git commit -m "feat: Add KeybindingsBar class with render and update_context methods"
```

---

## Task 2: Add CSS for KeybindingsBar

**Files:**
- Modify: `src/gantry/screens.py` (ClusterScreen CSS block)

**Context:**
The KeybindingsBar needs CSS styling to appear as a footer bar with no top border (stacked on StatusBar).

- [ ] **Step 1: Locate the CSS block in ClusterScreen**

Find the CSS property in ClusterScreen class (around line 204-279). It's a multi-line string starting with `CSS = """`.

- [ ] **Step 2: Add KeybindingsBar CSS at the end of the block**

Find the end of the CSS block (before the closing `"""`) and add this rule:

```python
    #keybindings-bar {
        height: 1;
        border: solid $accent;
        border-top: none;
        padding: 0 1;
        background: $panel;
        color: $text;
    }
```

Insert it after the StatusBar CSS rule (around line 285) and before the closing `"""`.

- [ ] **Step 3: Verify CSS syntax**

Check that the indentation matches other CSS rules in the block (typically 4-space indents within the CSS string).

- [ ] **Step 4: Run tests to ensure no CSS errors**

```bash
cd /Users/tanbirsagar/Documents/Personal/Projects/gantry
uv run pytest tests/test_app.py -v -k "test_cluster_screen_mount" 2>&1 | head -20
```

Expected: Tests should not fail due to CSS issues.

- [ ] **Step 5: Commit**

```bash
git add src/gantry/screens.py
git commit -m "feat: Add CSS styling for #keybindings-bar"
```

---

## Task 3: Integrate KeybindingsBar into ClusterScreen

**Files:**
- Modify: `src/gantry/screens.py` (ClusterScreen class)

**Context:**
ClusterScreen needs to yield the KeybindingsBar widget in compose(), initialize it in on_mount(), and update it when state changes.

- [ ] **Step 1: Add KeybindingsBar import at top of screens.py**

Find the imports section (line 1-20). Look for the line that imports from `gantry.widgets`. It should be around line 17:

```python
from gantry.widgets import ResourceTable, SearchInput, StatusBar
```

Change it to:

```python
from gantry.widgets import ResourceTable, SearchInput, StatusBar, KeybindingsBar
```

- [ ] **Step 2: Yield KeybindingsBar in ClusterScreen.compose()**

Find the `compose()` method (around line 303-324). Currently it yields:
- Horizontal#main-container
- StatusBar
- (nothing else)

Add a yield for KeybindingsBar after StatusBar:

```python
    # Status bar
    yield StatusBar(id="status-bar")
    
    # Keybindings bar
    yield KeybindingsBar(id="keybindings-bar")
```

So the full compose should end with:

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
        
        # Keybindings bar
        yield KeybindingsBar(id="keybindings-bar")
```

- [ ] **Step 3: Initialize bar reference in on_mount()**

Find the `on_mount()` method (around line 325). At the end of the method, add:

```python
        # Initialize keybindings bar
        self.keybindings_bar = self.query_one("#keybindings-bar", KeybindingsBar)
        self.keybindings_bar.update_context("cluster", "sidebar", False, False)
```

- [ ] **Step 4: Add watchers for state changes**

Find the `watch_current_resource_type()` method (around line 727). After it, add these two watcher methods:

```python
    def watch_current_panel(self, new_panel: str) -> None:
        """React to current_panel changes."""
        if hasattr(self, 'keybindings_bar'):
            self.keybindings_bar.update_context(
                "cluster", new_panel, self.detail_panel_open, False
            )
    
    def watch_detail_panel_open(self, new_open: bool) -> None:
        """React to detail_panel_open changes."""
        if hasattr(self, 'keybindings_bar'):
            self.keybindings_bar.update_context(
                "cluster", self.current_panel, new_open, False
            )
```

These watchers respond to reactive property changes automatically.

- [ ] **Step 5: Test the changes**

```bash
cd /Users/tanbirsagar/Documents/Personal/Projects/gantry
uv run pytest tests/test_app.py::test_cluster_screen_mount -v
```

Expected: Test should pass (or fail only due to new widget, not due to syntax errors).

- [ ] **Step 6: Commit**

```bash
git add src/gantry/screens.py
git commit -m "feat: Integrate KeybindingsBar into ClusterScreen with watchers"
```

---

## Task 4: Integrate KeybindingsBar into HelmScreen

**Files:**
- Modify: `src/gantry/screens.py` (HelmScreen class)

**Context:**
HelmScreen follows the same pattern as ClusterScreen but with `screen_type="helm"` and no detail_panel or search.

- [ ] **Step 1: Yield KeybindingsBar in HelmScreen.compose()**

Find the `compose()` method in HelmScreen (around line 927-944). It currently ends with:

```python
        yield StatusBar(id="status-bar")
```

Add after it:

```python
        yield StatusBar(id="status-bar")
        
        # Keybindings bar
        yield KeybindingsBar(id="keybindings-bar")
```

- [ ] **Step 2: Initialize bar reference in HelmScreen.on_mount()**

Find or add the `on_mount()` method in HelmScreen. If it doesn't exist, add it after the `compose()` method:

```python
    def on_mount(self) -> None:
        """Initialize helm screen on mount."""
        # Initialize keybindings bar (helm screen has no detail panel or search)
        self.keybindings_bar = self.query_one("#keybindings-bar", KeybindingsBar)
        self.keybindings_bar.update_context("helm", "table", False, False)
```

If `on_mount()` already exists, add the keybindings bar initialization to the end of it.

- [ ] **Step 3: Add watcher for panel focus changes**

If HelmScreen doesn't have a `watch_current_panel()` method, add it:

```python
    def watch_current_panel(self, new_panel: str) -> None:
        """React to current_panel changes."""
        if hasattr(self, 'keybindings_bar'):
            self.keybindings_bar.update_context(
                "helm", new_panel, False, False
            )
```

- [ ] **Step 4: Add CSS for HelmScreen's KeybindingsBar**

Find the CSS block in HelmScreen class (around line 853-909). Add the same CSS rule at the end, before the closing `"""`:

```python
    #keybindings-bar {
        height: 1;
        border: solid $accent;
        border-top: none;
        padding: 0 1;
        background: $panel;
        color: $text;
    }
```

- [ ] **Step 5: Test the changes**

```bash
cd /Users/tanbirsagar/Documents/Personal/Projects/gantry
uv run pytest tests/test_app.py -v
```

Expected: All existing tests should still pass.

- [ ] **Step 6: Commit**

```bash
git add src/gantry/screens.py
git commit -m "feat: Integrate KeybindingsBar into HelmScreen with context awareness"
```

---

## Task 5: Write tests for KeybindingsBar

**Files:**
- Modify: `tests/test_app.py`

**Context:**
Add tests to verify KeybindingsBar renders correctly for different contexts.

- [ ] **Step 1: Add import for KeybindingsBar**

At the top of `tests/test_app.py`, find the imports section. Add KeybindingsBar to the imports:

```python
from gantry.widgets import ResourceTable, SearchInput, StatusBar, KeybindingsBar
```

- [ ] **Step 2: Add test for detail panel open state**

Add this test function to `tests/test_app.py`:

```python
async def test_keybindings_bar_detail_panel_open(client: Pilot):
    """KeybindingsBar should show detail panel hints when detail is open."""
    screen = client.app.screen
    assert isinstance(screen, ClusterScreen)
    
    bar = screen.query_one("#keybindings-bar", KeybindingsBar)
    bar.update_context("cluster", "detail", detail_open=True, search_active=False)
    
    output = bar.render()
    assert "← Back" in output
    assert "Esc Close" in output
    assert "↑↓ Scroll" in output
    assert "Desc" not in output  # Should NOT show normal cluster bindings
```

- [ ] **Step 3: Add test for search active state**

Add this test:

```python
async def test_keybindings_bar_search_active(client: Pilot):
    """KeybindingsBar should show search hints when search is active."""
    screen = client.app.screen
    assert isinstance(screen, ClusterScreen)
    
    bar = screen.query_one("#keybindings-bar", KeybindingsBar)
    bar.update_context("cluster", "sidebar", detail_open=False, search_active=True)
    
    output = bar.render()
    assert "Esc Cancel" in output
    assert "↵ Select" in output
    assert "Desc" not in output  # Should NOT show normal cluster bindings
```

- [ ] **Step 4: Add test for ClusterScreen normal state**

Add this test:

```python
async def test_keybindings_bar_cluster_normal(client: Pilot):
    """KeybindingsBar should show cluster screen bindings in normal state."""
    screen = client.app.screen
    assert isinstance(screen, ClusterScreen)
    
    bar = screen.query_one("#keybindings-bar", KeybindingsBar)
    bar.update_context("cluster", "table", detail_open=False, search_active=False)
    
    output = bar.render()
    assert "←→ Nav" in output
    assert "d Desc" in output
    assert "l Logs" in output
    assert "r Refr" in output
    assert "c Ctx" in output
    assert "/ Srch" in output
    assert "Tab Helm" in output
    assert "q Quit" in output
```

- [ ] **Step 5: Add test for HelmScreen normal state**

Add this test:

```python
async def test_keybindings_bar_helm_normal(client: Pilot):
    """KeybindingsBar should show helm screen bindings in normal state."""
    screen = client.app.screen
    assert isinstance(screen, ClusterScreen)  # We're in cluster by default
    
    bar = screen.query_one("#keybindings-bar", KeybindingsBar)
    bar.update_context("helm", "table", detail_open=False, search_active=False)
    
    output = bar.render()
    assert "←→ Nav" in output
    assert "↵ Deploy" in output
    assert "r Refr" in output
    assert "c Ctx" in output
    assert "/ Srch" in output
    assert "Tab Cluster" in output
    assert "q Quit" in output
    # Should NOT show cluster-specific bindings
    assert "Desc" not in output
    assert "Logs" not in output
```

- [ ] **Step 6: Run the new tests**

```bash
cd /Users/tanbirsagar/Documents/Personal/Projects/gantry
uv run pytest tests/test_app.py::test_keybindings_bar_detail_panel_open -v
uv run pytest tests/test_app.py::test_keybindings_bar_search_active -v
uv run pytest tests/test_app.py::test_keybindings_bar_cluster_normal -v
uv run pytest tests/test_app.py::test_keybindings_bar_helm_normal -v
```

Expected: All 4 tests should pass.

- [ ] **Step 7: Run all tests**

```bash
cd /Users/tanbirsagar/Documents/Personal/Projects/gantry
uv run pytest tests/test_app.py -v
```

Expected: All tests pass (no regressions).

- [ ] **Step 8: Commit**

```bash
git add tests/test_app.py
git commit -m "test: Add tests for KeybindingsBar context-aware rendering"
```

---

## Task 6: Manual testing of KeybindingsBar

**Files:**
- None (testing only)

**Context:**
Verify end-to-end behavior by launching Gantry and observing the keybindings bar in different contexts.

- [ ] **Step 1: Start Gantry**

```bash
cd /Users/tanbirsagar/Documents/Personal/Projects/gantry
uv run python -m gantry --debug
```

- [ ] **Step 2: Verify bar appears at the bottom**

1. The app should show two footer rows: StatusBar on top, KeybindingsBar below
2. The KeybindingsBar should show: `←→ Nav | d Desc | l Logs | r Refr | c Ctx | / Srch | Tab Helm | q Quit`

- [ ] **Step 3: Test panel navigation changes bar**

1. Press `right` arrow to move focus to table
2. Verify: Bar still shows the same bindings (panel focus doesn't change hints in normal state)

- [ ] **Step 4: Test detail panel open changes bar**

1. With a pod selected, press `d` to describe
2. Verify: Bar changes to show `← Back | → Fwd | Esc Close | ↑↓ Scroll`
3. Press Escape to close detail
4. Verify: Bar returns to normal cluster bindings

- [ ] **Step 5: Test search active changes bar**

1. Press `/` to activate search
2. Verify: Bar changes to show `Esc Cancel | ↵ Select`
3. Press Escape to close search
4. Verify: Bar returns to normal cluster bindings

- [ ] **Step 6: Test HelmScreen shows correct bindings**

1. Press `Tab` to switch to Helm view
2. Verify: Bar changes to show `←→ Nav | ↵ Deploy | r Refr | c Ctx | / Srch | Tab Cluster | q Quit`
3. Verify: "Deploy" appears instead of "Desc" and "Logs"
4. Verify: "Tab Cluster" instead of "Tab Helm"

- [ ] **Step 7: Test keyboard still works**

1. In any state, verify that the keybindings still work (press d to describe, etc.)
2. Verify: The bar is display-only and doesn't interfere with actual keybindings

All manual tests should pass without errors.

---

## Task 7: Final commit and cleanup

**Files:**
- None (summary only)

**Context:**
Verify all changes are committed and review the implementation.

- [ ] **Step 1: Check git status**

```bash
cd /Users/tanbirsagar/Documents/Personal/Projects/gantry
git status
```

Expected: `nothing to commit, working tree clean`

- [ ] **Step 2: View recent commits**

```bash
git log --oneline -10
```

Expected: Should show 5-6 commits related to KeybindingsBar implementation.

- [ ] **Step 3: Run full test suite one final time**

```bash
uv run pytest tests/test_app.py -v
```

Expected: All tests pass.

All implementation tasks are complete!

---

## Verification & Success Criteria

All of the following should be true:
- [ ] KeybindingsBar widget exists in widgets.py with render() and update_context()
- [ ] ClusterScreen yields KeybindingsBar after StatusBar
- [ ] HelmScreen yields KeybindingsBar after StatusBar
- [ ] Both screens initialize and update the bar in on_mount() and watchers
- [ ] CSS styling is present for #keybindings-bar
- [ ] KeybindingsBar renders correct bindings for each context:
  - Detail panel open: `← Back | → Fwd | Esc Close | ↑↓ Scroll`
  - Search active: `Esc Cancel | ↵ Select`
  - ClusterScreen normal: `←→ Nav | d Desc | l Logs | r Refr | c Ctx | / Srch | Tab Helm | q Quit`
  - HelmScreen normal: `←→ Nav | ↵ Deploy | r Refr | c Ctx | / Srch | Tab Cluster | q Quit`
- [ ] State changes trigger immediate bar updates
- [ ] All existing tests still pass
- [ ] New tests for KeybindingsBar pass
- [ ] Manual testing confirms all contexts work end-to-end
- [ ] All changes committed to git with clear messages
