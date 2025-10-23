from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import auth, data_store, finance, ui


def main() -> None:
    user = auth.require_user()
    data_store.ensure_user_store(user.email)
    data = data_store.get_active_store()

    st.title("🧮 Budget")
    st.caption("Analyseer je maandelijkse cashflow en allocatie.")

    expenses = ui.safe_data_editor(
        data["expenses"],
        num_rows="dynamic",
        use_container_width=True,
        key="expenses-editor",
    )
    expenses = expenses.reindex(columns=data_store.EXPENSE_COLUMNS, fill_value="")
    expenses["Bedrag"] = expenses["Bedrag"].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    data["expenses"] = expenses

    summary = finance.compute_cashflow_summary(data)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Inkomen (pm)", f"€ {summary['income']:,.0f}")
    with col2:
        st.metric("Uitgaven (pm)", f"€ {summary['expenses']:,.0f}")
    with col3:
        st.metric("Sparen (pm)", f"€ {summary['savings_allocation']:,.0f}")
    with col4:
        st.metric("Investeren (pm)", f"€ {summary['investment_allocation']:,.0f}")

    st.subheader("Cashflow overzicht")
    overview = pd.DataFrame(
        {
            "Categorie": ["Inkomen", "Uitgaven", "Sparen", "Investeren", "Netto"],
            "Maandbedrag": [
                summary["income"],
                -summary["expenses"],
                -summary["savings_allocation"],
                -summary["investment_allocation"],
                summary["net_cashflow"],
            ],
        }
    )
    st.bar_chart(overview.set_index("Categorie"))

    st.subheader("Uitgaven details")
    if expenses.empty:
        st.info("Voeg categorieën toe in de tabel hierboven om een detailoverzicht te zien.")
    else:
        monthly = expenses.copy()
        monthly["Maandbedrag"] = monthly.apply(
            lambda row: finance.freq_to_monthly(str(row["Frequentie"]), float(row["Bedrag"])),
            axis=1,
        )
        st.dataframe(monthly[["Categorie", "Maandbedrag"]], use_container_width=True)

    st.divider()
    st.page_link("app.py", label="⬅️ Terug naar Home")


if __name__ == "__main__":
    main()
