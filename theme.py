"""Visual theme: dark navy with cyan / teal / violet accents.

All colours are defined once as CSS variables. Text/background pairs were chosen
for WCAG AA contrast (body text #e6edf8 on #0e1730 is about 14:1, muted text
#9fb0d0 on #0e1730 is about 7:1).
"""
import html

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --bg: #070d1f;
  --bg-2: #0a1228;
  --surface: #0e1730;
  --surface-2: #131f3d;
  --border: #22305a;
  --border-strong: #34467f;
  --ink: #e6edf8;
  --muted: #9fb0d0;
  --cyan: #38d6f5;
  --teal: #2dd4bf;
  --violet: #a78bfa;
  --amber: #fbbf24;
  --rose: #fb7185;
  --glow-c: 0 0 0 1px rgba(56,214,245,.35), 0 0 28px rgba(56,214,245,.14);
  --radius: 14px;
  --font: 'Manrope', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

/* ---------- App shell ---------- */
html, body, .stApp, [data-testid="stAppViewContainer"] {
  font-family: var(--font);
  color: var(--ink);
}
.stApp {
  background:
    radial-gradient(1100px 520px at 88% -8%, rgba(167,139,250,.14), transparent 60%),
    radial-gradient(900px 480px at 6% -4%, rgba(56,214,245,.12), transparent 60%),
    var(--bg);
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; height: 0; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1320px; }
h1, h2, h3, h4 { font-family: var(--font); letter-spacing: -0.015em; color: var(--ink); }
p, li, label, span, div { font-family: var(--font); }
code, pre, kbd, .mono { font-family: var(--mono) !important; }
a { color: var(--cyan); }
hr { border-color: var(--border) !important; }
::selection { background: rgba(56,214,245,.35); }

/* ---------- Keyboard focus (visible everywhere) ---------- */
button:focus-visible, input:focus-visible, textarea:focus-visible,
[role="tab"]:focus-visible, [data-baseweb="select"]:focus-within,
summary:focus-visible, a:focus-visible {
  outline: 2px solid var(--cyan) !important;
  outline-offset: 2px !important;
  box-shadow: 0 0 0 4px rgba(56,214,245,.18) !important;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0a1330 0%, #070d1f 100%);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container, [data-testid="stSidebarContent"] { padding-top: 1rem; }
.brand { display:flex; align-items:center; gap:.7rem; margin: .2rem 0 1.1rem; }
.brand-mark {
  width: 38px; height: 38px; border-radius: 11px; display:grid; place-items:center;
  background: linear-gradient(135deg, rgba(56,214,245,.22), rgba(167,139,250,.22));
  border: 1px solid var(--border-strong); box-shadow: var(--glow-c); font-size: 20px;
}
.brand-name { font-weight: 800; font-size: 1.02rem; line-height: 1.1; }
.brand-sub { color: var(--muted); font-size: .76rem; }
.nav-group { color: var(--muted); font-size: .78rem; font-weight: 600; margin: 1.1rem 0 .35rem .2rem; letter-spacing: .02em; }

/* nav buttons = secondary / primary buttons inside the sidebar */
[data-testid="stSidebar"] .stButton button {
  width: 100%; justify-content: flex-start; text-align: left;
  background: transparent; border: 1px solid transparent; color: var(--ink);
  padding: .5rem .75rem; border-radius: 10px; font-weight: 600; font-size: .92rem;
  transition: background .15s, border-color .15s;
}
[data-testid="stSidebar"] .stButton button:hover {
  background: rgba(56,214,245,.07); border-color: var(--border);
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
  background: linear-gradient(90deg, rgba(56,214,245,.16), rgba(167,139,250,.10));
  border-color: rgba(56,214,245,.45); color: #fff; box-shadow: var(--glow-c);
}
[data-testid="stSidebar"] .stButton button p { text-align: left; }
[data-testid="stSidebar"] .stButton button [data-testid="stMarkdownContainer"] { width: 100%; text-align: left; }
[data-testid="stSidebar"] .stButton button > div { width: 100%; justify-content: flex-start; }
.st-key-viewer-toggles [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: .5rem !important; }
.st-key-viewer-toggles [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
  min-width: 0 !important; flex: 1 1 0 !important; width: auto !important; }
.st-key-sb-recent .stButton button { font-family: var(--mono); font-size: .8rem; font-weight: 500; color: var(--muted); }
.sb-footer { color: var(--muted); font-size: .74rem; line-height: 1.5; margin-top: 1.2rem; }

/* ---------- Cards ---------- */
[class*="st-key-card"] {
  background: linear-gradient(180deg, var(--surface-2), var(--surface));
  border: 1px solid var(--border); border-radius: var(--radius);
  padding: 1.15rem 1.25rem 1.2rem;
  box-shadow: 0 10px 30px rgba(2,6,23,.35), inset 0 1px 0 rgba(255,255,255,.03);
}
[class*="st-key-card-glow"] { border-color: rgba(56,214,245,.38); box-shadow: var(--glow-c), 0 10px 30px rgba(2,6,23,.35); }
.card-title { font-weight: 700; font-size: 1.02rem; margin: 0 0 .15rem; }
.card-sub { color: var(--muted); font-size: .84rem; margin: 0 0 .8rem; }

/* ---------- Page header ---------- */
.page-head { margin: 0 0 1.3rem; }
.page-head h1 { font-size: clamp(1.6rem, 3.2vw, 2.3rem); font-weight: 800; margin: 0 0 .3rem; padding: 0; }
.page-head p { color: var(--muted); margin: 0; max-width: 70ch; font-size: 1rem; line-height: 1.55; }

/* ---------- Hero (home) ---------- */
.hero { padding: 1.2rem 0 .6rem; }
.hero h1 { font-size: clamp(2rem, 5vw, 3.4rem); font-weight: 800; line-height: 1.05; margin: 0 0 .8rem;
  background: linear-gradient(95deg, #e6edf8 20%, var(--cyan) 62%, var(--violet) 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent; padding: 0; }
.hero p.lead { color: var(--muted); font-size: 1.1rem; max-width: 62ch; line-height: 1.6; margin: 0 0 .4rem; }
.hero .inst { margin-bottom: 1.1rem; color: var(--ink); font-weight: 600; margin-top: .9rem; }
.hero .inst span { color: var(--muted); font-weight: 500; display:block; font-size: .9rem; }
.st-key-logo-plate [data-testid="stImage"] img { background: #f6f6f7; border-radius: 14px; padding: .5rem .7rem;
  border: 1px solid var(--border-strong); box-shadow: var(--glow-c); }
.st-key-logo-plate [data-testid="stCaptionContainer"], .st-key-logo-plate figcaption { text-align: center; }

/* ---------- Status chips ---------- */
.chip { display:inline-flex; align-items:center; gap:.4rem; padding:.28rem .7rem; border-radius:999px;
  font-size:.8rem; font-weight:600; border:1px solid var(--border); background: rgba(255,255,255,.03); color: var(--ink); }
.chip.ok { border-color: rgba(45,212,191,.55); color: #7ff0de; background: rgba(45,212,191,.09); }
.chip.warn { border-color: rgba(251,191,36,.55); color: #fcd978; background: rgba(251,191,36,.08); }
.chip.bad { border-color: rgba(251,113,133,.6); color: #fda4b1; background: rgba(251,113,133,.09); }
.chip.info { border-color: rgba(167,139,250,.55); color: #cbb9ff; background: rgba(167,139,250,.09); }

/* ---------- Molecule info panel ---------- */
.formula { font-size: clamp(1.8rem, 3vw, 2.4rem); font-weight: 800; letter-spacing: -.02em; margin: .1rem 0 .2rem; }
.formula sub { font-size: .55em; color: var(--cyan); }
.stat-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(132px, 1fr)); gap:.6rem; margin-top:.6rem; }
.stat { background: rgba(8,15,36,.6); border:1px solid var(--border); border-radius: 12px; padding:.65rem .8rem; }
.stat .k { color: var(--muted); font-size: .76rem; font-weight: 600; }
.stat .v { font-size: 1.28rem; font-weight: 700; margin-top: .1rem; font-variant-numeric: tabular-nums; }
.stat .u { color: var(--muted); font-size: .76rem; font-weight: 500; margin-left: .2rem; }
.stat.accent-c { border-color: rgba(56,214,245,.4); }
.stat.accent-v { border-color: rgba(167,139,250,.4); }
.stat.accent-t { border-color: rgba(45,212,191,.4); }
.kv { display:flex; justify-content: space-between; gap:1rem; padding:.45rem 0; border-bottom:1px solid var(--border); font-size:.9rem; }
.kv:last-child { border-bottom: 0; }
.kv .k { color: var(--muted); }
.kv .v { font-weight: 600; font-variant-numeric: tabular-nums; text-align:right; word-break: break-word; }
.smiles-label { color: var(--muted); font-size:.8rem; font-weight:600; margin:.7rem 0 .15rem; }

/* ---------- Message / error states ---------- */
.state { border-radius: 12px; padding: .9rem 1.1rem; border:1px solid var(--border); background: var(--surface); margin: .6rem 0; }
.state b { display:block; margin-bottom:.2rem; }
.state p, .state li { color: var(--muted); font-size: .92rem; margin: 0; line-height: 1.5; }
.state ul { margin: .4rem 0 0 1.1rem; padding: 0; }
.state.bad { border-color: rgba(251,113,133,.6); background: rgba(251,113,133,.07); }
.state.bad b { color: #fda4b1; }
.state.warn { border-color: rgba(251,191,36,.55); background: rgba(251,191,36,.07); }
.state.warn b { color: #fcd978; }
.state.empty { border-style: dashed; text-align: center; padding: 1.6rem 1rem; }
.state.ok { border-color: rgba(45,212,191,.5); background: rgba(45,212,191,.07); }
.state.ok b { color: #7ff0de; }

/* ---------- Tutor chat ---------- */
.msg { border-radius: 12px; padding: .7rem .9rem; margin: .45rem 0; font-size: .93rem; line-height: 1.55; white-space: pre-wrap; }
.msg.user { background: rgba(167,139,250,.12); border:1px solid rgba(167,139,250,.35); margin-left: 12%; }
.msg.bot { background: rgba(56,214,245,.07); border:1px solid rgba(56,214,245,.28); margin-right: 6%; }
.msg .who { display:block; color: var(--muted); font-size:.72rem; font-weight:700; margin-bottom:.2rem; }

/* ---------- Inputs ---------- */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {
  background: #0a1230 !important; border-color: var(--border) !important; border-radius: 10px !important;
}
[data-baseweb="input"]:hover, [data-baseweb="textarea"]:hover, [data-baseweb="select"] > div:hover { border-color: var(--border-strong) !important; }
input, textarea { color: var(--ink) !important; font-family: var(--mono) !important; }
.stTextInput label, .stTextArea label, .stSelectbox label, .stRadio label, .stCheckbox label, .stToggle label {
  color: var(--muted) !important; font-weight: 600; font-size: .85rem !important;
}
[data-testid="stWidgetLabel"] p { color: var(--muted); font-weight: 600; }

/* ---------- Buttons (main area) ---------- */
.main .stButton button, [data-testid="stMain"] .stButton button,
.stDownloadButton button, [data-testid="stFormSubmitButton"] button {
  border-radius: 10px; font-weight: 700; border: 1px solid var(--border-strong);
  background: linear-gradient(180deg, #17254a, #101b3a); color: var(--ink);
  transition: border-color .15s, box-shadow .15s, transform .05s;
}
[data-testid="stMain"] .stButton button:hover, .stDownloadButton button:hover,
[data-testid="stFormSubmitButton"] button:hover { border-color: var(--cyan); box-shadow: var(--glow-c); color:#fff; }
[data-testid="stMain"] .stButton button:active { transform: translateY(1px); }
[data-testid="stMain"] .stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"] {
  background: linear-gradient(90deg, #0fa3c4, #6d5bd0); border-color: rgba(56,214,245,.6); color:#fff;
}

/* ---------- Tabs, tables, expanders, metrics ---------- */
[data-baseweb="tab-list"] { gap: .3rem; border-bottom: 1px solid var(--border); }
[data-baseweb="tab"] { color: var(--muted) !important; font-weight: 600; padding: .5rem .9rem; }
[data-baseweb="tab"][aria-selected="true"] { color: var(--cyan) !important; }
[data-baseweb="tab-highlight"] { background-color: var(--cyan) !important; }
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
[data-testid="stExpander"] { border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }
[data-testid="stExpander"] summary { color: var(--ink); font-weight: 600; }
[data-testid="stMetric"] { background: var(--surface); border:1px solid var(--border); border-radius: 12px; padding:.7rem .9rem; }
[data-testid="stMetricLabel"] p { color: var(--muted); }
[data-testid="stCode"] pre, .stCodeBlock pre { background: #080f24 !important; border: 1px solid var(--border); border-radius: 10px; }
[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stImage"] img { border-radius: 12px; }
[class*="st-key-plate"] [data-testid="stImage"] img { background: #fff; border: 1px solid var(--border-strong); }

/* ---------- Responsive ---------- */
@media (max-width: 1000px) {
  .block-container { padding-left: 1.1rem; padding-right: 1.1rem; }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 1rem !important; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    min-width: 100% !important; flex: 1 1 100% !important; width: 100% !important;
  }
  .msg.user { margin-left: 4%; }
}
@media (max-width: 560px) {
  .block-container { padding-left: .85rem; padding-right: .85rem; padding-top: 1.4rem; }
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  [class*="st-key-card"] { padding: .9rem .9rem 1rem; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
"""


def inject_theme():
    st.markdown(CSS, unsafe_allow_html=True)


def esc(value):
    """HTML-escape any user-supplied value."""
    return html.escape(str(value), quote=True)


def page_header(title, subtitle):
    st.markdown(
        f'<div class="page-head"><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )


def state_box(kind, title, body_html):
    """kind: bad | warn | ok | empty | info. ``body_html`` must already be escaped."""
    st.markdown(
        f'<div class="state {kind}" role="{"alert" if kind in ("bad", "warn") else "status"}">'
        f"<b>{esc(title)}</b>{body_html}</div>",
        unsafe_allow_html=True,
    )


def formula_html(formula):
    """Render a molecular formula with subscripts (digits after letters/brackets)."""
    out, prev = [], ""
    for ch in formula:
        if ch.isdigit() and prev and (prev.isalpha() or prev in ")]"):
            out.append(f"<sub>{ch}</sub>")
        elif ch.isdigit() and prev.isdigit() and out and out[-1].startswith("<sub>"):
            out[-1] = out[-1].replace("</sub>", f"{ch}</sub>")
        else:
            out.append(esc(ch))
        prev = ch
    return "".join(out)


def stat_card(label, value, unit="", accent=""):
    cls = f"stat {accent}".strip()
    unit_html = f'<span class="u">{esc(unit)}</span>' if unit else ""
    return f'<div class="{cls}"><div class="k">{esc(label)}</div><div class="v">{esc(value)}{unit_html}</div></div>'
