"""Authentication helpers that rely on SSO."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import streamlit as st

from . import data_store


@dataclass
class UserIdentity:
    email: str
    name: str | None = None
    picture: str | None = None


SSO_STATE_KEY = "_sso_identity"


def _extract_identity(raw: Any) -> UserIdentity | None:
    if raw is None:
        return None

    if isinstance(raw, dict):
        email = raw.get("email")
        name = raw.get("name")
        picture = raw.get("picture") or raw.get("profileImage")
    else:
        email = getattr(raw, "email", None)
        name = getattr(raw, "name", None)
        picture = getattr(raw, "picture", None)

    if not email:
        return None

    return UserIdentity(email=str(email), name=name, picture=picture)


def _render_dev_login(config: Dict[str, Any]) -> None:
    st.warning(
        "SSO is nog niet geconfigureerd. Omdat `dev_mode` is ingeschakeld, kun je een "
        "testaccount invoeren om de app lokaal te proberen."
    )
    default_email = config.get("dev_email", "")
    email = st.text_input("E-mailadres", value=default_email, key="dev-email")
    name = st.text_input("Naam", value=config.get("dev_name", ""), key="dev-name")
    if st.button("Start testsessie"):
        if not email:
            st.error("Voer een e-mailadres in om door te gaan.")
            st.stop()
        identity = UserIdentity(email=email.strip(), name=name.strip() or None)
        st.session_state[SSO_STATE_KEY] = identity
        st.experimental_rerun()
    st.stop()


def require_user() -> UserIdentity:
    """Return the currently signed-in user, forcing SSO if necessary."""

    identity = st.session_state.get(SSO_STATE_KEY)
    if isinstance(identity, UserIdentity):
        return identity

    experimental_user = getattr(st, "experimental_user", None)
    identity = _extract_identity(experimental_user)
    if identity:
        st.session_state[SSO_STATE_KEY] = identity
        return identity

    connection = None
    try:
        connection = st.connection("sso", type="oauth")  # type: ignore[arg-type]
    except Exception:  # noqa: BLE001
        connection = None

    if connection is not None:
        candidate = _extract_identity(getattr(connection, "user", None))
        if candidate:
            st.session_state[SSO_STATE_KEY] = candidate
            return candidate

    config = st.secrets.get("sso", {}) if st.secrets else {}
    if config.get("dev_mode"):
        _render_dev_login(config)

    st.error(
        "SSO-authenticatie is vereist voordat je de applicatie kunt gebruiken. "
        "Volg de instructies in de Streamlit-documentatie om een SSO-provider in te stellen "
        "via `.streamlit/secrets.toml`."
    )
    st.stop()


def logout() -> None:
    """Clear the session state for the active user and rerun the app."""

    identity = st.session_state.pop(SSO_STATE_KEY, None)
    if identity:
        data_store.clear_active_store()
    st.experimental_rerun()
