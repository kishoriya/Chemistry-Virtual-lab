"""Functional-group detection using RDKit SMARTS patterns (no extra dependencies).

Every count and highlight comes from a real substructure match on the molecule.
"""
from rdkit import Chem
from rdkit.Chem import Draw

# name -> (SMARTS, short teaching note)
FUNCTIONAL_GROUPS = {
    "Alcohol (hydroxyl)": ("[CX4][OX2H]", "An –OH on a saturated carbon. Donates and accepts hydrogen bonds."),
    "Phenol": ("c[OX2H]", "An –OH on an aromatic ring. More acidic than an alcohol."),
    "Aldehyde": ("[CX3H1](=O)[#6]", "A carbonyl carbon with one hydrogen."),
    "Ketone": ("[#6][CX3](=O)[#6]", "A carbonyl carbon bonded to two carbons."),
    "Carboxylic acid": ("[CX3](=O)[OX2H1]", "A –COOH group. Acidic and hydrogen-bonding."),
    "Ester": ("[#6][CX3](=O)[OX2H0][#6]", "A carbonyl bonded to an –OR group."),
    "Amide": ("[NX3][CX3](=[OX1])[#6]", "A carbonyl bonded to nitrogen. Common in peptides."),
    "Ether": ("[OD2]([#6])[#6]", "An oxygen bridging two carbons."),
    "Primary amine": ("[NX3;H2][#6]", "An –NH2 group on carbon."),
    "Secondary amine": ("[NX3;H1]([#6])[#6]", "An N–H bonded to two carbons."),
    "Tertiary amine": ("[NX3;H0;!$(NC=O)]([#6])([#6])[#6]", "A nitrogen bonded to three carbons."),
    "Nitrile": ("[NX1]#[CX2]", "A C≡N triple bond."),
    "Nitro": ("[$([NX3](=O)=O),$([NX3+](=O)[O-])][!#8]", "An –NO2 group. Strongly electron-withdrawing."),
    "Thiol": ("[SX2H]", "An –SH group."),
    "Halogen": ("[F,Cl,Br,I]", "Fluorine, chlorine, bromine or iodine attached to the structure."),
    "Alkene": ("[CX3]=[CX3]", "A carbon–carbon double bond (non-aromatic)."),
    "Alkyne": ("[CX2]#[CX2]", "A carbon–carbon triple bond."),
    "Aromatic ring": ("a1aaaaa1", "A six-membered aromatic ring such as benzene."),
    "Carbonyl (any C=O)": ("[CX3]=[OX1]", "Any carbon–oxygen double bond."),
}

_COMPILED = {}
for _name, (_smarts, _note) in FUNCTIONAL_GROUPS.items():
    _patt = Chem.MolFromSmarts(_smarts)
    if _patt is not None:
        _COMPILED[_name] = _patt


def find_functional_groups(mol):
    """Return a list of dicts for the groups present in ``mol``.

    Each dict: name, count, atoms (flat tuple of matched atom indices), note.
    """
    results = []
    if mol is None:
        return results
    for name, patt in _COMPILED.items():
        matches = mol.GetSubstructMatches(patt)
        if not matches:
            continue
        atoms = sorted({idx for match in matches for idx in match})
        results.append(
            {
                "name": name,
                "count": len(matches),
                "atoms": tuple(atoms),
                "note": FUNCTIONAL_GROUPS[name][1],
            }
        )
    return results


def highlighted_image(mol, atom_indices, size=(640, 440)):
    """Draw ``mol`` in 2D with the given atoms highlighted."""
    atom_indices = list(atom_indices)
    bonds = []
    atom_set = set(atom_indices)
    for bond in mol.GetBonds():
        if bond.GetBeginAtomIdx() in atom_set and bond.GetEndAtomIdx() in atom_set:
            bonds.append(bond.GetIdx())
    colour = (0.22, 0.84, 0.96)
    return Draw.MolToImage(
        mol,
        size=size,
        highlightAtoms=atom_indices,
        highlightBonds=bonds,
        highlightColor=colour,
    )
