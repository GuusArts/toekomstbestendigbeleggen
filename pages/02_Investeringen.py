from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import auth, data_store, finance


def main() -> None:
    user = auth.require_user()
    data_store.ensure_user_store(user.email)
    data = data_store.get_active_store()

    st.title("📈 Investeringen")
    st.caption("Simuleer verschillende rendementsscenario's voor je portefeuille.")

    investments = data["investments"]
    plan = data["plan"]

    new_start = st.number_input(
        "Startwaarde portefeuille (EUR)",
        min_value=0.0,
        value=float(investments.get("start_balance", 0.0)),
        step=500.0,
    )
    new_phase1 = st.number_input(
        "Maandelijkse inleg Fase 1 (EUR)",
        min_value=0.0,
        value=float(investments.get("monthly_contribution_phase1", 0.0)),
        step=50.0,
    )
    new_phase2 = st.number_input(
        "Maandelijkse inleg Fase 2 (EUR)",
        min_value=0.0,
        value=float(investments.get("monthly_contribution_phase2", 0.0)),
        step=50.0,
    )
    avg_return = st.number_input(
        "Gemiddeld rendement (%/jaar)",
        min_value=-50.0,
        max_value=30.0,
        value=float(investments.get("avg_return_pa", 0.0) * 100),
        step=0.1,
    )
    good_return = st.number_input(
        "Optimistisch rendement (%/jaar)",
        min_value=-50.0,
        max_value=40.0,
        value=float(investments.get("good_return_pa", 0.0) * 100),
        step=0.1,
    )
    new_months_phase2 = st.number_input(
        "Duur Fase 2 (maanden)",
        min_value=0,
        max_value=240,
        value=int(plan.get("months_phase2", 0)),
    )
    inflation = st.number_input(
        "Inflatie (%/jaar)",
        min_value=0.0,
        max_value=15.0,
        value=float(plan.get("inflation_pa", 0.0) * 100),
        step=0.5,
    )

    investments.update(
        {
            "start_balance": new_start,
            "monthly_contribution_phase1": new_phase1,
            "monthly_contribution_phase2": new_phase2,
            "avg_return_pa": avg_return / 100,
            "good_return_pa": good_return / 100,
        }
    )
    plan.update({"months_phase2": int(new_months_phase2), "inflation_pa": inflation / 100})

    df_avg, df_good = finance.get_projection_frames(data)

    st.subheader("Ontwikkeling beleggingen")
    if df_avg.empty:
        st.info(
            "Voer je investeringsinleg, looptijden en rendementen in om de scenario's te bekijken."
        )
    else:
        chart_df = pd.DataFrame(
            {
                "Maand": df_avg["Maand"],
                "Gemiddeld scenario": df_avg["Investeringen"],
                "Optimistisch scenario": df_good["Investeringen"],
            }
        ).set_index("Maand")
        st.line_chart(chart_df)

        phase1_months = data["plan"].get("months_phase1", 0)
        invest_phase1 = finance.get_value_for_month(df_avg, int(phase1_months), "Investeringen")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Beleggingen einde Fase 1", f"€ {invest_phase1:,.0f}")
        with col2:
            st.metric("Beleggingen einde plan", f"€ {df_avg.iloc[-1]['Investeringen']:,.0f}")
        with col3:
            st.metric("Reëel vermogen", f"€ {df_avg.iloc[-1]['Totaal (reëel)']:,.0f}")

        st.dataframe(
            df_avg[["Maand", "Investeringen", "Storting Beleggen", "Totaal (nominaal)"]],
            use_container_width=True,
        )

    st.divider()
    st.page_link("app.py", label="⬅️ Terug naar Home")


if __name__ == "__main__":
    main()
