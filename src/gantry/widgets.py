"""Custom widgets for Gantry TUI."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, Tuple
from rich.text import Text
from textual.widgets import DataTable, Static, Input
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.events import Key, MouseDown
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
        self._column_keys: List[str] = []
        self._sort_columns: List[Tuple[int, bool]] = []  # (col_idx, reverse)
        self._shift_held: bool = False

    def on_mouse_down(self, event: MouseDown) -> None:
        """Record shift state before header click fires."""
        self._shift_held = event.shift

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column header click to update sort order."""
        ck = event.column_key
        col_key_str = str(getattr(ck, "value", ck))
        if col_key_str not in self._column_keys:
            self._shift_held = False
            return
        col_idx = self._column_keys.index(col_key_str)
        self._compute_next_sort(col_idx, self._shift_held)
        self._shift_held = False
        self._update_column_labels()
        self._apply_filter(self._search_term)

    def _compute_next_sort(self, col_idx: int, shift: bool) -> None:
        """Update _sort_columns based on which column was clicked and whether Shift was held."""
        existing_pos = next(
            (i for i, (idx, _) in enumerate(self._sort_columns) if idx == col_idx),
            None,
        )
        if shift:
            if existing_pos is not None:
                idx, rev = self._sort_columns[existing_pos]
                self._sort_columns[existing_pos] = (idx, not rev)
            else:
                if len(self._sort_columns) >= 3:
                    # Drop least-significant key to preserve primary sort intent
                    self._sort_columns.pop()
                self._sort_columns.append((col_idx, False))
        else:
            if existing_pos == 0 and len(self._sort_columns) == 1:
                idx, rev = self._sort_columns[0]
                self._sort_columns = [(idx, not rev)]
            else:
                self._sort_columns = [(col_idx, False)]

    def _build_column_label_text(self, col_name: str, col_idx: int) -> str:
        """Return column label with sort indicator appended if applicable."""
        sort_map = {idx: (rank, rev) for rank, (idx, rev) in enumerate(self._sort_columns)}
        multi = len(self._sort_columns) > 1
        if col_idx in sort_map:
            rank, rev = sort_map[col_idx]
            indicator = "▼" if rev else "▲"
            suffix = f" {indicator}{rank + 1}" if multi else f" {indicator}"
            return col_name + suffix
        return col_name

    def _update_column_labels(self) -> None:
        """Rewrite column header labels in-place to show current sort indicators."""
        for col_key_obj, column in self.columns.items():
            key_str = str(getattr(col_key_obj, "value", col_key_obj))
            if not key_str.startswith("col_"):
                continue
            try:
                i = int(key_str.split("_")[1])
            except (ValueError, IndexError):
                continue
            if i >= len(self._columns):
                continue
            column.label = Text(self._build_column_label_text(self._columns[i], i))
            self.refresh_column(i)

    def _coerce_sort_value(self, value: Any) -> Any:
        """Return a type-aware comparable value for stable multi-type sorting."""
        if value is None:
            return (2, "")
        s = str(value).strip()
        if s == "":
            return (2, "")
        try:
            return (0, int(s))
        except ValueError:
            pass
        try:
            return (0, float(s))
        except ValueError:
            pass
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return (1, dt.timestamp())
        except ValueError:
            return (2, s.lower())

    def _sort_items(self, items: List[Tuple[str, List[Any]]]) -> List[Tuple[str, List[Any]]]:
        """Stable multi-key sort of (row_key, row_values) pairs by _sort_columns."""
        for col_idx, reverse in reversed(self._sort_columns):
            items.sort(
                key=lambda item, c=col_idx: (
                    self._coerce_sort_value(item[1][c]) if c < len(item[1]) else (2, "")
                ),
                reverse=reverse,
            )
        return items

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
        columns_changed = columns != self._columns
        if columns_changed:
            self._sort_columns = []

        self.clear(columns=True)
        self._all_rows.clear()
        self._columns = columns
        self._column_keys = [f"col_{i}" for i in range(len(columns))]

        for i, col in enumerate(columns):
            label = self._build_column_label_text(col, i)
            self.add_column(label, key=f"col_{i}")

        for i, resource in enumerate(resources):
            row_key = f"row-{i}"
            row_values = [resource.get(key, "") for key in column_keys]
            self._all_rows[row_key] = row_values

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
        """Apply the search filter (and active sort) to the table."""
        self.clear()  # Keeps columns; only clears rows

        if search_term:
            visible = [
                (rk, rv)
                for rk, rv in self._all_rows.items()
                if any(search_term in str(val).lower() for val in rv)
            ]
        else:
            visible = list(self._all_rows.items())

        if self._sort_columns:
            visible = self._sort_items(visible)

        for row_key, row_values in visible:
            self.add_row(*[str(v) for v in row_values], key=row_key)

    def on_data_table_row_selected(self, event) -> None:
        """Handle row selection."""
        row_key = str(event.row_key)
        logger.debug(f"ResourceTable row selected: {row_key}")
        if row_key in self._all_rows:
            row_data = {"key": row_key}
            self.post_message(self.RowSelected(row_key, row_data))

    async def _on_key(self, event: Key) -> None:
        """Handle key events and allow right/left arrows to bubble up for panel navigation."""
        if event.key == "right":
            event.stop()
            self.screen.action_focus_next_panel()
        elif event.key == "left":
            event.stop()
            self.screen.action_focus_previous_panel()
        else:
            await super()._on_key(event)


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
        - helm_preview_open: Whether the Helm file preview is showing content
        """
        super().__init__(*args, **kwargs)
        self.screen_type = "cluster"  # "cluster" or "helm"
        self.current_panel = "sidebar"  # "sidebar", "table", "detail", "search"
        self.detail_panel_open = False
        self.search_active = False
        self.helm_preview_open = False
        # Render initial content immediately so Static has something to show on first paint
        self.update(self._build_text())

    def update_context(self, screen_type: str, current_panel: str, detail_open: bool, search_active: bool, helm_preview_open: bool = False) -> None:
        """Update the context state and refresh the display.

        Args:
            screen_type: "cluster" or "helm" (determines available bindings)
            current_panel: "sidebar", "table", "detail", or "search" (tracked for future context-aware enhancements)
            detail_open: whether detail panel is open
            search_active: whether search is active
            helm_preview_open: whether the Helm file preview pane is showing content
        """
        self.screen_type = screen_type
        self.current_panel = current_panel
        self.detail_panel_open = detail_open
        self.search_active = search_active
        self.helm_preview_open = helm_preview_open
        self.update(self._build_text())

    def _build_text(self) -> str:
        """Build keybindings string based on current context."""
        # Case 1: Detail panel open (cluster screen)
        if self.detail_panel_open:
            return "← Back | → Forward | Esc Close | ↑↓ Scroll"

        # Case 2: Search active
        if self.search_active:
            return "Esc Cancel | ↵ Select"

        # Case 3: Helm screen with file preview showing
        if self.screen_type == "helm" and self.helm_preview_open:
            return "↑↓ Navigate | ↵ Expand | Esc Clear preview | r Refresh | Tab Cluster | q Quit"

        # Case 4 & 5: Normal state (depends on screen type)
        if self.screen_type == "cluster":
            return "←→ Navigate | d Describe | l Logs | r Refresh | c Context | / Search | Tab Helm | q Quit"
        elif self.screen_type == "helm":
            return "↑↓ Navigate | ↵ Expand | r Refresh | Tab Cluster | q Quit"

        # Fallback (should not reach here)
        return ""
