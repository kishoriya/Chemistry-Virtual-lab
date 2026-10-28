"""AI chemistry tutor.

Two modes, always clearly labelled in the UI:

* **Grounded mode** (no API key needed): answers only from the real RDKit results
  for the current molecule plus the app's own descriptor explanations. If a
  question cannot be answered from that data it says so; it never invents
  properties.
* **Claude mode** (optional): if ``ANTHROPIC_API_KEY`` is present in the
  environment or in Streamlit secrets, questions are sent to the Anthropic API
  together with the molecule's *computed* data. The key is read server-side only,
  is never displayed, logged or written to disk.
"""
import json
import os
import re
import urllib.error
import urllib.request

from core.reports import get_property_interpretation

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-5-5"
MAX_QUESTION_CHARS = 1500
MAX_HISTORY_TURNS = 6

SYSTEM_PROMPT = (
    "You are a patient chemistry tutor inside a cheminformatics teaching lab for "
    "university students. Use ONLY the molecule data in the <molecule> block for "
    "any numbers about the current molecule; never invent values. If the data does "
    "not contain what is asked, say so and explain the concept in general terms. "
    "Explain clearly, keep answers under 200 words unless asked for more, and note "
    "when a value is a computed estimate (for example Crippen LogP) rather than a "
    "measurement."
)

SUGGESTED_QUESTIONS = [
    "Is this molecule drug-like?",
    "What functional groups does it contain?",
    "What does the LogP value mean?",
    "Why does TPSA matter?",
    "How many σ and π bonds are there?",
]


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

def find_api_key():
    """Return the API key from env or Streamlit secrets, or ``None``."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key.strip() or None
    try:  # Streamlit raises if no secrets file exists; that is fine.
        import streamlit as st

        key = st.secrets.get("ANTHROPIC_API_KEY")
        if key:
            return str(key).strip() or None
    except Exception:
        pass
    return None


def find_model():
    model = os.environ.get("ANTHROPIC_MODEL")
    if not model:
        try:
            import streamlit as st

            model = st.secrets.get("ANTHROPIC_MODEL")
        except Exception:
            model = None
    return (str(model).strip() if model else DEFAULT_MODEL) or DEFAULT_MODEL


# --------------------------------------------------------------------------
# Context
# --------------------------------------------------------------------------

def build_context(smiles, canonical, props, groups, lipinski_rows, violations):
    """Plain-text description of the current molecule built from real results."""
    lines = [f"Input SMILES: {smiles}", f"Canonical SMILES: {canonical}"]
    for key, value in props.items():
        lines.append(f"{key}: {value}")
    if groups:
        lines.append(
            "Functional groups: " + ", ".join(f"{g['name']} x{g['count']}" for g in groups)
        )
    else:
        lines.append("Functional groups: none of the tracked groups detected")
    for row in lipinski_rows:
        lines.append(
            f"Lipinski {row['label']}: {row['value']} (limit {row['limit']}) "
            + ("OK" if row["ok"] else "EXCEEDS")
        )
    lines.append(f"Lipinski violations: {violations}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Grounded mode
# --------------------------------------------------------------------------

_GLOSSARY = [
    (r"\bsmiles\b", "SMILES (Simplified Molecular Input Line Entry System) writes a molecule as text: atoms are letters, branches use parentheses, rings use matching digits, and lowercase letters mark aromatic atoms."),
    (r"\bcanonical\b", "A canonical SMILES is the single, standard string RDKit generates for a structure, so the same molecule always gives the same text however you typed it."),
    (r"\bcheminformatics\b", "Cheminformatics uses computing to store, search and analyse chemical information, such as structures and their calculated properties."),
]

_TOPICS = [
    # (regex, property key or special tag)
    (r"formula|composition", "Molecular Formula"),
    (r"exact (mass|weight)|monoisotopic", "Exact Molecular Weight"),
    (r"molecular weight|\bmw\b|\bmass\b", "Molecular Weight"),
    (r"logp|lipophil|hydrophob|hydrophil|partition", "LogP"),
    (r"tpsa|polar surface", "TPSA"),
    (r"donor|\bhbd\b", "Hydrogen Bond Donors"),
    (r"acceptor|\bhba\b", "Hydrogen Bond Acceptors"),
    (r"rotatab|flexib", "Rotatable Bonds"),
    (r"aromatic", "Aromatic Rings"),
    (r"\brings?\b", "Ring Count"),
    (r"fsp3|csp3|sp3", "Fraction Csp3"),
    (r"refractiv", "Molar Refractivity"),
    (r"heavy atom", "Heavy Atoms"),
]


def _unit(key):
    return {"Molecular Weight": " g/mol", "Exact Molecular Weight": " g/mol", "TPSA": " Å²"}.get(key, "")


def grounded_answer(question, props, groups, lipinski_rows, violations):
    """Answer from real computed data. Returns ``(text, answered)``."""
    q = question.lower()
    parts = []

    if re.search(r"drug|lipinski|rule of (5|five)|oral", q):
        detail = "; ".join(
            f"{r['label']} {r['value']:g} (limit {r['limit']:g}, {'OK' if r['ok'] else 'exceeds'})"
            for r in lipinski_rows
        )
        verdict = (
            "meets all four Lipinski rule-of-five criteria"
            if violations == 0
            else f"breaks {violations} of the four Lipinski criteria"
        )
        parts.append(
            f"By Lipinski's rule of five this molecule {verdict}: {detail}. "
            "The rule is a rough screening guide for oral drug-likeness, not proof "
            "that a compound is, or is not, a drug."
        )

    if re.search(r"functional|group|contain", q):
        if groups:
            items = "; ".join(f"{g['name']} ×{g['count']} ({g['note']})" for g in groups)
            parts.append(f"Detected functional groups: {items}")
        else:
            parts.append("None of the functional groups tracked by this lab were detected in this molecule.")

    if re.search(r"sigma|σ|\bpi\b|π|\bbonds?\b", q) and not re.search(r"rotatab|donor|acceptor", q):
        parts.append(
            f"σ bonds: {props['Sigma (σ) Bonds']}, π bonds: {props['Pi (π) Bonds']}, "
            f"total bond components: {props['Total Bonds (σ + π)']}. "
            "Every bonded atom pair has one σ bond; double bonds add one π bond and triple bonds add two."
        )

    for pattern, key in _TOPICS:
        if re.search(pattern, q) and key in props:
            value = props[key]
            parts.append(
                f"{key}: {value}{_unit(key)}. {get_property_interpretation(key, value, props)}"
            )

    for pattern, text in _GLOSSARY:
        if re.search(pattern, q):
            parts.append(text)

    if parts:
        seen, unique = set(), []
        for p in parts:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        return "\n\n".join(unique), True

    return (
        "I can't answer that from the calculated data alone. In built-in mode I can "
        "explain this molecule's formula, weight, LogP, TPSA, H-bond donors/acceptors, "
        "rotatable bonds, rings, σ/π bonds, functional groups and Lipinski drug-likeness. "
        "Add an Anthropic API key to ask open-ended questions.",
        False,
    )


# --------------------------------------------------------------------------
# Claude mode
# --------------------------------------------------------------------------

def claude_answer(question, context, history, api_key, model=None, timeout=45):
    """Ask Claude. Returns ``(ok, text)``; never raises and never echoes the key."""
    messages = []
    for role, content in history[-(MAX_HISTORY_TURNS * 2):]:
        messages.append({"role": role, "content": content})
    messages.append(
        {
            "role": "user",
            "content": f"<molecule>\n{context}\n</molecule>\n\nStudent question: {question}",
        }
    )
    body = json.dumps(
        {
            "model": model or DEFAULT_MODEL,
            "max_tokens": 700,
            "system": SYSTEM_PROMPT,
            "messages": messages,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": API_VERSION,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        text = "".join(
            block.get("text", "") for block in payload.get("content", []) if block.get("type") == "text"
        ).strip()
        if not text:
            return False, "The AI service returned an empty answer. Please try again."
        return True, text
    except urllib.error.HTTPError as err:
        if err.code in (401, 403):
            return False, "The API key was rejected. Check ANTHROPIC_API_KEY in your secrets."
        if err.code == 429:
            return False, "The AI service is rate-limited right now. Wait a moment and try again."
        if err.code == 404:
            return False, "The configured model was not found. Check ANTHROPIC_MODEL."
        return False, f"The AI service returned an error (HTTP {err.code})."
    except urllib.error.URLError:
        return False, "Could not reach the AI service. Check your internet connection."
    except Exception:
        return False, "Something went wrong while contacting the AI service."


def answer(question, *, smiles, canonical, props, groups, lipinski_rows, violations,
           history, api_key=None, model=None):
    """Main entry. Returns ``(text, mode, ok)`` where mode is 'claude' or 'built-in'."""
    question = (question or "").strip()[:MAX_QUESTION_CHARS]
    if not question:
        return "Type a question about the current molecule first.", "built-in", False
    if api_key:
        ctx = build_context(smiles, canonical, props, groups, lipinski_rows, violations)
        ok, text = claude_answer(question, ctx, history, api_key, model)
        if ok:
            return text, "claude", True
        # Fall back to grounded answer but keep the error visible.
        text2, _ = grounded_answer(question, props, groups, lipinski_rows, violations)
        return f"⚠️ {text}\n\nBuilt-in answer instead:\n\n{text2}", "built-in", False
    text, answered = grounded_answer(question, props, groups, lipinski_rows, violations)
    return text, "built-in", answered
