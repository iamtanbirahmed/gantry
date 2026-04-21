"""Tests for the Gantry app shell and screen switching."""

import pytest
from textual.containers import VerticalScroll
from textual.widgets import ListView

from gantry.app import GantryApp
from gantry.screens import ClusterScreen, HelmScreen
from gantry.widgets import KeybindingsBar


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
