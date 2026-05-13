"""Tests for the Gantry app shell and screen switching."""

import pytest
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import ListView, TextArea, Static
from unittest.mock import patch

from gantry.app import GantryApp
from gantry.screens import ClusterScreen, HelmScreen
from gantry.widgets import KeybindingsBar, ResourceTable


def test_app_initializes():
    """Test that the app initializes correctly."""
    app = GantryApp()
    assert app.TITLE == "Gantry"
    assert app.SUBTITLE == "Kubernetes Cluster Management & Helm Orchestration"


def test_cluster_screen_exists():
    """Test that ClusterScreen is registered."""
    app = GantryApp()
    assert "cluster" in app.SCREENS
    assert app.SCREENS["cluster"] is ClusterScreen


def test_helm_screen_exists():
    """Test that HelmScreen is registered."""
    app = GantryApp()
    assert "helm" in app.SCREENS
    assert app.SCREENS["helm"] is HelmScreen


def test_app_has_keybindings():
    """Test that the app has the required keybindings."""
    app = GantryApp()
    binding_keys = [binding.key for binding in app.BINDINGS]
    assert "tab" in binding_keys
    assert "q" in binding_keys


def test_cluster_screen_created():
    """Test that ClusterScreen can be instantiated."""
    screen = ClusterScreen()
    assert screen is not None
    assert isinstance(screen, ClusterScreen)


def test_helm_screen_created():
    """Test that HelmScreen can be instantiated."""
    screen = HelmScreen()
    assert screen is not None
    assert isinstance(screen, HelmScreen)


def test_cluster_screen_has_bindings():
    """Test that ClusterScreen has required keybindings."""
    screen = ClusterScreen()
    binding_keys = [binding[0] if isinstance(binding, tuple) else binding.key for binding in screen.BINDINGS]
    assert "tab" in binding_keys
    assert "q" in binding_keys


def test_helm_screen_has_bindings():
    """Test that HelmScreen has required keybindings."""
    screen = HelmScreen()
    binding_keys = [binding[0] if isinstance(binding, tuple) else binding.key for binding in screen.BINDINGS]
    assert "tab" in binding_keys
    assert "q" in binding_keys


@pytest.mark.asyncio
async def test_app_starts_on_cluster_screen():
    """Test that the app starts on the cluster screen."""
    app = GantryApp()
    async with app.run_test() as pilot:
        # The initial screen should be the cluster screen
        assert isinstance(app.screen, ClusterScreen)


@pytest.mark.asyncio
async def test_tab_switches_to_helm_screen():
    """Test that pressing Tab switches from Cluster to Helm screen."""
    app = GantryApp()
    async with app.run_test() as pilot:
        # Start on cluster screen
        assert isinstance(app.screen, ClusterScreen)

        # Press Tab to switch
        await pilot.press("tab")
        await pilot.pause()

        # Should now be on helm screen
        assert isinstance(app.screen, HelmScreen)


@pytest.mark.asyncio
async def test_tab_switches_back_to_cluster_screen():
    """Test that pressing Tab switches from Helm back to Cluster screen."""
    app = GantryApp()
    async with app.run_test() as pilot:
        # Start on cluster screen
        assert isinstance(app.screen, ClusterScreen)

        # Press Tab to switch to helm
        await pilot.press("tab")
        await pilot.pause()
        assert isinstance(app.screen, HelmScreen)

        # Press Tab again to switch back to cluster
        await pilot.press("tab")
        await pilot.pause()
        assert isinstance(app.screen, ClusterScreen)


def test_cluster_screen_has_sidebar():
    """Test that ClusterScreen has a resource type sidebar."""
    screen = ClusterScreen()
    # We can't test the full DOM without mounting, but we can check
    # that the sidebar list is defined in the class
    assert hasattr(screen, "_RESOURCE_TYPES")
    assert "Pods" in screen._RESOURCE_TYPES
    assert "Deployments" in screen._RESOURCE_TYPES
    assert "Services" in screen._RESOURCE_TYPES
    assert len(screen._RESOURCE_TYPES) == 16


@pytest.mark.asyncio
async def test_sidebar_default_selection():
    """Test that the sidebar defaults to Pods on load."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)
        assert screen.current_resource_type == "Pods"


@pytest.mark.asyncio
async def test_sidebar_selection_changes_resource_type():
    """Test that navigating the sidebar changes the resource type."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)
        # Arrow down to Deployments (second item), press Enter
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.pause()
        assert screen.current_resource_type == "Deployments"


@pytest.mark.asyncio
async def test_panel_navigation_right_arrow():
    """Test that pressing right arrow cycles panels forward."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        # Start on sidebar
        assert screen.current_panel == "sidebar"

        # Right arrow → table
        await pilot.press("right")
        await pilot.pause()
        assert screen.current_panel == "table"

        # Right arrow → sidebar (detail closed, so cycles back)
        await pilot.press("right")
        await pilot.pause()
        assert screen.current_panel == "sidebar"


@pytest.mark.asyncio
async def test_panel_navigation_left_arrow():
    """Test that pressing left arrow cycles panels backward."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        # Start on sidebar, move to table
        await pilot.press("right")
        await pilot.pause()
        assert screen.current_panel == "table"

        # Left arrow → sidebar
        await pilot.press("left")
        await pilot.pause()
        assert screen.current_panel == "sidebar"

        # Left arrow → table (wraps back)
        await pilot.press("left")
        await pilot.pause()
        assert screen.current_panel == "table"


@pytest.mark.asyncio
async def test_sidebar_up_down_updates_resources():
    """Test that navigating sidebar with arrows immediately updates resource type.

    Previously, Enter was required to apply the selection. Now up/down
    navigation immediately triggers a resource type change and fetch.
    """
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        # Start on Pods
        assert screen.current_resource_type == "Pods"

        # Down arrow to Deployments (index 1)
        await pilot.press("down")
        await pilot.pause()
        assert screen.current_resource_type == "Deployments"

        # Down arrow to ReplicaSets (index 2)
        await pilot.press("down")
        await pilot.pause()
        assert screen.current_resource_type == "ReplicaSets"

        # Up arrow back to Deployments
        await pilot.press("up")
        await pilot.pause()
        assert screen.current_resource_type == "Deployments"


@pytest.mark.asyncio
async def test_detail_panel_hidden_on_mount():
    """Detail panel should be hidden by default."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)
        # Check that detail_panel_open is False
        assert screen.detail_panel_open is False
        # Check that detail panel has the hidden class
        detail_panel = screen.query_one("#detail-panel", VerticalScroll)
        assert "show" not in detail_panel.classes


@pytest.mark.asyncio
async def test_panel_navigation_with_detail_open():
    """Panel cycle should include detail when open."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        # Open detail panel
        screen.detail_panel_open = True
        screen.query_one("#detail-panel", VerticalScroll).add_class("show")

        # Cycle: sidebar -> table -> detail -> sidebar
        screen.action_focus_next_panel()
        assert screen.current_panel == "table"

        screen.action_focus_next_panel()
        assert screen.current_panel == "detail"

        screen.action_focus_next_panel()
        assert screen.current_panel == "sidebar"


@pytest.mark.asyncio
async def test_escape_closes_detail_panel():
    """Pressing Escape should close the detail panel."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        # Manually open the detail panel
        screen.detail_panel_open = True
        screen.query_one("#detail-panel", VerticalScroll).add_class("show")

        # Simulate Escape key
        screen.action_close_detail_panel()

        # Verify panel is closed
        assert screen.detail_panel_open is False
        detail_panel = screen.query_one("#detail-panel", VerticalScroll)
        assert "show" not in detail_panel.classes

def test_keybindings_bar_detail_panel_open():
    """KeybindingsBar should show detail panel hints when detail is open."""
    bar = KeybindingsBar()
    bar.update_context("cluster", "detail", detail_open=True, search_active=False)

    output = bar._build_text()
    assert "← Back" in output
    assert "Esc Close" in output
    assert "↑↓ Scroll" in output
    assert "Desc" not in output  # Should NOT show normal cluster bindings


def test_keybindings_bar_search_active():
    """KeybindingsBar should show search hints when search is active."""
    bar = KeybindingsBar()
    bar.update_context("cluster", "sidebar", detail_open=False, search_active=True)

    output = bar._build_text()
    assert "Esc Cancel" in output
    assert "↵ Select" in output
    assert "Desc" not in output  # Should NOT show normal cluster bindings


def test_keybindings_bar_cluster_normal():
    """KeybindingsBar should show cluster screen bindings in normal state."""
    bar = KeybindingsBar()
    bar.update_context("cluster", "table", detail_open=False, search_active=False)

    output = bar._build_text()
    assert "←→ Navigate" in output
    assert "d Describe" in output
    assert "l Logs" in output
    assert "r Refresh" in output
    assert "c Context" in output
    assert "/ Search" in output
    assert "Tab Helm" in output
    assert "q Quit" in output


def test_keybindings_bar_helm_normal():
    """KeybindingsBar should show helm screen bindings in normal state."""
    bar = KeybindingsBar()
    bar.update_context("helm", "table", detail_open=False, search_active=False)

    output = bar._build_text()
    assert "↑↓ Navigate" in output
    assert "↵ Expand" in output
    assert "r Refresh" in output
    assert "Tab Cluster" in output
    assert "q Quit" in output
    # Should NOT show cluster-specific bindings or old helm bindings
    assert "Describe" not in output
    assert "Logs" not in output
    assert "Deploy" not in output
    assert "Context" not in output


@pytest.mark.asyncio
async def test_helm_screen_yaml_file_detection():
    """HelmScreen should set language='yaml' for .yaml files."""
    from pathlib import Path
    import tempfile

    app = GantryApp()
    async with app.run_test() as pilot:
        # Switch to HelmScreen
        await pilot.press("tab")
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, HelmScreen)

        # Get the TextArea widget
        text_area = screen.query_one("#yaml-preview", TextArea)

        # Simulate selecting a .yaml file by calling the event handler
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            f.write("apiVersion: v1\nkind: Pod\n")
            yaml_path = Path(f.name)
        try:
            # Create a mock DirectoryTree.FileSelected event
            from textual.widgets import DirectoryTree
            from unittest.mock import MagicMock
            mock_node = MagicMock()
            event = DirectoryTree.FileSelected(mock_node, yaml_path)
            screen.on_directory_tree_file_selected(event)

            # Check that language is set to yaml
            assert text_area.language == "yaml"
        finally:
            yaml_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_helm_screen_non_yaml_file_detection():
    """HelmScreen should set language=None for non-.yaml files."""
    from pathlib import Path
    import tempfile

    app = GantryApp()
    async with app.run_test() as pilot:
        # Switch to HelmScreen
        await pilot.press("tab")
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, HelmScreen)

        # Get the TextArea widget
        text_area = screen.query_one("#yaml-preview", TextArea)

        # Simulate selecting a non-yaml file
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
            f.write("plain text content\n")
            txt_path = Path(f.name)
        try:
            # Create a mock DirectoryTree.FileSelected event
            from textual.widgets import DirectoryTree
            from unittest.mock import MagicMock
            mock_node = MagicMock()
            event = DirectoryTree.FileSelected(mock_node, txt_path)
            screen.on_directory_tree_file_selected(event)

            # Check that language is None
            assert text_area.language is None
        finally:
            txt_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_helm_screen_renders_helm_keybindings():
    """When HelmScreen is active, the KeybindingsBar must render helm hints, not cluster hints."""
    app = GantryApp()
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        assert isinstance(app.screen, HelmScreen)

        bar = app.screen.query_one("#keybindings-bar", KeybindingsBar)
        rendered = bar._build_text()
        assert "↑↓ Navigate" in rendered
        assert "Tab Cluster" in rendered
        assert "d Describe" not in rendered  # cluster-only hint must not leak


# --- YAML Viewer Tests ---

def test_cluster_screen_has_yaml_bindings():
    """ClusterScreen should have 'y' and 'm' in BINDINGS."""
    binding_keys = [
        b[0] if isinstance(b, tuple) else b.key
        for b in ClusterScreen.BINDINGS
    ]
    assert "y" in binding_keys
    assert "m" in binding_keys


def test_cluster_screen_has_yaml_reactives():
    """ClusterScreen should have yaml_view_open and yaml_mode reactives."""
    screen = ClusterScreen()
    assert hasattr(screen, "yaml_view_open")
    assert hasattr(screen, "yaml_mode")
    assert screen.yaml_view_open is False
    assert screen.yaml_mode == "spec"


@pytest.mark.asyncio
async def test_yaml_panel_hidden_on_mount():
    """yaml_view_open should be False on mount."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)
        assert screen.yaml_view_open is False


@pytest.mark.asyncio
async def test_apply_yaml_result_mounts_text_area():
    """_apply_yaml_result should mount TextArea and set yaml_view_open=True."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._apply_yaml_result(("apiVersion: v1\nkind: Pod\n", "apiVersion: v1\n"))
        await pilot.pause()

        assert screen.yaml_view_open is True
        text_area = screen.query_one("#yaml-content", TextArea)
        assert "apiVersion: v1" in text_area.text


@pytest.mark.asyncio
async def test_apply_yaml_result_hides_static():
    """_apply_yaml_result should hide the #detail-panel-content Static."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._apply_yaml_result(("apiVersion: v1\n", "apiVersion: v1\n"))
        await pilot.pause()

        static = screen.query_one("#detail-panel-content", Static)
        assert "hidden" in static.classes


@pytest.mark.asyncio
async def test_apply_yaml_result_none_does_not_open_panel():
    """_apply_yaml_result with (None, None) should not open the YAML panel."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._apply_yaml_result((None, None))
        await pilot.pause()

        assert screen.yaml_view_open is False


@pytest.mark.asyncio
async def test_toggle_yaml_mode_switches_content():
    """'m' key should toggle between full and spec YAML content."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        full = "apiVersion: v1\nkind: Pod\nstatus:\n  phase: Running\n"
        spec = "apiVersion: v1\nkind: Pod\nspec: {}\n"
        screen._apply_yaml_result((full, spec))
        await pilot.pause()

        assert screen.yaml_mode == "spec"
        text_area = screen.query_one("#yaml-content", TextArea)
        assert "status:" not in text_area.text
        assert "spec:" in text_area.text

        screen.action_toggle_yaml_mode()
        await pilot.pause()

        assert screen.yaml_mode == "full"
        text_area = screen.query_one("#yaml-content", TextArea)
        assert "status:" in text_area.text

        screen.action_toggle_yaml_mode()
        await pilot.pause()

        assert screen.yaml_mode == "spec"
        text_area = screen.query_one("#yaml-content", TextArea)
        assert "status:" not in text_area.text
        assert "spec:" in text_area.text


@pytest.mark.asyncio
async def test_toggle_yaml_mode_no_op_when_panel_closed():
    """action_toggle_yaml_mode should be a no-op when yaml_view_open is False."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        assert screen.yaml_view_open is False
        screen.action_toggle_yaml_mode()
        await pilot.pause()

        assert screen.yaml_mode == "spec"


@pytest.mark.asyncio
async def test_status_bar_shows_yaml_mode_hint():
    """Status bar should show '(full)' or '(spec)' based on current mode."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        # Set up state directly without spawning background workers
        screen._yaml_full = "apiVersion: v1\n"
        screen._yaml_spec = "apiVersion: v1\n"
        screen._show_yaml_panel()  # synchronous: directly updates connection_status

        # Assert immediately — no background workers involved
        assert "spec" in screen.connection_status

        # Toggle is also synchronous
        screen.action_toggle_yaml_mode()
        assert "full" in screen.connection_status


@pytest.mark.asyncio
async def test_escape_closes_yaml_panel_and_removes_text_area():
    """Escape should clear YAML state and remove TextArea."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._apply_yaml_result(("apiVersion: v1\n", "apiVersion: v1\n"))
        await pilot.pause()
        assert screen.yaml_view_open is True

        screen.action_close_detail_panel()
        await pilot.pause()

        assert screen.yaml_view_open is False
        assert screen.detail_panel_open is False

        with pytest.raises(NoMatches):
            screen.query_one("#yaml-content", TextArea)

        static = screen.query_one("#detail-panel-content", Static)
        assert "hidden" not in static.classes


@pytest.mark.asyncio
async def test_teardown_yaml_panel_removes_text_area():
    """_teardown_yaml_panel should remove TextArea and show Static."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._apply_yaml_result(("apiVersion: v1\n", "apiVersion: v1\n"))
        await pilot.pause()
        assert screen.yaml_view_open is True

        screen._teardown_yaml_panel()
        await pilot.pause()

        assert screen.yaml_view_open is False
        with pytest.raises(NoMatches):
            screen.query_one("#yaml-content", TextArea)

        static = screen.query_one("#detail-panel-content", Static)
        assert "hidden" not in static.classes


@pytest.mark.asyncio
async def test_apply_yaml_result_twice_no_duplicate_ids():
    """Calling _apply_yaml_result twice must not raise DuplicateIds."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._apply_yaml_result(("apiVersion: v1\nkind: Pod\n", "apiVersion: v1\n"))
        await pilot.pause()
        assert screen.yaml_view_open is True

        # Second call simulates pressing 'y' while the panel is already open
        screen._apply_yaml_result(("apiVersion: v1\nkind: Service\n", "apiVersion: v1\n"))
        await pilot.pause()

        assert screen.yaml_view_open is True
        text_areas = screen.query("#yaml-content")
        assert len(text_areas) == 1, "Expected exactly one #yaml-content widget"


@pytest.mark.asyncio
async def test_yaml_panel_closed_when_describe_called():
    """yaml_view_open should be False after describe is invoked while YAML was open."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._apply_yaml_result(("apiVersion: v1\n", "apiVersion: v1\n"))
        await pilot.pause()
        assert screen.yaml_view_open is True

        # No resource data → describe returns early after teardown
        screen.action_describe_resource()
        await pilot.pause()

        assert screen.yaml_view_open is False


@pytest.mark.asyncio
async def test_y_key_triggers_yaml_worker():
    """Pressing 'y' with resource data should call _show_yaml_worker."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._resource_data = [{"name": "test-pod", "namespace": "default"}]
        screen.current_resource_type = "Pods"
        screen.current_namespace = "default"

        table = screen.query_one("#resource-table", ResourceTable)
        table.focus()

        with patch.object(screen, "_show_yaml_worker") as mock_worker:
            await pilot.press("y")
            await pilot.pause()
            mock_worker.assert_called_once_with("pod", "test-pod", "default")


@pytest.mark.asyncio
async def test_full_yaml_lifecycle_open_toggle_close():
    """Full lifecycle: open YAML panel, toggle mode, then close with escape."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        full = "apiVersion: v1\nkind: Pod\nstatus:\n  phase: Running\n"
        spec = "apiVersion: v1\nkind: Pod\nspec: {}\n"

        screen._apply_yaml_result((full, spec))
        await pilot.pause()

        assert screen.yaml_view_open is True
        assert screen.yaml_mode == "spec"
        text_area = screen.query_one("#yaml-content", TextArea)
        assert "status:" not in text_area.text

        await pilot.press("m")
        await pilot.pause()

        assert screen.yaml_mode == "full"
        text_area = screen.query_one("#yaml-content", TextArea)
        assert "status:" in text_area.text

        await pilot.press("escape")
        await pilot.pause()

        assert screen.yaml_view_open is False
        assert screen.detail_panel_open is False
        with pytest.raises(NoMatches):
            screen.query_one("#yaml-content", TextArea)


@pytest.mark.asyncio
async def test_yaml_then_describe_tears_down_yaml():
    """Pressing 'd' while YAML is open should tear down YAML."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._apply_yaml_result(("apiVersion: v1\n", "apiVersion: v1\n"))
        await pilot.pause()
        assert screen.yaml_view_open is True

        # Press 'd' — no resource data so describe exits early, but teardown runs first
        await pilot.press("d")
        await pilot.pause()

        assert screen.yaml_view_open is False
        with pytest.raises(NoMatches):
            screen.query_one("#yaml-content", TextArea)


@pytest.mark.asyncio
async def test_yaml_panel_closed_when_logs_called():
    """yaml_view_open should be False after 'l' is pressed while YAML was open."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._apply_yaml_result(("apiVersion: v1\n", "apiVersion: v1\n"))
        await pilot.pause()
        assert screen.yaml_view_open is True

        # Press 'l' — not in Pods view, so logs exits early, but teardown runs first
        await pilot.press("l")
        await pilot.pause()

        assert screen.yaml_view_open is False


@pytest.mark.asyncio
async def test_yaml_text_area_uses_monokai_theme():
    """TextArea for YAML should be created with the monokai theme."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._apply_yaml_result(("apiVersion: v1\nkind: Pod\n", "apiVersion: v1\n"))
        await pilot.pause()

        text_area = screen.query_one("#yaml-content", TextArea)
        assert text_area.theme == "monokai"


@pytest.mark.asyncio
async def test_yaml_text_area_uses_yaml_language():
    """TextArea for YAML should be created with language='yaml'."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        screen._apply_yaml_result(("apiVersion: v1\nkind: Pod\n", "apiVersion: v1\n"))
        await pilot.pause()

        text_area = screen.query_one("#yaml-content", TextArea)
        assert text_area.language == "yaml"


@pytest.mark.asyncio
async def test_yaml_language_preserved_after_toggle():
    """TextArea language must remain 'yaml' after toggling between full and spec mode."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        full = "apiVersion: v1\nkind: Pod\nstatus:\n  phase: Running\n"
        spec = "apiVersion: v1\nkind: Pod\nspec: {}\n"
        screen._apply_yaml_result((full, spec))
        await pilot.pause()

        # Initial state: spec mode
        text_area = screen.query_one("#yaml-content", TextArea)
        assert text_area.language == "yaml"

        # Toggle to full
        screen.action_toggle_yaml_mode()
        await pilot.pause()
        text_area = screen.query_one("#yaml-content", TextArea)
        assert text_area.language == "yaml"

        # Toggle back to spec
        screen.action_toggle_yaml_mode()
        await pilot.pause()
        text_area = screen.query_one("#yaml-content", TextArea)
        assert text_area.language == "yaml"


# --- Multi-column sort tests ---


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


def test_resource_table_initial_sort_state():
    """ResourceTable starts with no sort columns."""
    table = ResourceTable()
    assert table._sort_columns == []
    assert table._shift_held is False


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


def test_sort_state_reset_on_column_change():
    """Sort state resets when populate_resources is called with different columns."""
    table = _make_table()
    table._sort_columns = [(0, False)]
    # Call with different column set
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
    # Simulate firing header selection with an unknown key (early return path)
    from unittest.mock import MagicMock
    event = MagicMock()
    event.column_key = MagicMock()
    event.column_key.value = "unknown_key"
    table.on_data_table_header_selected(event)
    assert table._shift_held is False
