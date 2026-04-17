"""Screen components for Gantry TUI."""

import logging
from typing import Any, Dict, List, Optional
from textual.screen import Screen, ModalScreen
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Static, Button, OptionList, Input, TextArea
from textual.widgets._option_list import Option
from textual.widget import Widget
from textual.binding import Binding
from textual.message import Message
from textual import work
from textual.reactive import reactive
import json

from gantry import k8s, state
from gantry.widgets import ResourceTable, SearchInput, StatusBar

logger = logging.getLogger(__name__)


class ContextPickerModal(ModalScreen):
    """Modal for selecting Kubernetes context and namespace."""

    BINDINGS = [
        ("enter", "submit", "Select"),
        ("escape", "cancel", "Cancel"),
    ]

    CSS = """
    ContextPickerModal {
        align: center middle;
    }

    #picker-container {
        width: 60;
        height: auto;
        border: solid $accent;
        background: $panel;
        padding: 1;
    }

    #picker-header {
        dock: top;
        height: 1;
        margin-bottom: 1;
        text-style: bold;
    }

    #contexts-section,
    #namespaces-section {
        height: auto;
        margin-bottom: 1;
    }

    #contexts-label,
    #namespaces-label {
        height: 1;
        text-style: underline;
        margin-bottom: 1;
    }

    OptionList {
        height: auto;
        max-height: 10;
        width: 100%;
        border: solid $accent;
        background: $surface;
    }

    #picker-footer {
        dock: bottom;
        height: 1;
        margin-top: 1;
        text-style: dim;
    }
    """

    def __init__(self, contexts: List[Dict[str, Any]], current_context: str, current_namespace: str):
        super().__init__()
        self.contexts = contexts
        self.current_context = current_context
        self.current_namespace = current_namespace
        self.namespaces = ["all"]  # Start with "all" option
        self.selected_context = current_context
        self.selected_namespace = current_namespace

    def compose(self):
        """Compose the context picker modal."""
        with Container(id="picker-container"):
            yield Label("Select Context & Namespace", id="picker-header")

            with Vertical(id="contexts-section"):
                yield Label("Contexts:", id="contexts-label")
                options = [
                    Option(ctx.get("name", "Unknown"), id=ctx.get("name", "Unknown"))
                    for ctx in self.contexts
                ]
                yield OptionList(*options, id="context-list")

            with Vertical(id="namespaces-section"):
                yield Label("Namespaces:", id="namespaces-label")
                ns_options = [Option(ns, id=ns) for ns in self.namespaces]
                yield OptionList(*ns_options, id="namespace-list")

            yield Label("Press Enter to select or Esc to cancel", id="picker-footer")

    def on_mount(self) -> None:
        """Focus and highlight current selections."""
        try:
            ctx_list = self.query_one("#context-list", OptionList)
            ns_list = self.query_one("#namespace-list", OptionList)

            # Load namespaces asynchronously for the current context
            self._load_namespaces_worker(self.current_context)

            # Find and highlight current selections
            for i in range(ctx_list.option_count):
                opt = ctx_list.get_option_at_index(i)
                if opt.id == self.current_context:
                    ctx_list.highlighted = i
                    break

            for i in range(ns_list.option_count):
                opt = ns_list.get_option_at_index(i)
                if opt.id == self.current_namespace:
                    ns_list.highlighted = i
                    break

            ctx_list.focus()
        except Exception:
            pass

    @work(thread=True)
    def _load_namespaces_worker(self, context_name: str) -> None:
        """Load available namespaces from the cluster in a background thread."""
        namespaces = k8s.list_namespaces(context_name=context_name)
        self.app.call_from_thread(self._set_namespaces, namespaces)

    def _set_namespaces(self, namespaces: List[str]) -> None:
        """Update the namespace list with loaded values."""
        # Start with "all" option, then add actual namespaces
        self.namespaces = ["all"] + sorted(namespaces)

        # Update the namespace list options
        try:
            ns_list = self.query_one("#namespace-list", OptionList)
            ns_list.clear_options()
            for ns in self.namespaces:
                ns_list.add_option(Option(ns, id=ns))
        except Exception:
            pass

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection."""
        if event.option_list.id == "context-list":
            self.selected_context = event.option_id
            # Reload namespaces for the newly selected context
            self._load_namespaces_worker(self.selected_context)
        elif event.option_list.id == "namespace-list":
            self.selected_namespace = event.option_id
            self.action_submit()

    def action_submit(self) -> None:
        """Submit the selected context and namespace."""
        try:
            ctx_list = self.query_one("#context-list", OptionList)
            if ctx_list.highlighted is not None:
                self.selected_context = ctx_list.get_option_at_index(ctx_list.highlighted).id

            ns_list = self.query_one("#namespace-list", OptionList)
            if ns_list.highlighted is not None:
                self.selected_namespace = ns_list.get_option_at_index(ns_list.highlighted).id
        except Exception:
            pass
        logger.debug(f"action_submit: selected context={self.selected_context}, namespace={self.selected_namespace}")
        self.dismiss((self.selected_context, self.selected_namespace))

    def action_cancel(self) -> None:
        """Cancel the picker without selecting."""
        self.dismiss(None)


class ClusterScreen(Screen):
    """Screen for Kubernetes cluster exploration and management."""

    BINDINGS = [
        ("tab", "app.action_switch_screen", "Switch to Helm View"),
        ("slash", "focus_search", "Search"),
        ("c", "show_context_picker", "Pick Context"),
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
        padding: 0 1;
    }

    #resource-type-label {
        height: 1;
        width: 100%;
        content-align: left middle;
        text-style: bold;
    }

    #resource-type-selector {
        height: 1;
        width: 100%;
    }

    #resource-type-selector Button {
        margin-right: 1;
    }

    #resource-type-selector Button:focus {
        background: $accent;
    }

    #body-container {
        height: 1fr;
    }

    ResourceTable {
        height: 1fr;
        width: 100%;
    }

    ResourceTable > DataTable {
        background: $surface;
    }

    SearchInput {
        height: 1;
        width: 100%;
        display: none;
        border: solid $accent;
        padding: 0 1;
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
        margin: 1 0;
    }

    #detail-panel.show {
        display: block;
        height: auto;
    }

    StatusBar {
        height: 1;
        border: solid $accent;
        padding: 0 1;
    }
    """

    current_resource_type = reactive("Pods", init=False)
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

    def _load_context_info(self) -> None:
        """Load current Kubernetes context and namespace."""
        self._load_context_info_worker()

    @work(thread=True)
    def _load_context_info_worker(self) -> None:
        """Worker to load context information without blocking UI."""
        logger.debug("_load_context_info_worker started")
        contexts = k8s.list_contexts()
        context_name = "N/A"
        namespace = "default"
        status = "Error"
        if contexts:
            for ctx in contexts:
                if ctx.get("current"):
                    context_name = ctx.get("name", "N/A")
                    namespace = ctx.get("namespace", "default")
                    break
            status = "Connected"

        # Restore persisted state if available
        saved = state.load_state()
        if saved:
            valid_names = {ctx["name"] for ctx in contexts if "error" not in ctx}
            saved_ctx = saved.get("context")
            saved_ns = saved.get("namespace")
            if saved_ctx and saved_ctx in valid_names:
                if saved_ctx != context_name:
                    k8s.switch_context(saved_ctx)
                context_name = saved_ctx
                namespace = saved_ns or namespace
                status = "Connected"
                logger.debug(f"Restored from state: context={context_name}, namespace={namespace}")

        logger.debug(f"_load_context_info_worker completed: context={context_name}, namespace={namespace}")
        self.app.call_from_thread(self._apply_context_info, context_name, namespace, status)

    def _apply_context_info(self, context_name: str, namespace: str, status: str) -> None:
        """Apply context info on main thread."""
        self.current_context = context_name
        self.current_namespace = namespace
        self.connection_status = status
        self._update_status_bar()
        self._refresh_resources()

    def _update_status_bar(self) -> None:
        """Update the status bar with current info."""
        try:
            status_bar: StatusBar = self.query_one("#status-bar", StatusBar)
            status_bar.update_context(self.current_context)
            status_bar.update_namespace(self.current_namespace)
            status_bar.update_status(self.connection_status)
        except Exception:
            # Status bar not mounted yet, skip update
            pass

    def _refresh_resources(self) -> None:
        """Refresh the resource list based on current type."""
        resource_type = self.current_resource_type
        namespace = self.current_namespace
        self._fetch_resources_worker(resource_type, namespace)

    @work(thread=True)
    def _fetch_resources_worker(self, resource_type: str, namespace: str) -> None:
        """Worker to fetch resources without blocking UI."""
        logger.debug(f"_fetch_resources_worker started: resource_type={resource_type}, namespace={namespace}")
        resources = []
        status = "Connected"
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
            logger.debug(f"_fetch_resources_worker completed: {len(resources)} {resource_type} fetched")
            self.app.call_from_thread(self._display_resources, resource_type, namespace, resources)
        except Exception as e:
            logger.error(f"Error in _fetch_resources_worker: {e}", exc_info=True)
            status = f"Error: {str(e)}"
        finally:
            self.app.call_from_thread(self._apply_fetch_status, status)

    def _apply_fetch_status(self, status: str) -> None:
        """Apply fetch status on main thread."""
        self.connection_status = status
        self._update_status_bar()

    def _display_resources(self, resource_type: str, namespace: str, resources: List[Dict[str, Any]]) -> None:
        """Display resources in the table."""
        # Ignore stale fetch results - only render if this is the current request
        if resource_type != self.current_resource_type or namespace != self.current_namespace:
            return

        table: ResourceTable = self.query_one("#resource-table", ResourceTable)

        # Check if we're in all-namespace mode
        is_all_namespaces = namespace == "all"

        if resource_type == "Pods":
            if is_all_namespaces:
                columns = ["Name", "Namespace", "Status", "Ready", "Restarts"]
                keys = ["name", "namespace", "status", "ready", "restarts"]
            else:
                columns = ["Name", "Status", "Ready", "Restarts"]
                keys = ["name", "status", "ready", "restarts"]
        elif resource_type == "Services":
            if is_all_namespaces:
                columns = ["Name", "Namespace", "Type", "Cluster IP"]
                keys = ["name", "namespace", "type", "cluster_ip"]
            else:
                columns = ["Name", "Type", "Cluster IP"]
                keys = ["name", "type", "cluster_ip"]
        elif resource_type == "Deployments":
            if is_all_namespaces:
                columns = ["Name", "Namespace", "Replicas", "Ready", "Available"]
                keys = ["name", "namespace", "replicas", "ready_replicas", "available_replicas"]
            else:
                columns = ["Name", "Replicas", "Ready", "Available"]
                keys = ["name", "replicas", "ready_replicas", "available_replicas"]
        elif resource_type == "ConfigMaps":
            if is_all_namespaces:
                columns = ["Name", "Namespace", "Keys"]
                keys = ["name", "namespace", "key_count"]
            else:
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

        # Update button styles (reactive watcher handles refresh)
        self._update_button_styles()

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
        if not self._resource_data:
            return

        row_index = table.cursor_row
        if 0 <= row_index < len(self._resource_data):
            resource = self._resource_data[row_index]
            resource_name = resource.get("name", "Unknown")
            resource_type = self.current_resource_type.rstrip("s")  # Remove trailing 's'
            # Use row's namespace if in all-namespace mode, otherwise use current namespace
            namespace = resource.get("namespace", self.current_namespace) if self.current_namespace == "all" else self.current_namespace

            self._show_describe_dialog(resource_type, resource_name, namespace)

    def _show_describe_dialog(self, resource_type: str, resource_name: str, namespace: str) -> None:
        """Show a dialog with resource details."""
        self._describe_resource_worker(resource_type, resource_name, namespace)

    @work(thread=True)
    def _describe_resource_worker(self, resource_type: str, resource_name: str, namespace: str) -> None:
        """Worker to fetch resource description."""
        logger.debug(f"_describe_resource_worker started: {resource_type}/{resource_name} in {namespace}")
        result = k8s.describe_resource(
            resource_type, resource_name, namespace=namespace
        )
        if result:
            description = self._format_resource_description(resource_type, result)
            status = f"Described {resource_name}"
            logger.debug(f"_describe_resource_worker completed: {resource_type}/{resource_name}")
            self.app.call_from_thread(self._apply_describe_result, description, status)
        else:
            logger.error(f"Failed to describe {resource_type}/{resource_name}")
            self.app.call_from_thread(self._apply_fetch_status, f"Failed to describe {resource_name}")

    def _apply_describe_result(self, description: str, status: str) -> None:
        """Apply describe result on main thread."""
        self._display_detail_panel(description)
        self.connection_status = status
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
        if not self._resource_data:
            return

        row_index = table.cursor_row
        if 0 <= row_index < len(self._resource_data):
            pod = self._resource_data[row_index]
            pod_name = pod.get("name", "Unknown")
            # Use row's namespace if in all-namespace mode, otherwise use current namespace
            namespace = pod.get("namespace", self.current_namespace) if self.current_namespace == "all" else self.current_namespace
            self._show_logs_worker(pod_name, namespace)

    @work(thread=True)
    def _show_logs_worker(self, pod_name: str, namespace: str) -> None:
        """Worker to fetch and display pod logs."""
        logger.debug(f"_show_logs_worker started for pod {pod_name} in {namespace}")
        logs = k8s.get_pod_logs(pod_name, namespace=namespace)
        if logs:
            log_display = f"=== Logs for {pod_name} ===\n\n{logs}"
            status = f"Logs for {pod_name}"
            logger.debug(f"_show_logs_worker completed for pod {pod_name}")
            self.app.call_from_thread(self._apply_describe_result, log_display, status)
        else:
            logger.error(f"Failed to retrieve logs for pod {pod_name}")
            self.app.call_from_thread(self._apply_fetch_status, f"Failed to retrieve logs for {pod_name}")

    def action_refresh_resources(self) -> None:
        """Refresh the resource list."""
        self._refresh_resources()

    def action_show_context_picker(self) -> None:
        """Show the context/namespace picker modal."""
        self._load_contexts_for_picker_worker()

    @work(thread=True)
    def _load_contexts_for_picker_worker(self) -> None:
        """Load contexts in background for the picker modal."""
        contexts = k8s.list_contexts()
        self.app.call_from_thread(self._show_context_picker_modal, contexts)

    def _show_context_picker_modal(self, contexts: List[Dict[str, Any]]) -> None:
        """Show the context picker modal on main thread."""
        if not contexts or any("error" in ctx for ctx in contexts):
            self.connection_status = "Error: Unable to load contexts"
            self._update_status_bar()
            return

        modal = ContextPickerModal(contexts, self.current_context, self.current_namespace)
        self.app.push_screen(modal, callback=self._on_context_picker_dismiss)

    def _on_context_picker_dismiss(self, result: Optional[tuple]) -> None:
        """Handle context picker result."""
        if result:
            new_context, new_namespace = result
            if new_context != self.current_context:
                self._switch_context_worker(new_context, new_namespace)
            else:
                self.current_namespace = new_namespace
                state.save_state(self.current_context, new_namespace)
                self._refresh_resources()
                self._update_status_bar()

    @work(thread=True)
    def _switch_context_worker(self, new_context: str, new_namespace: str) -> None:
        """Switch context in background thread."""
        switch_result = k8s.switch_context(new_context)
        self.app.call_from_thread(
            self._apply_context_switch, new_context, new_namespace, switch_result
        )

    def _apply_context_switch(self, new_context: str, new_namespace: str, switch_result: Dict[str, Any]) -> None:
        """Apply context switch result on main thread."""
        if switch_result.get("success"):
            self.current_context = new_context
            self.current_namespace = new_namespace
            state.save_state(new_context, new_namespace)
            self.connection_status = f"Switched to context '{new_context}'"
            self._refresh_resources()
        else:
            self.connection_status = f"Error: {switch_result.get('error', 'Failed to switch context')}"
        self._update_status_bar()

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
        ("tab", "app.action_switch_screen", "Switch to Cluster View"),
        ("slash", "focus_search", "Search"),
        ("c", "show_context_picker", "Pick Context"),
        ("enter", "execute_action('deploy')", "Deploy Chart"),
        ("r", "refresh_charts", "Refresh"),
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
        padding: 0 1;
    }

    #repo-label {
        height: 1;
        width: 100%;
        content-align: left middle;
        text-style: bold;
    }

    #repo-selector {
        height: 1;
        width: 100%;
    }

    #repo-selector Button {
        margin-right: 1;
    }

    #repo-selector Button:focus {
        background: $accent;
    }

    #body-container {
        height: 1fr;
    }

    ResourceTable {
        height: 1fr;
        width: 100%;
    }

    ResourceTable > DataTable {
        background: $surface;
    }

    SearchInput {
        height: 1;
        width: 100%;
        display: none;
        border: solid $accent;
        padding: 0 1;
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
        margin: 1 0;
    }

    #detail-panel.show {
        display: block;
        height: auto;
    }

    StatusBar {
        height: 1;
        border: solid $accent;
        padding: 0 1;
    }
    """

    current_repo = reactive("Select a repo")
    connection_status = reactive("Loading repos...")
    current_namespace = reactive("default")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._repos: List[Dict[str, Any]] = []
        self._charts: List[Dict[str, Any]] = []
        self._all_charts: List[Dict[str, Any]] = []
        self._selected_repo: Optional[str] = None
        self._selected_chart: Optional[str] = None

    def compose(self):
        """Compose the helm screen."""
        # Header with repo selector
        with Vertical(id="header-container"):
            yield Label("Repository:", id="repo-label")
            with Horizontal(id="repo-selector"):
                yield Button("Repos", id="btn-repos-list", variant="primary")

        # Body with chart table and search
        with Vertical(id="body-container"):
            yield ResourceTable(id="chart-table")
            yield SearchInput(id="search-input")

        # Detail panel for deployment info
        yield Label(id="detail-panel")

        # Status bar
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        """Initialize helm screen on mount."""
        self.title = "Gantry - Helm Orchestration"
        self._load_repos()

    def _load_repos(self) -> None:
        """Load available Helm repositories."""
        self._load_repos_worker()

    @work(thread=True)
    def _load_repos_worker(self) -> None:
        """Worker to load repos without blocking UI."""
        logger.debug("_load_repos_worker started")
        from gantry import helm

        repos = helm.list_repos()

        # Filter out error entries
        repos = [r for r in repos if "error" not in r]

        logger.debug(f"_load_repos_worker completed: {len(repos)} repos loaded")
        self.app.call_from_thread(self._apply_repos, repos)

    def _apply_repos(self, repos: List[Dict[str, Any]]) -> None:
        """Apply loaded repos on main thread."""
        if repos:
            self._repos = repos
            self.connection_status = "Connected"
            self._selected_repo = repos[0].get("name")
            self._update_status_bar()
            self._load_charts(self._selected_repo)
        else:
            self._repos = []
            self.connection_status = "No repos configured"
            self._update_status_bar()

    def _load_charts(self, repo: str) -> None:
        """Load charts from a specific repository."""
        self._load_charts_worker(repo)

    @work(thread=True)
    def _load_charts_worker(self, repo: str) -> None:
        """Worker to load charts without blocking UI."""
        logger.debug(f"_load_charts_worker started for repo {repo}")
        from gantry import helm

        # Search for all charts in the repo by using an empty query
        charts = helm.search_charts("*", repo=repo)

        # Filter out error entries
        charts = [c for c in charts if "error" not in c]

        logger.debug(f"_load_charts_worker completed: {len(charts)} charts loaded from {repo}")
        self.app.call_from_thread(self._apply_charts, repo, charts)

    def _apply_charts(self, repo: str, charts: List[Dict[str, Any]]) -> None:
        """Apply loaded charts on main thread."""
        self._all_charts = charts
        self._display_charts(charts)
        self.current_repo = repo
        if charts:
            self.connection_status = f"Loaded {len(charts)} charts from {repo}"
        else:
            self.connection_status = f"No charts found in {repo}"
        self._update_status_bar()

    def _display_charts(self, charts: List[Dict[str, Any]]) -> None:
        """Display charts in the table."""
        table: ResourceTable = self.query_one("#chart-table", ResourceTable)

        columns = ["Chart", "Version", "App Version", "Description"]
        keys = ["name", "version", "app_version", "description"]

        table.populate_resources(charts, columns, keys)
        self._charts = charts

    def _update_status_bar(self) -> None:
        """Update the status bar with current info."""
        try:
            status_bar: StatusBar = self.query_one("#status-bar", StatusBar)
            status_bar.update_namespace(self.current_namespace)
            status_bar.context = self.current_repo
            status_bar.update_status(self.connection_status)
        except Exception:
            # Status bar not mounted yet, skip update
            pass

    def on_button_pressed(self, event) -> None:
        """Handle button presses for repo selection."""
        button_id = event.button.id
        if button_id == "btn-repos-list":
            # Show repo list in detail panel
            self._show_repo_list()

    def _show_repo_list(self) -> None:
        """Show the list of available repos."""
        if not self._repos:
            detail = "No repositories configured.\n\nUse 'helm repo add' to add repositories."
        else:
            lines = ["=== Available Repositories ===\n"]
            for repo in self._repos:
                name = repo.get("name", "Unknown")
                url = repo.get("url", "Unknown")
                lines.append(f"{name}: {url}")
            detail = "\n".join(lines)

        self._display_detail_panel(detail)

    def _display_detail_panel(self, content: str) -> None:
        """Display content in the detail panel."""
        try:
            detail_panel = self.query_one("#detail-panel", Label)
            detail_panel.update(content)
            detail_panel.add_class("show")
        except Exception:
            pass

    def action_focus_search(self) -> None:
        """Focus on the search input."""
        search_input: SearchInput = self.query_one("#search-input", SearchInput)
        search_input.add_class("show")
        search_input.focus()

    def action_refresh_charts(self) -> None:
        """Refresh the chart list."""
        if self._selected_repo:
            self._load_charts(self._selected_repo)

    def action_show_context_picker(self) -> None:
        """Show the context/namespace picker modal."""
        self._load_contexts_for_picker_worker()

    @work(thread=True)
    def _load_contexts_for_picker_worker(self) -> None:
        """Load contexts in background for the picker modal."""
        contexts = k8s.list_contexts()
        self.app.call_from_thread(self._show_context_picker_modal, contexts)

    def _show_context_picker_modal(self, contexts: List[Dict[str, Any]]) -> None:
        """Show the context picker modal on main thread."""
        if not contexts or any("error" in ctx for ctx in contexts):
            self.connection_status = "Error: Unable to load contexts"
            self._update_status_bar()
            return

        # Find the active context from the list
        current_context = next(
            (ctx["name"] for ctx in contexts if ctx.get("current")), ""
        )
        modal = ContextPickerModal(contexts, current_context, self.current_namespace)
        self.app.push_screen(modal, callback=self._on_context_picker_dismiss)

    def _on_context_picker_dismiss(self, result: Optional[tuple]) -> None:
        """Handle context picker result."""
        if result:
            new_context, new_namespace = result
            # Update namespace and refresh
            self.current_namespace = new_namespace
            self.connection_status = f"Switched namespace to '{new_namespace}'"
            self._update_status_bar()

    def action_switch_screen(self, screen: str = "cluster") -> None:
        """Switch screens via action."""
        self.app.action_switch_screen()

    def on_search_input_search_changed(self, message: SearchInput.SearchChanged) -> None:
        """Handle search input changes and filter the table."""
        table: ResourceTable = self.query_one("#chart-table", ResourceTable)
        table.filter_by_search(message.value)

    def on_data_table_row_selected(self, message) -> None:
        """Handle chart selection and trigger deploy flow."""
        table: ResourceTable = self.query_one("#chart-table", ResourceTable)

        if table.cursor_row is not None and 0 <= table.cursor_row < len(self._charts):
            chart = self._charts[table.cursor_row]
            self._selected_chart = chart.get("name", "Unknown")
            self._show_deploy_dialog(self._selected_chart)

    def _show_deploy_dialog(self, chart_name: str) -> None:
        """Show deployment confirmation dialog."""
        detail = f"=== Deploy Chart ===\n\nChart: {chart_name}\nNamespace: {self.current_namespace}\n\n"
        detail += "Press Enter to deploy or press any other key to cancel."

        self._display_detail_panel(detail)
        self.connection_status = f"Selected chart: {chart_name}"
        self._update_status_bar()

    def action_execute_action(self, action_name: str = "deploy") -> None:
        """Execute an action (for deployment confirmation)."""
        if action_name == "deploy" and self._selected_chart:
            self._deploy_chart(self._selected_chart)

    def _deploy_chart(self, chart_name: str) -> None:
        """Deploy a Helm chart."""
        # Extract chart name parts
        chart_parts = chart_name.split("/")
        if len(chart_parts) == 2:
            repo, chart = chart_parts
        else:
            chart = chart_parts[-1]
            repo = None

        # Generate release name from chart name
        release_name = chart.replace("/", "-").replace("_", "-").lower()

        self._deploy_chart_worker(release_name, chart_name)

    @work(thread=True)
    def _deploy_chart_worker(self, release_name: str, chart_name: str) -> None:
        """Worker to install chart without blocking UI."""
        logger.debug(f"_deploy_chart_worker started: release_name={release_name}, chart_name={chart_name}")
        from gantry import helm

        result = helm.install_chart(
            release_name,
            chart_name,
            namespace=self.current_namespace
        )

        if result.get("success"):
            detail = f"=== Deployment Successful ===\n\n{result.get('message', 'Chart deployed')}"
            status = f"Deployed: {release_name}"
            logger.debug(f"_deploy_chart_worker completed: {chart_name} deployed as {release_name}")
        else:
            error_msg = result.get("error", "Unknown error")
            detail = f"=== Deployment Failed ===\n\nError: {error_msg}"
            status = f"Error: {error_msg[:50]}"
            logger.error(f"_deploy_chart_worker failed: {error_msg}")

        self.app.call_from_thread(self._apply_deploy_result, detail, status)

    def _apply_deploy_result(self, detail: str, status: str) -> None:
        """Apply deployment result on main thread."""
        self.connection_status = status
        self._display_detail_panel(detail)
        self._update_status_bar()
