# Debug Logging Setup for Gantry

## Context

Gantry currently has no logging infrastructure. When crashes occur or debugging is needed, errors disappear into the terminal with raw tracebacks. This plan adds structured logging to:
- Always capture crash logs to `gantry.log`
- Enable verbose debug output when `--debug` flag is passed
- Log across all backend (k8s, helm) and UI (screens, widgets) layers

## Design

### Log File
- **Location**: Project root (`gantry.log`, next to `pyproject.toml`)
- **Path resolution**: `Path(__file__).resolve().parents[2] / "gantry.log"` from `__main__.py`

### Log Levels
- **Default (no flag)**: `WARNING` level to file (captures crashes via exception handler)
- **With `--debug`**: `DEBUG` level to file + Textual's internal log directed to same file

### Architecture
- Single logger tree under `gantry` namespace
- Each module uses `logging.getLogger(__name__)` — no handler configuration
- Only `__main__.py` configures handlers (FileHandler at project root)
- Textual's `log_file` parameter passed to `app.run()` when `--debug` active

## Implementation Steps

### 1. `src/gantry/__main__.py`
- Add `argparse.ArgumentParser` with `--debug` flag
- Create `setup_logging(debug: bool, log_path: Path)` helper
- Configure Python logging module: FileHandler to `gantry.log`
  - Default: WARNING level
  - Debug mode: DEBUG level + formatter with timestamp/level/name
- Wrap `app.run()` in `try/except Exception` to log crashes via `logging.exception()`
- All logs (Python and application) go through the configured FileHandler

### 2. `src/gantry/k8s.py`
Add module-level logger:
```python
import logging
logger = logging.getLogger(__name__)
```
In each function:
- Log `DEBUG` on entry: `logger.debug(f"list_pods called with namespace={namespace}")`
- In `except Exception` blocks before returning error dict: `logger.error(f"Error in list_pods: {e}", exc_info=True)`

Functions to instrument:
- `list_contexts()`, `switch_context()`, `list_namespaces()`
- `list_pods()`, `list_services()`, `list_deployments()`, `list_configmaps()`
- `describe_resource()`, `get_pod_logs()`

### 3. `src/gantry/helm.py`
Same pattern as k8s.py:
- Module-level logger
- DEBUG on function entry with args
- ERROR on exception in catch blocks

Functions: `list_repos()`, `search_charts()`, `repo_add()`, `repo_remove()`, `repo_update()`, `install_chart()`

### 4. `src/gantry/screens.py`
Add module-level logger and log:
- `@work` methods: `DEBUG` on worker start, completion
- Fetch failures: `ERROR` with message
- Worker callbacks: `DEBUG` on thread callback execution

Key methods:
- `_load_context_info_worker()`, `_fetch_resources_worker()`, `_describe_resource_worker()`, `_show_logs_worker()`
- `_load_repos_worker()`, `_load_charts_worker()`, `_deploy_chart_worker()`

### 5. `src/gantry/widgets.py`
Add module-level logger and log:
- `SearchInput.on_input_changed()`: `DEBUG` on search term change
- `ResourceTable.on_data_table_row_selected()`: `DEBUG` on row selection with row key

## Verification

1. **Crash logging**:
   - Run `uv run python -m gantry`, trigger an unhandled exception (e.g., bad kubeconfig)
   - Check `gantry.log` exists at project root with traceback

2. **Debug mode**:
   - Run `uv run python -m gantry --debug`
   - Interact with UI (switch namespaces, search, view logs)
   - Check `gantry.log` contains DEBUG-level messages from all layers

3. **No regression**:
   - Run `uv run pytest tests/ -v` — all 68 tests still pass

## Critical Files to Modify
- `src/gantry/__main__.py` (add 40 lines: argparse + logging setup + crash handler)
- `src/gantry/k8s.py` (add logger + ~20 log statements)
- `src/gantry/helm.py` (add logger + ~10 log statements)
- `src/gantry/screens.py` (add logger + ~15 log statements)
- `src/gantry/widgets.py` (add logger + 5 log statements)
