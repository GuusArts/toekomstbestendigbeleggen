from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import auth, data_store, finance, ui


def main() -> None:
    user = auth.require_user()
    data_store.ensure_user_store(user.email)
    data = data_store.get_active_store()

    st.title("💼 Inkomen")
    st.caption("Werk al je inkomensstromen bij.")

    st.write(
        "Gebruik de tabel hieronder om bronnen, bedragen en frequenties aan te passen. "
        "De wijzigingen worden direct opgeslagen en gebruikt in andere pagina's."
    )

    edited = ui.safe_data_editor(
        data["income"],
        num_rows="dynamic",
        use_container_width=True,
        key="income-editor",
    )
    edited = edited.reindex(columns=data_store.INCOME_COLUMNS, fill_value="")
    edited["Bedrag"] = edited["Bedrag"].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    data["income"] = edited

    summary = finance.compute_cashflow_summary(data)
    st.metric("Totale inkomens per maand", f"€ {summary['income']:,.0f}")

    st.divider()
    st.page_link("app.py", label="⬅️ Terug naar Home")


if __name__ == "__main__":
    main()
