"""Custom widgets for Gantry TUI."""

from typing import Any, Dict, List, Optional, Callable
from textual.widgets import DataTable, Static, Input
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message


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

    ResourceTable:focus {
        border: double $accent;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._all_rows: Dict[str, List[Any]] = {}
        self._search_term: str = ""

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
        self.clear()
        self._all_rows.clear()

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
        self.clear()

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
        row_key = event.cursor_row
        if row_key in self._all_rows:
            # Find the row data based on the visible row
            # For now, we'll create a simple row_data from visible cells
            row_data = {"key": str(row_key)}
            self.post_message(self.RowSelected(str(row_key), row_data))


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
        super().__init__(*args, **kwargs)
        self.prefix = "/"

    def render_line(self, y: int) -> str:
        """Render the input line with prefix."""
        base_line = super().render_line(y)
        return self.prefix + base_line if y == 0 else base_line

    def on_input_changed(self, message: Input.Changed) -> None:
        """Post a SearchChanged message when input changes."""
        self.post_message(self.SearchChanged(message.value))


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
