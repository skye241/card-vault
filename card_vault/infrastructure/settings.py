"""Read a secret from the environment, a local ``.env``, or Streamlit secrets."""

import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


def setting(name: str, *, required: bool = False) -> str:
    """Return one named secret, stripped. Empty when it is optional and unset.

    Raises:
        ValueError: ``required`` is set and every source is empty.
    """
    value = os.environ.get(name, "")
    if not value:
        from dotenv import load_dotenv
        load_dotenv(_ROOT / ".env")
        value = os.environ.get(name, "")
    if not value:
        value = _streamlit_secret(name, required=required)
    value = str(value or "").strip()
    if required and not value:
        raise ValueError(f"{name} is not set")
    return value


def _streamlit_secret(name: str, *, required: bool) -> str:
    try:
        import streamlit as st
        raw = st.secrets[name] if required else st.secrets.get(name, "")
    except Exception:
        raw = ""
    return str(raw or "")
