# YAML Manifest Viewer Design

**Feature:** Display full YAML manifest of Kubernetes resources in the right detail panel via 'y' keybinding.

**Date:** 2026-04-22  
**Status:** Design approved, ready for implementation

---

## Overview

Users can press 'y' while a resource is selected to view its YAML manifest in the right panel. The YAML is syntax-highlighted and read-only. Users can toggle between full manifest (with metadata, status, spec) and spec-only view using the 'm' keybinding while the panel is open.

This complements the existing 'd' (Describe) action, giving users access to the raw manifest representation alongside the formatted describe output.

---

## User Flow

1. User selects resource in cluster table (pods, deployments, services, etc.)
2. Presses 'y' → right panel opens showing YAML manifest (full mode by default)
3. Presses 'm' → toggles to spec-only view (compact, recreatable manifest)
4. Presses 'm' again → back to full manifest
5. Presses 'd' → switches to Describe view (YAML closes)
6. Presses 'Escape' → closes detail panel entirely

**Status bar hints update** based on context:
- Table selected: `"Cluster | y: yaml · d: describe · r: refresh"` (existing)
- YAML panel open: `"YAML (full) | m: toggle · d: describe · ↑↓ scroll"`
- Spec mode: `"YAML (spec) | m: toggle · d: describe · ↑↓ scroll"`

---

## Architecture

### Backend: `src/gantry/k8s.py`

**New function:** `get_resource_yaml(resource_type, resource_name, namespace)`

```
Returns: tuple (full_yaml: str | None, spec_yaml: str | None)

Steps:
1. Fetch resource object via K8s Python client (same as describe_resource)
2. Serialize to YAML using yaml.dump():
   - full_yaml: Complete object (metadata, spec, status)
   - spec_yaml: Extract spec and metadata.name/namespace only
3. Return both strings or (None, None) on error
```

**Implementation details:**
- Uses existing K8s client setup (config.load_kube_config, CoreV1Api, AppsV1Api, etc.)
- Same error handling as `describe_resource()` — returns None if fetch fails
- YAML formatting: `default_flow_style=False, sort_keys=False, default_style=None` for readable output
- Handles all resource types (pods, deployments, services, configmaps, statefulsets, daemonsets, jobs, cronjobs, ingresses, endpoints, secrets, pvcs, etc.)

### Frontend: `src/gantry/screens.py`

**New reactive state (ClusterScreen):**
- `yaml_view_open: reactive[bool] = False` — tracks if YAML panel visible
- `yaml_mode: reactive[str] = "full"` — "full" or "spec"

**New keybindings:**
- `('y', 'action_show_yaml', 'YAML')` — shows YAML manifest
- `('m', 'action_toggle_yaml_mode', 'Toggle')` — toggles manifest/spec (only when YAML open)

**New actions:**
1. `action_show_yaml()` — triggered by 'y' key
   - Gets selected resource from table
   - Calls `_show_yaml_dialog(resource_type, name, namespace)`
   - Spawns worker thread to fetch YAML

2. `_show_yaml_dialog()` — private method
   - Validates selection
   - Calls `_show_yaml_worker()` in background

3. `_show_yaml_worker()` — worker thread
   - Calls `k8s.get_resource_yaml()`
   - On success: calls main thread with `_apply_yaml_result(full_yaml, spec_yaml)`
   - On error: calls main thread with error message

4. `_apply_yaml_result()` — main thread callback
   - Stores both YAML strings internally (e.g., `self._yaml_full`, `self._yaml_spec`)
   - Sets `yaml_view_open = True`, `yaml_mode = "full"`
   - Calls `_show_yaml_panel()`

5. `_show_yaml_panel()` — display logic
   - Gets detail panel (VerticalScroll)
   - Replaces content with TextArea widget, `language='yaml'`, `read_only=True`
   - Sets title: "YAML (full)" or "YAML (spec)" based on `yaml_mode`
   - Updates status bar with: `"YAML (full) | m: toggle · d: describe · ↑↓ scroll"`
   - Sets `detail_panel_open = True`, adds "show" class to panel

6. `action_toggle_yaml_mode()` — triggered by 'm' key
   - Only works if `yaml_view_open == True`
   - Toggles `yaml_mode` between "full" and "spec"
   - Calls `_show_yaml_panel()` to refresh display

**Updates to existing methods:**
- `action_close_detail_panel()` — sets `yaml_view_open = False` (already closes both Describe and YAML)
- `action_describe_resource()` — sets `yaml_view_open = False` before showing Describe (replaces YAML)
- Status bar hints now context-aware (check `yaml_view_open` state)

**Detail panel widget swap:**
- Currently uses `Static` widget for all detail content
- When showing YAML: replace with `TextArea` widget (read-only)
- When showing Describe: keep `Static` widget
- Store reference to active widget so `escape` key can close properly

---

## Data Structures

**Internal storage (ClusterScreen):**
```python
self._resource_data = []  # Existing: table row data
self._yaml_full = ""      # New: full manifest YAML
self._yaml_spec = ""      # New: spec-only YAML
```

**YAML serialization format (Python yaml.dump output):**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: example-pod
  namespace: default
  ...
spec:
  containers:
  - image: nginx:latest
    name: nginx
    ...
status:
  phase: Running
  ...
```

**Spec-only format (extracted from resource object):**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: example-pod
  namespace: default
spec:
  containers:
  - image: nginx:latest
    name: nginx
    ...
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Resource not found | Display: `"Resource no longer exists"` in detail panel |
| YAML serialization fails | Log error, display: `"Failed to fetch YAML manifest"` |
| K8s client error (auth, connection) | Propagate to detail panel as error message |
| Very large manifest | TextArea handles it (pagination, scrolling work) |
| All-namespace mode | Works correctly — `get_resource_yaml()` uses namespace param |

---

## Compatibility

**All resource types:** Pods, Deployments, Services, ConfigMaps, StatefulSets, DaemonSets, Jobs, CronJobs, Ingresses, Endpoints, Secrets, PVCs

Tested with:
- Single-namespace resources (default)
- All-namespaces view
- System namespaces (kube-system, kube-public, etc.)

---

## Testing

**Unit tests (test_k8s.py):**
- `test_get_resource_yaml_pod()` — fetch pod manifest
- `test_get_resource_yaml_deployment()` — fetch deployment manifest
- `test_get_resource_yaml_not_found()` — handle missing resource
- `test_get_resource_yaml_spec_only()` — verify spec extraction

**Integration tests (test_app.py):**
- `test_action_show_yaml()` — trigger 'y', verify panel shows
- `test_action_toggle_yaml_mode()` — toggle 'm', verify mode change
- `test_yaml_with_all_namespaces()` — YAML works in all-namespace mode
- `test_yaml_closes_on_describe()` — 'd' key closes YAML, opens Describe
- `test_yaml_closes_on_escape()` — 'Escape' key closes detail panel

---

## Keybinding Reference

| Key | Action | Context | Note |
|-----|--------|---------|------|
| `y` | Show YAML | Table selected | Opens YAML panel (full mode) |
| `m` | Toggle mode | YAML panel open | Switches between full/spec |
| `d` | Describe | Any | Replaces YAML with Describe |
| `Escape` | Close panel | Any | Closes both Describe and YAML |

---

## Future Enhancements (Out of Scope)

- Export YAML to file
- Diff YAML between resources
- Edit YAML inline and apply changes
- Search within YAML
- Syntax validation (warns on invalid YAML structure)

---

## Implementation Notes

1. **TextArea widget:** Use Textual's built-in TextArea with `language='yaml'` and `read_only=True`. No custom highlighting needed.

2. **Storage:** Keep both YAML strings in memory (`_yaml_full`, `_yaml_spec`) to avoid re-fetching on toggle.

3. **Worker pattern:** Follow existing describe/logs pattern — async fetch, callback on completion.

4. **Status bar:** Update keybindings hint to show context-specific help (hint changes when YAML panel open).

5. **All-namespace handling:** Existing code already manages namespace switching. `get_resource_yaml()` respects namespace parameter like `describe_resource()`.

---

## Files Modified

- `src/gantry/k8s.py` — Add `get_resource_yaml()`
- `src/gantry/screens.py` — Add ClusterScreen methods, keybindings, reactive state
- `tests/test_k8s.py` — Add unit tests for `get_resource_yaml()`
- `tests/test_app.py` — Add integration tests for YAML actions

---

## Success Criteria

✅ Press 'y' on any resource → YAML appears in right panel  
✅ YAML is syntax-highlighted (yaml language support)  
✅ Press 'm' → toggles between full and spec modes  
✅ Press 'd' → switches to Describe view  
✅ Press 'Escape' → closes detail panel  
✅ Works with all resource types (pods, deployments, etc.)  
✅ Works in all-namespace mode  
✅ Error messages display gracefully  
✅ Status bar shows context-appropriate hints  
✅ All new tests pass  
