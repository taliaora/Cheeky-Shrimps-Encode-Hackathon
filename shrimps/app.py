"""
Application entrypoint for the Cheeky Shrimps learning interface.

This module wires together:
- Dash application setup
- the initial UI tree
- callback registration
- runtime configuration for local execution
"""

from __future__ import annotations

import os
from typing import Any

import dash
from dash import Input, Output

from shrimps.callback_handlers import CallbackHandlers
from shrimps.components import (
    control_panel,
    cytoscape_graph,
    data_stores,
    graph_container,
    info_box,
    main_layout,
    sidebar,
    timers,
)
from shrimps.config import default_port, html_shell, motion_settings, palette, ui_styles
from shrimps.graph_layout_cytoscape import build_cytoscape_elements
from shrimps.state_manager import StateManager


def create_dash_app() -> dash.Dash:
    """
    Build and configure the Dash application instance.

    Returns:
        A fully configured Dash app.
    """
    app = dash.Dash(
        __name__,
        suppress_callback_exceptions=True,
        external_stylesheets=[
            "https://cdnjs.cloudflare.com/ajax/libs/rc-slider/10.6.2/assets/index.min.css",
        ],
    )
    app.enable_dev_tools(
        debug=False,
        dev_tools_hot_reload=False,
        dev_tools_ui=False,
        dev_tools_props_check=False,
    )
    app.index_string = html_shell()
    return app


def build_initial_graph_component(initial_state: dict[str, Any]):
    """
    Create the initial Cytoscape graph widget from the starting application state.

    Args:
        initial_state: Freshly initialized application state.

    Returns:
        A Cytoscape graph component.
    """
    elements = build_cytoscape_elements(
        initial_state["node_data"],
        initial_state["clicked_nodes_list"],
        initial_state["last_clicked"],
    )
    return cytoscape_graph(elements, graph_key=0)


def compose_layout() -> list[Any]:
    """
    Build the full top-level Dash layout tree.

    Returns:
        A list of top-level components for the application layout.
    """
    initial_state = StateManager.get_initial_state()
    graph_widget = build_initial_graph_component(initial_state)

    state_components = data_stores(initial_state)
    timer_components = timers()

    controls = control_panel()
    details_panel = info_box([])
    side_panel = sidebar(controls, details_panel)
    graph_panel = graph_container(graph_widget)

    page = main_layout(graph_panel, side_panel)

    return [*state_components, *timer_components, page]


def submit_button_style(is_flashing: bool) -> dict[str, Any]:
    """
    Compute the submit button style for its normal or highlighted state.

    Args:
        is_flashing: Whether the button should display its flash/highlight style.

    Returns:
        A style dictionary for the submit button.
    """
    colors = palette()
    styles = ui_styles()
    animation = motion_settings()

    base_style = {
        **styles["buttons"]["common"],
        **styles["buttons"]["submit"],
        "transition": (
            f"box-shadow {animation['submit_flash_duration'] / 1000}s, "
            f"background {animation['submit_flash_duration'] / 1000}s, "
            f"color {animation['submit_flash_duration'] / 1000}s"
        ),
    }

    if not is_flashing:
        return base_style

    highlighted_style = {
        "backgroundColor": "#fff",
        "color": colors["accent_green"],
        "boxShadow": "0 0 24px 8px #f0fff0",
    }
    return {**base_style, **highlighted_style}


def register_local_callbacks(app: dash.Dash) -> None:
    """
    Register callbacks that are intentionally kept in this module.

    Args:
        app: The Dash application instance.
    """

    @app.callback(
        Output("submit-btn", "style"),
        Input("submit-btn-flash", "data"),
    )
    def update_submit_button_style(flash: bool) -> dict[str, Any]:
        """
        Update the submit button appearance when the flash state changes.

        Args:
            flash: Whether the button should be highlighted.

        Returns:
            A Dash style dictionary.
        """
        return submit_button_style(bool(flash))


def create_application() -> tuple[dash.Dash, Any]:
    """
    Create the full application and its associated WSGI server.

    Returns:
        A tuple of (Dash app, server).
    """
    app = create_dash_app()
    app.layout = compose_layout()

    CallbackHandlers(app)
    register_local_callbacks(app)

    return app, app.server


app, server = create_application()


def main() -> None:
    """
    Launch the application in local/server mode.
    """
    port = int(os.getenv("PORT", default_port()))
    app.run(
        debug=False,
        host="0.0.0.0",
        port=port,
        dev_tools_ui=False,
        dev_tools_props_check=False,
        dev_tools_hot_reload=False,
    )


if __name__ == "__main__":
    main()
