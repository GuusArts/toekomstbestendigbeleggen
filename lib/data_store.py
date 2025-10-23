"""Data storage helpers shared between Streamlit pages."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Iterable

import pandas as pd
import streamlit as st

INCOME_COLUMNS = ["Bron", "Bedrag", "Frequentie"]
EXPENSE_COLUMNS = ["Categorie", "Bedrag", "Frequentie"]
WISHLIST_COLUMNS = ["Doel", "Doelbedrag", "Maandelijkse Bijdrage"]

TABLE_NAMES = {
    "income": INCOME_COLUMNS,
    "expenses": EXPENSE_COLUMNS,
    "wishlist": WISHLIST_COLUMNS,
}


@dataclass
class UserStore:
    """Wrap the mutable profile state that lives in ``st.session_state``."""

    owner: str
    payload: Dict[str, object]


def _empty_tables() -> Dict[str, pd.DataFrame]:
    return {
        name: pd.DataFrame(columns=columns)
        for name, columns in TABLE_NAMES.items()
    }


def create_empty_payload() -> Dict[str, object]:
    return {
        "buffer": {"amount": 0.0},
        "savings": {
            "start_balance": 0.0,
            "monthly_contribution": 0.0,
            "interest_rate_pa": 0.0,
        },
        "investments": {
            "start_balance": 0.0,
            "monthly_contribution_phase1": 0.0,
            "monthly_contribution_phase2": 0.0,
            "avg_return_pa": 0.0,
            "good_return_pa": 0.0,
        },
        "plan": {
            "months_phase1": 12,
            "months_phase2": 0,
            "inflation_pa": 0.0,
            "target_savings": 0.0,
        },
        **_empty_tables(),
    }


def ensure_user_store(user_id: str) -> UserStore:
    """Ensure the given user's profile lives in the session."""

    stores: Dict[str, Dict[str, object]] = st.session_state.setdefault("_profiles", {})
    if user_id not in stores:
        stores[user_id] = create_empty_payload()

    st.session_state["data_store"] = stores[user_id]
    st.session_state["data_owner"] = user_id
    return UserStore(owner=user_id, payload=stores[user_id])


def get_active_store() -> Dict[str, object]:
    """Return the active user's payload, ensuring authentication happened first."""

    if "data_store" not in st.session_state:
        raise RuntimeError("Data store is not initialised yet")
    return st.session_state["data_store"]


def _frame_to_records(frame: pd.DataFrame, *, columns: Iterable[str]) -> list[dict]:
    if frame.empty:
        return []
    return frame[columns].to_dict(orient="records")


def export_payload() -> bytes:
    """Serialise the active store so the user can download a JSON backup."""

    data = get_active_store()
    payload = {
        "buffer": data["buffer"],
        "savings": data["savings"],
        "investments": data["investments"],
        "plan": data["plan"],
        "income": _frame_to_records(data["income"], columns=INCOME_COLUMNS),
        "expenses": _frame_to_records(data["expenses"], columns=EXPENSE_COLUMNS),
        "wishlist": _frame_to_records(data["wishlist"], columns=WISHLIST_COLUMNS),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def import_payload(raw: bytes) -> None:
    """Replace the active store with data uploaded by the signed-in user."""

    data = json.loads(raw.decode("utf-8"))
    store = create_empty_payload()

    for key in ("buffer", "savings", "investments", "plan"):
        if key in data and isinstance(data[key], dict):
            store[key].update(data[key])

    for table, columns in TABLE_NAMES.items():
        rows = data.get(table, [])
        if isinstance(rows, list):
            frame = pd.DataFrame(rows)
            store[table] = frame.reindex(columns=columns, fill_value="")

    owner = st.session_state.get("data_owner")
    if not owner:
        raise RuntimeError("Cannot import data before a user signed in")

    st.session_state.setdefault("_profiles", {})[owner] = store
    st.session_state["data_store"] = store


def clear_active_store() -> None:
    """Forget the profile assigned to the current session."""

    owner = st.session_state.pop("data_owner", None)
    st.session_state.pop("data_store", None)
