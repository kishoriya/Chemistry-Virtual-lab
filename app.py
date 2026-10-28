"""Cheminformatics Virtual Laboratory: entry point.

Run with:  streamlit run app.py
The original single-file app is preserved in original_backup/app.py.
"""
import streamlit as st

st.set_page_config(
    page_title="Cheminformatics Virtual Laboratory",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="auto",
)

from ui import state  # noqa: E402
from ui.theme import inject_theme  # noqa: E402
from ui.components import render_sidebar  # noqa: E402
from ui.pages import PAGE_FUNCS  # noqa: E402

inject_theme()
state.init_state()

try:
    PAGE_FUNCS[st.session_state.page]()
except Exception as exc:  # last-resort guard: show a clear message instead of a stack trace
    st.error(
        f"Something went wrong while drawing this page ({type(exc).__name__}). "
        "Try another molecule or reload the page."
    )
    with st.expander("Technical details"):
        st.exception(exc)

# The sidebar is drawn after the page so "Recent molecules" is always up to date.
render_sidebar()

st.markdown(
    '<div class="sb-footer" style="text-align:center;margin-top:2.5rem">'
    "Cheminformatics Virtual Laboratory · Python, Streamlit, RDKit and py3Dmol · "
    "Calculated values are computational estimates.</div>",
    unsafe_allow_html=True,
)
