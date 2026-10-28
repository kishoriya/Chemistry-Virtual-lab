"""Dark-theme Matplotlib charts built from real RDKit descriptors."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE = "#0e1730"
INK = "#e6edf8"
MUTED = "#9fb0d0"
GRID = "#22305a"
# Validated for colour-blind separation on the navy surface (see README).
SERIES = ["#38d6f5", "#a78bfa", "#fbbf24", "#fb7185"]
GOOD = "#2dd4bf"
BAD = "#fb7185"

LIPINSKI_RULES = [
    # label, property key, limit, unit
    ("Molecular weight", "Molecular Weight", 500, "g/mol"),
    ("LogP", "LogP", 5, ""),
    ("H-bond donors", "Hydrogen Bond Donors", 5, ""),
    ("H-bond acceptors", "Hydrogen Bond Acceptors", 10, ""),
]


def _style(ax, fig):
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=10)
    ax.yaxis.label.set_color(MUTED)
    ax.xaxis.label.set_color(MUTED)
    ax.title.set_color(INK)
    ax.grid(axis="y", color=GRID, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def lipinski_summary(props):
    """Return (rows, violations). Rows use the real computed descriptors."""
    rows = []
    violations = 0
    for label, key, limit, unit in LIPINSKI_RULES:
        value = props[key]
        ok = value <= limit
        if not ok:
            violations += 1
        rows.append({"label": label, "value": value, "limit": limit, "unit": unit, "ok": ok})
    return rows, violations


def lipinski_chart(props):
    """Horizontal bars: each descriptor as a % of its Lipinski limit."""
    rows, _ = lipinski_summary(props)
    fig, ax = plt.subplots(figsize=(5.0, 2.8), dpi=150)
    _style(ax, fig)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=0.6, alpha=0.7)
    labels = [r["label"] for r in rows][::-1]
    pct = [max(r["value"], 0) / r["limit"] * 100 for r in rows][::-1]
    colours = [GOOD if r["ok"] else BAD for r in rows][::-1]
    bars = ax.barh(labels, pct, color=colours, height=0.5)
    ax.axvline(100, color=INK, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(100, len(rows) - 0.35, " limit", color=INK, fontsize=9, va="bottom")
    ax.set_xlim(0, max(130, max(pct) * 1.18))
    ax.set_xlabel("% of Lipinski limit")
    for bar, r in zip(bars, rows[::-1]):
        text = f"{r['value']:g} / {r['limit']:g}" + ("" if r["ok"] else "  exceeds")
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2, text,
                va="center", color=INK, fontsize=9)
    fig.tight_layout()
    return fig


def property_bar_chart(df, column, unit=""):
    """One bar per molecule for a single property. ``df`` has a 'Molecule' column."""
    fig, ax = plt.subplots(figsize=(5.0, 3.2), dpi=150)
    _style(ax, fig)
    bars = ax.bar(df["Molecule"], df[column], color=SERIES[0], width=0.55)
    for bar in bars:
        bar.set_linewidth(0)
    ax.axhline(0, color=GRID, linewidth=1)
    ax.set_ylabel(f"{column} {unit}".strip())
    top = max(df[column].max(), 0)
    ax.set_ylim(min(df[column].min() * 1.2, 0), top * 1.15 if top else 1)
    for bar, value in zip(bars, df[column]):
        y = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, y, f"{value:g}", ha="center",
                va="bottom" if y >= 0 else "top", color=INK, fontsize=9)
    plt.setp(ax.get_xticklabels(), rotation=25 if len(df) > 4 else 0,
             ha="right" if len(df) > 4 else "center")
    fig.tight_layout()
    return fig


def logp_tpsa_scatter(df):
    """LogP vs TPSA scatter with every molecule labelled directly."""
    fig, ax = plt.subplots(figsize=(5.0, 3.6), dpi=150)
    _style(ax, fig)
    ax.grid(axis="x", color=GRID, linewidth=0.6, alpha=0.7)
    sizes = [max(m, 20) * 0.9 for m in df["MW"]]
    ax.scatter(df["LogP"], df["TPSA"], s=sizes, color=SERIES[1], edgecolor=SURFACE,
               linewidth=1.5, alpha=0.95, zorder=3)
    for _, row in df.iterrows():
        ax.annotate(row["Molecule"], (row["LogP"], row["TPSA"]), xytext=(7, 6),
                    textcoords="offset points", color=INK, fontsize=9)
    ax.set_xlabel("LogP (lipophilicity)")
    ax.set_ylabel("TPSA (Å²)")
    ax.set_title("Marker size = molecular weight", fontsize=10, color=MUTED, loc="left")
    xr = df["LogP"].max() - df["LogP"].min()
    yr = df["TPSA"].max() - df["TPSA"].min()
    ax.set_xlim(df["LogP"].min() - max(xr * 0.15, 0.6), df["LogP"].max() + max(xr * 0.3, 0.9))
    ax.set_ylim(df["TPSA"].min() - max(yr * 0.15, 8), df["TPSA"].max() + max(yr * 0.2, 12))
    fig.tight_layout()
    return fig
