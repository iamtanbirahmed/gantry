# KeybindingsBar Widget Design

**Date:** 2026-04-19  
**Feature:** Context-aware keybindings display in footer  
**Status:** Approved for implementation planning

## Problem & Motivation

Currently, users must memorize all keybindings or rely on external documentation. The app provides no in-UI help. Adding a dynamic keybindings bar at the bottom shows users what keys are available in their current context.

**Goal:** Display abbreviated keybindings in the footer, updating dynamically based on screen, panel focus, detail panel state, and search state.

## Architecture

### Layout

**Current footer (2 rows):**
```
Row 1: StatusBar (context | namespace | status)
Row 2: (empty)
```

**New footer (2 rows):**
```
Row 1: StatusBar (context | namespace | status)
Row 2: KeybindingsBar (abbreviated keybindings)
```

### Widget Structure

Both screens (ClusterScreen, HelmScreen) will yield widgets in this order:
```
Horizontal#main-container (content)
StatusBar (row 1 of footer)
KeybindingsBar (row 2 of footer)
```

The KeybindingsBar is a new `Static` widget that renders a single line of abbreviated key+label pairs.

### KeybindingsBar Widget

**Inherits from:** `Static`

**Location:** `src/gantry/widgets.py` (alongside StatusBar)

**Responsibility:**
- Render abbreviated keybindings for the current context
- Update display when screen, panel focus, or state changes
- Handle responsive wrapping if needed

**Input (passed from screen, updated via `update_context()`):**
- `screen_type` — "cluster" or "helm" (determines available bindings)
- `current_panel` — "sidebar", "table", "detail", "search" (shapes nav hints)
- `detail_panel_open` — boolean (show "Esc" hint when True)
- `search_active` — boolean (show search-specific hints when True)

**Output:**
Single line of abbreviated keybindings separated by ` | ` (pipe + space).

### Context-Aware Rendering Logic

The `render()` method builds the display based on context:

**Case 1: Detail panel open**
```
← Back | → Fwd | Esc Close | ↑↓ Scroll
```
- Only navigation and escape shown
- ↑↓ indicates scrolling within the detail panel

**Case 2: Search active**
```
Esc Cancel | ↵ Select
```
- Only search-related actions shown

**Case 3: ClusterScreen, normal state**
```
←→ Nav | d Desc | l Logs | r Refr | c Ctx | / Srch | Tab Helm | q Quit
```
- Full set of bindings relevant to ClusterScreen
- ← and → abbreviated as "Nav"

**Case 4: HelmScreen, normal state**
```
←→ Nav | ↵ Deploy | r Refr | c Ctx | / Srch | Tab Cluster | q Quit
```
- HelmScreen-specific: Deploy instead of Describe/Logs
- Tab label says "Cluster" instead of "Helm"

**Case 5: Current panel is detail (ClusterScreen only)**
If detail panel is **visible but not open** (edge case), show:
```
←→ Nav | d Desc | l Logs | r Refr | c Ctx | / Srch | Tab Helm | q Quit
```
(Same as Case 3 — detail panel doesn't change the binding hints, only open/close state does.)

### Abbreviation Mapping

All labels are 1-4 characters:

| Full | Abbr | Context |
|------|------|---------|
| Panels | Nav | Left/right arrow navigation |
| Describe | Desc | ClusterScreen, d key |
| Logs | Logs | ClusterScreen (pods only), l key |
| Refresh | Refr | Both screens, r key |
| Context | Ctx | Both screens, c key |
| Search | Srch | Both screens, / key |
| Helm View | Helm | ClusterScreen, tab key |
| Cluster View | Cluster | HelmScreen, tab key |
| Deploy | Deploy | HelmScreen, enter key |
| Back | Back | Left arrow when detail open |
| Forward | Fwd | Right arrow when detail open |
| Close | Close | Escape when detail open |
| Scroll | Scroll | Up/down arrows when detail focused |
| Cancel | Cancel | Escape when search active |
| Select | Select | Enter when search active |
| Quit | Quit | q key, both screens |

### Implementation Approach

**Method: `__init__()`**
Initialize state attributes:
- `self.screen_type = "cluster"`
- `self.current_panel = "sidebar"`
- `self.detail_panel_open = False`
- `self.search_active = False`

**Method: `render() → str`**
1. If `detail_panel_open`, return detail panel hints
2. Else if `search_active`, return search hints
3. Else, build bindings list based on `screen_type`
4. Join with ` | ` separator
5. Return formatted string

**Method: `update_context(screen_type, current_panel, detail_open, search_active) → None`**
Update all state attributes and call `self.refresh()`.

**No child widgets** — Renders as plain text (like StatusBar), no `compose()` method.

### Integration with Screens

**ClusterScreen changes:**
- Yield `KeybindingsBar(id="keybindings-bar")` after `StatusBar`
- In `on_mount()`, get the bar: `bar = self.query_one("#keybindings-bar", KeybindingsBar)`
- Watch `current_panel`, `detail_panel_open` and call `bar.update_context()` when they change
- When search is activated/deactivated, call `bar.update_context()`

**HelmScreen changes:**
- Same pattern: yield bar, update it in watchers
- Pass `screen_type="helm"` in first call to `update_context()`

**HelmScreen note:** HelmScreen doesn't currently have detail panel or search features (search is commented out), so `detail_panel_open` always False, `search_active` always False for Helm. The bar will show standard Helm bindings.

### CSS

```css
#keybindings-bar {
    height: 1;
    border: solid $accent;
    border-top: none;          /* No border between StatusBar and KeybindingsBar */
    padding: 0 1;
    background: $panel;
    color: $text;
}
```

Place this in the ClusterScreen and HelmScreen CSS blocks (or in app.css if shared).

### Testing Checklist

- [ ] KeybindingsBar renders correctly for each context (unit tests on `render()` logic)
- [ ] State updates trigger re-render (test `update_context()` calls `self.refresh()`)
- [ ] Screen transitions show correct bindings (ClusterScreen vs HelmScreen)
- [ ] Panel focus changes update hints (sidebar → table → detail)
- [ ] Detail panel open/close toggles Escape hint
- [ ] Search activation/deactivation toggles search hints
- [ ] ClusterScreen tests updated if needed (new widget in compose)
- [ ] HelmScreen tests updated if needed (new widget in compose)
- [ ] Manual testing: Launch Gantry, verify bar appears, try different contexts

### Out of Scope (For Now)

- Scrolling/pagination if bindings exceed terminal width (use wrapping or truncation)
- Customizable keybindings (would require changes to BINDINGS format)
- Mouse support for clicking keys
- Internationalization

## Files to Modify

- `src/gantry/widgets.py` — Add `KeybindingsBar` class
- `src/gantry/screens.py` — Update ClusterScreen and HelmScreen to:
  - Import and yield `KeybindingsBar`
  - Add watchers for state changes
  - Call `bar.update_context()` when state changes
- `src/gantry/app.css` or inline CSS in screens.py — Add CSS for `#keybindings-bar`
- `tests/test_app.py` — Add tests for KeybindingsBar (optional but recommended)

## Success Criteria

- [ ] KeybindingsBar widget renders without errors
- [ ] All 5 context cases produce correct output
- [ ] State changes update the display immediately
- [ ] ClusterScreen and HelmScreen both show correct bindings
- [ ] All existing tests still pass
- [ ] Manual testing confirms all contexts work end-to-end
