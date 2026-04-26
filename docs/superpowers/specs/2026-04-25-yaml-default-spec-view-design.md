# YAML Default Spec View

**Date:** 2026-04-25

## Summary

When the user presses `y` to open the YAML panel, default to spec view instead of full manifest view.

## Current Behavior

`_apply_yaml_result` in `screens.py` sets `self.yaml_mode = "full"` every time `y` is pressed, so the YAML panel always opens showing the complete manifest including status and managedFields.

## Desired Behavior

`y` always opens in spec view (apiVersion/kind/metadata name+namespace/spec — no status or managedFields). The `m` key still toggles between spec and full. No persistent mode memory across opens.

## Change

**File:** `src/gantry/screens.py`  
**Line:** 717  
**Before:** `self.yaml_mode = "full"`  
**After:** `self.yaml_mode = "spec"`

## Rationale

Spec view is the most actionable content for users — it shows what they care about (desired state) without noise from status fields and managed metadata. Full manifest remains accessible via `m` toggle.

## Testing

- Existing tests for `_apply_yaml_result` and `action_toggle_yaml_mode` should be updated to reflect `"spec"` as the initial mode.
- Verify: press `y` → spec shown; press `m` → full shown; press `m` again → spec shown.
