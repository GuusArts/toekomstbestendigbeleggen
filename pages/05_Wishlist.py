from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from lib import auth, data_store, ui


def _analyse_goals(goals: pd.DataFrame, plan_months: int) -> pd.DataFrame:
    if goals.empty:
        return pd.DataFrame(columns=["Doel", "Doelbedrag", "Maandelijkse Bijdrage", "Maanden", "Binnen plan"])

    rows = []
    for _, row in goals.iterrows():
        target = float(row.get("Doelbedrag", 0.0))
        monthly = float(row.get("Maandelijkse Bijdrage", 0.0))
        if monthly <= 0:
            months = math.inf
        else:
            months = math.ceil(target / monthly)
        rows.append(
            {
                "Doel": row.get("Doel", ""),
                "Doelbedrag": target,
                "Maandelijkse Bijdrage": monthly,
                "Maanden": months,
                "Binnen plan": months <= plan_months if math.isfinite(months) else False,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    user = auth.require_user()
    data_store.ensure_user_store(user.email)
    data = data_store.get_active_store()

    st.title("🎯 Wishlist")
    st.caption("Zet spaardoelen uit en volg de voortgang.")

    goals = ui.safe_data_editor(
        data["wishlist"],
        num_rows="dynamic",
        use_container_width=True,
        key="wishlist-editor",
    )
    goals = goals.reindex(columns=data_store.WISHLIST_COLUMNS, fill_value="")
    goals["Doelbedrag"] = goals["Doelbedrag"].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    goals["Maandelijkse Bijdrage"] = goals["Maandelijkse Bijdrage"].apply(
        pd.to_numeric, errors="coerce"
    ).fillna(0.0)
    data["wishlist"] = goals

    plan_months = int(data["plan"].get("months_phase1", 0)) + int(data["plan"].get("months_phase2", 0))
    analysis = _analyse_goals(goals, plan_months)

    if analysis.empty:
        st.info("Voeg doelen toe om de doorlooptijd te berekenen.")
    else:
        st.subheader("Voortgang")
        for _, goal in analysis.iterrows():
            label = goal["Doel"] or "Doel zonder naam"
            if math.isfinite(goal["Maanden"]):
                months = int(goal["Maanden"])
                within_plan = "✅ Binnen plan" if goal["Binnen plan"] else "⚠️ Buiten plan"
                st.write(f"**{label}** — € {goal['Doelbedrag']:,.0f} • {months} maanden • {within_plan}")
                ui.safe_progress(min(months / max(plan_months, 1), 1.0))
            else:
                st.write(f"**{label}** — vul een maandelijkse bijdrage in om een prognose te zien.")

        st.subheader("Details")
        display = analysis.copy()
        display["Maanden"] = display["Maanden"].replace(math.inf, "∞")
        display["Binnen plan"] = display["Binnen plan"].map({True: "Ja", False: "Nee"})
        st.dataframe(display, use_container_width=True)

    st.divider()
    st.page_link("app.py", label="⬅️ Terug naar Home")


if __name__ == "__main__":
    main()
