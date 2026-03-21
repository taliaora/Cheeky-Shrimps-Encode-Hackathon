"""Runtime settings and presentation theme for the Cheeky Shrimps app."""

from copy import deepcopy

SETTINGS = {
    "app": {
        "title": "🦐 Cheeky Shrimps",
        "port": 8050,
    },
    "learning_map": {
        "spacing": 5.0,
        "radius_limit": 10.0,
        "physics": {
            "iterations": 100,
            "attraction": 0.02,
            "repulsion": 0.2,
        },
        "sizes": {
            "root_default": 120,
            "root_floor": 80,
            "node_default": 50,
            "node_breadth_bonus": 30,
        },
    },
    "llm": {
        "initial_branch_count": 4,
        "expansion_branch_count": 3,
        "recommendation_count": 4,
        "retry_seconds": 1.0,
    },
    "motion": {
        "explanation_toggle_ms": 700,
        "poll_interval_ms": 500,
        "submit_pulse_ms": 1200,
    },
    "theme": {
        "palette": {
            "sea": "#0a7a8a",
            "panel_glass": "rgba(0,80,100,0.4)",
            "text_main": "#ffffff",
            "text_soft": "#b8f0e8",
            "coral": "#ff6b35",
            "coral_dark": "#e05520",
            "coral_glow": "#ff9a6a",
            "depth": "rgba(0,60,80,0.5)",
            "reef_mid": "#0a4a5a",
            "reef_light": "#2a8a9a",
            "border": "rgba(255,255,255,0.2)",
            "void": "#000000",
            "shell": "#B87333",
            "foam": "#ffffff",
            "sand": "#F5DEB3",
        },
        "fonts": {
            "display": "'Fredoka One', 'Bubblegum Sans', 'Inter', system-ui, sans-serif",
            "body": "'Inter', 'Segoe UI', system-ui, sans-serif",
        },
        "icons": {
            "refresh": "\u21bb",
            "details": "\U0001F4DA",
            "submit": "↑",
        },
    },
}

COMPONENT_SKIN = {
    "buttons": {
        "common": {
            "border": "none",
            "cursor": "pointer",
            "transition": "all 0.2s ease",
        },
        "toolbar": {
            "padding": "7px 16px",
            "fontSize": "0.85em",
            "borderRadius": "8px",
            "backgroundColor": "rgba(0,180,160,0.1)",
            "border": "1px solid rgba(0,180,160,0.2)",
            "color": SETTINGS["theme"]["palette"]["text_main"],
            "letterSpacing": "0.02em",
            "fontWeight": "500",
        },
        "submit": {
            "position": "absolute",
            "right": "0.4em",
            "top": 0,
            "bottom": 0,
            "margin": "auto",
            "width": "1.9em",
            "height": "1.9em",
            "borderRadius": "50%",
            "backgroundColor": SETTINGS["theme"]["palette"]["coral"],
            "color": SETTINGS["theme"]["palette"]["foam"],
            "fontSize": "1.1em",
            "fontWeight": "700",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "boxShadow": "0 0 12px rgba(255,107,53,0.6)",
        },
        "tag": {
            "display": "inline-block",
            "background": "rgba(255,107,53,0.15)",
            "color": "#ffcc99",
            "borderRadius": "20px",
            "padding": "6px 16px",
            "margin": "0 6px 6px 0",
            "fontWeight": "500",
            "fontSize": "0.95em",
            "border": "1px solid rgba(255,107,53,0.35)",
            "backdropFilter": "blur(4px)",
        },
    },
    "inputs": {
        "search": {
            "padding": "14px 50px 14px 24px",
            "fontSize": "1.05em",
            "borderRadius": "50px",
            "backgroundColor": "rgba(0,80,100,0.5)",
            "border": "1px solid rgba(255,255,255,0.3)",
            "color": "#ffffff",
            "boxShadow": "0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.15)",
            "outline": "none",
            "width": "100%",
            "textAlign": "center",
            "boxSizing": "border-box",
            "backdropFilter": "blur(12px)",
            "letterSpacing": "0.01em",
        },
    },
    "layout": {
        "page": {
            "backgroundColor": SETTINGS["theme"]["palette"]["sea"],
            "backgroundImage": "linear-gradient(180deg, #0a9ab0 0%, #0a7a8a 40%, #0a5a6a 75%, #c8a96e 100%)",
            "minHeight": "100vh",
            "padding": "0 32px 80px 32px",
            "boxSizing": "border-box",
            "display": "flex",
            "flexDirection": "column",
            "fontFamily": SETTINGS["theme"]["fonts"]["display"],
        },
        "content": {
            "display": "flex",
            "flexDirection": "row",
            "alignItems": "flex-start",
            "flexGrow": 1,
            "gap": "24px",
            "marginBottom": "32px",
        },
        "map_panel": {
            "flex": "3 1 0%",
            "position": "relative",
            "minHeight": "700px",
            "borderRadius": "20px",
            "overflow": "visible",
            "border": "1px solid rgba(255,255,255,0.2)",
            "boxShadow": "0 8px 40px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
            "paddingBottom": "24px",
        },
        "side_column": {
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "stretch",
            "flex": "1 1 0%",
        },
        "glass_card": {
            "border": "1px solid rgba(255,255,255,0.2)",
            "padding": "20px",
            "backgroundColor": "rgba(0,60,80,0.55)",
            "backdropFilter": "blur(20px)",
            "WebkitBackdropFilter": "blur(20px)",
            "color": SETTINGS["theme"]["palette"]["text_main"],
            "borderRadius": "16px",
            "width": "350px",
            "maxWidth": "350px",
            "minWidth": "350px",
            "marginTop": "0px",
            "boxSizing": "border-box",
            "boxShadow": "0 4px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
        },
    },
    "graph": {
        "frame": {
            "flex": "3 1 0%",
            "position": "relative",
            "zIndex": 1,
        },
        "plotly": {
            "displayModeBar": False,
        },
    },
    "overlay": {
        "center_prompt": {
            "position": "absolute",
            "left": "50%",
            "top": "55%",
            "transform": "translate(-50%, -50%)",
            "zIndex": 10,
            "transition": "opacity 0.3s ease, transform 0.3s ease",
            "width": "100%",
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
        },
        "center_prompt_inner": {
            "position": "relative",
            "width": "21rem",
            "display": "flex",
            "alignItems": "center",
        },
    },
}

GUIDE_TEXT = """## 🦐 Welcome to Cheeky Shrimps

Time to upgrade your shrimp intelligence.

---

### Your Mission

1. **Pick a quest**  
   Type something you want to learn — e.g. *"Gauge theory"* or *"m6 RNA modifications"*.

2. **Get your map**  
   We generate a concept web around your topic — your learning battlefield.

3. **Reveal your gaps**  
   Click anything you don't fully understand.  
   Each click tells us: *"this is where I need help."*

4. **Level up your understanding**  
   The map adapts as you explore, guiding you through the exact concepts you're missing.

5. **Unlock clarity**  
   Once your path is mapped, get a personalised explanation built around what you know.

6. **Build your deck**  
   Generate flashcards for any concept and drill the details.

7. **Prove it**  
   Take a quiz to confirm the knowledge has actually landed.

---

### Under the hood

Every click shapes your learning profile:
- what you already have locked in
- what the explainer should skip
- what needs to be broken down next

---

### Controls

- 🔄 Refresh the explanation
- 📚 Switch between concise and detailed mode

---

### Pro tip

Start with the nodes that feel shakiest.  
That is how Cheeky Shrimps finds the sharpest path to understanding.

---

Ready? Dive in. 🌊
"""

PAGE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fredoka+One&family=Inter:wght@400;500;600;700&display=swap');

html, body {
    margin: 0; padding: 0; height: 100%; width: 100%;
    background: linear-gradient(180deg, #0a9ab0 0%, #0a7a8a 40%, #0a5a6a 75%, #c8a96e 100%);
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}
#_dash-root-content { height: 100%; }

body::before {
    content: ''; position: fixed; inset: -10% auto auto 50%;
    transform: translateX(-50%); width: 160%; height: 90%;
    background: conic-gradient(from -20deg at 50% 0%,
        transparent 0deg, rgba(255,255,220,0.07) 4deg, transparent 8deg,
        rgba(255,255,220,0.05) 13deg, transparent 17deg, rgba(255,255,220,0.08) 22deg,
        transparent 26deg, rgba(255,255,220,0.04) 31deg, transparent 35deg,
        rgba(255,255,220,0.07) 40deg, transparent 44deg, rgba(255,255,220,0.05) 49deg,
        transparent 53deg, rgba(255,255,220,0.06) 58deg, transparent 62deg, transparent 360deg);
    animation: lightRays 12s ease-in-out infinite alternate;
    pointer-events: none; z-index: 0;
}
body::after {
    content: ''; position: fixed; left: 0; bottom: 0; width: 100%; height: 120px;
    background: linear-gradient(180deg, transparent 0%, rgba(200,169,110,0.6) 40%, #c8a96e 100%);
    pointer-events: none; z-index: 0;
}
@keyframes lightRays {
    0%   { opacity: 0.7; transform: translateX(-50%) rotate(-3deg); }
    50%  { opacity: 1;   transform: translateX(-50%) rotate(0deg); }
    100% { opacity: 0.8; transform: translateX(-50%) rotate(3deg); }
}

.bubbles-layer {
    position: fixed; inset: auto 0 0 0; width: 100%; height: 100%;
    background-image:
        radial-gradient(circle, rgba(255,255,255,0.18) 2px, transparent 2px),
        radial-gradient(circle, rgba(255,255,255,0.12) 1px, transparent 1px),
        radial-gradient(circle, rgba(255,255,255,0.1)  3px, transparent 3px);
    background-size: 180px 220px, 120px 160px, 260px 300px;
    background-position: 20px 40px, 80px 120px, 150px 200px;
    animation: bubbleRise 20s linear infinite;
    pointer-events: none; z-index: 0;
}
@keyframes bubbleRise {
    0%   { background-position: 20px 100%,  80px 100%,  150px 100%; }
    100% { background-position: 20px -300px, 80px -500px, 150px -400px; }
}

.seaweed-left, .seaweed-right {
    position: fixed; bottom: 0; pointer-events: none; z-index: 1;
    font-size: 3rem; line-height: 1;
    filter: drop-shadow(0 0 6px rgba(0,180,80,0.4));
}
.seaweed-left  { left: 1%; }
.seaweed-right { right: 1%; }
@keyframes seaweedSway {
    0%   { transform: rotate(-6deg) translateX(0); }
    50%  { transform: rotate(6deg)  translateX(4px); }
    100% { transform: rotate(-6deg) translateX(0); }
}
.seaweed-left  { animation: seaweedSway 4s ease-in-out infinite; transform-origin: bottom center; }
.seaweed-right { animation: seaweedSway 4s ease-in-out infinite reverse; transform-origin: bottom center; }

@keyframes shrimpA {
    0%   { transform: translate(0,0) rotate(-10deg) scaleX(1);  opacity: 0; }
    5%   { opacity: 0.7; }
    45%  { transform: translate(120px,-280px) rotate(15deg) scaleX(1);  opacity: 0.7; }
    50%  { transform: translate(130px,-300px) rotate(15deg) scaleX(-1); opacity: 0.7; }
    95%  { transform: translate(-20px,-10px)  rotate(-10deg) scaleX(-1); opacity: 0.7; }
    100% { transform: translate(0,0) rotate(-10deg) scaleX(1);  opacity: 0; }
}
@keyframes shrimpB {
    0%   { transform: translate(0,0) rotate(5deg) scaleX(-1);   opacity: 0; }
    8%   { opacity: 0.6; }
    40%  { transform: translate(-90px,-220px) rotate(-20deg) scaleX(-1); opacity: 0.6; }
    50%  { transform: translate(-100px,-240px) rotate(-20deg) scaleX(1); opacity: 0.6; }
    92%  { transform: translate(30px,-20px) rotate(5deg) scaleX(1);      opacity: 0.6; }
    100% { transform: translate(0,0) rotate(5deg) scaleX(-1);   opacity: 0; }
}
@keyframes shrimpC {
    0%   { transform: translate(0,0) rotate(-5deg) scaleX(1);  opacity: 0; }
    6%   { opacity: 0.65; }
    50%  { transform: translate(60px,-350px) rotate(25deg) scaleX(1);  opacity: 0.65; }
    55%  { transform: translate(65px,-360px) rotate(25deg) scaleX(-1); opacity: 0.65; }
    94%  { transform: translate(-10px,-5px)  rotate(-5deg) scaleX(-1); opacity: 0.65; }
    100% { transform: translate(0,0) rotate(-5deg) scaleX(1);  opacity: 0; }
}
@keyframes shrimpD {
    0%   { transform: translate(0,0) rotate(12deg) scaleX(-1);   opacity: 0; }
    7%   { opacity: 0.55; }
    48%  { transform: translate(-150px,-180px) rotate(-8deg) scaleX(-1); opacity: 0.55; }
    52%  { transform: translate(-155px,-190px) rotate(-8deg) scaleX(1);  opacity: 0.55; }
    93%  { transform: translate(10px,5px) rotate(12deg) scaleX(1);       opacity: 0.55; }
    100% { transform: translate(0,0) rotate(12deg) scaleX(-1);   opacity: 0; }
}
.shrimp {
    position: fixed; font-size: 1.8rem; pointer-events: none; z-index: 1;
    filter: drop-shadow(0 0 4px rgba(255,160,100,0.5));
}
.shrimp-1 { bottom: 12%; left: 8%;  animation: shrimpA 22s ease-in-out infinite; animation-delay: 0s; }
.shrimp-2 { bottom: 30%; left: 75%; animation: shrimpB 28s ease-in-out infinite; animation-delay: 6s; }
.shrimp-3 { bottom: 5%;  left: 45%; animation: shrimpC 25s ease-in-out infinite; animation-delay: 12s; }
.shrimp-4 { bottom: 55%; left: 20%; animation: shrimpD 32s ease-in-out infinite; animation-delay: 3s; }

@keyframes spinLoop { 100% { transform: rotate(360deg); } }
.spin-animation {
    animation: spinLoop 1s linear infinite; transform-origin: center;
    display: flex; align-items: center; justify-content: center;
}

.trim-mode-active, .trim-mode-active * {
    cursor: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'><text y='26' font-size='26'>✂️</text></svg>") 8 8, crosshair !important;
}
.trim-btn-active {
    background-color: rgba(255,80,80,0.25) !important;
    border-color: rgba(255,80,80,0.7) !important;
    color: #ff4444 !important;
    box-shadow: 0 0 10px rgba(255,80,80,0.4) !important;
}

.toggle-btn:hover  { transform: scale(1.15); opacity: 0.85; }
.reload-btn:hover  { transform: scale(1.15); opacity: 0.85; }
.submit-btn:hover  { transform: scale(1.08); box-shadow: 0 0 22px rgba(255,107,53,0.8) !important; }
.reload-btn:active { transform: scale(0.95); }
.toggle-btn:active { transform: scale(0.95); }
.submit-btn:active { transform: scale(0.95); }

input::placeholder { color: rgba(255,255,255,0.5); }
input:focus {
    border-color: rgba(255,255,255,0.6) !important;
    box-shadow: 0 0 0 3px rgba(255,255,255,0.15), 0 4px 24px rgba(0,0,0,0.3) !important;
}
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 2px; }
"""

HTML_PAGE = """<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <style>{styles}</style>
    </head>
    <body>
        <div class="bubbles-layer"></div>
        <div class="seaweed-left">🌿🌿🌿</div>
        <div class="seaweed-right">🌿🌿🌿</div>
        <div class="shrimp shrimp-1">🦐</div>
        <div class="shrimp shrimp-2">🦐</div>
        <div class="shrimp shrimp-3">🦐</div>
        <div class="shrimp shrimp-4">🦐</div>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>""".format(styles=PAGE_CSS)


def app_title() -> str:
    return SETTINGS["app"]["title"]

def default_port() -> int:
    return SETTINGS["app"]["port"]

def graph_settings() -> dict:
    g = SETTINGS["learning_map"]
    return {
        "base_spacing": g["spacing"],
        "target_radius": g["radius_limit"],
        "force_layout": {
            "iterations": g["physics"]["iterations"],
            "k_attract":  g["physics"]["attraction"],
            "k_repel":    g["physics"]["repulsion"],
        },
        "root_size_base":     g["sizes"]["root_default"],
        "root_size_min":      g["sizes"]["root_floor"],
        "node_size_base":     g["sizes"]["node_default"],
        "node_size_multiplier": g["sizes"]["node_breadth_bonus"],
    }

def llm_settings() -> dict:
    l = SETTINGS["llm"]
    return {
        "starter_terms":    l["initial_branch_count"],
        "further_terms":    l["expansion_branch_count"],
        "suggestion_terms": l["recommendation_count"],
        "retry_delay":      l["retry_seconds"],
    }

def motion_settings() -> dict:
    m = SETTINGS["motion"]
    return {
        "toggle_duration":      m["explanation_toggle_ms"],
        "reload_timer_interval": m["poll_interval_ms"],
        "submit_flash_duration": m["submit_pulse_ms"],
    }

def palette() -> dict:
    c = SETTINGS["theme"]["palette"]
    return {
        "background":       c["sea"],
        "secondary_bg":     c["panel_glass"],
        "text_primary":     c["text_main"],
        "text_secondary":   c["text_soft"],
        "accent_green":     c["coral"],
        "accent_green_dark": c["coral_dark"],
        "accent_green_glow": c["coral_glow"],
        "neutral_gray":     c["reef_mid"],
        "neutral_dark":     c["depth"],
        "neutral_medium":   c["reef_mid"],
        "neutral_light":    c["reef_light"],
        "border_color":     c["border"],
        "black":            c["void"],
        "brown":            c["shell"],
        "white":            c["foam"],
        "wheat":            c["sand"],
    }

def ui_styles() -> dict:
    return deepcopy(COMPONENT_SKIN)

def icons() -> dict:
    i = SETTINGS["theme"]["icons"]
    return {
        "reload":  i["refresh"],
        "toggle":  i["details"],
        "submit":  i["submit"],
    }

def help_markdown() -> str:
    return GUIDE_TEXT

def html_shell() -> str:
    return HTML_PAGE
