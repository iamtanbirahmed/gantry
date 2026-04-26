# gantry

Keyboard-first TUI for Kubernetes cluster management and Helm orchestration.

![Gantry screenshot](docs/images/screenshot.svg)

## Features

- Browse **16 Kubernetes resource types**: Pods, Deployments, ReplicaSets, StatefulSets, DaemonSets, Jobs, CronJobs, Services, Ingresses, Endpoints, ConfigMaps, Secrets, PVCs, PVs, Namespaces, Nodes
- Left sidebar for fast resource type switching
- Describe resources and view pod logs in a right-side detail panel
- View and toggle YAML manifests (full / spec-only mode)
- Vim-style `/` search and filter across resources and charts
- Manage Helm repositories and deploy charts interactively
- Context and namespace switching via modal picker
- State persistence across sessions

## Requirements

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) (package manager)
- `kubectl` + valid kubeconfig for Kubernetes features
- `helm` CLI for Helm features (optional — graceful degradation if missing)

## Install

```bash
git clone https://github.com/iamtanbirahmed/gantry.git
cd gantry
uv sync
```

## Run

```bash
uv run python -m gantry

# With debug logging (writes to gantry.log)
uv run python -m gantry --debug
```

## Keybindings

### Global

| Key | Action |
|-----|--------|
| `Tab` | Switch between Cluster and Helm views |
| `q` | Quit |

### Cluster View

| Key | Action |
|-----|--------|
| `←` / `→` | Navigate panels |
| `c` | Open context + namespace picker |
| `/` | Search / filter resources |
| `d` | Describe selected resource |
| `y` | View YAML manifest |
| `m` | Toggle YAML mode (full / spec-only) |
| `l` | View pod logs (pods only) |
| `r` | Refresh resources |
| `Escape` | Close panel / cancel search |

### Helm View

| Key | Action |
|-----|--------|
| `←` / `→` | Navigate panels |
| `/` | Search charts |
| `r` | Refresh charts |
| `Enter` | Deploy selected Helm chart |
| `Escape` | Cancel |

## Development

```bash
# Install all extras
uv sync --all-extras

# Run tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_k8s.py -v

# Run linting
uv run ruff check src/

# Format code
uv run ruff format src/
```

## Project Structure

```
src/gantry/
├── __main__.py    # Entry point, CLI args, logging setup
├── app.py         # GantryApp — main Textual app, screen switching
├── screens.py     # ClusterScreen, HelmScreen, ContextPickerModal
├── widgets.py     # ResourceTable, SearchInput, StatusBar
├── k8s.py         # Kubernetes API wrapper
├── helm.py        # Helm CLI wrapper
└── state.py       # State persistence (context & namespace)

tests/
├── test_app.py    # App initialization, screen switching, keybindings
├── test_k8s.py    # K8s backend tests
└── test_helm.py   # Helm backend tests
```

## Update Screenshot

```bash
bash scripts/screenshot.sh
```

## License

MIT
