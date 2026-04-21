"""Custom widgets for Gantry TUI."""

import logging
from typing import Any, Dict, List, Optional, Callable
from textual.widget import Widget
from textual.widgets import DataTable, Static, Input, ListView, ListItem, Label, Collapsible
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.events import Key
from textual.css.query import NoMatches

logger = logging.getLogger(__name__)


class ResourceTable(DataTable):
    """
    Custom DataTable for displaying Kubernetes resources.

    Supports filtering via search term and fires custom messages when rows are selected.
    """

    class RowSelected(Message):
        """Message posted when a row is selected."""

        def __init__(self, row_key: str, row_data: Dict[str, Any]) -> None:
            self.row_key = row_key
            self.row_data = row_data
            super().__init__()

    CSS = """
    ResourceTable {
        height: 1fr;
        width: 100%;
    }

    ResourceTable > DataTable {
        height: 1fr;
        border: solid $accent;
    }

    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("cursor_type", "row")
        super().__init__(*args, **kwargs)
        self._all_rows: Dict[str, List[Any]] = {}
        self._search_term: str = ""
        self._columns: List[str] = []

    def populate_resources(
        self,
        resources: List[Dict[str, Any]],
        columns: List[str],
        column_keys: List[str],
    ) -> None:
        """
        Populate the table with resources.

        Args:
            resources: List of resource dictionaries from K8s API.
            columns: List of column headers to display.
            column_keys: List of keys to extract from each resource dict.
        """
        self.clear(columns=True)
        self._all_rows.clear()
        self._columns = columns

        # Add columns
        for col in columns:
            self.add_column(col)

        # Add rows
        for i, resource in enumerate(resources):
            row_key = f"row-{i}"
            row_values = [str(resource.get(key, "")) for key in column_keys]
            self.add_row(*row_values, key=row_key)
            self._all_rows[row_key] = row_values

        # Apply current search filter
        if self._search_term:
            self._apply_filter(self._search_term)

    def filter_by_search(self, search_term: str) -> None:
        """
        Filter the table rows by search term.

        Args:
            search_term: The search text to filter by.
        """
        self._search_term = search_term.lower()
        self._apply_filter(self._search_term)

    def _apply_filter(self, search_term: str) -> None:
        """Apply the search filter to the table."""
        self.clear()  # Keeps columns; only clears rows

        if not search_term:
            # Show all rows
            for row_key, row_values in self._all_rows.items():
                self.add_row(*row_values, key=row_key)
        else:
            # Filter rows by search term
            for row_key, row_values in self._all_rows.items():
                if any(search_term in str(val).lower() for val in row_values):
                    self.add_row(*row_values, key=row_key)

    def on_data_table_row_selected(self, event) -> None:
        """Handle row selection."""
        row_key = str(event.row_key)
        logger.debug(f"ResourceTable row selected: {row_key}")
        if row_key in self._all_rows:
            row_data = {"key": row_key}
            self.post_message(self.RowSelected(row_key, row_data))

    def _on_key(self, event: Key) -> None:
        """Handle key events and allow right/left arrows to bubble up for panel navigation."""
        if event.key == "right":
            event.stop()
            self.screen.action_focus_next_panel()
        elif event.key == "left":
            event.stop()
            self.screen.action_focus_previous_panel()
        else:
            super()._on_key(event)


class SearchInput(Input):
    """
    Input widget for search/filter text with "/" prefix.

    Displays "/" as a prefix prompt.
    """

    class SearchChanged(Message):
        """Message posted when search text changes."""

        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    CSS = """
    SearchInput {
        height: 1;
        width: 100%;
        border: solid $accent;
        padding: 0 1;
        margin: 1 0;
        display: none;
    }

    SearchInput.show {
        display: block;
    }

    SearchInput:focus {
        border: double $accent;
        background: $boost;
    }

    SearchInput Input {
        border: none;
    }
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("placeholder", "Type to search...")
        super().__init__(*args, **kwargs)

    def on_input_changed(self, message: Input.Changed) -> None:
        """Post a SearchChanged message when input changes."""
        logger.debug(f"SearchInput changed: '{message.value}'")
        self.post_message(self.SearchChanged(message.value))

    def _on_key(self, event: Key) -> None:
        """Handle key events for search input."""
        if event.key == "escape":
            event.stop()
            self.value = ""
            self.post_message(self.SearchChanged(""))
            self.remove_class("show")
            try:
                table = self.screen.query_one(ResourceTable)
                table.focus()
            except NoMatches:
                logger.debug("SearchInput: no ResourceTable found to return focus to")
        elif event.key == "enter":
            # Confirm search: hide the bar but keep filter active (do not clear value)
            event.stop()
            self.remove_class("show")
            try:
                table = self.screen.query_one(ResourceTable)
                table.focus()
            except NoMatches:
                logger.debug("SearchInput: no ResourceTable found to return focus to")
        elif event.key == "right":
            event.stop()
            self.screen.action_focus_next_panel()
        elif event.key == "left":
            event.stop()
            self.screen.action_focus_previous_panel()
        else:
            super()._on_key(event)


class StatusBar(Static):
    """
    Status bar widget showing cluster context, namespace, and connection status.

    Displays errors with "Error: " prefix for clear visibility.
    """

    CSS = """
    StatusBar {
        height: 1;
        border: solid $accent;
        padding: 0 1;
        background: $panel;
        color: $text;
    }

    StatusBar.error {
        background: $error;
        color: $text;
    }

    StatusBar.success {
        background: $panel;
        color: $text;
    }
    """

    def __init__(
        self,
        context: str = "N/A",
        namespace: str = "default",
        status: str = "Connected",
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.context = context
        self.namespace = namespace
        self.status = status

    def render(self) -> str:
        """Render the status bar content."""
        # Format with more readable status display
        parts = []
        if self.context != "N/A":
            parts.append(f"Context: {self.context}")
        if self.namespace != "N/A":
            parts.append(f"Namespace: {self.namespace}")

        # Add status with better formatting for errors
        if self.status.startswith("Error"):
            status_text = self.status
        elif self.status.startswith("Status:"):
            status_text = self.status
        else:
            status_text = f"Status: {self.status}"

        parts.append(status_text)
        return " | ".join(parts)

    def update_context(self, context: str) -> None:
        """Update the displayed context."""
        self.context = context
        self.refresh()

    def update_namespace(self, namespace: str) -> None:
        """Update the displayed namespace."""
        self.namespace = namespace
        self.refresh()

    def update_status(self, status: str) -> None:
        """Update the displayed status and apply error styling if needed."""
        self.status = status
        # Add error class if status contains "Error"
        if "Error" in status or "error" in status.lower():
            self.add_class("error")
            self.remove_class("success")
        else:
            self.add_class("success")
            self.remove_class("error")
        self.refresh()


class KeybindingsBar(Static):
    """Context-aware keybindings bar displaying abbreviated key hints."""

    CSS = """
    KeybindingsBar {
        height: 1;
        border: solid $accent;
        padding: 0 1;
        background: $panel;
        color: $text;
    }
    """

    def __init__(self, *args, **kwargs):
        """Initialize the keybindings bar with default state.

        State attributes:
        - screen_type: Currently displayed screen ("cluster" or "helm")
        - current_panel: Focused panel (tracked for future context-aware hints)
        - detail_panel_open: Whether detail panel is open
        - search_active: Whether search is active
        """
        super().__init__(*args, **kwargs)
        self.screen_type = "cluster"  # "cluster" or "helm"
        self.current_panel = "sidebar"  # "sidebar", "table", "detail", "search"
        self.detail_panel_open = False
        self.search_active = False
        # Render initial content immediately so Static has something to show on first paint
        self.update(self._build_text())

    def update_context(self, screen_type: str, current_panel: str, detail_open: bool, search_active: bool) -> None:
        """Update the context state and refresh the display.

        Args:
            screen_type: "cluster" or "helm" (determines available bindings)
            current_panel: "sidebar", "table", "detail", or "search" (tracked for future context-aware enhancements)
            detail_open: whether detail panel is open
            search_active: whether search is active
        """
        self.screen_type = screen_type
        self.current_panel = current_panel
        self.detail_panel_open = detail_open
        self.search_active = search_active
        self.update(self._build_text())

    def _build_text(self) -> str:
        """Build keybindings string based on current context."""
        # Case 1: Detail panel open
        if self.detail_panel_open:
            return "← Back | → Forward | Esc Close | ↑↓ Scroll"

        # Case 2: Search active
        if self.search_active:
            return "Esc Cancel | ↵ Select"

        # Case 3 & 4: Normal state (depends on screen type)
        if self.screen_type == "cluster":
            return "←→ Navigate | d Describe | l Logs | r Refresh | c Context | / Search | Tab Helm | q Quit"
        elif self.screen_type == "helm":
            return "←→ Navigate | ↵ Deploy | r Refresh | c Context | / Search | Tab Cluster | q Quit"

        # Fallback (should not reach here)
        return ""


class ResourceSidebar(Widget):
    """Grouped, collapsible sidebar for Kubernetes resource type selection."""

    GROUPS: list[tuple[str, list[tuple[str, bool]]]] = [
        ("Workloads", [
            ("Pods", True),
            ("Deployments", True),
            ("Daemon Sets", False),
            ("Stateful Sets", False),
            ("Replica Sets", False),
            ("Replication Controllers", False),
            ("Jobs", False),
            ("Cron Jobs", False),
        ]),
        ("Service", [
            ("Services", True),
            ("Ingresses", False),
            ("Ingress Classes", False),
        ]),
        ("Config & Storage", [
            ("Config Maps", True),
            ("Secrets", False),
            ("Persistent Volume Claims", False),
            ("Storage Classes", False),
        ]),
        ("Cluster", [
            ("Nodes", False),
            ("Namespaces", False),
            ("Events", False),
            ("Roles", False),
            ("Role Bindings", False),
            ("Cluster Roles", False),
            ("Cluster Role Bindings", False),
            ("Service Accounts", False),
            ("Network Policies", False),
            ("Persistent Volumes", False),
        ]),
        ("Custom Resource Definitions", [
            ("CRDs", False),
        ]),
    ]

    CSS = """
    ResourceSidebar {
        width: 24;
        height: 100%;
        border-right: solid $accent;
        background: $panel;
        overflow-y: auto;
    }

    ResourceSidebar Collapsible {
        border: none;
        padding: 0;
        background: $panel;
    }

    ResourceSidebar Collapsible > CollapsibleTitle {
        color: $accent;
        text-style: bold;
        padding: 0 1;
        background: $panel;
    }

    ResourceSidebar ListView {
        border: none;
        background: $panel;
        padding: 0;
        height: auto;
    }

    ResourceSidebar ListItem {
        padding: 0 2;
        height: 1;
    }

    ResourceSidebar ListItem > Label {
        color: $text;
        width: 100%;
    }

    ResourceSidebar ListItem.stub-item > Label {
        color: $text-muted;
        opacity: 0.5;
    }
    """

    class ResourceSelected(Message):
        """Posted when the user highlights a resource type in the sidebar."""

        def __init__(self, resource_type: str, implemented: bool) -> None:
            super().__init__()
            self.resource_type = resource_type
            self.implemented = implemented

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Pre-build the lookup: ListView ID → list of (name, implemented)
        self._list_view_items: dict[str, list[tuple[str, bool]]] = {
            (
                "sidebar-"
                + group_name.lower()
                .replace(" ", "-")
                .replace("&", "and")
                .replace("(", "")
                .replace(")", "")
            ): items
            for group_name, items in self.GROUPS
        }
        # Guard: suppress auto-highlight events fired during mount
        self._ready: bool = False

    def on_mount(self) -> None:
        """Allow ResourceSelected events after the initial mount cycle completes."""
        self.call_after_refresh(self._set_ready)

    def _set_ready(self) -> None:
        self._ready = True

    def compose(self):
        with VerticalScroll():
            for group_name, items in self.GROUPS:
                lv_id = (
                    "sidebar-"
                    + group_name.lower()
                    .replace(" ", "-")
                    .replace("&", "and")
                    .replace("(", "")
                    .replace(")", "")
                )
                with Collapsible(title=group_name):
                    yield ListView(
                        *[
                            ListItem(
                                Label(name),
                                classes="stub-item" if not impl else "",
                            )
                            for name, impl in items
                        ],
                        id=lv_id,
                    )

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Post ResourceSelected when the user moves highlight in any group ListView."""
        if not self._ready:
            return
        lv_id = event.list_view.id
        if lv_id not in self._list_view_items:
            return
        idx = event.list_view.index
        if idx is None:
            return
        items = self._list_view_items[lv_id]
        if 0 <= idx < len(items):
            name, implemented = items[idx]
            self.post_message(self.ResourceSelected(name, implemented))

    def focus_first_item(self) -> None:
        """Focus the first inner ListView (Workloads group)."""
        try:
            first_lv_id = next(iter(self._list_view_items))
            self.query_one(f"#{first_lv_id}", ListView).focus()
        except (StopIteration, Exception):
            pass

    async def _on_key(self, event: Key) -> None:
        """Forward right-arrow to screen panel navigation."""
        if event.key == "right":
            event.stop()
            self.screen.action_focus_next_panel()
        else:
            await super()._on_key(event)
