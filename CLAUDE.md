# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

**Gantry** — A keyboard-first TUI for Kubernetes cluster management and Helm chart orchestration. Built with Python + [Textual](https://textual.textualize.io/).

## Commands

```bash
# Install dependencies
uv sync

# Run the app
uv run python -m gantry

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_k8s.py -v

# Run a single test
uv run pytest tests/test_k8s.py::TestListPods::test_list_pods_success -v
```

**Requirements**: Python 3.11+, `kubectl` + kubeconfig configured, `helm` CLI (for Helm features).

## Architecture

### Layer Separation

```
app.py          GantryApp shell — screen registration, global keybindings (Tab, q)
screens.py      ClusterScreen, HelmScreen, ContextPickerModal — orchestrate user interactions
widgets.py      ResourceTable, SearchInput, StatusBar — reusable UI components
k8s.py          Kubernetes API wrapper (official kubernetes-python client)
helm.py         Helm CLI wrapper (subprocess calls, JSON output parsing)
```

### Key Design Patterns

**Async workers**: All K8s/Helm I/O runs in `@work(thread=True)` threads to keep the UI responsive. Screens track a `_current_fetch_id` counter to discard stale results when a new fetch starts before the previous one completes.

**Structured error returns**: Backend functions (`k8s.py`, `helm.py`) never raise — they return dicts with an `"error"` key on failure. Screens check for this key before rendering.

**Reactive properties + message passing**: Textual's `reactive()` drives re-renders. Widgets post custom `Message` subclasses (e.g., `ResourceTable.RowSelected`, `SearchInput.SearchChanged`) that screens handle via `on_*` methods.

**Column preservation during filtering**: `ResourceTable.filter_by_search()` preserves column definitions so they aren't lost when rows are filtered.

### Backend Modules

**`k8s.py`** — 9 functions wrapping the kubernetes client:
- `list_contexts()`, `switch_context(name)`
- `list_namespaces(context)`, `list_pods/services/deployments/configmaps(namespace)`
- `describe_resource(type, name, namespace)`, `get_pod_logs(pod_name, namespace)`
- Pass `namespace="all"` to any list function for all-namespaces mode

**`helm.py`** — 6 functions wrapping helm CLI subprocess:
- `list_repos()`, `search_charts(query, repo)`, `repo_add/remove/update()`
- `install_chart(release_name, chart, namespace, values)`

### Screen Architecture

**`ClusterScreen`** — resource explorer with reactive `current_resource_type`, `current_namespace`, `current_context`. Uses ContextPickerModal for context/namespace switching.

**`HelmScreen`** — repo browser and chart deployment. Same async worker pattern.

**`ContextPickerModal`** — modal that dynamically loads namespaces for the selected context.

## File Organization

- **`/plans`** — Implementation plans and architecture decisions (create here before major work)
- **`/docs`** — User guides and reference materials
- **`src/gantry/`** — Source code
- **`tests/`** — Test suite (68 tests, 100% passing)

## Keybindings Reference

| Key | Action |
|-----|--------|
| `Tab` | Switch Cluster ↔ Helm views |
| `c` | Open context/namespace picker |
| `/` | Search/filter resources or charts |
| `d` | Describe selected resource |
| `L` | View pod logs (pods only) |
| `r` | Refresh current view |
| `Enter` | Deploy selected Helm chart |
| `Escape` | Close dialogs |
| `q` | Quit |
