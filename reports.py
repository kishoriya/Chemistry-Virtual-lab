"""PDF / PNG report generation (moved unchanged from the original app.py)."""
from io import BytesIO
import tempfile
import os

from rdkit import Chem
from rdkit.Chem import Draw, AllChem, Descriptors, Crippen, Lipinski, rdMolDescriptors

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, Preformatted,
)
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader

from core.chem import (
    get_molecule, calculate_bond_information, calculate_properties,
    generate_2d_image, generate_3d_molecule,
)

def generate_molecule_pdf(
    input_smiles,
    mol,
    properties
):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=45,
        rightMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=20,
        alignment=TA_CENTER,
        textColor=HexColor("#17365D")
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading1"],
        fontSize=14,
        textColor=HexColor("#17365D")
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY
    )

    story = []

    story.append(
        Paragraph(
            "MOLECULAR PROPERTIES REPORT",
            title_style
        )
    )

    story.append(
        Spacer(1, 0.3 * inch)
    )

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "1. Molecular Information",
            heading_style
        )
    )

    canonical_smiles = Chem.MolToSmiles(mol)

    basic_data = [

        ["Property", "Value"],

        ["Input SMILES", input_smiles],

        ["Canonical SMILES", canonical_smiles],

        [
            "Molecular Formula",
            properties["Molecular Formula"]
        ]
    ]

    basic_table = Table(
        basic_data,
        colWidths=[2 * inch, 4 * inch]
    )

    basic_table.setStyle(
        TableStyle([

            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#17365D")),

            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

            ("VALIGN", (0, 0), (-1, -1), "TOP"),

            ("PADDING", (0, 0), (-1, -1), 7)

        ])
    )

    story.append(basic_table)

    story.append(
        Spacer(1, 0.3 * inch)
    )

    # --------------------------------------------------------
    # PROPERTY TABLE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "2. Molecular Properties",
            heading_style
        )
    )

    property_data = [
        ["Property", "Value"]
    ]

    for key, value in properties.items():

        property_data.append(
            [key, str(value)]
        )

    property_table = Table(
        property_data,
        colWidths=[3 * inch, 3 * inch],
        repeatRows=1
    )

    property_table.setStyle(
        TableStyle([

            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2F5597")),

            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

            ("VALIGN", (0, 0), (-1, -1), "TOP"),

            ("PADDING", (0, 0), (-1, -1), 6)

        ])
    )

    story.append(property_table)

    story.append(
        Spacer(1, 0.3 * inch)
    )

    story.append(
        Paragraph(
            "3. Interpretation",
            heading_style
        )
    )

    interpretation = """
    This report was generated automatically using the
    Cheminformatics Virtual Laboratory. The molecular properties
    were calculated from the chemical structure represented by
    the submitted SMILES notation using the RDKit cheminformatics
    toolkit.
    """

    story.append(
        Paragraph(
            interpretation,
            body_style
        )
    )

    # --------------------------------------------------------
    # BUILD PDF
    # --------------------------------------------------------

    doc.build(story)

    pdf_data = buffer.getvalue()

    buffer.close()

    return pdf_data


# ============================================================
# REPORT IMAGE HELPERS
# ============================================================

def save_2d_structure_png(mol):
    """Create a temporary PNG for inclusion in PDF reports."""
    img = Draw.MolToImage(mol, size=(700, 500))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.close()
    img.save(tmp.name)
    return tmp.name


def save_3d_structure_png(mol):
    """
    Create a high-clarity ball-and-stick image for the PDF report.

    The RDKit 3D coordinates are projected onto the best viewing plane so
    elongated molecules fill the page instead of appearing as a tiny object.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    mol3d = generate_3d_molecule(mol)
    if mol3d is None:
        return None

    conf = mol3d.GetConformer()
    n_atoms = mol3d.GetNumAtoms()

    # Collect 3D coordinates.
    coords = np.array([
        [
            conf.GetAtomPosition(i).x,
            conf.GetAtomPosition(i).y,
            conf.GetAtomPosition(i).z,
        ]
        for i in range(n_atoms)
    ], dtype=float)

    # Principal-component projection chooses the clearest overall view.
    centered = coords - coords.mean(axis=0)
    if n_atoms >= 3 and np.linalg.matrix_rank(centered) >= 2:
        _, _, vh = np.linalg.svd(centered, full_matrices=False)
        projected = centered @ vh[:2].T
    else:
        projected = centered[:, :2]

    # CPK-style colours and readable atom sizes.
    cpk = {
        "H": "#FFFFFF", "C": "#3F3F3F", "N": "#2F5BFF",
        "O": "#E53935", "F": "#65C466", "P": "#F39C12",
        "S": "#F4D03F", "Cl": "#27AE60", "Br": "#8E3B2F",
        "I": "#8E44AD",
    }
    sizes = {
        "H": 70, "C": 240, "N": 270, "O": 285, "F": 260,
        "P": 300, "S": 310, "Cl": 310, "Br": 330, "I": 350,
    }

    fig, ax = plt.subplots(figsize=(8.8, 6.4), facecolor="white")
    ax.set_facecolor("white")

    # Draw bonds first. Multiple bonds are shown with parallel lines.
    for bond in mol3d.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        x1, y1 = projected[i]
        x2, y2 = projected[j]

        dx, dy = x2 - x1, y2 - y1
        length = float(np.hypot(dx, dy))
        if length == 0:
            continue

        # Perpendicular direction for double/triple bond separation.
        px, py = -dy / length, dx / length
        btype = bond.GetBondType()
        if btype == Chem.BondType.DOUBLE:
            offsets = (-0.035, 0.035)
        elif btype == Chem.BondType.TRIPLE:
            offsets = (-0.055, 0.0, 0.055)
        else:
            offsets = (0.0,)

        for off in offsets:
            ax.plot(
                [x1 + px * off, x2 + px * off],
                [y1 + py * off, y2 + py * off],
                color="#707070", linewidth=3.0,
                solid_capstyle="round", zorder=1
            )

    # Draw atoms over bonds.
    for i, atom in enumerate(mol3d.GetAtoms()):
        symbol = atom.GetSymbol()
        x, y = projected[i]
        ax.scatter(
            x, y,
            s=sizes.get(symbol, 250),
            c=cpk.get(symbol, "#A0A0A0"),
            edgecolors="#222222",
            linewidths=1.0,
            zorder=3
        )

        # Label important/non-carbon hetero atoms only; this keeps the model clean.
        if symbol not in ("H", "C"):
            ax.text(
                x, y, symbol,
                ha="center", va="center",
                fontsize=8, fontweight="bold",
                color="black", zorder=4
            )

    # Tight, equal-aspect limits make the molecule large and clear.
    xmin, ymin = projected.min(axis=0)
    xmax, ymax = projected.max(axis=0)
    width = max(xmax - xmin, 1.0)
    height = max(ymax - ymin, 1.0)
    pad = 0.22 * max(width, height)

    ax.set_xlim(xmin - pad, xmax + pad)
    ax.set_ylim(ymin - pad, ymax + pad)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_title("3D Molecular Structure (Ball-and-Stick)", fontsize=18, fontweight="bold", pad=18)

    fig.tight_layout(pad=1.2)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.close()
    fig.savefig(
        tmp.name,
        dpi=320,
        bbox_inches="tight",
        facecolor="white",
        pad_inches=0.12
    )
    plt.close(fig)
    return tmp.name


# ============================================================
# PROPERTY INTERPRETATION HELPERS
# ============================================================

def get_property_interpretation(property_name, value, properties):
    """Return a student-friendly interpretation for each reported property."""

    if property_name == "Molecular Formula":
        return (
            "Shows the elemental composition of the molecule and is useful "
            "for understanding its basic chemical composition."
        )

    if property_name == "Molecular Weight":
        return (
            "Represents the average molecular mass. Molecular size and mass "
            "can influence diffusion, formulation and many physicochemical behaviours."
        )

    if property_name == "Exact Molecular Weight":
        return (
            "The monoisotopic mass calculated from exact isotopic masses; "
            "this is especially useful when comparing mass-spectrometry data."
        )

    if property_name == "LogP":
        if value < 0:
            return "A negative value indicates a preference toward the aqueous phase and relatively high hydrophilicity."
        elif value < 1:
            return "Indicates low to moderate lipophilicity, suggesting a reasonable preference for polar environments."
        elif value < 3:
            return "Indicates moderate lipophilicity, often reflecting a balance between hydrophilic and hydrophobic character."
        else:
            return "Indicates relatively high lipophilicity and a stronger preference for non-polar environments."

    if property_name == "TPSA":
        if value < 60:
            return "A relatively low polar surface area, indicating limited overall molecular polarity."
        elif value < 140:
            return "A moderate polar surface area, reflecting the contribution of heteroatoms to molecular polarity."
        else:
            return "A high polar surface area, indicating substantial polarity and strong hydrogen-bonding potential."

    if property_name == "Hydrogen Bond Donors":
        return (
            f"The molecule has {value} donor site(s) capable of donating hydrogen in hydrogen-bond interactions."
        )

    if property_name == "Hydrogen Bond Acceptors":
        return (
            f"The molecule has {value} acceptor site(s) capable of accepting hydrogen in hydrogen-bond interactions."
        )

    if property_name == "Rotatable Bonds":
        if value == 0:
            return "No freely rotatable bonds are detected, suggesting a relatively rigid molecular framework."
        return f"{value} rotatable bond(s) indicate conformational flexibility in the molecular structure."

    if property_name == "Ring Count":
        return f"The molecule contains {value} ring(s), which contribute to its overall shape and structural rigidity."

    if property_name == "Aromatic Rings":
        return f"{value} aromatic ring(s) contribute to aromaticity, planarity and delocalized π-electron character."

    if property_name == "Aliphatic Rings":
        return f"{value} non-aromatic ring(s) contribute to cyclic structure without aromatic π-electron delocalization."

    if property_name == "Number of Atoms":
        return "Counts atoms explicitly present in the RDKit molecular representation; implicit hydrogens are not included here."

    if property_name == "Heavy Atoms":
        return "Counts all non-hydrogen atoms and provides a useful measure of molecular structural size."

    if property_name == "Heavy Atom Bonds":
        return "Counts connections between non-hydrogen atoms in the molecular graph."

    if property_name == "Sigma (σ) Bonds":
        return "Every bonded atom pair contains one σ bond; this value includes bonds involving explicit or added hydrogens."

    if property_name == "Pi (π) Bonds":
        return "π bonds arise from multiple bonds and aromatic systems and are associated with electron delocalization."

    if property_name == "Total Bonds (σ + π)":
        return "Represents the total bond components obtained by adding the calculated σ and π bond counts."

    if property_name == "Fraction Csp3":
        if value < 0.25:
            return "A low sp³ fraction suggests a comparatively planar, unsaturated or aromatic structural character."
        elif value < 0.60:
            return "An intermediate sp³ fraction indicates a balance between saturated and unsaturated structural features."
        return "A high sp³ fraction indicates a more saturated, three-dimensional molecular framework."

    if property_name == "Molar Refractivity":
        return "Relates to molecular volume and electronic polarizability and reflects how the electron cloud responds to an electric field."

    return "This descriptor provides additional quantitative information about the molecular structure and physicochemical behaviour."


def build_key_interpretation_points(properties):
    """Create concise point-wise conclusions for the final report."""
    points = []

    points.append(
        f"<b>• Molecular identity:</b> The submitted structure has molecular formula "
        f"<b>{properties['Molecular Formula']}</b> and molecular weight "
        f"<b>{properties['Molecular Weight']}</b>."
    )

    logp = properties["LogP"]
    if logp < 0:
        lipophilic_text = "more hydrophilic than lipophilic"
    elif logp < 1:
        lipophilic_text = "low in lipophilicity"
    elif logp < 3:
        lipophilic_text = "moderately lipophilic"
    else:
        lipophilic_text = "strongly lipophilic"

    points.append(
        f"<b>• Lipophilicity:</b> LogP = <b>{logp}</b>, indicating that the molecule is "
        f"<b>{lipophilic_text}</b>. This descriptor describes the balance between "
        f"preference for non-polar and polar environments."
    )

    points.append(
        f"<b>• Molecular polarity:</b> TPSA = <b>{properties['TPSA']}</b> Å². "
        f"TPSA reflects the contribution of polar atoms and functional groups to the "
        f"overall surface polarity of the molecule."
    )

    points.append(
        f"<b>• Hydrogen bonding:</b> The structure contains "
        f"<b>{properties['Hydrogen Bond Donors']}</b> hydrogen-bond donor(s) and "
        f"<b>{properties['Hydrogen Bond Acceptors']}</b> acceptor(s), which helps "
        f"describe possible intermolecular interactions."
    )

    points.append(
        f"<b>• Flexibility:</b> {properties['Rotatable Bonds']} rotatable bond(s) "
        f"indicate the degree of conformational freedom available to the molecule."
    )

    points.append(
        f"<b>• Cyclic and aromatic character:</b> The molecule contains "
        f"{properties['Ring Count']} ring(s), including "
        f"{properties['Aromatic Rings']} aromatic ring(s). Aromatic rings are "
        f"associated with delocalized π-electron systems."
    )

    points.append(
        f"<b>• Bonding pattern:</b> The calculated structure contains "
        f"<b>{properties['Sigma (σ) Bonds']}</b> σ bonds and "
        f"<b>{properties['Pi (π) Bonds']}</b> π bonds. This helps distinguish the "
        f"framework-forming σ bonds from multiple-bond and delocalized π bonding."
    )

    points.append(
        f"<b>• Three-dimensional character:</b> Fraction Csp³ = "
        f"<b>{properties['Fraction Csp3']}</b>. This descriptor provides a simple "
        f"indication of the balance between saturated 3D carbon environments and "
        f"planar/unsaturated environments."
    )

    points.append(
        "<b>• Overall conclusion:</b> The calculated descriptors should be interpreted "
        "together with the 2D connectivity and generated 3D geometry to understand "
        "the molecule's composition, bonding, polarity, flexibility and structural character."
    )

    return points


# ============================================================
# GENERATE GENERAL FINAL PROJECT REPORT
# ============================================================

def generate_final_report(student_name, registration_number, input_smiles, mol, properties):
    """Generate a detailed personalized final report for the student's molecule."""

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=38,
        rightMargin=38,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ProjectTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=25,
        alignment=TA_CENTER,
        textColor=HexColor("#17365D")
    )

    heading_style = ParagraphStyle(
        "ProjectHeading",
        parent=styles["Heading1"],
        fontSize=14,
        leading=18,
        textColor=HexColor("#17365D"),
        spaceBefore=8,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "ProjectBody",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
        alignment=TA_JUSTIFY
    )

    small_style = ParagraphStyle(
        "SmallTableText",
        parent=styles["BodyText"],
        fontSize=7.5,
        leading=9.5
    )

    header_style = ParagraphStyle(
        "HeaderTableText",
        parent=styles["BodyText"],
        fontSize=8,
        leading=9,
        textColor=colors.white,
        alignment=TA_CENTER
    )

    story = []

    story += [
        Spacer(1, 0.25 * inch),
        Paragraph("CHEMINFORMATICS VIRTUAL LABORATORY", title_style),
        Spacer(1, 0.12 * inch),
        Paragraph("FINAL STUDENT MOLECULAR ANALYSIS REPORT", heading_style),
        Spacer(1, 0.18 * inch)
    ]

    student_data = [
        ["Student Name", student_name or "Not provided"],
        ["Registration Number", registration_number or "Not provided"],
        ["Input SMILES", input_smiles],
        ["Canonical SMILES", Chem.MolToSmiles(mol)],
        ["Molecular Formula", properties["Molecular Formula"]]
    ]

    student_table = Table(student_data, colWidths=[2.0 * inch, 4.7 * inch])
    student_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), HexColor("#EAF0F8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6)
    ]))

    story += [student_table, Spacer(1, 0.22 * inch)]

    # --------------------------------------------------------
    # 1. STRUCTURES
    # --------------------------------------------------------
    story.append(Paragraph("1. Molecular Structures", heading_style))

    img2d = save_2d_structure_png(mol)
    img3d = save_3d_structure_png(mol)

    if img2d and img3d:
        structure_table = Table(
            [[
                Image(img2d, width=3.15 * inch, height=2.25 * inch),
                Image(img3d, width=3.15 * inch, height=2.25 * inch)
            ]],
            colWidths=[3.3 * inch, 3.3 * inch]
        )

        structure_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER")
        ]))

        story += [
            structure_table,
            Spacer(1, 0.08 * inch),
            Paragraph(
                "<b>Figure 1.</b> Left: 2D molecular connectivity. "
                "Right: generated 3D ball-and-stick geometry showing the spatial arrangement of atoms.",
                body_style
            )
        ]

    elif img2d:
        story.append(Image(img2d, width=5.8 * inch, height=4.1 * inch))

    story += [Spacer(1, 0.18 * inch)]

    # --------------------------------------------------------
    # 2. COMPLETE PROPERTIES WITH INTERPRETATION COLUMN
    # --------------------------------------------------------
    story.append(Paragraph("2. Complete Molecular Properties and Interpretation", heading_style))

    prop_data = [[
        Paragraph("<b>Property</b>", header_style),
        Paragraph("<b>Value</b>", header_style),
        Paragraph("<b>Interpretation</b>", header_style)
    ]]

    for key, value in properties.items():
        interpretation = get_property_interpretation(key, value, properties)
        prop_data.append([
            Paragraph(str(key), small_style),
            Paragraph(str(value), small_style),
            Paragraph(interpretation, small_style)
        ])

    property_table = Table(
        prop_data,
        colWidths=[1.75 * inch, 1.0 * inch, 3.85 * inch],
        repeatRows=1
    )

    property_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2F5597")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4)
    ]))

    story += [property_table, Spacer(1, 0.18 * inch)]

    # --------------------------------------------------------
    # 3. POINT-WISE INTERPRETATION
    # --------------------------------------------------------
    story.append(Paragraph("3. Point-wise Molecular Interpretation", heading_style))

    intro = (
        "The following points summarize the most important structural and "
        "physicochemical features calculated from the student's submitted SMILES."
    )
    story.append(Paragraph(intro, body_style))
    story.append(Spacer(1, 0.08 * inch))

    for point in build_key_interpretation_points(properties):
        story.append(Paragraph(point, body_style))
        story.append(Spacer(1, 0.06 * inch))

    # --------------------------------------------------------
    # 4. LEARNING NOTE
    # --------------------------------------------------------
    story += [
        Spacer(1, 0.12 * inch),
        Paragraph("4. Learning Note", heading_style),
        Paragraph(
            "The numerical descriptors in this report are computationally calculated "
            "from the submitted molecular structure. They are useful for molecular "
            "comparison and cheminformatics learning, but experimental measurements "
            "may differ depending on conditions and methodology.",
            body_style
        )
    ]


    # --------------------------------------------------------
    # 5. PYTHON LIBRARIES AND THEIR IMPORTANCE
    # --------------------------------------------------------
    story += [
        Spacer(1, 0.12 * inch),
        Paragraph("5. Python Libraries Used and Their Importance", heading_style),
        Paragraph(
            "The virtual laboratory uses the following libraries to process "
            "molecular structures, calculate descriptors, display results and "
            "create this PDF report.",
            body_style
        ),
        Spacer(1, 0.08 * inch)
    ]

    library_rows = [
        [
            Paragraph("<b>Library</b>", header_style),
            Paragraph("<b>Importance in this project</b>", header_style)
        ],
        [
            Paragraph("Streamlit", small_style),
            Paragraph("Builds the interactive web application, input fields, navigation, "
                      "visualization controls and download buttons.", small_style)
        ],
        [
            Paragraph("RDKit (Chem, Descriptors, Crippen, Lipinski, rdMolDescriptors, Draw, AllChem)",
                      small_style),
            Paragraph("Reads SMILES, validates molecular structures, generates 2D drawings "
                      "and 3D coordinates, and calculates molecular formula, molecular weight, "
                      "LogP, TPSA, hydrogen-bond counts, ring counts and other descriptors.",
                      small_style)
        ],
        [
            Paragraph("Pandas", small_style),
            Paragraph("Organizes molecular properties into tables and supports CSV export.",
                      small_style)
        ],
        [
            Paragraph("Matplotlib", small_style),
            Paragraph("Creates a clear 2D projection of the generated 3D molecular geometry "
                      "for inclusion in the PDF report.", small_style)
        ],
        [
            Paragraph("NumPy", small_style),
            Paragraph("Processes 3D atomic coordinates and uses numerical linear algebra "
                      "to select a clear projection of the molecule.", small_style)
        ],
        [
            Paragraph("py3Dmol", small_style),
            Paragraph("Displays interactive 3D molecular models in the web application.",
                      small_style)
        ],
        [
            Paragraph("ReportLab", small_style),
            Paragraph("Creates the downloadable PDF, including student details, structures, "
                      "property tables, interpretations, code examples and library notes.",
                      small_style)
        ],
        [
            Paragraph("Python standard libraries: io, os, tempfile", small_style),
            Paragraph("Manage in-memory PDF data and temporary image files, and clean up "
                      "temporary files after report generation.", small_style)
        ]
    ]

    library_table = Table(
        library_rows,
        colWidths=[2.05 * inch, 4.65 * inch],
        repeatRows=1
    )
    library_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2F5597")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5)
    ]))
    story += [library_table, Spacer(1, 0.18 * inch)]

    # --------------------------------------------------------
    # 6. ILLUSTRATIVE PYTHON CODE
    # --------------------------------------------------------
    story.append(Paragraph("6. Python Code: SMILES to Molecular Properties", heading_style))
    story.append(Paragraph(
        "The following educational example shows the core workflow used by this "
        "laboratory. It is a compact example of the main calculation steps, not the "
        "complete Streamlit application source code.",
        body_style
    ))
    story.append(Spacer(1, 0.08 * inch))

    code_style = ParagraphStyle(
        "EducationalCode",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7,
        leading=8.5,
        leftIndent=5,
        rightIndent=5,
        spaceBefore=4,
        spaceAfter=4
    )

    educational_code = '''from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, Lipinski, rdMolDescriptors, Draw
from rdkit.Chem import AllChem

# 1. Convert a SMILES string into a molecular object
smiles = "CCO"  # Example: ethanol
mol = Chem.MolFromSmiles(smiles)

if mol is None:
    raise ValueError("Invalid SMILES notation")

# 2. Calculate selected molecular descriptors
formula = rdMolDescriptors.CalcMolFormula(mol)
molecular_weight = Descriptors.MolWt(mol)
logp = Crippen.MolLogP(mol)
tpsa = rdMolDescriptors.CalcTPSA(mol)
h_bond_donors = Lipinski.NumHDonors(mol)
h_bond_acceptors = Lipinski.NumHAcceptors(mol)

print("Formula:", formula)
print("Molecular weight:", round(molecular_weight, 3), "g/mol")
print("LogP:", round(logp, 3))
print("TPSA:", round(tpsa, 3), "A^2")
print("H-bond donors:", h_bond_donors)
print("H-bond acceptors:", h_bond_acceptors)

# 3. Save a 2D molecular structure image
Draw.MolToFile(mol, "molecule_2d.png", size=(700, 500))

# 4. Generate a 3D conformer (coordinates)
mol_3d = Chem.AddHs(mol)
status = AllChem.EmbedMolecule(mol_3d, randomSeed=42)
if status == 0:
    AllChem.MMFFOptimizeMolecule(mol_3d)
    print("3D coordinates generated successfully")'''

    story.append(Preformatted(educational_code, code_style, maxLineLength=92))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("How to read the code", heading_style))
    code_notes = [
        "<b>SMILES input:</b> A text representation of the molecular connectivity.",
        "<b>Validation:</b> <font name='Courier'>Chem.MolFromSmiles()</font> attempts to parse the input; "
        "an invalid structure returns <font name='Courier'>None</font>.",
        "<b>Descriptors:</b> RDKit functions calculate numerical properties from the parsed molecular graph.",
        "<b>2D drawing:</b> <font name='Courier'>Draw.MolToFile()</font> writes a molecular diagram to an image file.",
        "<b>3D geometry:</b> Explicit hydrogens are added, a conformer is generated, and MMFF optimization "
        "is attempted to refine its geometry."
    ]
    for note in code_notes:
        story.append(Paragraph("• " + note, body_style))
        story.append(Spacer(1, 0.04 * inch))

    # --------------------------------------------------------
    # 7. REPRODUCIBILITY NOTE
    # --------------------------------------------------------
    story += [
        Spacer(1, 0.10 * inch),
        Paragraph("7. Reproducibility and Limitations", heading_style),
        Paragraph(
            "This code is an educational illustration of the principal workflow. "
            "The web application contains additional functions for student inputs, "
            "property interpretation, 3D display and PDF formatting. Calculated "
            "descriptors are computational estimates and should be interpreted with "
            "their definitions and, where appropriate, compared with experimental data.",
            body_style
        )
    ]


    doc.build(story)

    pdf_data = buffer.getvalue()
    buffer.close()

    for path in [img2d, img3d]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    return pdf_data



# ============================================================
# GENERATE ONE PDF FOR MULTIPLE MOLECULES
# ============================================================

def generate_multi_final_report(student_name, registration_number, molecule_records):
    """Create one PDF containing results for every valid SMILES supplied."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=38, rightMargin=38,
        topMargin=40, bottomMargin=40
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "MultiReportTitle", parent=styles["Title"], fontSize=19,
        leading=23, alignment=TA_CENTER, textColor=HexColor("#17365D")
    )
    heading_style = ParagraphStyle(
        "MultiReportHeading", parent=styles["Heading1"], fontSize=13,
        leading=16, textColor=HexColor("#17365D"), spaceBefore=7, spaceAfter=7
    )
    body_style = ParagraphStyle(
        "MultiReportBody", parent=styles["BodyText"], fontSize=9,
        leading=12, alignment=TA_JUSTIFY
    )
    small_style = ParagraphStyle(
        "MultiReportSmall", parent=styles["BodyText"], fontSize=7.2, leading=8.8
    )
    header_style = ParagraphStyle(
        "MultiReportHeader", parent=styles["BodyText"], fontSize=7.5,
        leading=9, textColor=colors.white, alignment=TA_CENTER
    )
    story = [
        Spacer(1, 0.15 * inch),
        Paragraph("CHEMINFORMATICS VIRTUAL LABORATORY", title_style),
        Spacer(1, 0.08 * inch),
        Paragraph("MULTI-MOLECULE STUDENT ANALYSIS REPORT", heading_style),
        Paragraph(
            f"Student: {student_name or 'Not provided'} &nbsp;&nbsp;&nbsp; "
            f"Registration Number: {registration_number or 'Not provided'}",
            body_style
        ),
        Paragraph(f"Number of molecules analyzed: {len(molecule_records)}", body_style),
        Spacer(1, 0.15 * inch)
    ]

    temp_images = []
    for index, record in enumerate(molecule_records, start=1):
        input_smiles, mol, properties = record
        if index > 1:
            story.append(PageBreak())

        story.append(Paragraph(f"Molecule {index}: Molecular Information", heading_style))
        basic_data = [
            ["Input SMILES", input_smiles],
            ["Canonical SMILES", Chem.MolToSmiles(mol)],
            ["Molecular Formula", properties["Molecular Formula"]],
            ["Molecular Weight", str(properties["Molecular Weight"]) + " g/mol"]
        ]
        basic_table = Table(basic_data, colWidths=[1.8 * inch, 4.9 * inch])
        basic_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), HexColor("#EAF0F8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5)
        ]))
        story += [basic_table, Spacer(1, 0.12 * inch)]

        story.append(Paragraph("Molecular Structures", heading_style))
        img2d = save_2d_structure_png(mol)
        img3d = save_3d_structure_png(mol)
        if img2d:
            temp_images.append(img2d)
        if img3d:
            temp_images.append(img3d)

        if img2d and img3d:
            structure_table = Table([[
                Image(img2d, width=3.05 * inch, height=2.0 * inch),
                Image(img3d, width=3.05 * inch, height=2.0 * inch)
            ]], colWidths=[3.25 * inch, 3.25 * inch])
            structure_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER")
            ]))
            story += [structure_table, Spacer(1, 0.12 * inch)]
        elif img2d:
            story += [Image(img2d, width=4.8 * inch, height=3.2 * inch),
                      Spacer(1, 0.12 * inch)]

        story.append(Paragraph("Molecular Properties and Interpretation", heading_style))
        prop_data = [[
            Paragraph("<b>Property</b>", header_style),
            Paragraph("<b>Value</b>", header_style),
            Paragraph("<b>Interpretation</b>", header_style)
        ]]
        for key, value in properties.items():
            prop_data.append([
                Paragraph(str(key), small_style),
                Paragraph(str(value), small_style),
                Paragraph(get_property_interpretation(key, value, properties), small_style)
            ])
        prop_table = Table(
            prop_data, colWidths=[1.55 * inch, 0.9 * inch, 4.0 * inch], repeatRows=1
        )
        prop_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2F5597")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 3)
        ]))
        story += [prop_table, Spacer(1, 0.12 * inch)]

        story.append(Paragraph("Key Interpretation", heading_style))
        for point in build_key_interpretation_points(properties):
            story.append(Paragraph(point, body_style))
            story.append(Spacer(1, 0.04 * inch))

    story.append(PageBreak())
    story.append(Paragraph("Python Libraries Used and Their Importance", heading_style))
    library_data = [
        [Paragraph("<b>Library</b>", header_style),
         Paragraph("<b>Importance in this project</b>", header_style)],
        [Paragraph("Streamlit", small_style),
         Paragraph("Creates the interactive web app, input controls and PDF download interface.", small_style)],
        [Paragraph("RDKit", small_style),
         Paragraph("Parses SMILES, validates structures, creates molecular drawings and 3D conformers, and calculates molecular descriptors.", small_style)],
        [Paragraph("Pandas", small_style),
         Paragraph("Organizes molecular properties in tables and supports CSV export.", small_style)],
        [Paragraph("Matplotlib and NumPy", small_style),
         Paragraph("Process molecular coordinates and generate a clear 2D projection of 3D geometry for the report.", small_style)],
        [Paragraph("py3Dmol", small_style),
         Paragraph("Displays interactive 3D molecular structures in the web application.", small_style)],
        [Paragraph("ReportLab", small_style),
         Paragraph("Builds the downloadable PDF with tables, figures and explanatory text.", small_style)],
        [Paragraph("io, os, tempfile", small_style),
         Paragraph("Handle in-memory PDF data and temporary image files.", small_style)]
    ]
    lib_table = Table(library_data, colWidths=[1.8 * inch, 4.9 * inch], repeatRows=1)
    lib_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2F5597")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5)
    ]))
    story += [lib_table, Spacer(1, 0.15 * inch)]

    story.append(Paragraph("Illustrative Python Code", heading_style))
    code_style = ParagraphStyle(
        "MultiReportCode", parent=styles["Code"], fontName="Courier",
        fontSize=7, leading=8.5, leftIndent=4, rightIndent=4
    )
    code_example = "\n".join([
        "from rdkit import Chem",
        "from rdkit.Chem import Descriptors, Crippen, rdMolDescriptors",
        "",
        'smiles_list = ["CCO", "c1ccccc1"]  # Add more SMILES strings here',
        "",
        "for smiles in smiles_list:",
        "    mol = Chem.MolFromSmiles(smiles)",
        "    if mol is None:",
        '        print("Invalid SMILES:", smiles)',
        "        continue",
        "",
        '    print("SMILES:", smiles)',
        '    print("Formula:", rdMolDescriptors.CalcMolFormula(mol))',
        '    print("Molecular weight:", Descriptors.MolWt(mol))',
        '    print("LogP:", Crippen.MolLogP(mol))'
    ])
    story.append(Preformatted(code_example, code_style, maxLineLength=92))
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph(
        "This compact code example demonstrates processing multiple SMILES in one run. "
        "The complete application includes additional code for visualization, descriptor "
        "interpretation, student information and PDF generation. Calculated descriptors "
        "are computational results and should be interpreted appropriately.",
        body_style
    ))

    try:
        doc.build(story)
        return buffer.getvalue()
    finally:
        buffer.close()
        for image_path in temp_images:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception:
                pass

