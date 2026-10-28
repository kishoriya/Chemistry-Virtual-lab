"""Session state, cached chemistry helpers and SMILES diagnostics."""
import streamlit as st
from rdkit import Chem

from core.chem import (
    EXAMPLE_MOLECULES,
    get_molecule,
    calculate_properties,
    generate_3d_molecule,
)

MAX_RECENT = 8
MAX_HEAVY_ATOMS_3D = 120
DEFAULT_SMILES = "CC(=O)Oc1ccccc1C(=O)O"  # aspirin: a rich first impression

PAGES = {
    "home": "Home",
    "lab": "Lab",
    "compare": "Compare",
    "groups": "Functional groups",
    "charts": "Property charts",
    "theory": "Theory",
    "assessment": "Assessment",
    "reports": "Reports",
    "final": "Final project report",
}


def init_state():
    ss = st.session_state
    ss.setdefault("smiles", DEFAULT_SMILES)
    ss.setdefault("recent", [])
    ss.setdefault("tutor_history", {})
    ss.setdefault("pdf_cache", {})
    if "page" not in ss:
        wanted = st.query_params.get("page", "home")
        ss.page = wanted if wanted in PAGES else "home"


# ---------------------------------------------------------------- navigation
def go(page):
    """Callback: navigate to ``page``."""
    st.session_state.page = page
    try:
        st.query_params["page"] = page
    except Exception:
        pass


# ------------------------------------------------------------------ molecule
def set_molecule(smiles):
    """Make ``smiles`` the active molecule everywhere (callback-safe)."""
    st.session_state.smiles = smiles
    st.session_state["smiles_input"] = smiles


def on_smiles_typed():
    st.session_state.smiles = st.session_state.get("smiles_input", "")


def on_example_chosen():
    name = st.session_state.get("example_choice")
    if name in EXAMPLE_MOLECULES:
        set_molecule(EXAMPLE_MOLECULES[name])


def load_recent(smiles):
    set_molecule(smiles)


@st.cache_data(show_spinner=False, max_entries=256)
def cached_properties(smiles):
    """Real RDKit properties for ``smiles`` (``None`` if invalid)."""
    mol = get_molecule(smiles)
    if mol is None:
        return None
    return calculate_properties(mol)


@st.cache_resource(show_spinner=False, max_entries=64)
def cached_3d(smiles):
    """3D conformer (ETKDG + force-field) for ``smiles``; ``None`` on failure."""
    mol = get_molecule(smiles)
    if mol is None:
        return None
    return generate_3d_molecule(mol)


def canonical_of(mol):
    return Chem.MolToSmiles(mol)


def molecule_name(canonical):
    for name, smi in EXAMPLE_MOLECULES.items():
        m = Chem.MolFromSmiles(smi)
        if m is not None and Chem.MolToSmiles(m) == canonical:
            return name
    return None


def register_recent(smiles, mol, props):
    """Remember a valid molecule (session only; nothing is stored on disk)."""
    canonical = canonical_of(mol)
    recent = [r for r in st.session_state.recent if r["canonical"] != canonical]
    recent.insert(
        0,
        {
            "smiles": smiles,
            "canonical": canonical,
            "name": molecule_name(canonical),
            "formula": props["Molecular Formula"],
        },
    )
    st.session_state.recent = recent[:MAX_RECENT]


def clear_recent():
    st.session_state.recent = []


# --------------------------------------------------------------- diagnostics
def diagnose_smiles(text):
    """Return plausible reasons a SMILES failed to parse (hints, not certainties)."""
    hints = []
    s = (text or "").strip()
    if not s:
        return ["The input is empty."]
    if any(c.isspace() for c in s):
        hints.append("It contains spaces. A SMILES string is a single word with no spaces.")
    if s.count("(") != s.count(")"):
        hints.append("Parentheses are unbalanced. Every “(” needs a matching “)”.")
    if s.count("[") != s.count("]"):
        hints.append("Square brackets are unbalanced. Every “[” needs a matching “]”.")
    digits = [c for c in s if c.isdigit()]
    if digits:
        counts = {}
        for d in digits:
            counts[d] = counts.get(d, 0) + 1
        if "[" not in s and any(v % 2 for v in counts.values()):
            hints.append("A ring-closure digit is used an odd number of times. Ring digits must come in pairs.")
    if not hints:
        hints.append(
            "Check atom symbols (use C, N, O, Cl, Br…), bond symbols (=, #) and valences, "
            "for example C(=O)(=O)(=O) gives carbon too many bonds."
        )
    return hints
