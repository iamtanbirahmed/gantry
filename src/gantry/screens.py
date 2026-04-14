"""Screen components for Gantry TUI."""

from typing import Any, Dict, List, Optional
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Static, Button, OptionList, Input, TextArea
from textual.widget import Widget
from textual.binding import Binding
from textual.message import Message
from textual import work
from textual.reactive import reactive
import json

from gantry import k8s
from gantry.widgets import ResourceTable, SearchInput, StatusBar


class ClusterScreen(Screen):
    """Screen for Kubernetes cluster exploration and management."""

    BINDINGS = [
        ("tab", "switch_screen('helm')", "Switch to Helm View"),
        ("slash", "focus_search", "Search"),
        ("d", "describe_resource", "Describe"),
        ("l", "show_logs", "Logs"),
        ("r", "refresh_resources", "Refresh"),
        ("q", "quit", "Quit Gantry"),
    ]

    CSS = """
    Screen {
        layout: vertical;
        background: $surface;
        color: $text;
    }

    #header-container {
        height: 3;
        border: solid $accent;
    }

    #resource-type-label {
        height: 1;
        width: 100%;
        content-align: left middle;
    }

    #resource-type-selector {
        height: 1;
        width: 100%;
    }

    #body-container {
        height: 1fr;
    }

    ResourceTable {
        height: 1fr;
        width: 100%;
    }

    SearchInput {
        height: 1;
        width: 100%;
        display: none;
    }

    SearchInput.show {
        display: block;
    }

    #detail-panel {
        height: auto;
        border: solid $accent;
        display: none;
        background: $boost;
        color: $text;
        padding: 1;
    }

    #detail-panel.show {
        display: block;
        height: auto;
    }

    StatusBar {
        height: 1;
        border: solid $accent;
    }
    """

    current_resource_type = reactive("Pods")
    current_namespace = reactive("default")
    current_context = reactive("N/A")
    connection_status = reactive("Disconnected")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_row: Optional[str] = None
        self._resource_data: List[Dict[str, Any]] = []
        self._all_resources: Dict[str, List[Dict[str, Any]]] = {
            "Pods": [],
            "Services": [],
            "Deployments": [],
            "ConfigMaps": [],
        }

    def compose(self):
        """Compose the cluster screen."""
        # Header with resource type selector
        with Vertical(id="header-container"):
            yield Label("Resource Type:", id="resource-type-label")
            with Horizontal(id="resource-type-selector"):
                yield Button("Pods", id="btn-pods", variant="primary")
                yield Button("Services", id="btn-services")
                yield Button("Deployments", id="btn-deployments")
                yield Button("ConfigMaps", id="btn-configmaps")

        # Body with resource table and search
        with Vertical(id="body-container"):
            yield ResourceTable(id="resource-table")
            yield SearchInput(id="search-input")

        # Detail panel for descriptions and logs
        yield Label(id="detail-panel")

        # Status bar
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        """Initialize cluster screen on mount."""
        self.title = "Gantry - Cluster Management"
        # Load initial context and namespace
        self._load_context_info()
        # Load initial resources
        self._refresh_resources()

    def _load_context_info(self) -> None:
        """Load current Kubernetes context and namespace."""
        self._load_context_info_worker()

    @work(thread=True)
    def _load_context_info_worker(self) -> None:
        """Worker to load context information without blocking UI."""
        contexts = k8s.list_contexts()
        if contexts:
            for ctx in contexts:
                if ctx.get("current"):
                    self.current_context = ctx.get("name", "N/A")
                    self.current_namespace = ctx.get("namespace", "default")
                    break
            self.connection_status = "Connected"
        else:
            self.connection_status = "Error"
        self._update_status_bar()

    def _update_status_bar(self) -> None:
        """Update the status bar with current info."""
        status_bar: StatusBar = self.query_one("#status-bar", StatusBar)
        status_bar.update_context(self.current_context)
        status_bar.update_namespace(self.current_namespace)
        status_bar.update_status(self.connection_status)

    def _refresh_resources(self) -> None:
        """Refresh the resource list based on current type."""
        resource_type = self.current_resource_type
        namespace = self.current_namespace
        self._fetch_resources_worker(resource_type, namespace)

    @work(thread=True)
    def _fetch_resources_worker(self, resource_type: str, namespace: str) -> None:
        """Worker to fetch resources without blocking UI."""
        resources = []
        try:
            if resource_type == "Pods":
                resources = k8s.list_pods(namespace)
            elif resource_type == "Services":
                resources = k8s.list_services(namespace)
            elif resource_type == "Deployments":
                resources = k8s.list_deployments(namespace)
            elif resource_type == "ConfigMaps":
                resources = k8s.list_configmaps(namespace)

            # Filter out error entries
            resources = [r for r in resources if "error" not in r]

            # Store and display
            self._all_resources[resource_type] = resources
            self._display_resources(resource_type, resources)
            self.connection_status = "Connected"
        except Exception as e:
            self.connection_status = f"Error: {str(e)}"
        finally:
            self._update_status_bar()

    def _display_resources(self, resource_type: str, resources: List[Dict[str, Any]]) -> None:
        """Display resources in the table."""
        table: ResourceTable = self.query_one("#resource-table", ResourceTable)

        if resource_type == "Pods":
            columns = ["Name", "Status", "Ready", "Restarts"]
            keys = ["name", "status", "ready", "restarts"]
        elif resource_type == "Services":
            columns = ["Name", "Type", "Cluster IP"]
            keys = ["name", "type", "cluster_ip"]
        elif resource_type == "Deployments":
            columns = ["Name", "Replicas", "Ready", "Available"]
            keys = ["name", "replicas", "ready_replicas", "available_replicas"]
        elif resource_type == "ConfigMaps":
            columns = ["Name", "Keys"]
            keys = ["name", "key_count"]
        else:
            return

        table.populate_resources(resources, columns, keys)
        # Store resource data for actions like describe and logs
        self._resource_data = resources

    def on_button_pressed(self, event) -> None:
        """Handle button presses for resource type selection."""
        button_id = event.button.id
        if button_id == "btn-pods":
            self.current_resource_type = "Pods"
        elif button_id == "btn-services":
            self.current_resource_type = "Services"
        elif button_id == "btn-deployments":
            self.current_resource_type = "Deployments"
        elif button_id == "btn-configmaps":
            self.current_resource_type = "ConfigMaps"

        # Update button styles
        self._update_button_styles()
        # Refresh resources
        self._refresh_resources()

    def _update_button_styles(self) -> None:
        """Update button styles based on current resource type."""
        buttons = {
            "Pods": "btn-pods",
            "Services": "btn-services",
            "Deployments": "btn-deployments",
            "ConfigMaps": "btn-configmaps",
        }

        for resource_type, btn_id in buttons.items():
            btn = self.query_one(f"#{btn_id}", Button)
            if resource_type == self.current_resource_type:
                btn.variant = "primary"
            else:
                btn.variant = "default"

    def action_focus_search(self) -> None:
        """Focus on the search input."""
        search_input: SearchInput = self.query_one("#search-input", SearchInput)
        search_input.add_class("show")
        search_input.focus()

    def action_describe_resource(self) -> None:
        """Describe the selected resource."""
        table: ResourceTable = self.query_one("#resource-table", ResourceTable)
        if not table.cursor_row or not self._resource_data:
            return

        row_index = table.cursor_row
        if 0 <= row_index < len(self._resource_data):
            resource = self._resource_data[row_index]
            resource_name = resource.get("name", "Unknown")
            resource_type = self.current_resource_type.rstrip("s")  # Remove trailing 's'

            self._show_describe_dialog(resource_type, resource_name)

    def _show_describe_dialog(self, resource_type: str, resource_name: str) -> None:
        """Show a dialog with resource details."""
        self._describe_resource_worker(resource_type, resource_name)

    @work(thread=True)
    def _describe_resource_worker(self, resource_type: str, resource_name: str) -> None:
        """Worker to fetch resource description."""
        result = k8s.describe_resource(
            resource_type, resource_name, namespace=self.current_namespace
        )
        if result:
            # Format the result as a readable string
            description = self._format_resource_description(resource_type, result)
            self._display_detail_panel(description)
            self.connection_status = f"Described {resource_name}"
        else:
            self.connection_status = f"Failed to describe {resource_name}"
        self._update_status_bar()

    def _format_resource_description(self, resource_type: str, result: Dict[str, Any]) -> str:
        """Format resource description for display."""
        if "error" in result:
            return f"Error: {result.get('error', 'Unknown error')}"

        lines = [f"=== {resource_type}: {result.get('name', 'Unknown')} ==="]
        lines.append(f"Namespace: {result.get('namespace', 'N/A')}")

        # Add resource-type-specific info
        if resource_type == "Pod":
            lines.append(f"Status: {result.get('status', 'N/A')}")
            if "spec" in result and "containers" in result["spec"]:
                lines.append("Containers:")
                for container in result["spec"]["containers"]:
                    lines.append(f"  - {container.get('name', 'N/A')}: {container.get('image', 'N/A')}")

        elif resource_type == "Service":
            lines.append(f"Type: {result.get('type', 'N/A')}")
            lines.append(f"Cluster IP: {result.get('cluster_ip', 'N/A')}")
            if "ports" in result:
                lines.append("Ports:")
                for port in result["ports"]:
                    lines.append(f"  - {port.get('port', 'N/A')}/{port.get('protocol', 'N/A')}")

        elif resource_type == "Deployment":
            lines.append(f"Replicas: {result.get('replicas', 0)}")
            if "status" in result:
                status = result["status"]
                lines.append(f"Ready: {status.get('ready_replicas', 0)}/{result.get('replicas', 0)}")

        elif resource_type == "ConfigMap":
            if "data" in result:
                lines.append(f"Keys: {', '.join(result['data'].keys())}")

        return "\n".join(lines)

    def _display_detail_panel(self, content: str) -> None:
        """Display content in the detail panel."""
        try:
            detail_panel = self.query_one("#detail-panel", Label)
            detail_panel.update(content)
            detail_panel.add_class("show")
        except Exception:
            # If detail panel is not available, just update status bar
            pass

    def action_show_logs(self) -> None:
        """Show logs for the selected pod."""
        if self.current_resource_type != "Pods":
            self.connection_status = "Logs available for Pods only"
            self._update_status_bar()
            return

        table: ResourceTable = self.query_one("#resource-table", ResourceTable)
        if not table.cursor_row or not self._resource_data:
            return

        row_index = table.cursor_row
        if 0 <= row_index < len(self._resource_data):
            pod = self._resource_data[row_index]
            pod_name = pod.get("name", "Unknown")
            self._show_logs_worker(pod_name)

    @work(thread=True)
    def _show_logs_worker(self, pod_name: str) -> None:
        """Worker to fetch and display pod logs."""
        logs = k8s.get_pod_logs(pod_name, namespace=self.current_namespace)
        if logs:
            log_display = f"=== Logs for {pod_name} ===\n\n{logs}"
            self._display_detail_panel(log_display)
            self.connection_status = f"Logs for {pod_name}"
        else:
            self.connection_status = f"Failed to retrieve logs for {pod_name}"
        self._update_status_bar()

    def action_refresh_resources(self) -> None:
        """Refresh the resource list."""
        self._refresh_resources()

    def watch_current_resource_type(self, new_type: str) -> None:
        """React to resource type changes."""
        self._refresh_resources()

    def on_search_input_search_changed(self, message: SearchInput.SearchChanged) -> None:
        """Handle search input changes and filter the table."""
        table: ResourceTable = self.query_one("#resource-table", ResourceTable)
        table.filter_by_search(message.value)


class HelmScreen(Screen):
    """Screen for Helm chart exploration and deployment."""

    BINDINGS = [
        ("tab", "switch_screen('cluster')", "Switch to Cluster View"),
        ("q", "quit", "Quit"),
    ]

    def compose(self):
        """Compose the helm screen."""
        yield Container(
            Label("Helm View", id="helm-label"),
            id="helm-container",
        )

    def on_mount(self) -> None:
        """Initialize helm screen on mount."""
        self.title = "Gantry - Helm Orchestration"
