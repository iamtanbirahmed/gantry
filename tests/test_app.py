"""Tests for the Gantry app shell and screen switching."""

import pytest
from textual.containers import VerticalScroll
from textual.widgets import ListView

from gantry.app import GantryApp
from gantry.screens import ClusterScreen, HelmScreen
from gantry.widgets import KeybindingsBar, ResourceSidebar


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


def test_cluster_screen_has_dispatch_tables():
    """Test that ClusterScreen has dispatch tables for resource types."""
    screen = ClusterScreen()
    # After migration to ResourceSidebar, dispatch tables replace _RESOURCE_TYPES
    assert hasattr(screen, "_FETCH_FNS")
    assert hasattr(screen, "_COLUMN_DEFS")
    assert "Pods" in screen._FETCH_FNS
    assert "Services" in screen._FETCH_FNS
    assert "Deployments" in screen._FETCH_FNS
    assert "Config Maps" in screen._FETCH_FNS


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
        # Allow the _ready flag to be set after the initial mount cycle
        await pilot.pause()
        # Arrow down from Pods → Deployments (second item in Workloads group)
        await pilot.press("down")
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

    Arrow navigation within a group fires ResourceSelected on each highlight change.
    The Workloads group contains: Pods, Deployments, Daemon Sets, ...
    """
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)

        # Allow the _ready flag to be set after the initial mount cycle
        await pilot.pause()

        # Start on Pods
        assert screen.current_resource_type == "Pods"

        # Down arrow → Deployments (second item in Workloads group)
        await pilot.press("down")
        await pilot.pause()
        assert screen.current_resource_type == "Deployments"

        # Down arrow → Daemon Sets (third item, stub)
        await pilot.press("down")
        await pilot.pause()
        assert screen.current_resource_type == "Daemon Sets"

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
    assert "←→ Navigate" in output
    assert "↵ Deploy" in output
    assert "r Refresh" in output
    assert "c Context" in output
    assert "/ Search" in output
    assert "Tab Cluster" in output
    assert "q Quit" in output
    # Should NOT show cluster-specific bindings
    assert "Describe" not in output
    assert "Logs" not in output


def test_resource_sidebar_instantiates():
    sidebar = ResourceSidebar()
    assert sidebar is not None


def test_resource_sidebar_has_five_groups():
    sidebar = ResourceSidebar()
    assert len(sidebar.GROUPS) == 5


def test_resource_sidebar_pods_implemented():
    """Pods must be in Workloads and marked implemented."""
    sidebar = ResourceSidebar()
    workloads = next(g for g in sidebar.GROUPS if g[0] == "Workloads")
    items = {name: impl for name, impl in workloads[1]}
    assert items["Pods"] is True


def test_resource_sidebar_daemon_sets_stub():
    """Daemon Sets must be in Workloads and marked as stub."""
    sidebar = ResourceSidebar()
    workloads = next(g for g in sidebar.GROUPS if g[0] == "Workloads")
    items = {name: impl for name, impl in workloads[1]}
    assert items["Daemon Sets"] is False


def test_resource_sidebar_resource_selected_message():
    """ResourceSelected carries resource_type and implemented flag."""
    msg = ResourceSidebar.ResourceSelected("Pods", True)
    assert msg.resource_type == "Pods"
    assert msg.implemented is True


def test_resource_sidebar_stub_resource_selected_message():
    msg = ResourceSidebar.ResourceSelected("Nodes", False)
    assert msg.resource_type == "Nodes"
    assert msg.implemented is False


@pytest.mark.asyncio
async def test_cluster_screen_mounts_resource_sidebar():
    """ClusterScreen must contain a ResourceSidebar, not a bare ListView with id resource-type-sidebar."""
    app = GantryApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, ClusterScreen)
        sidebar = screen.query_one(ResourceSidebar)
        assert sidebar is not None


@pytest.mark.asyncio
async def test_cluster_screen_no_legacy_sidebar():
    """The old #resource-type-sidebar ListView must not exist (element is now ResourceSidebar)."""
    from textual.css.query import QueryError
    app = GantryApp()
    async with app.run_test() as pilot:
        # Querying for a ListView at this ID must fail because the element
        # is now a ResourceSidebar, not a ListView.
        with pytest.raises(QueryError):
            app.screen.query_one("#resource-type-sidebar", ListView)
