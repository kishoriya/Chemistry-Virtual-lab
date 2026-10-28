# Cheminformatics Virtual Laboratory

Dark, responsive Streamlit app for representing and analysing chemical structures.
Every number comes from RDKit; nothing is hard-coded or simulated.

## Run it
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
On Linux you may also need the packages in `packages.txt` (`sudo xargs apt install -y < packages.txt`).
Open http://localhost:8501. The 3D viewer loads 3Dmol.js from a CDN, so it needs internet access.

## Pages
Home · Lab (3D viewer, info panel, 2D structure, Lipinski, AI tutor) · Compare · Functional groups ·
Property charts · Theory · Assessment · Reports (CSV, PNG, 3D MOL, PDF) · Final project report (multi-molecule PDF).
Deep links work: `?page=lab`, `?page=compare`, …

## AI tutor
* **Built-in mode (default, no key):** answers only from the calculated results for the current molecule.
  If it cannot answer, it says so.
* **Claude mode (optional):** add `ANTHROPIC_API_KEY` to `.streamlit/secrets.toml` (see `secrets.toml.example`)
  or set it as an environment variable. The key is read on the server only and never shown or logged.
  Your molecule's *calculated* data is sent with each question. `ANTHROPIC_MODEL` overrides the model.

## Project layout
```
app.py                entry point (page config, theme, routing)
core/chem.py          SMILES parsing, descriptors, σ/π bonds, 2D/3D generation (original code, moved unchanged)
core/reports.py       ReportLab PDFs + PNG helpers (original code, moved unchanged)
core/viewer.py        py3Dmol dark 3D viewer
core/functional_groups.py   RDKit SMARTS functional-group detection
core/charts.py        Matplotlib dark charts, Lipinski rule of five
core/tutor.py         AI tutor (built-in + optional Claude)
ui/                   theme (CSS), state, shared components, pages
tests/                pytest regression + UI smoke tests
original_backup/      the untouched original app.py, requirements and README
```

## Tests
```bash
pip install -r requirements-dev.txt && pytest -q
```

## Notes
* Calculated values (for example Crippen LogP) are computational estimates, not measurements.
* Recent molecules and tutor history live only in the browser session; nothing is written to disk.
* Removed: the "Cartoon" 3D style (it was only sticks plus small spheres, not a real cartoon rendering).
