## Introduction

**Gantry** — TUI for Kubernetes cluster management + Helm orchestration. Keyboard-first. Visualize, manage, deploy resources from terminal.

## Project Vision

**Gantry** = container crane. Handles deployment pipeline heavy lifting. Bridges local config to production clusters.

## Core Features

### ☸️ Cluster Exploration
- **Multi-Cluster Context:** Switch K8s clusters + contexts
- **Deep Resource Discovery:** Real-time Pods, Services, Deployments, ConfigMaps visibility
- **Live Status Monitoring:** Instant resource health + cluster event feedback

### ⛵ Helm Orchestration
- **Chart Browser:** Explore + search Helm charts
- **Repository Management:** Add, remove, update Helm repos from TUI
- **Streamlined Deployment:** Configure + deploy Helm charts to active namespaces

## Implementation Status

**v1.0 - COMPLETE** ✅

- ✅ Cluster Exploration: Browse pods, services, deployments, configmaps
- ✅ Helm Orchestration: List repos, search charts, deploy charts
- ✅ Multi-cluster: Switch contexts, manage namespaces
- ✅ Resource Details: Describe resources, view pod logs
- ✅ Search/Filter: Find resources and charts quickly
- ✅ Responsive UI: Async workers keep TUI responsive
- ✅ Error Handling: Graceful degradation for missing kubeconfig/helm

**Test Coverage**: 68 tests passing (100%)

**Project Status**: PR #1 created, ready for review

## Default Keybindings

| Key | Action |
| --- | --- |
| `Tab` | Switch between Cluster and Helm views |
| `c` | Open context/namespace picker |
| `/` | Search/Filter resources or charts |
| `d` | Describe selected resource |
| `L` | View Pod logs (pods only) |
| `r` | Refresh current view |
| `Enter` | Deploy selected Helm chart |
| `Escape` | Close dialogs/pickers |
| `q` | Quit Gantry |

## Project Structure

```
gantry/
├── src/gantry/              # Main package
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Entry point (python -m gantry)
│   ├── app.py               # Textual App + screen management
│   ├── screens.py           # ClusterScreen, HelmScreen, ContextPickerModal
│   ├── widgets.py           # ResourceTable, SearchInput, StatusBar
│   ├── k8s.py               # Kubernetes client wrapper
│   └── helm.py              # Helm CLI subprocess wrapper
├── tests/                   # Test suite (68 tests)
│   ├── test_app.py          # App + screen tests
│   ├── test_k8s.py          # K8s backend tests
│   └── test_helm.py         # Helm backend tests
├── plans/                   # Architecture + design docs
├── pyproject.toml           # Project configuration
├── README.md                # User documentation
└── CLAUDE.md                # This file
```

## File Organization Constraints

Project files organization:

- **`/plans`** — Implementation plans, design docs, architecture decisions
- **`/docs`** — User guides, API docs, reference materials
- **`src/gantry/`** — Source code organized by component
- **`tests/`** — Test suite with full coverage

## Getting Started

```bash
# Install dependencies
uv sync

# Run Gantry
uv run python -m gantry

# Run tests
uv run pytest tests/ -v
```

**Requirements**:
- Python 3.11+
- kubectl + kubeconfig configured
- helm installed (for Helm features)

## Development Guidelines

1. Update README when adding features or changing keybindings
2. Document architecture decisions + design choices in `/docs`
3. Create implementation plans in `/plans` before major work
4. Reference README for features + capabilities
5. Keep docs current with code changes

## License

MIT License. See `LICENSE` for details.