"""Shared UI pieces: sidebar, molecule input bar, info panel, tutor panel."""
import os

import streamlit as st
from rdkit import Chem

from core.chem import EXAMPLE_MOLECULES, get_molecule, generate_2d_image
from core.charts import lipinski_summary
from core.functional_groups import find_functional_groups
from core import tutor
from ui import state
from ui.theme import esc, formula_html, stat_card, state_box

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NAV = [
    ("Workspace", [("home", "Home"), ("lab", "Lab"), ("compare", "Compare")]),
    ("Analysis", [("groups", "Functional groups"), ("charts", "Property charts")]),
    ("Learn", [("theory", "Theory"), ("assessment", "Assessment")]),
    ("Reports", [("reports", "Reports"), ("final", "Final project report")]),
]


# ------------------------------------------------------------------ sidebar
def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-mark" aria-hidden="true">⬡</div>'
            '<div><div class="brand-name">Virtual Lab</div>'
            '<div class="brand-sub">Cheminformatics</div></div></div>',
            unsafe_allow_html=True,
        )
        for group, items in NAV:
            st.markdown(f'<div class="nav-group">{esc(group)}</div>', unsafe_allow_html=True)
            for page_id, label in items:
                active = st.session_state.page == page_id
                st.button(
                    label,
                    key=f"nav_{page_id}",
                    type="primary" if active else "secondary",
                    on_click=state.go,
                    args=(page_id,),
                    width="stretch",
                    help=f"Open {label}",
                )

        st.markdown('<div class="nav-group">Recent molecules</div>', unsafe_allow_html=True)
        recent = st.session_state.recent
        if not recent:
            st.caption("Molecules you analyse appear here.")
        else:
            with st.container(key="sb-recent"):
                for i, item in enumerate(recent):
                    label = item["name"] or item["smiles"]
                    if len(label) > 24:
                        label = label[:23] + "…"
                    st.button(
                        f"{label}  ·  {item['formula']}",
                        key=f"recent_{i}",
                        on_click=_open_recent,
                        args=(item["smiles"],),
                        help=f"Load {item['smiles']} in the Lab",
                        width="stretch",
                    )
            st.button("Clear recent", key="clear_recent", on_click=state.clear_recent)

        with st.expander("Student details"):
            st.text_input("Student name", key="student_name")
            st.text_input("Registration number", key="registration_number")
            st.caption("Used on the PDF reports.")

        st.markdown(
            '<div class="sb-footer">SRM Institute of Science and Technology, Tiruchirappalli<br>'
            "Division of Chemistry · Dr. R. Subramanian</div>",
            unsafe_allow_html=True,
        )


def _open_recent(smiles):
    state.load_recent(smiles)
    state.go("lab")


# ------------------------------------------------------------ molecule input
def molecule_bar():
    """SMILES input + example loader. Returns (smiles, mol, props); mol is None if invalid."""
    if "smiles_input" not in st.session_state:
        st.session_state["smiles_input"] = st.session_state.smiles

    with st.container(key="card-input"):
        c1, c2 = st.columns([3, 1.4])
        with c1:
            st.text_input(
                "SMILES",
                key="smiles_input",
                on_change=state.on_smiles_typed,
                placeholder="Type a SMILES string, e.g. CCO",
                help="Press Enter to analyse. SMILES is a text notation for a structure.",
            )
        with c2:
            st.selectbox(
                "Example molecules",
                list(EXAMPLE_MOLECULES.keys()),
                index=None,
                placeholder="Load an example",
                key="example_choice",
                on_change=state.on_example_chosen,
            )

    smiles = st.session_state.smiles
    if not smiles.strip():
        state_box(
            "empty",
            "No molecule yet",
            "<p>Type a SMILES string above or load an example to begin.</p>",
        )
        return smiles, None, None

    mol = get_molecule(smiles)
    props = state.cached_properties(smiles) if mol is not None else None
    if mol is None or props is None:
        hints = "".join(f"<li>{esc(h)}</li>" for h in state.diagnose_smiles(smiles))
        state_box(
            "bad",
            "That SMILES could not be read",
            f"<p>“{esc(smiles)}” is not a valid structure. Possible causes:</p><ul>{hints}</ul>",
        )
        return smiles, None, None

    state.register_recent(smiles, mol, props)
    return smiles, mol, props


# --------------------------------------------------------------- info panel
def molecule_info_panel(smiles, mol, props):
    canonical = Chem.MolToSmiles(mol)
    name = state.molecule_name(canonical)
    with st.container(key="card-info"):
        st.markdown(
            f'<div class="card-title">{esc(name) if name else "Molecule information"}</div>'
            f'<div class="card-sub">Calculated with RDKit from the structure you entered.</div>'
            f'<div class="formula" aria-label="Molecular formula">{formula_html(props["Molecular Formula"])}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="smiles-label">Canonical SMILES</div>', unsafe_allow_html=True)
        st.code(canonical, language=None)
        if canonical != smiles.strip():
            st.markdown('<div class="smiles-label">Input SMILES</div>', unsafe_allow_html=True)
            st.code(smiles.strip(), language=None)

        grid = "".join(
            [
                stat_card("Molecular weight", f"{props['Molecular Weight']:.2f}", "g/mol", "accent-c"),
                stat_card("LogP", f"{props['LogP']:.2f}", "", "accent-v"),
                stat_card("TPSA", f"{props['TPSA']:.1f}", "Å²", "accent-t"),
                stat_card("H-bond donors", props["Hydrogen Bond Donors"]),
                stat_card("H-bond acceptors", props["Hydrogen Bond Acceptors"]),
                stat_card("Rotatable bonds", props["Rotatable Bonds"]),
                stat_card("Rings", props["Ring Count"]),
                stat_card("Heavy atoms", props["Heavy Atoms"]),
            ]
        )
        st.markdown(f'<div class="stat-grid">{grid}</div>', unsafe_allow_html=True)

        with st.expander("All calculated properties"):
            rows = "".join(
                f'<div class="kv"><span class="k">{esc(k)}</span><span class="v">{esc(v)}</span></div>'
                for k, v in props.items()
            )
            st.markdown(rows, unsafe_allow_html=True)


def structure_2d_card(mol, title="2D structure"):
    with st.container(key="card-2d"):
        st.markdown(f'<div class="card-title">{esc(title)}</div>', unsafe_allow_html=True)
        with st.container(key="plate-2d"):
            st.image(generate_2d_image(mol), width="stretch")


# -------------------------------------------------------------------- tutor
def tutor_panel(smiles, mol, props):
    canonical = Chem.MolToSmiles(mol)
    groups = find_functional_groups(mol)
    rows, violations = lipinski_summary(props)
    api_key = tutor.find_api_key()
    model = tutor.find_model() if api_key else None
    histories = st.session_state.tutor_history
    history = histories.setdefault(canonical, [])

    with st.container(key="card-glow-tutor"):
        st.markdown('<div class="card-title">AI chemistry tutor</div>', unsafe_allow_html=True)
        if api_key:
            st.markdown(
                f'<span class="chip ok">Claude connected · {esc(model)}</span>',
                unsafe_allow_html=True,
            )
            st.caption("Answers use your molecule’s calculated data. Check important facts against a textbook.")
        else:
            st.markdown('<span class="chip info">Built-in mode</span>', unsafe_allow_html=True)
            st.caption(
                "Answers come only from the calculated results for this molecule. "
                "To enable open-ended answers, add ANTHROPIC_API_KEY (see README)."
            )

        box = st.container(height=340, border=False)
        with box:
            if not history:
                st.markdown(
                    '<div class="state empty"><p>Ask about this molecule, or pick a question below.</p></div>',
                    unsafe_allow_html=True,
                )
            for item in history:
                cls = "user" if item["role"] == "user" else "bot"
                who = "You" if item["role"] == "user" else f"Tutor · {item['mode']}"
                st.markdown(
                    f'<div class="msg {cls}"><span class="who">{esc(who)}</span>{esc(item["content"])}</div>',
                    unsafe_allow_html=True,
                )

        with st.form(key=f"tutor_form_{abs(hash(canonical)) % 10**8}", clear_on_submit=True):
            question = st.text_input(
                "Your question",
                placeholder="e.g. Why is this molecule polar?",
            )
            ask = st.form_submit_button("Ask tutor", type="primary")

        st.caption("Suggested questions")
        for i, q in enumerate(tutor.SUGGESTED_QUESTIONS):
            if st.button(q, key=f"suggest_{i}_{abs(hash(canonical)) % 10**6}"):
                question, ask = q, True

        if ask:
            if not (question or "").strip():
                st.warning("Type a question first.")
            else:
                with st.spinner("Thinking…"):
                    text, mode, _ok = tutor.answer(
                        question,
                        smiles=smiles,
                        canonical=canonical,
                        props=props,
                        groups=groups,
                        lipinski_rows=rows,
                        violations=violations,
                        history=[(h["role"], h["content"]) for h in history],
                        api_key=api_key,
                        model=model,
                    )
                history.append({"role": "user", "content": question.strip(), "mode": mode})
                history.append({"role": "assistant", "content": text, "mode": mode})
                st.rerun()

        if history and st.button("Clear conversation", key="tutor_clear"):
            histories[canonical] = []
            st.rerun()
