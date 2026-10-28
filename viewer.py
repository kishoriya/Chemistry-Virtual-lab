"""Interactive 3D viewer (py3Dmol) styled for the dark theme.

Replaces the original ``display_3d_structure`` (white background, fixed size)
with a dark, spin-able, label-able version. The 3D geometry itself still comes
from ``core.chem.generate_3d_molecule``.
"""
import py3Dmol
import streamlit as st
import streamlit.components.v1 as components
from rdkit import Chem

VIEW_STYLES = ["Ball and Stick", "Stick", "Space Filling", "Wireframe"]

# Slightly brighter, navy-friendly element colours (Jmol-like, tuned for dark).
_COLORS = {
    "C": "#6ee7d8",
    "H": "#e6edf8",
    "O": "#ff6b81",
    "N": "#7aa2ff",
    "S": "#ffd166",
    "P": "#ffa94d",
    "F": "#9be564",
    "Cl": "#4ade80",
    "Br": "#d9843b",
    "I": "#b07cff",
}


def _style_spec(style):
    if style == "Stick":
        return {"stick": {"radius": 0.2, "colorscheme": {"prop": "elem", "map": _COLORS}}}
    if style == "Space Filling":
        return {"sphere": {"scale": 1.0, "colorscheme": {"prop": "elem", "map": _COLORS}}}
    if style == "Wireframe":
        return {"line": {"linewidth": 2, "colorscheme": {"prop": "elem", "map": _COLORS}}}
    # Ball and Stick (default)
    return {
        "stick": {"radius": 0.15, "colorscheme": {"prop": "elem", "map": _COLORS}},
        "sphere": {"scale": 0.3, "colorscheme": {"prop": "elem", "map": _COLORS}},
    }


def build_3d_html(mol3d, style="Ball and Stick", show_surface=False, spin=False,
                  show_labels=False, height=520):
    """Return the HTML for a dark py3Dmol viewer of ``mol3d``."""
    mol_block = Chem.MolToMolBlock(mol3d)
    view = py3Dmol.view(width="100%", height=height)
    view.addModel(mol_block, "mol")
    view.setStyle(_style_spec(style))

    if show_surface:
        view.addSurface(py3Dmol.VDW, {"opacity": 0.55, "color": "#38d6f5"})

    if show_labels:
        for atom in mol3d.GetAtoms():
            if atom.GetAtomicNum() == 1:
                continue
            pos = mol3d.GetConformer().GetAtomPosition(atom.GetIdx())
            view.addLabel(
                atom.GetSymbol(),
                {
                    "position": {"x": pos.x, "y": pos.y, "z": pos.z},
                    "fontColor": "#ffffff",
                    "fontSize": 13,
                    "backgroundColor": "#0b1330",
                    "backgroundOpacity": 0.65,
                    "borderThickness": 0,
                    "inFront": True,
                },
            )

    view.setBackgroundColor("#080f24")
    view.zoomTo()
    if spin:
        view.spin("y", 0.6)
    return view._make_html()


def display_3d_structure(mol3d, style="Ball and Stick", show_surface=False,
                         spin=False, show_labels=False, height=520):
    """Render the viewer inside Streamlit."""
    html = build_3d_html(mol3d, style, show_surface, spin, show_labels, height)
    wrapped = (
        '<div style="border:1px solid #22305a;border-radius:14px;overflow:hidden;'
        'background:#080f24;box-shadow:0 0 32px rgba(56,214,245,.10)">'
        + html
        + "</div>"
    )
    if hasattr(st, "iframe"):  # newer Streamlit
        st.iframe(wrapped, height=height + 12)
    else:  # older Streamlit
        components.html(wrapped, height=height + 12)
