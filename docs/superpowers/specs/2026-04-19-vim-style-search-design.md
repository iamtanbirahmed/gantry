# Vim-Style Search

## Context

The search bar is currently always visible with `ctrl+f` to focus. The user wants vim-style search behavior: hidden by default, activated with `/`, with Enter to confirm and Escape to cancel.

## Behavior

### Default State
- Search bar is hidden (`display: none`)
- No filter applied to resource/chart tables

### `/` Activates Search
- Search bar becomes visible (add `show` CSS class)
- Input is focused
- `/` appears as a visual prefix (not part of the search value)
- Typing filters results live (existing `SearchChanged` message flow)

### Enter Confirms Search
- Search bar hides (remove `show` CSS class)
- Current filter remains active on the table
- Focus returns to the resource/chart table

### Escape Cancels Search
- Search text is cleared
- Filter is reset (all rows shown via `SearchChanged("")`)
- Search bar hides (remove `show` CSS class)
- Focus returns to the resource/chart table

## Files to Modify

### `src/gantry/widgets.py` — SearchInput
- Add Enter key handler: hide search bar, return focus to table, keep filter
- Keep existing Escape handler, add hiding logic
- The `/` prefix is cosmetic — not part of the search value

### `src/gantry/screens.py` — ClusterScreen
- Change binding from `Binding("ctrl+f", ...)` back to `("slash", "focus_search", "Search")`
- Re-add `display: none` to SearchInput CSS
- Add `SearchInput.show { display: block; }` CSS rule
- Update `action_focus_search()` to add `show` class and focus

### `src/gantry/screens.py` — HelmScreen
- Same binding, CSS, and action changes as ClusterScreen

### `src/gantry/widgets.py` — KeybindingsBar
- Update keybinding hints to show `/` for search

## Verification

1. `uv run pytest tests/ -v` — all tests pass
2. Search bar hidden on screen load
3. `/` shows search bar with `/` prefix, focuses input
4. Typing filters live
5. Enter hides bar, keeps filter, focuses table
6. Escape clears filter, hides bar, focuses table
