# Right Panel Detail Viewer Design

**Date:** 2026-04-19  
**Feature:** Right-side scrollable panel for resource details and pod logs  
**Status:** Approved for implementation planning

## Problem & Motivation

Currently, when users press `d` (describe) or `l` (logs) on a resource, the output appears as plain text in a non-scrollable `Label` widget at the bottom of the screen. This is problematic for:
- Long logs that exceed the available space (unscrollable, content lost)
- Layout shift when panel appears/disappears
- No focus within the panel to navigate logs with arrow keys

**Goal:** Provide a dedicated right-side scrollable panel that displays describe/logs output, with full keyboard navigation support.

## Architecture

### Layout

**Current (simplified):**
```
Screen (vertical)
├── Horizontal #main-container
│   ├── ListView #resource-type-sidebar (20 chars)
│   └── Vertical #content-area
│       ├── ResourceTable (1fr)
│       └── SearchInput (1 line, hidden)
├── Label #detail-panel (bottom, non-scrollable)
└── StatusBar
```

**New:**
```
Screen (vertical)
├── Horizontal #main-container
│   ├── ListView #resource-type-sidebar (20 chars)
│   ├── Vertical #content-area
│   │   ├── ResourceTable (1fr)
│   │   └── SearchInput (1 line, hidden)
│   └── VerticalScroll #detail-panel (40% width, hidden by default)
│       └── Static (renders text output)
├── StatusBar
```

The detail panel is a **first-class panel** in the horizontal layout, not an overlay or bottom bar. It is:
- **Hidden by default** (`display: none`)
- **40% of screen width** when visible
- **Scrollable** via `VerticalScroll` container
- **Focusable** with `up/down` arrow navigation

### Panel State & Navigation

**Reactive state:** Add `current_panel` tracking (already exists; extend to include "detail")

**Panel cycle when detail is open:** `sidebar → table → detail → sidebar`  
**Cycle reversed:** `sidebar ← detail ← table ← sidebar`

- `right` arrow from **table** → focus **detail**
- `left` arrow from **detail** → focus **table**
- `up`/`down` when detail has focus → scroll text within panel
- Search panel (`/` key) is **excluded from this cycle** for now — handled separately later

**Focus defaults:**
- When detail panel opens, **auto-focus it** so user can immediately scroll
- When `Esc` closes detail, **return focus to table**

### Actions: Describe & Logs

**`d` (describe):**
1. Fetch resource description via `k8s.describe_resource()`
2. Call `_show_detail_panel(title="DESCRIBE", content=description_text)`
3. Panel appears with header "DESCRIBE", text renders in Static, panel gets focus
4. User can scroll with `up/down`, navigate out with `left`, close with `Esc`

**`l` (logs, pods only):**
1. Fetch pod logs via `k8s.get_pod_logs()`
2. Call `_show_detail_panel(title="LOGS", content=logs_text)`
3. Panel appears with header "LOGS", text renders in Static, panel gets focus
4. User can scroll with `up/down`, navigate out with `left`, close with `Esc`

**No re-fetching:** Once open, the panel stays with the same content until explicitly closed. Pressing `d` again does nothing; user must press `Esc` and then `d` to refresh.

### Panel Lifecycle

**Opening:**
```
action_describe_resource() or action_show_logs()
  ↓
_describe_resource_worker() / _show_logs_worker()
  ↓
_show_detail_panel(title, content)
  ↓
Query `#detail-panel`
Set content in Static widget
Remove `.hidden` class (show panel)
Update panel cycle in `current_panel` watch
Focus detail panel
```

**Closing:**
```
on_key(Escape)
  ↓
_close_detail_panel()
  ↓
Add `.hidden` class (hide panel)
Update panel cycle in `current_panel` watch
Return focus to table
```

## Implementation

### Files to Modify

**`src/gantry/screens.py`** (ClusterScreen)
- **compose()** (line 303): Move `#detail-panel` from bottom Label to right-side `VerticalScroll` + `Static` inside `#main-container`
- **on_mount()** (line 324): Initialize `current_panel` state to "sidebar"; set up detail panel focus behavior
- **action_focus_next_panel()** (line 629): Add "detail" to cycle only when visible
- **action_focus_previous_panel()** (line 654): Add "detail" to cycle only when visible
- **_show_detail_panel()** [NEW]: Helper to set title, content, show panel, focus it
- **_close_detail_panel()** [NEW]: Helper to hide panel, update focus
- **_apply_describe_result()** (line 536): Change to call `_show_detail_panel("DESCRIBE", content)`
- **_apply_logs_result()** [NEW]: Similar helper for logs, calls `_show_detail_panel("LOGS", content)`
- **on_key()** [NEW or extend existing]: Intercept `Escape` to call `_close_detail_panel()` if panel is visible

**`src/gantry/app.css`** (if separate file) or inline CSS in screens.py:
- Add styles for `#detail-panel`: `width: 40%`, `border-left: solid $accent`, `background: $panel`
- Add `.hidden` class: `display: none`

### Key Design Decisions

1. **VerticalScroll over TextArea:** TextArea is editor-like; VerticalScroll + Static is read-only and lighter
2. **Auto-focus on open:** User can immediately scroll without extra keypress
3. **Hide vs remove:** Panel stays in DOM tree, just `display: none` — no panel cycle updates when hidden
4. **Single content at a time:** No tab switching between describe and logs; user must close and re-press
5. **No search in cycle:** Search handled separately; detail cycle is sidebar ↔ table ↔ detail only

### Testing Checklist

- [ ] Open detail panel with `d` on a deployment → describe output appears, is scrollable
- [ ] Open detail panel with `l` on a pod → logs appear, are scrollable
- [ ] Press `right` from table → focus enters detail panel
- [ ] Press `up`/`down` in detail → text scrolls
- [ ] Press `left` in detail → focus returns to table
- [ ] Press `Esc` in detail → panel hides, focus returns to table
- [ ] Panel cycle correct with arrow keys: sidebar → table → detail → sidebar (when detail is visible)
- [ ] Panel cycle correct with arrow keys: sidebar ↔ table (when detail is hidden)
- [ ] Pressing `d` again while panel open does nothing (no re-fetch)
- [ ] Status bar updates when panel opens (show hint: "ESC to close · ↑↓ scroll")

## Out of Scope (For Now)

- Search panel navigation (will handle later)
- Resizing the detail panel width
- Switching between describe and logs within the same panel session
- Syntax highlighting or color coding in the output
