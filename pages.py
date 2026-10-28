"""All page renderers. Chemistry is always computed by the functions in ``core``."""
import os

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from rdkit import Chem
from rdkit.Chem import Draw

from core.chem import EXAMPLE_MOLECULES, get_molecule, calculate_properties
from core.charts import (
    lipinski_chart,
    lipinski_summary,
    logp_tpsa_scatter,
    property_bar_chart,
)
from core.functional_groups import FUNCTIONAL_GROUPS, find_functional_groups, highlighted_image
from core.reports import (
    generate_molecule_pdf,
    generate_multi_final_report,
)
from core.viewer import VIEW_STYLES, display_3d_structure
from ui import state
from ui.components import (
    APP_DIR,
    molecule_bar,
    molecule_info_panel,
    structure_2d_card,
    tutor_panel,
)
from ui.theme import esc, page_header, state_box

MAX_COMPARE = 12


def _show_fig(fig, caption=None):
    st.pyplot(fig, clear_figure=True, width="stretch")
    plt.close(fig)
    if caption:
        st.caption(caption)


def _open_in_lab(smiles):
    state.set_molecule(smiles)
    state.go("lab")


# ======================================================================= HOME
def home():
    c1, c2 = st.columns([1.5, 1], vertical_alignment="center")
    with c1:
        st.markdown(
            '<div class="hero"><h1>Cheminformatics Virtual Laboratory</h1>'
            '<p class="lead">Turn a SMILES string into a rotatable 3D model, calculated '
            "properties, functional-group analysis and a printable report. Every number is "
            "computed by RDKit from your structure.</p>"
            '<div class="inst">SRM Institute of Science and Technology, Tiruchirappalli'
            "<span>Faculty of Engineering and Technology · School of Sciences · Division of Chemistry</span></div></div>",
            unsafe_allow_html=True,
        )
        b1, b2, _ = st.columns([1, 1, 1.2])
        b1.button("Open the lab", type="primary", on_click=state.go, args=("lab",), key="home_lab")
        b2.button("Compare molecules", on_click=state.go, args=("compare",), key="home_compare")
    with c2:
        logo = os.path.join(APP_DIR, "srm_logo.jpeg")
        if os.path.exists(logo):
            with st.container(key="logo-plate"):
                st.image(logo, width="stretch", caption="SRM Institute of Science and Technology")

    st.markdown("### What you can do")
    features = [
        ("Lab", "lab", "Interactive 3D viewer, molecular information, 2D structure and an AI tutor for one molecule."),
        ("Compare", "compare", "Put several molecules side by side with a table, structures and charts."),
        ("Functional groups", "groups", "See which groups are present and highlighted on the structure."),
        ("Property charts", "charts", "Lipinski rule-of-five view and charts across your recent molecules."),
        ("Reports", "reports", "Download CSV, PNG, 3D MOL file and PDF reports."),
        ("Assessment", "assessment", "A 12-question quiz with explanations of every answer."),
    ]
    cols = st.columns(3)
    for i, (title, page, text) in enumerate(features):
        with cols[i % 3]:
            with st.container(key=f"card-feature-{page}"):
                st.markdown(f'<div class="card-title">{esc(title)}</div><div class="card-sub">{esc(text)}</div>',
                            unsafe_allow_html=True)
                st.button(f"Open {title.lower()}", key=f"feat_{page}", on_click=state.go, args=(page,))

    st.markdown("### Try an example molecule")
    ex_cols = st.columns(len(EXAMPLE_MOLECULES))
    for col, (name, smi) in zip(ex_cols, EXAMPLE_MOLECULES.items()):
        col.button(name, key=f"home_ex_{name}", on_click=_open_in_lab, args=(smi,), help=smi, width="stretch")

    st.divider()
    st.markdown(
        "**Developed by Dr. R. Subramanian**, Assistant Professor, Division of Chemistry, School of Sciences, "
        "Faculty of Engineering and Technology, SRM Institute of Science and Technology, Tiruchirappalli.  \n"
        "Queries: rsmani84@gmail.com"
    )


# ========================================================================= LAB
def lab():
    page_header("Lab", "Enter a structure, inspect it in 3D and ask the tutor about what you see.")
    smiles, mol, props = molecule_bar()
    if mol is None:
        return

    left, right = st.columns([1.55, 1])
    with left:
        with st.container(key="card-glow-viewer"):
            st.markdown('<div class="card-title">3D viewer</div>'
                        '<div class="card-sub">Drag to rotate, scroll to zoom. Geometry from ETKDG with force-field optimisation.</div>',
                        unsafe_allow_html=True)
            style = st.selectbox("Model", VIEW_STYLES, key="view_style")
            with st.container(key="viewer-toggles"):
                k2, k3, k4 = st.columns(3)
                surface = k2.toggle("Surface", key="view_surface")
                spin = k3.toggle("Spin", key="view_spin")
                labels = k4.toggle("Labels", key="view_labels")

            if mol.GetNumHeavyAtoms() > state.MAX_HEAVY_ATOMS_3D:
                state_box("warn", "Molecule too large for the 3D viewer",
                          f"<p>3D generation is limited to {state.MAX_HEAVY_ATOMS_3D} heavy atoms so the lab stays responsive. "
                          "The 2D structure and all properties are still available.</p>")
            else:
                with st.spinner("Generating 3D structure…"):
                    mol3d = state.cached_3d(smiles)
                if mol3d is None:
                    state_box("bad", "3D structure could not be generated",
                              "<p>RDKit could not find a 3D geometry for this molecule. "
                              "The 2D structure and properties are still shown.</p>")
                else:
                    display_3d_structure(mol3d, style, surface, spin, labels)
    with right:
        molecule_info_panel(smiles, mol, props)

    left2, right2 = st.columns([1, 1])
    with left2:
        structure_2d_card(mol)
        with st.container(key="card-lipinski"):
            rows, violations = lipinski_summary(props)
            chip = "ok" if violations == 0 else "warn"
            msg = "Meets all four rule-of-five limits" if violations == 0 else f"{violations} limit(s) exceeded"
            st.markdown(f'<div class="card-title">Lipinski rule of five</div><span class="chip {chip}">{msg}</span>',
                        unsafe_allow_html=True)
            _show_fig(lipinski_chart(props), "Each bar is the property as a percentage of its limit.")
    with right2:
        tutor_panel(smiles, mol, props)


# ===================================================================== COMPARE
def _parse_compare(text):
    entries, errors = [], []
    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if "," in line:
            name, smi = line.split(",", 1)
            name, smi = name.strip(), smi.strip()
        else:
            name, smi = f"Molecule {len(entries) + 1}", line
        mol = get_molecule(smi)
        if mol is None:
            errors.append((n, line))
            continue
        entries.append((name or smi, smi, mol))
    return entries, errors


COMPARE_DEFAULT = """Ethanol,CCO
Benzene,c1ccccc1
Phenol,Oc1ccccc1
Acetic Acid,CC(=O)O
Aspirin,CC(=O)Oc1ccccc1C(=O)O"""


def _save_compare():
    st.session_state.compare_saved = st.session_state.get("compare_input", "")


def _append_current():
    smi = st.session_state.smiles
    m = get_molecule(smi)
    if m is None:
        return
    name = state.molecule_name(Chem.MolToSmiles(m)) or "Current molecule"
    text = st.session_state.get("compare_input", st.session_state.get("compare_saved", COMPARE_DEFAULT))
    text = (text.rstrip("\n") + f"\n{name},{smi}").strip("\n")
    st.session_state.compare_saved = text
    st.session_state["compare_input"] = text


def compare():
    page_header("Compare", "Enter one molecule per line as Name,SMILES, or just a SMILES string.")
    st.session_state.setdefault("compare_saved", COMPARE_DEFAULT)
    with st.container(key="card-compare-input"):
        st.text_area(
            "Molecules",
            value=st.session_state.compare_saved,
            key="compare_input",
            height=170,
            on_change=_save_compare,
            help="Press Ctrl+Enter (or click outside the box) to apply changes.",
        )
        st.button("Add the current molecule", on_click=_append_current, key="cmp_add")

    entries, errors = _parse_compare(st.session_state.get("compare_input", st.session_state.compare_saved))
    if errors:
        items = "".join(f"<li>Line {n}: {esc(line)}</li>" for n, line in errors)
        state_box("bad", f"{len(errors)} line(s) could not be read and were skipped", f"<ul>{items}</ul>")
    if not entries:
        state_box("empty", "Nothing to compare yet", "<p>Enter at least one valid molecule above.</p>")
        return
    if len(entries) > MAX_COMPARE:
        state_box("warn", f"Showing the first {MAX_COMPARE} molecules", "<p>More than that makes the charts hard to read.</p>")
        entries = entries[:MAX_COMPARE]

    rows = []
    for name, smi, mol in entries:
        p = calculate_properties(mol)
        _, viol = lipinski_summary(p)
        rows.append({
            "Molecule": name, "Formula": p["Molecular Formula"], "MW": p["Molecular Weight"],
            "LogP": p["LogP"], "TPSA": p["TPSA"], "HBD": p["Hydrogen Bond Donors"],
            "HBA": p["Hydrogen Bond Acceptors"], "Rotatable Bonds": p["Rotatable Bonds"],
            "Ring Count": p["Ring Count"], "Lipinski violations": viol,
        })
    df = pd.DataFrame(rows)

    t1, t2, t3 = st.tabs(["Table", "Structures", "Charts"])
    with t1:
        st.dataframe(df, hide_index=True, width="stretch")
        st.download_button("Download comparison (CSV)", df.to_csv(index=False).encode("utf-8"),
                           "structure_property_comparison.csv", "text/csv", key="cmp_csv")
    with t2:
        img = Draw.MolsToGridImage([m for _, _, m in entries], molsPerRow=3, subImgSize=(300, 240),
                                   legends=[n for n, _, _ in entries])
        with st.container(key="plate-compare"):
            st.image(img, width="stretch")
    with t3:
        metric = st.selectbox("Property", ["MW", "LogP", "TPSA", "HBD", "HBA", "Rotatable Bonds", "Ring Count"], key="cmp_metric")
        unit = {"MW": "(g/mol)", "TPSA": "(Å²)"}.get(metric, "")
        c1, c2 = st.columns(2)
        with c1:
            _show_fig(property_bar_chart(df, metric, unit), f"{metric} for each molecule.")
        with c2:
            if len(df) >= 2:
                _show_fig(logp_tpsa_scatter(df), "Each point is one molecule, labelled directly.")
            else:
                state_box("empty", "Add a second molecule", "<p>The LogP vs TPSA plot needs at least two molecules.</p>")


# ================================================================ FUNCTIONAL GROUPS
def groups():
    page_header("Functional groups", "Substructure matching with SMARTS patterns shows which groups are in your molecule.")
    smiles, mol, props = molecule_bar()
    if mol is None:
        return
    found = find_functional_groups(mol)
    left, right = st.columns([1, 1])
    with left:
        with st.container(key="card-groups-img"):
            st.markdown('<div class="card-title">Highlighted structure</div>', unsafe_allow_html=True)
            options = ["All detected groups"] + [g["name"] for g in found]
            choice = st.selectbox("Highlight", options, key="grp_choice") if found else None
            if found:
                if choice not in options:
                    choice = options[0]
                atoms = sorted({a for g in found for a in g["atoms"]}) if choice == options[0] else \
                    next(g["atoms"] for g in found if g["name"] == choice)
            else:
                atoms = []
            with st.container(key="plate-groups"):
                st.image(highlighted_image(mol, atoms), width="stretch")
            st.caption("Highlighted atoms are the ones matched by the selected pattern.")
    with right:
        with st.container(key="card-groups-list"):
            st.markdown('<div class="card-title">Detected groups</div>', unsafe_allow_html=True)
            if not found:
                state_box("empty", "No tracked groups found",
                          "<p>This molecule has none of the functional groups this lab checks for (it may be a plain hydrocarbon).</p>")
            else:
                df = pd.DataFrame([{"Group": g["name"], "Count": g["count"], "What it is": g["note"]} for g in found])
                st.dataframe(df, hide_index=True, width="stretch")
                st.download_button("Download (CSV)", df.to_csv(index=False).encode("utf-8"),
                                   "functional_groups.csv", "text/csv", key="grp_csv")
        with st.expander("Patterns this lab checks"):
            ref = pd.DataFrame([{"Group": n, "SMARTS": s} for n, (s, _) in FUNCTIONAL_GROUPS.items()])
            st.dataframe(ref, hide_index=True, width="stretch")
    st.caption("Overlapping patterns can count the same atoms twice, for example an ester also contains a carbonyl.")


# ===================================================================== CHARTS
def charts():
    page_header("Property charts", "Drug-likeness for the current molecule and trends across your recent molecules.")
    smiles, mol, props = molecule_bar()
    if mol is None:
        return
    rows, violations = lipinski_summary(props)
    left, right = st.columns([1, 1])
    with left:
        with st.container(key="card-chart-lip"):
            chip = "ok" if violations == 0 else "warn"
            st.markdown(f'<div class="card-title">Lipinski rule of five</div>'
                        f'<span class="chip {chip}">{violations} of 4 limits exceeded</span>', unsafe_allow_html=True)
            _show_fig(lipinski_chart(props), "Bars show each property as a percentage of its limit; the dashed line is 100%.")
    with right:
        with st.container(key="card-chart-table"):
            st.markdown('<div class="card-title">Values</div>', unsafe_allow_html=True)
            table = pd.DataFrame([{"Property": r["label"], "Value": r["value"], "Limit": r["limit"],
                                   "Status": "OK" if r["ok"] else "Exceeds"} for r in rows])
            st.dataframe(table, hide_index=True, width="stretch")
            st.caption("The rule of five is a screening guide for oral drugs, not a verdict.")

    st.markdown("### Recent molecules")
    recent = st.session_state.recent
    if len(recent) < 2:
        state_box("empty", "Analyse a second molecule to compare",
                  "<p>Load another molecule and the charts below will compare everything you have analysed this session.</p>")
        return
    data = []
    for item in recent:
        p = state.cached_properties(item["smiles"])
        if p:
            data.append({"Molecule": item["name"] or item["formula"], "MW": p["Molecular Weight"],
                         "LogP": p["LogP"], "TPSA": p["TPSA"]})
    df = pd.DataFrame(data)
    c1, c2 = st.columns(2)
    with c1:
        _show_fig(property_bar_chart(df, "MW", "(g/mol)"), "Molecular weight of your recent molecules.")
    with c2:
        _show_fig(logp_tpsa_scatter(df), "LogP vs TPSA; marker size shows molecular weight.")
    st.dataframe(df, hide_index=True, width="stretch")


# ===================================================================== THEORY
def theory():
    page_header("Theory", "The ideas behind the lab, with a button to try each one.")
    with st.container(key="card-theory-1"):
        st.markdown("""
#### What is cheminformatics?
Cheminformatics combines chemistry, computer science and data analysis. It uses computational
techniques to store, process, visualise and analyse chemical information.
""")
    with st.container(key="card-theory-2"):
        st.markdown("""
#### SMILES
**S**implified **M**olecular **I**nput **L**ine **E**ntry **S**ystem represents a structure as text.

| Molecule | SMILES |
|---|---|
| Ethanol | `CCO` |
| Benzene | `c1ccccc1` |
| Acetic acid | `CC(=O)O` |
""")
        c1, c2, c3 = st.columns(3)
        for col, name in zip((c1, c2, c3), ("Ethanol", "Benzene", "Acetic Acid")):
            col.button(f"Open {name.lower()} in the lab", key=f"th_{name}", on_click=_open_in_lab,
                       args=(EXAMPLE_MOLECULES[name],))
    with st.container(key="card-theory-3"):
        st.markdown("""
#### Molecular descriptors
Numbers that describe a structure: molecular weight, LogP (lipophilicity), TPSA (polar surface area),
hydrogen-bond donors and acceptors, rotatable bonds and ring count.
""")
    with st.container(key="card-theory-4"):
        st.markdown("""
#### 3D molecular models
- **Ball and stick**: atoms as spheres, bonds as sticks.
- **Stick**: emphasises bonding.
- **Space filling**: approximate molecular volume.
- **Wireframe**: a simplified skeleton.
""")
    with st.container(key="card-theory-5"):
        st.markdown("""
#### Lipinski’s rule of five
A screening guide for oral drug-likeness: molecular weight ≤ 500, LogP ≤ 5, H-bond donors ≤ 5,
H-bond acceptors ≤ 10. The Lab and Property charts pages apply it to your molecule.
""")


# =================================================================== ASSESSMENT
QUESTIONS = [
    {"question": "What is the full form of SMILES?", "options": ["Simplified Molecular Input Line Entry System", "Standard Molecular Information Language Encoding System", "Simple Molecular Identification and Labeling System"], "answer": "Simplified Molecular Input Line Entry System"},
    {"question": "What does a SMILES string represent?", "options": ["A molecular structure using text", "A spectroscopy technique", "A laboratory instrument"], "answer": "A molecular structure using text"},
    {"question": "Which SMILES represents ethanol?", "options": ["CCO", "c1ccccc1", "CC(=O)O"], "answer": "CCO"},
    {"question": "Which SMILES represents benzene?", "options": ["c1ccccc1", "CCO", "O=C=O"], "answer": "c1ccccc1"},
    {"question": "In SMILES, parentheses are mainly used to indicate:", "options": ["Branches", "Molecular weight", "Atom colour"], "answer": "Branches"},
    {"question": "Which property is commonly associated with molecular lipophilicity?", "options": ["LogP", "TPSA", "HBD"], "answer": "LogP"},
    {"question": "What does TPSA describe?", "options": ["Topological Polar Surface Area", "Total Pi Surface Area", "Thermal Property Surface Analysis"], "answer": "Topological Polar Surface Area"},
    {"question": "What does HBA mean?", "options": ["Hydrogen Bond Acceptor", "Heavy Bond Atom", "Hydrogen Bond Analysis"], "answer": "Hydrogen Bond Acceptor"},
    {"question": "What does HBD mean?", "options": ["Hydrogen Bond Donor", "Heavy Bond Descriptor", "Hydrogen Bond Distance"], "answer": "Hydrogen Bond Donor"},
    {"question": "A double bond contains how many pi (π) bonds?", "options": ["1", "2", "0"], "answer": "1"},
    {"question": "A triple bond contains how many pi (π) bonds?", "options": ["2", "1", "3"], "answer": "2"},
    {"question": "Which model is useful for visualizing approximate molecular volume?", "options": ["Space Filling", "Wireframe only", "Text SMILES"], "answer": "Space Filling"},
]


def assessment():
    page_header("Assessment", "Twelve questions on SMILES, descriptors and molecular models. You see the answers after you submit.")
    with st.form("assessment_form"):
        answers = []
        for i, q in enumerate(QUESTIONS):
            answers.append(st.radio(f"{i + 1}. {q['question']}", q["options"], index=None, key=f"assessment_v2_{i}"))
        submitted = st.form_submit_button("Submit assessment", type="primary")

    if not submitted:
        return
    missing = [str(i + 1) for i, a in enumerate(answers) if a is None]
    if missing:
        state_box("warn", "Some questions are unanswered", f"<p>Answer question(s) {esc(', '.join(missing))} and submit again.</p>")
        return
    score = sum(a == q["answer"] for a, q in zip(answers, QUESTIONS))
    pct = score / len(QUESTIONS) * 100
    kind = "ok" if pct >= 80 else "warn" if pct < 50 else "ok"
    msg = ("Excellent work." if pct >= 80 else "Good. Keep practising." if pct >= 50
           else "Review the Theory page and try again.")
    state_box(kind, f"Score: {score}/{len(QUESTIONS)} ({pct:.0f}%)", f"<p>{msg}</p>")
    if pct >= 80:
        st.balloons()
    with st.expander("Review your answers", expanded=pct < 100):
        for i, (a, q) in enumerate(zip(answers, QUESTIONS), start=1):
            if a == q["answer"]:
                st.markdown(f"**{i}. {q['question']}**  \nCorrect: {q['answer']}")
            else:
                st.markdown(f"**{i}. {q['question']}**  \nYour answer: {a}  \nCorrect answer: **{q['answer']}**")


# ===================================================================== REPORTS
def _properties_csv(smiles, mol, props):
    data = [["Input SMILES", smiles], ["Canonical SMILES", Chem.MolToSmiles(mol)]]
    data += [[k, v] for k, v in props.items()]
    return pd.DataFrame(data, columns=["Property", "Value"])


def reports():
    page_header("Reports", "Download results for the current molecule. Files are generated from the same calculations you see in the lab.")
    smiles, mol, props = molecule_bar()
    if mol is None:
        return
    canonical = Chem.MolToSmiles(mol)
    df = _properties_csv(smiles, mol, props)

    c1, c2 = st.columns(2)
    with c1:
        with st.container(key="card-report-data"):
            st.markdown('<div class="card-title">Data files</div>'
                        '<div class="card-sub">Properties, structure image and 3D coordinates.</div>', unsafe_allow_html=True)
            st.download_button("Properties (CSV)", df.to_csv(index=False).encode("utf-8"),
                               "Molecular_Properties_Report.csv", "text/csv", key="rep_csv", width="stretch")
            buf = _png_bytes(mol)
            st.download_button("2D structure (PNG)", buf, "structure_2d.png", "image/png", key="rep_png", width="stretch")
            mol3d = state.cached_3d(smiles) if mol.GetNumHeavyAtoms() <= state.MAX_HEAVY_ATOMS_3D else None
            if mol3d is not None:
                st.download_button("3D structure (MOL file)", Chem.MolToMolBlock(mol3d), "structure_3d.mol",
                                   "chemical/x-mdl-molfile", key="rep_mol", width="stretch")
            else:
                st.caption("3D file unavailable: a 3D structure could not be generated for this molecule.")
    with c2:
        with st.container(key="card-report-pdf"):
            st.markdown('<div class="card-title">PDF report</div>'
                        '<div class="card-sub">Structure, descriptors and interpretations.</div>', unsafe_allow_html=True)
            cache = st.session_state.pdf_cache
            if st.button("Generate PDF report", key="rep_pdf_btn", type="primary"):
                with st.spinner("Building PDF…"):
                    try:
                        cache[canonical] = generate_molecule_pdf(smiles, mol, props)
                    except Exception as exc:  # report a clear error, never a fake file
                        st.session_state.pdf_error = f"{type(exc).__name__}: {exc}"
                        cache.pop(canonical, None)
                    else:
                        st.session_state.pdf_error = None
            if st.session_state.get("pdf_error"):
                state_box("bad", "The PDF could not be created", f"<p>{esc(st.session_state.pdf_error)}</p>")
            if canonical in cache:
                st.download_button("Download PDF", cache[canonical], "Molecular_Properties_Report.pdf",
                                   "application/pdf", key="rep_pdf_dl", width="stretch")
    st.caption("Looking for a multi-molecule student report? Use Final project report.")


def _png_bytes(mol):
    from io import BytesIO
    from core.chem import generate_2d_image
    buf = BytesIO()
    generate_2d_image(mol).save(buf, format="PNG")
    return buf.getvalue()


# ================================================================ FINAL REPORT
def final_report():
    page_header("Final project report", "Enter one SMILES per line. Every valid molecule goes into a single PDF.")
    name = st.text_input("Student name", value=st.session_state.get("student_name", ""), key="final_report_name")
    reg = st.text_input("Registration number", value=st.session_state.get("registration_number", ""), key="final_report_reg")

    st.session_state.setdefault("final_saved", st.session_state.smiles)
    def _save():
        st.session_state.final_saved = st.session_state.get("final_report_smiles_multi", "")
    text = st.text_area("SMILES (one molecule per line)", value=st.session_state.final_saved,
                        height=150, key="final_report_smiles_multi", on_change=_save,
                        help="Example: CCO on the first line, c1ccccc1 on the second.")

    records, invalid = [], []
    for item in [ln.strip() for ln in text.splitlines() if ln.strip()]:
        m = get_molecule(item)
        if m is None:
            invalid.append(item)
        else:
            records.append((item, m, calculate_properties(m)))
    if invalid:
        state_box("bad", "These lines could not be read and will be left out",
                  "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in invalid) + "</ul>")
    if not records:
        state_box("empty", "No valid molecules yet", "<p>Enter at least one valid SMILES to build the report.</p>")
        return
    st.markdown(f'<span class="chip ok">{len(records)} valid molecule(s)</span>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([{"No.": i, "Input SMILES": s, "Molecular formula": p["Molecular Formula"],
                                "Molecular weight (g/mol)": p["Molecular Weight"]}
                               for i, (s, _, p) in enumerate(records, start=1)]), hide_index=True, width="stretch")
    if not (name.strip() and reg.strip()):
        st.caption("Tip: add your name and registration number so they appear on the report.")
    if st.button("Generate combined PDF", type="primary", key="final_btn"):
        with st.spinner(f"Building one PDF for {len(records)} molecule(s)…"):
            try:
                st.session_state.final_pdf = generate_multi_final_report(name, reg, records)
                st.session_state.final_pdf_error = None
            except Exception as exc:
                st.session_state.final_pdf = None
                st.session_state.final_pdf_error = f"{type(exc).__name__}: {exc}"
    if st.session_state.get("final_pdf_error"):
        state_box("bad", "The PDF could not be created", f"<p>{esc(st.session_state.final_pdf_error)}</p>")
    elif st.session_state.get("final_pdf"):
        state_box("ok", "Report ready", "<p>Your combined report has been generated.</p>")
        st.download_button("Download combined report (PDF)", st.session_state.final_pdf,
                           "Cheminformatics_Multi_Molecule_Report.pdf", "application/pdf", key="final_dl")


PAGE_FUNCS = {
    "home": home, "lab": lab, "compare": compare, "groups": groups, "charts": charts,
    "theory": theory, "assessment": assessment, "reports": reports, "final": final_report,
}
