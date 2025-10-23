from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import auth, data_store, finance


def main() -> None:
    user = auth.require_user()
    data_store.ensure_user_store(user.email)
    data = data_store.get_active_store()

    st.title("💰 Spaarrekening")
    st.caption("Beheer je noodbuffer en maandelijkse stortingen.")

    buffer_data = data["buffer"]
    savings = data["savings"]
    plan = data["plan"]

    new_buffer = st.number_input(
        "Noodbuffer (EUR)",
        min_value=0.0,
        value=float(buffer_data.get("amount", 0.0)),
        step=500.0,
    )
    buffer_data["amount"] = new_buffer

    new_start_balance = st.number_input(
        "Start saldo spaarrekening (EUR)",
        min_value=0.0,
        value=float(savings.get("start_balance", 0.0)),
        step=500.0,
    )
    new_monthly = st.number_input(
        "Maandelijkse storting in Fase 1 (EUR)",
        min_value=0.0,
        value=float(savings.get("monthly_contribution", 0.0)),
        step=50.0,
    )
    new_interest = st.number_input(
        "Rente spaarrekening (%/jaar)",
        min_value=0.0,
        max_value=20.0,
        value=float(savings.get("interest_rate_pa", 0.0) * 100),
        step=0.1,
    )
    new_months_phase1 = st.number_input(
        "Duur Fase 1 (maanden)",
        min_value=1,
        max_value=120,
        value=int(plan.get("months_phase1", 12)),
    )

    savings.update(
        {
            "start_balance": new_start_balance,
            "monthly_contribution": new_monthly,
            "interest_rate_pa": new_interest / 100,
        }
    )
    plan["months_phase1"] = int(new_months_phase1)

    df_avg, df_good = finance.get_projection_frames(data)

    st.subheader("Ontwikkeling spaarrekening")
    if df_avg.empty:
        st.info(
            "Voer maanden, stortingen en rente in om een prognose voor de spaarrekening te zien."
        )
    else:
        chart_df = pd.DataFrame(
            {
                "Maand": df_avg["Maand"],
                "Gemiddeld scenario": df_avg["Spaarrekening"],
                "Optimistisch scenario": df_good["Spaarrekening"],
            }
        ).set_index("Maand")
        st.line_chart(chart_df)

        phase1_months = plan.get("months_phase1", 0)
        buffer_phase1 = finance.get_value_for_month(df_avg, int(phase1_months), "Spaarrekening")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Saldo einde Fase 1", f"€ {buffer_phase1:,.0f}")
        with col2:
            st.metric("Saldo einde plan", f"€ {df_avg.iloc[-1]['Spaarrekening']:,.0f}")
        with col3:
            st.metric("Reëel vermogen", f"€ {df_avg.iloc[-1]['Totaal (reëel)']:,.0f}")

        st.dataframe(
            df_avg[["Maand", "Spaarrekening", "Storting Sparen", "Totaal (nominaal)"]],
            use_container_width=True,
        )

    st.divider()
    st.page_link("app.py", label="⬅️ Terug naar Home")


if __name__ == "__main__":
    main()
