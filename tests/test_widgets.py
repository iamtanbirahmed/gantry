"""Tests for custom Gantry widgets (ResourceTable, SearchInput, StatusBar, etc.)."""

from unittest.mock import MagicMock

from gantry.widgets import ResourceTable


# --- Helpers ---


def _make_table() -> ResourceTable:
    """Return a ResourceTable with three columns and three rows populated."""
    table = ResourceTable()
    resources = [
        {"name": "banana", "age": "10", "status": "Running"},
        {"name": "apple", "age": "2", "status": "Pending"},
        {"name": "cherry", "age": "9", "status": "Running"},
    ]
    table.populate_resources(resources, ["Name", "Age", "Status"], ["name", "age", "status"])
    return table


# --- Initial state ---


def test_resource_table_initial_sort_state():
    """ResourceTable starts with no sort columns."""
    table = ResourceTable()
    assert table._sort_columns == []
    assert table._shift_held is False


# --- _sort_items ---


def test_sort_items_noop_when_empty():
    """_sort_items returns items unchanged when _sort_columns is empty."""
    table = _make_table()
    items = [("row-0", ["banana", "10"]), ("row-1", ["apple", "2"])]
    result = table._sort_items(items)
    assert result == items


def test_sort_items_single_column_ascending():
    """_sort_items sorts by single column ascending."""
    table = _make_table()
    table._sort_columns = [(0, False)]
    items = [("row-0", ["banana"]), ("row-1", ["apple"]), ("row-2", ["cherry"])]
    result = table._sort_items(items)
    assert [r[1][0] for r in result] == ["apple", "banana", "cherry"]


def test_sort_items_single_column_descending():
    """_sort_items sorts by single column descending."""
    table = _make_table()
    table._sort_columns = [(0, True)]
    items = [("row-0", ["banana"]), ("row-1", ["apple"]), ("row-2", ["cherry"])]
    result = table._sort_items(items)
    assert [r[1][0] for r in result] == ["cherry", "banana", "apple"]


def test_sort_items_case_insensitive():
    """_sort_items performs case-insensitive string comparison."""
    table = _make_table()
    table._sort_columns = [(0, False)]
    items = [("r0", ["Banana"]), ("r1", ["apple"]), ("r2", ["Cherry"])]
    result = table._sort_items(items)
    assert [r[1][0] for r in result] == ["apple", "Banana", "Cherry"]


def test_sort_items_numeric_ordering():
    """_sort_items sorts numeric strings numerically, not lexicographically."""
    table = _make_table()
    table._sort_columns = [(0, False)]
    items = [("r0", ["10"]), ("r1", ["2"]), ("r2", ["9"])]
    result = table._sort_items(items)
    assert [r[1][0] for r in result] == ["2", "9", "10"]


def test_sort_items_multi_column():
    """_sort_items applies secondary sort when primary values are equal."""
    table = _make_table()
    table._sort_columns = [(1, False), (0, False)]  # primary=Status, secondary=Name
    items = [
        ("r0", ["banana", "Running"]),
        ("r1", ["apple", "Pending"]),
        ("r2", ["cherry", "Running"]),
    ]
    result = table._sort_items(items)
    names = [r[1][0] for r in result]
    assert names == ["apple", "banana", "cherry"]


def test_sort_items_mixed_naive_aware_datetimes():
    """_sort_items sorts rows with mixed naive and aware ISO timestamps without TypeError."""
    table = _make_table()
    table._sort_columns = [(0, False)]
    items = [
        ("r0", ["2024-01-02T00:00:00"]),       # naive
        ("r1", ["2024-01-01T00:00:00+00:00"]), # aware
        ("r2", ["2024-01-03T00:00:00Z"]),       # aware via Z suffix
    ]
    result = table._sort_items(items)
    assert [r[0] for r in result] == ["r1", "r0", "r2"]


# --- _compute_next_sort ---


def test_compute_next_sort_primary_setup():
    """Clicking a column with no existing sort makes it the primary ascending sort."""
    table = ResourceTable()
    table._compute_next_sort(0, False)
    assert table._sort_columns == [(0, False)]


def test_compute_next_sort_primary_toggle():
    """Clicking the only primary column toggles its direction."""
    table = ResourceTable()
    table._sort_columns = [(0, False)]
    table._compute_next_sort(0, False)
    assert table._sort_columns == [(0, True)]


def test_compute_next_sort_shift_adds_secondary():
    """Shift-clicking a new column appends it as secondary sort."""
    table = ResourceTable()
    table._sort_columns = [(0, False)]
    table._compute_next_sort(1, True)
    assert table._sort_columns == [(0, False), (1, False)]


def test_compute_next_sort_shift_toggles_existing():
    """Shift-clicking an existing secondary column toggles its direction."""
    table = ResourceTable()
    table._sort_columns = [(0, False), (1, False)]
    table._compute_next_sort(1, True)
    assert table._sort_columns == [(0, False), (1, True)]


def test_compute_next_sort_primary_toggle_preserves_secondary():
    """Clicking the primary column toggles its direction even when secondary sorts exist."""
    table = ResourceTable()
    table._sort_columns = [(0, False), (1, False)]
    table._compute_next_sort(0, False)
    # Primary direction toggled, secondary preserved
    assert table._sort_columns == [(0, True), (1, False)]


def test_compute_next_sort_max_three_columns():
    """Adding a 4th column via Shift-click drops the least significant (last) one."""
    table = ResourceTable()
    table._sort_columns = [(0, False), (1, False), (2, False)]
    table._compute_next_sort(3, True)
    assert len(table._sort_columns) == 3
    assert table._sort_columns[0] == (0, False)  # primary preserved
    assert table._sort_columns[-1] == (3, False)  # new column is now last


def test_compute_next_sort_max_three_preserves_primary():
    """Primary sort key is never dropped when overflow occurs."""
    table = ResourceTable()
    table._sort_columns = [(0, False), (1, False), (2, False)]
    table._compute_next_sort(5, True)
    col_indices = [idx for idx, _ in table._sort_columns]
    assert 0 in col_indices, "Primary sort key must survive overflow"


# --- _build_column_label_text ---


def test_build_column_label_text_no_sort():
    """Column label has no suffix when not sorted."""
    table = ResourceTable()
    assert table._build_column_label_text("Name", 0) == "Name"


def test_build_column_label_text_single_sort_ascending():
    """Column label shows ▲ for single ascending sort (no rank number)."""
    table = ResourceTable()
    table._sort_columns = [(0, False)]
    assert table._build_column_label_text("Name", 0) == "Name ▲"


def test_build_column_label_text_single_sort_descending():
    """Column label shows ▼ for single descending sort."""
    table = ResourceTable()
    table._sort_columns = [(0, True)]
    assert table._build_column_label_text("Name", 0) == "Name ▼"


def test_build_column_label_text_multi_sort_shows_rank():
    """Column label includes rank number when multiple columns are sorted."""
    table = ResourceTable()
    table._sort_columns = [(0, False), (1, True)]
    assert table._build_column_label_text("Name", 0) == "Name ▲1"
    assert table._build_column_label_text("Age", 1) == "Age ▼2"


# --- Sort state management ---


def test_sort_state_reset_on_column_change():
    """Sort state resets when populate_resources is called with different columns."""
    table = _make_table()
    table._sort_columns = [(0, False)]
    table.populate_resources(
        [{"pod": "p1", "node": "n1"}],
        ["Pod", "Node"],
        ["pod", "node"],
    )
    assert table._sort_columns == []


def test_sort_state_preserved_on_same_columns():
    """Sort state is preserved when populate_resources is called with the same columns."""
    table = _make_table()
    table._sort_columns = [(0, False)]
    resources = [
        {"name": "z-pod", "age": "1", "status": "Running"},
        {"name": "a-pod", "age": "5", "status": "Pending"},
    ]
    table.populate_resources(resources, ["Name", "Age", "Status"], ["name", "age", "status"])
    assert table._sort_columns == [(0, False)]


def test_shift_held_reset_after_header_selection():
    """_shift_held is reset to False after on_data_table_header_selected fires."""
    table = _make_table()
    table._shift_held = True
    event = MagicMock()
    event.column_key = MagicMock()
    event.column_key.value = "unknown_key"
    table.on_data_table_header_selected(event)
    assert table._shift_held is False
