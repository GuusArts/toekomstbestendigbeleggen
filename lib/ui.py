"""UI helpers shared across Streamlit pages."""
from __future__ import annotations

import contextlib
from typing import Iterator

import pandas as pd
import streamlit as st


def bordered_container(*, border: bool = False) -> contextlib.AbstractContextManager[None]:
    """Return a container context that works on older Streamlit versions too."""

    @contextlib.contextmanager
    def _context() -> Iterator[None]:
        if border:
            try:
                container = st.container(border=True)
            except TypeError:
                container = st.container()
        else:
            container = st.container()

        with container:
            yield

    return _context()


def safe_data_editor(data: pd.DataFrame, *, key: str, **kwargs) -> pd.DataFrame:
    """Render an editable dataframe while tolerating Streamlit fallbacks."""

    editor = getattr(st, "data_editor", None)
    if callable(editor):
        return editor(data, key=key, **kwargs)

    experimental = getattr(st, "experimental_data_editor", None)
    if callable(experimental):
        return experimental(data, key=key, **kwargs)

    st.warning(
        "Deze Streamlit-versie ondersteunt geen interactieve tabelbewerking. "
        "De gegevens worden alleen weergegeven."
    )
    st.dataframe(data, use_container_width=kwargs.get("use_container_width", False))
    return data


def safe_progress(value: float, *, text: str | None = None):
    """Render a progress bar and gracefully downgrade on older runtimes."""

    if text is None:
        return st.progress(value)

    try:
        return st.progress(value, text=text)
    except TypeError:
        return st.progress(value)
