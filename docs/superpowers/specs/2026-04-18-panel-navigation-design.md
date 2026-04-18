# Panel Navigation & Live Sidebar Preview Design

## Context
Currently, users navigate between panels (sidebar, resource table, search) using Tab/Shift+Tab, which conflicts with the screen-switching feature. We're replacing panel navigation with left/right arrows for better UX and adding live preview when browsing resource types in the sidebar.

## Feature Overview

### 1. Panel Navigation (Left/Right Arrows)
Replace Tab/Shift+Tab for panel switching with left/right arrow keys that cycle through three panels:
- **Panel 1: Resource Type Sidebar** — browse and select resource types
- **Panel 2: Resource Table** — view and interact with the resource list
- **Panel 3: Search Input** — search/filter the current resource list

**Navigation flow:**
```
Left Arrow:  SearchInput ← ResourceTable ← Sidebar ← (wraps to SearchInput)
Right Arrow: Sidebar → ResourceTable → SearchInput → (wraps to Sidebar)
```

**Behavior:**
- Left/right arrows move focus between panels
- When focus changes, the target panel becomes immediately interactive
- Tab key continues to switch between Cluster and Helm screens (unchanged)

### 2. Live Sidebar Preview (Up/Down Arrows)
When the sidebar has focus, moving up/down with arrow keys triggers immediate resource list updates:

**Current behavior:**
- Up/down navigate the sidebar list
- Enter key selects and triggers resource fetch

**New behavior:**
- Up/down navigate AND immediately select the resource type
- Resource table updates in real-time as you navigate (no Enter needed)
- Provides instant preview of each resource type's data

### 3. Focus Management
**On mount:**
- Sidebar receives initial focus (existing behavior, kept)

**Panel focus transitions:**
- When focus moves to ResourceTable via left/right arrow, the table becomes interactive
- When focus moves to SearchInput via left/right arrow, the input receives focus for immediate typing
- When focus moves back to Sidebar via left/right arrow, sidebar regains focus and up/down navigation resumes

## Implementation Details

### New Keybindings (ClusterScreen)
```python
BINDINGS = [
    # Panel navigation (replaces manual Tab usage for panels)
    ("left", "focus_previous_panel", "Previous Panel"),
    ("right", "focus_next_panel", "Next Panel"),
    
    # Existing keybindings (unchanged)
    ("tab", "app.action_switch_screen", "Switch to Helm View"),
    ("slash", "focus_search", "Search"),
    ("c", "show_context_picker", "Pick Context"),
    ("d", "describe_resource", "Describe"),
    ("l", "show_logs", "Logs"),
    ("r", "refresh_resources", "Refresh"),
    ("q", "quit", "Quit Gantry"),
]
```

### State Tracking
Add reactive variable to track current panel:
```python
current_panel = reactive("sidebar")  # "sidebar", "table", or "search"
```

### Action Handlers
```python
def action_focus_next_panel(self) -> None:
    """Move focus to the next panel (right arrow)."""
    # Cycle: sidebar → table → search → sidebar
    
def action_focus_previous_panel(self) -> None:
    """Move focus to the previous panel (left arrow)."""
    # Cycle: search ← table ← sidebar ← search
```

### Sidebar Navigation
Modify `on_list_view_selected()` to trigger on every highlight change (not just Enter):
- Rename to `on_list_view_highlighted()` to catch the `ListView.Highlighted` event
- Set `current_resource_type` immediately when navigating
- Resource table updates reactively via existing `watch_current_resource_type()` watcher

## HelmScreen
Apply the same pattern to HelmScreen for consistency:
- Same left/right panel navigation
- 3 panels: [Chart/Repo sidebar] → [Chart table] → [Search input]
- Live preview when browsing repos or charts (if applicable)

## Testing
- **test_panel_navigation_left_arrow** — verify left arrow cycles panels backwards
- **test_panel_navigation_right_arrow** — verify right arrow cycles panels forwards
- **test_sidebar_up_down_updates_resources** — verify resource list updates immediately when navigating sidebar
- **test_focus_transitions** — verify correct panel receives focus after arrow key press
- Existing tests should continue to pass (no breaking changes to resource fetching logic)

## Backwards Compatibility
- Tab key still switches between Cluster/Helm screens ✓
- Search activation (/) still works ✓
- All existing keybindings remain functional ✓
- No database/API changes required ✓
