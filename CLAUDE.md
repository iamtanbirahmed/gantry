# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Gantry** is a keyboard-first TUI for Kubernetes cluster management and Helm orchestration. It allows users to visualize, manage, and deploy resources directly from the terminal.

### Core Architecture

The application is built with **Textual** (Python TUI framework) and uses the Kubernetes Python client for cluster interaction. It consists of two main screens:

1. **Cluster Screen** — Browse and manage K8s resources (pods, services, deployments, configmaps)
2. **Helm Screen** — Manage Helm repositories and deploy charts

### Key Design Patterns

- **Async Resource Loading** — K8s operations use async workers to keep the TUI responsive
- **Graceful Degradation** — Missing kubeconfig/helm is handled without crashing
- **Context/Namespace Switching** — Modal dialog for switching K8s contexts and namespaces
- **Search & Filter** — Integrated search across resources and charts
- **Logging** — Debug logging available via `--debug` flag, crashes logged to `gantry.log`

## Quick Start

```bash
# Install dependencies
uv sync

# Run Gantry (basic)
uv run python -m gantry

# Run with debug logging
uv run python -m gantry --debug

# Run tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_k8s.py -v

# Run a specific test
uv run pytest tests/test_k8s.py::test_list_resources_success -v
```

## Key Commands & Workflows

### Development

```bash
# Install in editable mode
uv sync --all-extras

# Run type checking (if using mypy)
uv run mypy src/gantry

# Run linting
uv run ruff check src/

# Format code
uv run ruff format src/
```

### Debugging

- **Debug Logging**: Use `uv run python -m gantry --debug` to enable detailed logging
- **Log Location**: Debug output is written to `gantry.log` in project root
- **Crash Logs**: Unhandled exceptions are caught and logged (see `__main__.py:setup_logging()`)
- **Test Debugging**: Use `pytest -s` to see print statements, `-vv` for verbose output

## Project Structure

```
src/gantry/
├── __init__.py           # Package init
├── __main__.py           # Entry point with CLI args (--debug flag)
├── app.py                # GantryApp (main Textual app, screen switching)
├── screens.py            # ClusterScreen, HelmScreen, ContextPickerModal
├── widgets.py            # ResourceTable, SearchInput, StatusBar
├── k8s.py                # Kubernetes API wrapper (list resources, switch contexts)
├── helm.py               # Helm CLI wrapper (list repos, search/deploy charts)
└── state.py              # State persistence (saves/loads context & namespace)

tests/
├── test_app.py           # App initialization, screen switching, keybindings
├── test_k8s.py           # K8s backend (list contexts, list resources, etc)
└── test_helm.py          # Helm backend (repos, charts, deployments)

plans/                     # Implementation plans and design decisions
```

## Important Files & Their Responsibilities

### `screens.py` (38KB+)
- **ClusterScreen**: Resource table, namespace/context picker, search, resource details, pod logs
- **HelmScreen**: Chart table, repository management, chart search, deployment
- **ContextPickerModal**: Dialog for switching K8s contexts and namespaces
- Key logic: Resource fetching, filtering, modal interactions, keybinding handlers

### `k8s.py` (17KB+)
- **list_contexts()** — Get all K8s contexts with current context marked
- **switch_context()** — Switch to different K8s context
- **list_resources()** — Fetch pods, services, deployments, configmaps
- **list_resources_all_namespaces()** — Fetch resources across all namespaces
- **describe_resource()** — Get detailed resource info
- **get_pod_logs()** — Stream pod logs
- Error handling: Returns empty lists or error dicts instead of raising exceptions

### `helm.py` (9KB+)
- **list_repos()** — Get Helm repositories
- **search_chart()** — Search charts in repositories
- **add_repo()** — Add new Helm repository
- **deploy_chart()** — Install Helm chart to namespace
- All operations use subprocess calls to `helm` CLI

### `__main__.py` (1.6KB)
- CLI argument parsing (`--debug` flag)
- Logging setup (file handler, DEBUG/WARNING levels)
- Exception handling with crash logging to `gantry.log`
- App initialization and exit handling

## Default Keybindings

| Key | Action |
|-----|--------|
| `Tab` | Switch between Cluster and Helm views |
| `c` | Open context/namespace picker modal |
| `/` | Search/filter resources or charts |
| `d` | Describe selected resource (Cluster view) |
| `l` | View pod logs (pods only) |
| `r` | Refresh current view |
| `Enter` | Deploy selected Helm chart |
| `Escape` | Close dialogs/modals |
| `q` | Quit Gantry |

## Testing

- **68 tests** covering all major functionality
- Test structure mirrors source files (`test_app.py`, `test_k8s.py`, `test_helm.py`)
- Uses `pytest` with async support via `pytest-asyncio`
- Mock K8s client and subprocess calls for isolation

Key test patterns:
- App initialization and screen creation
- Context/namespace switching behavior
- Resource listing and filtering
- Helm repository and chart operations
- Error handling for missing kubeconfig/helm

## Common Development Tasks

### Adding a New Resource Type
1. Add fetch function to `k8s.py` (e.g., `list_statefulsets()`)
2. Add column definitions to `ClusterScreen.RESOURCE_COLUMNS`
3. Add keybinding handler in `ClusterScreen.action_show_*` if needed
4. Add tests to `test_k8s.py`

### Adding a New Keybinding
1. Add `Binding()` to screen's `BINDINGS` list
2. Implement `action_*()` method on screen class
3. Update keybinding table in this file
4. Add test to verify keybinding is registered

### Debugging Resource Loading Issues
- Check `k8s.py` for fetch function errors (look for `logger.error()` calls)
- Verify kubeconfig is valid: `kubectl config view`
- Run with `--debug` flag to see detailed logs
- Check `test_k8s.py` for similar scenarios that are tested

### Debugging UI Issues
- Use Textual's devtools: `from textual.devtools import devtools; devtools(app)`
- Check CSS styling in `app.py` and `screens.py`
- Verify column widths in `RESOURCE_COLUMNS` dicts
- Test screen switching with `action_switch_screen()` in `app.py`

## Recent Fixes & Important Context

### Resource Loading
- Fixed race condition where resources could load before context is set
- Added all-namespaces support for comprehensive resource visibility
- Resources now properly filter by namespace when context is switched

### Context Picker Modal
- Fixed namespace selection capture in `ContextPickerModal.handle_namespace_selected()`
- Modal properly closes and applies both context + namespace changes

### Error Handling
- All K8s operations return empty lists or error dicts (never raise)
- Helm operations catch subprocess errors gracefully
- Crash logging captures unexpected exceptions with full traceback

## Dependencies

- **textual** (>=0.40.0) — TUI framework
- **kubernetes** (>=28.0.0) — K8s Python client
- **pytest**, **pytest-asyncio** — Testing
- **uv** — Package/environment manager (not in pyproject.toml, external tool)

Requirements:
- Python 3.11+
- `kubectl` + valid kubeconfig for K8s features
- `helm` CLI installed for Helm features (graceful degradation if missing)

## License

MIT License. See `LICENSE` for details.
