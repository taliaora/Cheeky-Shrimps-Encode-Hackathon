"""
Cytoscape Graph Manager for Cheeky Shrimps app
Converts node_data into Cytoscape elements with coral reef styling
"""

import numpy as np
from shrimps.graph_layout import GraphManager  # reuse position logic

# Coral reef emojis to scatter along edges
CORAL_EMOJIS = ["🪸", "🪸", "🪸", "🪸", "🪸", "🪸", "🪸", "🪸"]
EMOJI_STEPS = 0  # number of emoji nodes per edge


def _node_class(node, node_data, clicked_nodes_set, last_clicked, node_flash, practiced, caught, selected_node=None, has_flashcards=False, quiz_stats=None, srs_due=None):
    base = ""
    if node == "start":
        base = "reef-root"
    elif node_flash and node == node_flash:
        base = "reef-flash"
    elif node in caught:
        base = "reef-caught"
    elif node in practiced:
        base = "reef-practiced"
    elif node == selected_node and node != "start":
        base = "reef-selected"
    elif node == last_clicked:
        base = "reef-active"
    elif node in clicked_nodes_set:
        base = "reef-visited"
    else:
        base = "reef-unvisited"

    classes = base

    # Quiz performance overlay
    if quiz_stats and node in quiz_stats and node != "start":
        stats = quiz_stats[node]
        total = stats["correct"] + stats["wrong"]
        if total > 0:
            ratio = stats["correct"] / total
            if ratio >= 0.8:
                classes += " quiz-strong"
            elif ratio <= 0.4:
                classes += " quiz-weak"
            else:
                classes += " quiz-shaky"

    if has_flashcards and node != "start":
        classes += " reef-has-flashcards"

    if srs_due and node in srs_due:
        classes += " srs-due"

    return classes


def build_cytoscape_elements(node_data, clicked_nodes_list, last_clicked="start", node_flash=None, practiced=None, caught=None, flashcards=None, selected_node=None, quiz_stats=None, srs_due=None):
    """Convert node_data dict into Cytoscape elements — emoji chains replace edges."""
    clicked_nodes_set = set(clicked_nodes_list)
    practiced = set(practiced or [])
    caught = set(caught or [])
    srs_due_set = set(srs_due or [])

    positions = GraphManager.build_node_positions(node_data, focus_node=last_clicked or "start")
    positions = GraphManager.apply_force_directed_layout(positions, node_data)
    positions = GraphManager.rescale_positions_if_needed(positions)

    SCALE = 60
    OFFSET_X = 500
    OFFSET_Y = 380

    elements = []

    # Real nodes
    for node, (x, y) in positions.items():
        label = node_data[node].get("label", node) if node == "start" else node
        has_fc = node in (flashcards or {})
        cls = _node_class(node, node_data, clicked_nodes_set, last_clicked, node_flash, practiced, caught,
                          selected_node=selected_node, has_flashcards=has_fc,
                          quiz_stats=quiz_stats, srs_due=srs_due_set)
        elements.append({
            "data": {"id": node, "label": label},
            "position": {
                "x": OFFSET_X + x * SCALE,
                "y": OFFSET_Y - y * SCALE
            },
            "classes": cls
        })

    # Replace each edge with a chain of emoji phantom nodes
    emoji_idx = 0
    for node, data in node_data.items():
        parent = data.get("parent")
        if not parent or parent not in positions:
            continue

        px = OFFSET_X + positions[parent][0] * SCALE
        py = OFFSET_Y - positions[parent][1] * SCALE
        cx = OFFSET_X + positions[node][0] * SCALE
        cy = OFFSET_Y - positions[node][1] * SCALE

        is_visited = node in clicked_nodes_set

        # visible thick underline edge behind the emoji chain
        elements.append({
            "data": {"source": parent, "target": node},
            "classes": "edge-coral"
        })

        prev_id = parent
        for step in range(1, EMOJI_STEPS + 1):
            t = step / (EMOJI_STEPS + 1)
            ix = px + (cx - px) * t
            iy = py + (cy - py) * t
            emoji = CORAL_EMOJIS[emoji_idx % len(CORAL_EMOJIS)]
            emoji_idx += 1
            phantom_id = f"__emoji_{node}_{step}"

            elements.append({
                "data": {"id": phantom_id, "label": emoji},
                "position": {"x": ix, "y": iy},
                "classes": "reef-emoji-visited" if is_visited else "reef-emoji"
            })
            # invisible edge connecting chain
            elements.append({
                "data": {"source": prev_id, "target": phantom_id},
                "classes": "edge-hidden"
            })
            prev_id = phantom_id

        # final invisible edge to real target node
        elements.append({
            "data": {"source": prev_id, "target": node},
            "classes": "edge-hidden"
        })

    return elements


# Cytoscape stylesheet — bright coral reef aesthetic
CYTOSCAPE_STYLESHEET = [
    # ── Base node ──────────────────────────────────────────────────────────
    {
        "selector": "node",
        "style": {
            "label": "data(label)",
            "text-valign": "bottom",
            "text-halign": "center",
            "text-margin-y": "6px",
            "font-family": "Inter, Segoe UI, sans-serif",
            "font-size": "11px",
            "color": "#ffffff",
            "text-outline-color": "#0a4a5a",
            "text-outline-width": "2px",
            "width": "38px",
            "height": "38px",
            "border-width": "2px",
            "border-color": "rgba(255,255,255,0.4)",
            "background-color": "#48cae4",
            "transition-property": "background-color, border-color, width, height, opacity",
            "transition-duration": "0.35s",
        }
    },
    # ── Root — glowing orange brain ─────────────────────────────────────────
    {
        "selector": ".reef-root",
        "style": {
            "background-color": "transparent",
            "border-color": "#ff8c35",
            "border-width": "3px",
            "width": "72px",
            "height": "72px",
            "font-size": "13px",
            "font-weight": "700",
            "color": "#fff8e7",
            "shape": "ellipse",
            "background-image": "data:image/svg+xml;utf8,"
                "<svg xmlns='http://www.w3.org/2000/svg' width='72' height='72'>"
                "<defs>"
                "<radialGradient id='brainGlow' cx='50%' cy='50%' r='50%'>"
                "<stop offset='0%' stop-color='%23ffcc66' stop-opacity='1'/>"
                "<stop offset='60%' stop-color='%23ff8c35' stop-opacity='0.9'/>"
                "<stop offset='100%' stop-color='%23ff5500' stop-opacity='0.7'/>"
                "</radialGradient>"
                "</defs>"
                "<circle cx='36' cy='36' r='30' fill='url(%23brainGlow)' stroke='%23ffcc66' stroke-width='2'/>"
                "<text x='36' y='46' text-anchor='middle' font-size='30'>&#x1F9E0;</text>"
                "</svg>",
            "background-fit": "cover",
            "background-clip": "none",
        }
    },
    # ── Selected — bright cyan highlight ────────────────────────────────────
    {
        "selector": ".reef-selected",
        "style": {
            "background-color": "#00e5ff",
            "border-color": "#ffffff",
            "border-width": "4px",
            "width": "54px",
            "height": "54px",
            "shape": "ellipse",
            "background-image": "none",
            "color": "#002030",
            "text-outline-color": "#00e5ff",
            "text-outline-width": "2px",
            "font-weight": "700",
        }
    },
    # ── Unvisited — pink anemone ────────────────────────────────────────────
    {
        "selector": ".reef-unvisited",
        "style": {
            "background-color": "transparent",
            "border-color": "rgba(255,150,200,0.5)",
            "border-width": "2px",
            "shape": "ellipse",
            "width": "44px",
            "height": "50px",
            "background-image": "data:image/svg+xml;utf8,"
                "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='50'>"
                "<defs>"
                "<radialGradient id='an' cx='50%' cy='60%' r='55%'>"
                "<stop offset='0%' stop-color='%23ffb3d9' stop-opacity='0.95'/>"
                "<stop offset='100%' stop-color='%23e040a0' stop-opacity='0.7'/>"
                "</radialGradient>"
                "</defs>"
                "<ellipse cx='22' cy='30' rx='18' ry='16' fill='url(%23an)' stroke='%23ffb3d9' stroke-width='1.5'/>"
                "<ellipse cx='22' cy='14' rx='5' ry='12' fill='%23ff80c0' opacity='0.8'/>"
                "<ellipse cx='12' cy='16' rx='4' ry='10' fill='%23ff99cc' opacity='0.75' transform='rotate(-20,12,16)'/>"
                "<ellipse cx='32' cy='16' rx='4' ry='10' fill='%23ff99cc' opacity='0.75' transform='rotate(20,32,16)'/>"
                "<ellipse cx='7' cy='24' rx='3' ry='8' fill='%23ffb3d9' opacity='0.65' transform='rotate(-35,7,24)'/>"
                "<ellipse cx='37' cy='24' rx='3' ry='8' fill='%23ffb3d9' opacity='0.65' transform='rotate(35,37,24)'/>"
                "</svg>",
            "background-fit": "cover",
            "background-clip": "none",
        }
    },
    # ── Visited — purple coral sponge ───────────────────────────────────────
    {
        "selector": ".reef-visited",
        "style": {
            "background-color": "transparent",
            "border-color": "#b388ff",
            "border-width": "2px",
            "shape": "ellipse",
            "width": "44px",
            "height": "50px",
            "background-image": "data:image/svg+xml;utf8,"
                "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='50'>"
                "<defs>"
                "<radialGradient id='sp' cx='50%' cy='50%' r='55%'>"
                "<stop offset='0%' stop-color='%23ce93d8' stop-opacity='0.95'/>"
                "<stop offset='100%' stop-color='%237b1fa2' stop-opacity='0.75'/>"
                "</radialGradient>"
                "</defs>"
                "<rect x='6' y='10' width='32' height='34' rx='8' fill='url(%23sp)' stroke='%23ce93d8' stroke-width='1.5'/>"
                "<circle cx='14' cy='20' r='3' fill='%23f3e5f5' opacity='0.6'/>"
                "<circle cx='22' cy='16' r='2.5' fill='%23f3e5f5' opacity='0.5'/>"
                "<circle cx='30' cy='20' r='3' fill='%23f3e5f5' opacity='0.6'/>"
                "<circle cx='14' cy='32' r='2.5' fill='%23f3e5f5' opacity='0.5'/>"
                "<circle cx='22' cy='36' r='3' fill='%23f3e5f5' opacity='0.6'/>"
                "<circle cx='30' cy='32' r='2.5' fill='%23f3e5f5' opacity='0.5'/>"
                "<line x1='10' y1='44' x2='8' y2='50' stroke='%23ce93d8' stroke-width='2' stroke-linecap='round'/>"
                "<line x1='22' y1='44' x2='22' y2='50' stroke='%23b39ddb' stroke-width='2' stroke-linecap='round'/>"
                "<line x1='34' y1='44' x2='36' y2='50' stroke='%23ce93d8' stroke-width='2' stroke-linecap='round'/>"
                "</svg>",
            "background-fit": "cover",
            "background-clip": "none",
        }
    },
    # ── Active — orange coral branch ────────────────────────────────────────
    {
        "selector": ".reef-active",
        "style": {
            "background-color": "transparent",
            "border-color": "#ff8c35",
            "border-width": "3px",
            "width": "56px",
            "height": "62px",
            "shape": "ellipse",
            "background-image": "data:image/svg+xml;utf8,"
                "<svg xmlns='http://www.w3.org/2000/svg' width='56' height='62'>"
                "<defs>"
                "<linearGradient id='co' x1='0%' y1='100%' x2='0%' y2='0%'>"
                "<stop offset='0%' stop-color='%23ff6d00'/>"
                "<stop offset='100%' stop-color='%23ffcc80'/>"
                "</linearGradient>"
                "</defs>"
                "<line x1='28' y1='58' x2='28' y2='30' stroke='url(%23co)' stroke-width='5' stroke-linecap='round'/>"
                "<line x1='28' y1='44' x2='14' y2='24' stroke='%23ff8c35' stroke-width='4' stroke-linecap='round'/>"
                "<line x1='28' y1='44' x2='42' y2='24' stroke='%23ff8c35' stroke-width='4' stroke-linecap='round'/>"
                "<line x1='14' y1='24' x2='8' y2='12' stroke='%23ffb74d' stroke-width='3' stroke-linecap='round'/>"
                "<line x1='14' y1='24' x2='20' y2='10' stroke='%23ffb74d' stroke-width='3' stroke-linecap='round'/>"
                "<line x1='42' y1='24' x2='36' y2='10' stroke='%23ffb74d' stroke-width='3' stroke-linecap='round'/>"
                "<line x1='42' y1='24' x2='48' y2='12' stroke='%23ffb74d' stroke-width='3' stroke-linecap='round'/>"
                "<circle cx='8' cy='10' r='4' fill='%23ff6d00'/>"
                "<circle cx='20' cy='8' r='4' fill='%23ff8c35'/>"
                "<circle cx='36' cy='8' r='4' fill='%23ff8c35'/>"
                "<circle cx='48' cy='10' r='4' fill='%23ff6d00'/>"
                "<circle cx='28' cy='28' r='5' fill='%23ffcc80'/>"
                "</svg>",
            "background-fit": "cover",
            "background-clip": "none",
        }
    },
    # ── Practiced — teal sea fan 🐟 ─────────────────────────────────────────
    {
        "selector": ".reef-practiced",
        "style": {
            "background-color": "transparent",
            "border-color": "#26c6da",
            "border-width": "2px",
            "shape": "ellipse",
            "width": "44px",
            "height": "50px",
            "background-image": "data:image/svg+xml;utf8,"
                "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='50'>"
                "<defs>"
                "<radialGradient id='tf' cx='50%' cy='60%' r='55%'>"
                "<stop offset='0%' stop-color='%2380deea' stop-opacity='0.95'/>"
                "<stop offset='100%' stop-color='%2300838f' stop-opacity='0.75'/>"
                "</radialGradient>"
                "</defs>"
                "<ellipse cx='22' cy='30' rx='18' ry='16' fill='url(%23tf)' stroke='%2380deea' stroke-width='1.5'/>"
                "<text x='22' y='35' text-anchor='middle' font-size='14'>&#x1F41F;</text>"
                "<line x1='10' y1='46' x2='8' y2='50' stroke='%2326c6da' stroke-width='2' stroke-linecap='round'/>"
                "<line x1='22' y1='46' x2='22' y2='50' stroke='%2380deea' stroke-width='2' stroke-linecap='round'/>"
                "<line x1='34' y1='46' x2='36' y2='50' stroke='%2326c6da' stroke-width='2' stroke-linecap='round'/>"
                "</svg>",
            "background-fit": "cover",
            "background-clip": "none",
        }
    },
    # ── Caught — gold trophy coral 🎣 ───────────────────────────────────────
    {
        "selector": ".reef-caught",
        "style": {
            "background-color": "transparent",
            "border-color": "#ffd54f",
            "border-width": "3px",
            "width": "56px",
            "height": "62px",
            "shape": "ellipse",
            "background-image": "data:image/svg+xml;utf8,"
                "<svg xmlns='http://www.w3.org/2000/svg' width='56' height='62'>"
                "<defs>"
                "<radialGradient id='gc' cx='50%' cy='50%' r='55%'>"
                "<stop offset='0%' stop-color='%23fff176' stop-opacity='0.95'/>"
                "<stop offset='100%' stop-color='%23f9a825' stop-opacity='0.8'/>"
                "</radialGradient>"
                "</defs>"
                "<circle cx='28' cy='28' r='24' fill='url(%23gc)' stroke='%23ffd54f' stroke-width='2'/>"
                "<text x='28' y='36' text-anchor='middle' font-size='22'>&#x1F3A3;</text>"
                "</svg>",
            "background-fit": "cover",
            "background-clip": "none",
        }
    },
    {
        "selector": ".reef-flash",
        "style": {
            "background-color": "transparent",
            "border-color": "#ffffff",
            "border-width": "3px",
            "width": "60px",
            "height": "66px",
            "background-image": "data:image/svg+xml;utf8,"
                "<svg xmlns='http://www.w3.org/2000/svg' width='60' height='66'>"
                "<defs>"
                "<radialGradient id='fl' cx='50%' cy='50%' r='55%'>"
                "<stop offset='0%' stop-color='%23ffffff' stop-opacity='1'/>"
                "<stop offset='100%' stop-color='%23ffd54f' stop-opacity='0.8'/>"
                "</radialGradient>"
                "</defs>"
                "<circle cx='30' cy='30' r='26' fill='url(%23fl)' stroke='%23fff' stroke-width='2'/>"
                "</svg>",
            "background-fit": "cover",
            "background-clip": "none",
        }
    },
    # ── Has flashcards — warm orange border overlay ─────────────────────────
    {
        "selector": ".reef-has-flashcards",
        "style": {
            "border-color": "rgba(255,180,80,0.9)",
            "border-width": "3px",
        }
    },
    # ── Quiz performance overlays ───────────────────────────────────────────
    {
        "selector": ".quiz-strong",
        "style": {
            "border-color": "#00e676",
            "border-width": "3px",
            "border-style": "solid",
        }
    },
    {
        "selector": ".quiz-shaky",
        "style": {
            "border-color": "#ffd740",
            "border-width": "3px",
            "border-style": "dashed",
        }
    },
    {
        "selector": ".quiz-weak",
        "style": {
            "border-color": "#ff1744",
            "border-width": "3px",
            "border-style": "dashed",
        }
    },
    # ── SRS due — pulsing white ring ────────────────────────────────────────
    {
        "selector": ".srs-due",
        "style": {
            "border-color": "#ffffff",
            "border-width": "3px",
            "border-style": "dotted",
        }
    },
    # ── Edges — hidden connectors ───────────────────────────────────────────
    {
        "selector": "edge",
        "style": {
            "width": 0,
            "opacity": 0,
            "line-color": "transparent",
            "target-arrow-shape": "none",
        }
    },
    {
        "selector": ".edge-hidden",
        "style": {
            "width": 0,
            "opacity": 0,
        }
    },
    {
        "selector": ".edge-coral",
        "style": {
            "width": 48,
            "opacity": 0.60,
            "line-color": "#ff6d00",
            "target-arrow-shape": "none",
            "line-cap": "round",
        }
    },
    # ── Emoji phantom nodes ─────────────────────────────────────────────────
    {
        "selector": ".reef-emoji",
        "style": {
            "label": "data(label)",
            "text-valign": "center",
            "text-halign": "center",
            "font-size": "18px",
            "width": "24px",
            "height": "24px",
            "background-color": "transparent",
            "background-opacity": 0,
            "border-width": 0,
            "text-outline-width": 0,
            "opacity": 0.85,
        }
    },
    {
        "selector": ".reef-emoji-visited",
        "style": {
            "label": "data(label)",
            "text-valign": "center",
            "text-halign": "center",
            "font-size": "20px",
            "width": "24px",
            "height": "24px",
            "background-color": "transparent",
            "background-opacity": 0,
            "border-width": 0,
            "text-outline-width": 0,
            "opacity": 1.0,
        }
    },
    # ── Hover ───────────────────────────────────────────────────────────────
    {
        "selector": "node:active",
        "style": {
            "overlay-color": "#ffd54f",
            "overlay-padding": "6px",
            "overlay-opacity": 0.25,
        }
    },
]
