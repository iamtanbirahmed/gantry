"""Tests for the Gantry app shell and screen switching."""

import pytest
from textual.widgets import ListView

from gantry.app import GantryApp
from gantry.screens import ClusterScreen, HelmScreen


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
    assert screen._RESOURCE_TYPES == ["Pods", "Services", "Deployments", "ConfigMaps"]


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
        # Arrow down to Services, press Enter
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.pause()
        assert screen.current_resource_type == "Services"


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

        # Right arrow → search
        await pilot.press("right")
        await pilot.pause()
        assert screen.current_panel == "search"

        # Right arrow → sidebar (wraps)
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

        # Start on sidebar, move to search first
        await pilot.press("right")
        await pilot.press("right")
        await pilot.pause()
        assert screen.current_panel == "search"

        # Left arrow → table
        await pilot.press("left")
        await pilot.pause()
        assert screen.current_panel == "table"

        # Left arrow → sidebar
        await pilot.press("left")
        await pilot.pause()
        assert screen.current_panel == "sidebar"

        # Left arrow → search (wraps)
        await pilot.press("left")
        await pilot.pause()
        assert screen.current_panel == "search"
