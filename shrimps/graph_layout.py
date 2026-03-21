"""Concept graph rendering utilities for the Cheeky Shrimps app.

This module is responsible for:
- computing radial tree positions
- relaxing the layout with simple spring forces
- deriving visual styles for nodes and edges
- building the final Plotly figure
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import plotly.graph_objs as go

from shrimps.config import GRAPH_CONFIG

PALETTE = {
    "bg":           "#020d1a",
    "paper":        "#020d1a",
    "text":         "#e8f4f0",
    "text_dim":     "#4a8a7a",
    "edge":         "rgba(0,180,160,0.2)",
    "edge_active":  "rgba(255,140,80,0.5)",
    "edge_loading": "rgba(0,180,160,0.07)",
    "root":         "#ffd166",
    "current":      "#ff6b6b",
    "visited":      "#06d6a0",
    "idle":         "#48cae4",
    "flash":        "#ffd166",
    "outline":      "rgba(232,244,240,0.5)",
    "hover_bg":     "rgba(2,13,26,0.97)",
    "idle_outline": "rgba(226, 232, 240, 0.55)",
}

ICONS = {
    "root":    "🧠",
    "visited": "✨",
    "current": "🎯",
    "idle":    "📘",
}


@dataclass
class NodeStyleBundle:
    x: List[float]
    y: List[float]
    labels: List[str]
    fills: List[str]
    sizes: List[float]
    alpha: List[float]
    border_widths: List[float]
    border_colors: List[str]


@dataclass
class EdgeStyleBundle:
    x: List[float]
    y: List[float]
    colors: List[str]
    widths: List[float]


class GraphFigureBuilder:
    """Builds a Plotly figure for a concept graph."""

    @classmethod
    def render(
        cls,
        graph: Dict[str, dict],
        visited_order: List[str],
        focus: str = "start",
        flash_node: Optional[str] = None,
        current_node: Optional[str] = None,
    ) -> go.Figure:
        if current_node is None and visited_order:
            current_node = visited_order[-1]

        coords = cls._initial_radial_layout(graph, focus)
        coords = cls._relax_layout(coords, graph)
        coords = cls._shrink_if_oversized(coords)

        node_bundle = cls._style_nodes(
            graph=graph,
            coords=coords,
            visited_order=visited_order,
            current_node=current_node,
            flash_node=flash_node,
        )
        edge_bundle = cls._style_edges(
            graph=graph,
            coords=coords,
            visited_order=visited_order,
            current_node=current_node,
        )

        x_bounds, y_bounds = cls._viewport(coords, focus)
        traces = cls._build_edge_traces(edge_bundle)
        traces.append(cls._build_node_trace(node_bundle, coords))

        return go.Figure(
            data=traces,
            layout=cls._build_layout(x_bounds, y_bounds),
        )

    @staticmethod
    def autoscale(fig: go.Figure) -> go.Figure:
        fig.update_layout(xaxis={"autorange": True}, yaxis={"autorange": True})
        return fig

    @classmethod
    def _initial_radial_layout(
        cls,
        graph: Dict[str, dict],
        focus: str,
    ) -> Dict[str, Tuple[float, float]]:
        spacing = GRAPH_CONFIG["base_spacing"]
        placed: Dict[str, Tuple[float, float]] = {}
        emphasis_path = cls._path_from_root(graph, focus)

        def place_branch(node_id: str, heading: float, arc_width: float) -> None:
            if node_id in placed:
                return
            if node_id == "start":
                placed[node_id] = (0.0, 0.0)
            else:
                parent_id = graph[node_id]["parent"]
                parent_x, parent_y = placed.get(parent_id, (0.0, 0.0))
                radius = spacing * graph[node_id]["distance"]
                placed[node_id] = (
                    parent_x + radius * math.cos(heading),
                    parent_y + radius * math.sin(heading),
                )

            children = cls._children_of(graph, node_id)
            if not children:
                return

            highlighted_child = cls._next_node_on_path(node_id, emphasis_path)
            child_weights = [
                3.2 if child_id == highlighted_child else 1.0
                for child_id in children
            ]
            total_weight = sum(child_weights)
            sweep_start = heading - arc_width / 2.0
            for child_id, weight in zip(children, child_weights):
                local_arc = arc_width * (weight / total_weight)
                child_heading = sweep_start + local_arc / 2.0
                place_branch(child_id, child_heading, local_arc)
                sweep_start += local_arc

        place_branch("start", 0.0, math.tau)
        return placed

    @staticmethod
    def _children_of(graph: Dict[str, dict], parent_id: str) -> List[str]:
        return [nid for nid, p in graph.items() if p["parent"] == parent_id]

    @staticmethod
    def _path_from_root(graph: Dict[str, dict], target: str) -> List[str]:
        path: List[str] = []
        cursor = target
        while cursor and cursor in graph:
            path.append(cursor)
            cursor = graph[cursor].get("parent")
        path.reverse()
        return path

    @staticmethod
    def _next_node_on_path(node_id: str, ordered_path: List[str]) -> Optional[str]:
        if node_id not in ordered_path:
            return None
        idx = ordered_path.index(node_id)
        return ordered_path[idx + 1] if idx + 1 < len(ordered_path) else None

    @classmethod
    def _relax_layout(
        cls,
        coords: Dict[str, Tuple[float, float]],
        graph: Dict[str, dict],
    ) -> Dict[str, Tuple[float, float]]:
        settings = GRAPH_CONFIG["force_layout"]
        repulsion = settings["k_repel"]
        attraction = settings["k_attract"]
        rounds = settings["iterations"]
        preferred_spacing = GRAPH_CONFIG["base_spacing"]
        node_ids = list(coords.keys())

        for _ in range(rounds):
            offsets = {nid: np.array([0.0, 0.0]) for nid in node_ids}
            cls._apply_pairwise_repulsion(node_ids, coords, offsets, repulsion)
            cls._apply_parent_child_springs(graph, coords, offsets, attraction, preferred_spacing)
            cls._move_nodes(coords, offsets)

        return coords

    @staticmethod
    def _apply_pairwise_repulsion(
        node_ids: List[str],
        coords: Dict[str, Tuple[float, float]],
        offsets: Dict[str, np.ndarray],
        repulsion: float,
    ) -> None:
        for left in range(len(node_ids)):
            for right in range(left + 1, len(node_ids)):
                a, b = node_ids[left], node_ids[right]
                pa, pb = np.array(coords[a]), np.array(coords[b])
                delta = pa - pb
                distance = max(np.linalg.norm(delta), 0.1)
                push = repulsion / distance
                direction = delta / distance
                offsets[a] += direction * push
                offsets[b] -= direction * push

    @staticmethod
    def _apply_parent_child_springs(
        graph: Dict[str, dict],
        coords: Dict[str, Tuple[float, float]],
        offsets: Dict[str, np.ndarray],
        attraction: float,
        preferred_spacing: float,
    ) -> None:
        for node_id, payload in graph.items():
            parent_id = payload["parent"]
            if parent_id is None or parent_id not in coords:
                continue
            child_pos = np.array(coords[node_id])
            parent_pos = np.array(coords[parent_id])
            delta = child_pos - parent_pos
            distance = max(np.linalg.norm(delta), 0.1)
            target_length = payload["distance"] * preferred_spacing
            spring_force = attraction * (distance - target_length)
            direction = delta / distance
            offsets[node_id] -= direction * spring_force
            offsets[parent_id] += direction * spring_force

    @staticmethod
    def _move_nodes(
        coords: Dict[str, Tuple[float, float]],
        offsets: Dict[str, np.ndarray],
    ) -> None:
        for node_id, displacement in offsets.items():
            if node_id == "start":
                continue
            magnitude = np.linalg.norm(displacement)
            if magnitude > 1.0:
                displacement = displacement / magnitude
            x, y = coords[node_id]
            coords[node_id] = (x + displacement[0], y + displacement[1])

    @staticmethod
    def _shrink_if_oversized(
        coords: Dict[str, Tuple[float, float]],
    ) -> Dict[str, Tuple[float, float]]:
        max_radius = GRAPH_CONFIG["target_radius"]
        non_center = [(x, y) for (x, y) in coords.values() if (x, y) != (0, 0)]
        if not non_center:
            return coords
        current_radius = max(math.hypot(x, y) for x, y in non_center)
        if current_radius <= max_radius:
            return coords
        factor = max_radius / current_radius
        return {nid: (x * factor, y * factor) for nid, (x, y) in coords.items()}

    @classmethod
    def _style_nodes(
        cls,
        graph: Dict[str, dict],
        coords: Dict[str, Tuple[float, float]],
        visited_order: List[str],
        current_node: Optional[str],
        flash_node: Optional[str],
    ) -> NodeStyleBundle:
        visited = set(visited_order)
        root_base = GRAPH_CONFIG["root_size_base"]
        root_floor = GRAPH_CONFIG["root_size_min"]
        node_base = GRAPH_CONFIG["node_size_base"]
        node_scale = GRAPH_CONFIG["node_size_multiplier"]

        in_loading_mode = bool(
            current_node
            and current_node != "start"
            and current_node not in visited_order
        )

        x_vals, y_vals, labels, fills, sizes, alpha, border_widths, border_colors = (
            [], [], [], [], [], [], [], []
        )

        root_size = max(root_floor, root_base - 2 * (len(coords) - 1))

        for node_id, (x, y) in coords.items():
            x_vals.append(x)
            y_vals.append(y)
            labels.append(cls._display_label(node_id, graph, visited, current_node))

            if node_id == "start":
                size = root_size
                fill = PALETTE["root"]
                border = PALETTE["outline"]
                border_w = 3.0
            else:
                breadth = graph[node_id].get("breadth", 1.0)
                size = node_base + node_scale * breadth
                if node_id == current_node:
                    fill = PALETTE["current"]
                    border = PALETTE["flash"]
                    border_w = 3.0
                elif node_id in visited:
                    fill = PALETTE["visited"]
                    border = PALETTE["outline"]
                    border_w = 2.5
                else:
                    fill = PALETTE["idle"]
                    border = PALETTE["idle_outline"]
                    border_w = 2.0

            if flash_node is not None and node_id == flash_node:
                size *= 1.25
                border = PALETTE["flash"]
                border_w = 4.0

            opacity = 0.38 if (in_loading_mode and node_id != current_node) else 1.0

            fills.append(fill)
            sizes.append(size)
            alpha.append(opacity)
            border_widths.append(border_w)
            border_colors.append(border)

        return NodeStyleBundle(
            x=x_vals, y=y_vals, labels=labels, fills=fills,
            sizes=sizes, alpha=alpha, border_widths=border_widths, border_colors=border_colors,
        )

    @staticmethod
    def _display_label(
        node_id: str,
        graph: Dict[str, dict],
        visited: set,
        current_node: Optional[str],
    ) -> str:
        if node_id == "start":
            return f"{ICONS['root']} {graph[node_id].get('label', 'Start')}"
        if node_id == current_node:
            return f"{ICONS['current']} {node_id}"
        if node_id in visited:
            return f"{ICONS['visited']} {node_id}"
        return f"{ICONS['idle']} {node_id}"

    @classmethod
    def _style_edges(
        cls,
        graph: Dict[str, dict],
        coords: Dict[str, Tuple[float, float]],
        visited_order: List[str],
        current_node: Optional[str],
    ) -> EdgeStyleBundle:
        visited = set(visited_order)
        loading = bool(
            current_node
            and current_node != "start"
            and current_node not in visited_order
        )

        x_vals, y_vals, colors, widths = [], [], [], []

        for node_id, (x, y) in coords.items():
            parent_id = graph[node_id]["parent"]
            if not parent_id or parent_id not in coords:
                continue
            px, py = coords[parent_id]
            x_vals.extend([px, x, None])
            y_vals.extend([py, y, None])

            if loading:
                colors.append(PALETTE["edge_loading"])
                widths.append(2.0)
            elif node_id == current_node:
                colors.append(PALETTE["edge_active"])
                widths.append(4.0)
            elif node_id in visited:
                colors.append(PALETTE["edge_active"])
                widths.append(3.0)
            else:
                colors.append(PALETTE["edge"])
                widths.append(2.5)

        return EdgeStyleBundle(x=x_vals, y=y_vals, colors=colors, widths=widths)

    @staticmethod
    def _viewport(
        coords: Dict[str, Tuple[float, float]],
        focus: str,
    ) -> Tuple[List[float], List[float]]:
        if len(coords) < 2:
            return [-10, 10], [-10, 10]
        fx, fy = coords.get(focus, (0, 0))
        xs = [p[0] for p in coords.values()]
        ys = [p[1] for p in coords.values()]
        radius_x = max(fx - min(xs), max(xs) - fx)
        radius_y = max(fy - min(ys), max(ys) - fy)
        radius = max(radius_x, radius_y) * 1.25 + 5
        return [fx - radius, fx + radius], [fy - radius, fy + radius]

    @staticmethod
    def _build_edge_traces(edge_bundle: EdgeStyleBundle) -> List[go.Scatter]:
        traces = []
        for offset in range(0, len(edge_bundle.x), 3):
            idx = offset // 3
            traces.append(go.Scatter(
                x=edge_bundle.x[offset:offset + 2],
                y=edge_bundle.y[offset:offset + 2],
                mode="lines",
                line=dict(
                    width=edge_bundle.widths[idx] if idx < len(edge_bundle.widths) else 2.5,
                    color=edge_bundle.colors[idx] if idx < len(edge_bundle.colors) else PALETTE["edge"],
                ),
                hoverinfo="none",
                showlegend=False,
            ))
        return traces

    @staticmethod
    def _build_node_trace(
        node_bundle: NodeStyleBundle,
        coords: Dict[str, Tuple[float, float]],
    ) -> go.Scatter:
        click_payload = [None if nid == "start" else nid for nid in coords.keys()]
        text_colors = [
            f"rgba(229, 231, 235, {opacity})" if opacity < 1.0 else PALETTE["text"]
            for opacity in node_bundle.alpha
        ]
        trace = go.Scatter(
            x=node_bundle.x,
            y=node_bundle.y,
            mode="markers+text",
            text=node_bundle.labels,
            textposition="top center",
            textfont=dict(color=text_colors, size=13, family="Inter, Arial, sans-serif"),
            hovertemplate="<b>%{text}</b><extra></extra>",
            hoverlabel=dict(
                bgcolor=PALETTE["hover_bg"],
                bordercolor=PALETTE["outline"],
                font=dict(color="white", size=15),
            ),
            marker=dict(
                size=node_bundle.sizes,
                color=node_bundle.fills,
                opacity=node_bundle.alpha,
                line=dict(width=0),
                symbol="circle",
            ),
            customdata=click_payload,
            hoverinfo="text",
            selected=dict(marker=dict(opacity=1)),
            unselected=dict(marker=dict(opacity=1)),
        )
        trace.update(
            marker_line_width=node_bundle.border_widths,
            marker_line_color=node_bundle.border_colors,
        )
        return trace

    @staticmethod
    def _build_layout(x_range: List[float], y_range: List[float]) -> go.Layout:
        return go.Layout(
            clickmode="event+select",
            xaxis=dict(visible=False, range=x_range, showgrid=False, zeroline=False),
            yaxis=dict(
                visible=False, range=y_range, showgrid=False, zeroline=False,
                scaleanchor="x", scaleratio=1,
            ),
            margin=dict(l=20, r=20, t=30, b=20),
            height=720,
            transition={"duration": 450, "easing": "cubic-in-out"},
            showlegend=False,
            plot_bgcolor=PALETTE["bg"],
            paper_bgcolor=PALETTE["paper"],
            font=dict(family="Inter, Segoe UI, system-ui, sans-serif"),
        )


class GraphManager:
    """Backward-compatible wrapper exposing the original public API."""

    @staticmethod
    def build_node_positions(node_data, focus_node="start"):
        return GraphFigureBuilder._initial_radial_layout(node_data, focus_node)

    @staticmethod
    def apply_force_directed_layout(positions, node_data):
        return GraphFigureBuilder._relax_layout(positions, node_data)

    @staticmethod
    def rescale_positions_if_needed(positions):
        return GraphFigureBuilder._shrink_if_oversized(positions)

    @staticmethod
    def calculate_node_visual_properties(node_data, positions, clicked_nodes_list, last_clicked, node_flash):
        bundle = GraphFigureBuilder._style_nodes(
            graph=node_data,
            coords=positions,
            visited_order=clicked_nodes_list,
            current_node=last_clicked,
            flash_node=node_flash,
        )
        return (
            bundle.x, bundle.y, bundle.labels, bundle.fills,
            bundle.sizes, bundle.alpha, bundle.border_widths, bundle.border_colors,
        )

    @staticmethod
    def calculate_edge_properties(node_data, positions, clicked_nodes_list, last_clicked=None):
        bundle = GraphFigureBuilder._style_edges(
            graph=node_data,
            coords=positions,
            visited_order=clicked_nodes_list,
            current_node=last_clicked,
        )
        return bundle.x, bundle.y, bundle.colors, bundle.widths

    @staticmethod
    def calculate_view_range(positions, focus_node="start"):
        return GraphFigureBuilder._viewport(positions, focus_node)

    @staticmethod
    def create_edge_traces(edge_xs, edge_ys, edge_colors, edge_widths):
        return GraphFigureBuilder._build_edge_traces(
            EdgeStyleBundle(edge_xs, edge_ys, edge_colors, edge_widths)
        )

    @staticmethod
    def create_node_trace(xs, ys, labels, colors, sizes, opacities, line_widths, line_colors, positions):
        return GraphFigureBuilder._build_node_trace(
            NodeStyleBundle(
                x=xs, y=ys, labels=labels, fills=colors,
                sizes=sizes, alpha=opacities, border_widths=line_widths, border_colors=line_colors,
            ),
            positions,
        )

    @staticmethod
    def create_layout(x_range, y_range):
        return GraphFigureBuilder._build_layout(x_range, y_range)

    @staticmethod
    def generate_figure(node_data, clicked_nodes_list, focus_node="start", node_flash=None, last_clicked=None):
        return GraphFigureBuilder.render(
            graph=node_data,
            visited_order=clicked_nodes_list,
            focus=focus_node,
            flash_node=node_flash,
            current_node=last_clicked,
        )

    @staticmethod
    def autoscale_figure(fig):
        return GraphFigureBuilder.autoscale(fig)
