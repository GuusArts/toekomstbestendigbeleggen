from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Toekomstbestendig Beleggen", page_icon="📱", layout="wide")


@dataclass
class Page:
    name: str
    icon: str
    description: str
    renderer: Callable[[], None]


INCOME_COLUMNS = ["Bron", "Bedrag", "Frequentie"]
EXPENSE_COLUMNS = ["Categorie", "Bedrag", "Frequentie"]
WISHLIST_COLUMNS = ["Doel", "Doelbedrag", "Maandelijkse Bijdrage"]


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


CREDENTIALS: Dict[str, str] = {
    "planner": hash_password("veiligwachtwoord"),
}


def init_session_state() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None

    if "data_store" not in st.session_state:
        st.session_state.data_store = {
            "buffer": {"amount": 6000.0},
            "savings": {
                "start_balance": 10_000.0,
                "monthly_contribution": 250.0,
                "interest_rate_pa": 0.0275,
            },
            "investments": {
                "start_balance": 3500.0,
                "monthly_contribution_phase1": 100.0,
                "monthly_contribution_phase2": 250.0,
                "avg_return_pa": 0.05,
                "good_return_pa": 0.07,
            },
            "plan": {
                "months_phase1": 24,
                "months_phase2": 60,
                "inflation_pa": 0.035,
                "target_savings": 27_500.0,
            },
            "income": pd.DataFrame(
                [
                    {"Bron": "Salaris", "Bedrag": 3200.0, "Frequentie": "Maandelijks"},
                    {"Bron": "Freelance", "Bedrag": 600.0, "Frequentie": "Maandelijks"},
                ]
            ),
            "expenses": pd.DataFrame(
                [
                    {"Categorie": "Huur/Hypotheek", "Bedrag": 1200.0, "Frequentie": "Maandelijks"},
                    {"Categorie": "Boodschappen", "Bedrag": 450.0, "Frequentie": "Maandelijks"},
                    {"Categorie": "Vrije tijd", "Bedrag": 200.0, "Frequentie": "Maandelijks"},
                ]
            ),
            "wishlist": pd.DataFrame(
                [
                    {
                        "Doel": "Noodbuffer 6 maanden",
                        "Doelbedrag": 9000.0,
                        "Maandelijkse Bijdrage": 300.0,
                    },
                    {
                        "Doel": "Vakantie Canada",
                        "Doelbedrag": 5000.0,
                        "Maandelijkse Bijdrage": 200.0,
                    },
                ]
            ),
        }

    if "active_page" not in st.session_state:
        st.session_state.active_page = "Home"


def authenticate(username: str, password: str) -> bool:
    stored = CREDENTIALS.get(username)
    return stored == hash_password(password)


def logout() -> None:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.active_page = "Home"
    st.experimental_rerun()


def freq_to_monthly(freq: str, amount: float) -> float:
    mapping = {
        "Maandelijks": 1.0,
        "Jaarlijks": 1.0 / 12.0,
        "Eenmalig": 1.0 / 12.0,
    }
    factor = mapping.get(freq, 1.0)
    return amount * factor


def get_value_for_month(df: pd.DataFrame, month: int, column: str) -> float:
    match = df.loc[df["Maand"] == month, column]
    if match.empty:
        return float("nan")
    return float(match.iloc[0])


def simulate_plan(
    start_buffer: float,
    start_savings: float,
    start_investment: float,
    monthly_savings_phase1: float,
    monthly_invest_phase1: float,
    monthly_invest_phase2: float,
    months_phase1: int,
    months_phase2: int,
    savings_interest_pa: float,
    investment_return_pa: float,
    inflation_pa: float,
) -> pd.DataFrame:
    monthly_savings_interest = (1 + savings_interest_pa) ** (1 / 12) - 1
    monthly_invest_return = (1 + investment_return_pa) ** (1 / 12) - 1
    monthly_inflation = (1 + inflation_pa) ** (1 / 12) - 1

    savings_balance = start_savings
    investment_balance = start_investment
    buffer_amount = start_buffer

    rows: List[Dict[str, float]] = []
    total_months = months_phase1 + months_phase2
    inflation_index = 1.0

    for month in range(1, total_months + 1):
        in_phase1 = month <= months_phase1
        deposit_savings = monthly_savings_phase1 if in_phase1 else 0.0
        deposit_investments = (
            monthly_invest_phase1 if in_phase1 else monthly_invest_phase2
        )

        savings_balance = (savings_balance + deposit_savings) * (
            1 + monthly_savings_interest
        )
        investment_balance = (investment_balance + deposit_investments) * (
            1 + monthly_invest_return
        )

        inflation_index *= 1 + monthly_inflation
        total_nominal = buffer_amount + savings_balance + investment_balance
        total_real = total_nominal / inflation_index

        rows.append(
            {
                "Maand": month,
                "Fase": "Fase 1" if in_phase1 else "Fase 2",
                "Spaarrekening": round(savings_balance, 2),
                "Investeringen": round(investment_balance, 2),
                "Buffer": round(buffer_amount, 2),
                "Totaal (nominaal)": round(total_nominal, 2),
                "Inflatie Index": inflation_index,
                "Totaal (reëel)": round(total_real, 2),
                "Storting Sparen": deposit_savings,
                "Storting Beleggen": deposit_investments,
            }
        )

    return pd.DataFrame(rows)


def get_projection_frames() -> Tuple[pd.DataFrame, pd.DataFrame]:
    data = st.session_state.data_store
    df_avg = simulate_plan(
        start_buffer=data["buffer"]["amount"],
        start_savings=data["savings"]["start_balance"],
        start_investment=data["investments"]["start_balance"],
        monthly_savings_phase1=data["savings"]["monthly_contribution"],
        monthly_invest_phase1=data["investments"]["monthly_contribution_phase1"],
        monthly_invest_phase2=data["investments"]["monthly_contribution_phase2"],
        months_phase1=data["plan"]["months_phase1"],
        months_phase2=data["plan"]["months_phase2"],
        savings_interest_pa=data["savings"]["interest_rate_pa"],
        investment_return_pa=data["investments"]["avg_return_pa"],
        inflation_pa=data["plan"]["inflation_pa"],
    )
    df_good = simulate_plan(
        start_buffer=data["buffer"]["amount"],
        start_savings=data["savings"]["start_balance"],
        start_investment=data["investments"]["start_balance"],
        monthly_savings_phase1=data["savings"]["monthly_contribution"],
        monthly_invest_phase1=data["investments"]["monthly_contribution_phase1"],
        monthly_invest_phase2=data["investments"]["monthly_contribution_phase2"],
        months_phase1=data["plan"]["months_phase1"],
        months_phase2=data["plan"]["months_phase2"],
        savings_interest_pa=data["savings"]["interest_rate_pa"],
        investment_return_pa=data["investments"]["good_return_pa"],
        inflation_pa=data["plan"]["inflation_pa"],
    )
    return df_avg, df_good


def compute_cashflow_summary() -> Dict[str, float]:
    data = st.session_state.data_store
    income_df = data["income"].copy()
    expenses_df = data["expenses"].copy()

    income_df["Bedrag"] = pd.to_numeric(income_df["Bedrag"], errors="coerce").fillna(0.0)
    expenses_df["Bedrag"] = pd.to_numeric(
        expenses_df["Bedrag"], errors="coerce"
    ).fillna(0.0)

    income_df["Maandbedrag"] = income_df.apply(
        lambda row: freq_to_monthly(row["Frequentie"], float(row["Bedrag"])), axis=1
    )
    expenses_df["Maandbedrag"] = expenses_df.apply(
        lambda row: freq_to_monthly(row["Frequentie"], float(row["Bedrag"])), axis=1
    )

    total_income = float(income_df["Maandbedrag"].sum())
    total_expenses = float(expenses_df["Maandbedrag"].sum())

    plan = data["plan"]
    months_total = plan["months_phase1"] + plan["months_phase2"]
    if months_total > 0:
        average_invest = (
            data["investments"]["monthly_contribution_phase1"] * plan["months_phase1"]
            + data["investments"]["monthly_contribution_phase2"] * plan["months_phase2"]
        ) / months_total
    else:
        average_invest = 0.0

    savings_allocation = data["savings"]["monthly_contribution"]

    return {
        "income": total_income,
        "expenses": total_expenses,
        "savings_allocation": float(savings_allocation),
        "investment_allocation": float(average_invest),
        "net_cashflow": float(
            total_income - total_expenses - savings_allocation - average_invest
        ),
        "plan_months_total": months_total,
        "plan_months_phase1": plan["months_phase1"],
    }


def render_savings() -> None:
    st.header("💰 Spaarrekening")
    st.caption("Beheer je noodbuffer en maandelijkse storting.")

    savings = st.session_state.data_store["savings"]
    plan = st.session_state.data_store["plan"]
    buffer_data = st.session_state.data_store["buffer"]

    new_buffer = st.number_input(
        "Noodbuffer (EUR)",
        min_value=0.0,
        value=float(buffer_data["amount"]),
        step=500.0,
    )
    st.session_state.data_store["buffer"]["amount"] = new_buffer

    new_start_balance = st.number_input(
        "Start saldo spaarrekening (EUR)",
        min_value=0.0,
        value=float(savings["start_balance"]),
        step=500.0,
    )
    new_monthly = st.number_input(
        "Maandelijkse storting in Fase 1 (EUR)",
        min_value=0.0,
        value=float(savings["monthly_contribution"]),
        step=50.0,
    )
    new_interest = st.number_input(
        "Rente spaarrekening (%/jaar)",
        min_value=0.0,
        max_value=20.0,
        value=float(savings["interest_rate_pa"] * 100),
        step=0.1,
    )
    new_months_phase1 = st.number_input(
        "Duur Fase 1 (maanden)",
        min_value=1,
        max_value=120,
        value=int(plan["months_phase1"]),
    )

    st.session_state.data_store["savings"].update(
        {
            "start_balance": new_start_balance,
            "monthly_contribution": new_monthly,
            "interest_rate_pa": new_interest / 100,
        }
    )
    st.session_state.data_store["plan"]["months_phase1"] = new_months_phase1

    df_avg, df_good = get_projection_frames()

    st.subheader("Ontwikkeling spaarrekening")
    chart_df = pd.DataFrame(
        {
            "Maand": df_avg["Maand"],
            "Gemiddeld scenario": df_avg["Spaarrekening"],
            "Optimistisch scenario": df_good["Spaarrekening"],
        }
    ).set_index("Maand")
    st.line_chart(chart_df)

    saldo_phase1 = get_value_for_month(df_avg, new_months_phase1, "Spaarrekening")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Saldo na Fase 1", f"€ {saldo_phase1:,.0f}")
    with col2:
        st.metric(
            "Saldo einde plan (gemiddeld)", f"€ {df_avg.iloc[-1]['Spaarrekening']:,.0f}"
        )

    st.dataframe(
        df_avg[["Maand", "Fase", "Spaarrekening", "Storting Sparen"]],
        use_container_width=True,
    )

    if st.button("⬅️ Terug naar Home", key="back-savings"):
        st.session_state.active_page = "Home"
        st.experimental_rerun()


def render_investments() -> None:
    st.header("📈 Investeringen")
    st.caption("Stel je inleg en rendementsscenario's bij.")

    investments = st.session_state.data_store["investments"]
    plan = st.session_state.data_store["plan"]

    new_start = st.number_input(
        "Startwaarde beleggingen (EUR)",
        min_value=0.0,
        value=float(investments["start_balance"]),
        step=500.0,
    )
    new_phase1 = st.number_input(
        "Maandelijkse inleg Fase 1 (EUR)",
        min_value=0.0,
        value=float(investments["monthly_contribution_phase1"]),
        step=50.0,
    )
    new_phase2 = st.number_input(
        "Maandelijkse inleg Fase 2 (EUR)",
        min_value=0.0,
        value=float(investments["monthly_contribution_phase2"]),
        step=50.0,
    )
    new_months_phase2 = st.number_input(
        "Duur Fase 2 (maanden)",
        min_value=0,
        max_value=240,
        value=int(plan["months_phase2"]),
    )
    avg_return = st.number_input(
        "Gemiddeld rendement (%/jaar)",
        min_value=0.0,
        max_value=30.0,
        value=float(investments["avg_return_pa"] * 100),
        step=0.5,
    )
    good_return = st.number_input(
        "Optimistisch rendement (%/jaar)",
        min_value=0.0,
        max_value=30.0,
        value=float(investments["good_return_pa"] * 100),
        step=0.5,
    )
    inflation = st.number_input(
        "Inflatie (%/jaar)",
        min_value=0.0,
        max_value=15.0,
        value=float(st.session_state.data_store["plan"]["inflation_pa"] * 100),
        step=0.5,
    )

    st.session_state.data_store["investments"].update(
        {
            "start_balance": new_start,
            "monthly_contribution_phase1": new_phase1,
            "monthly_contribution_phase2": new_phase2,
            "avg_return_pa": avg_return / 100,
            "good_return_pa": good_return / 100,
        }
    )
    st.session_state.data_store["plan"].update(
        {"months_phase2": new_months_phase2, "inflation_pa": inflation / 100}
    )

    df_avg, df_good = get_projection_frames()

    st.subheader("Ontwikkeling beleggingen")
    chart_df = pd.DataFrame(
        {
            "Maand": df_avg["Maand"],
            "Gemiddeld scenario": df_avg["Investeringen"],
            "Optimistisch scenario": df_good["Investeringen"],
        }
    ).set_index("Maand")
    st.line_chart(chart_df)

    phase1_months = st.session_state.data_store["plan"]["months_phase1"]
    belegging_phase1 = get_value_for_month(df_avg, phase1_months, "Investeringen")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Beleggingen einde Fase 1", f"€ {belegging_phase1:,.0f}")
    with col2:
        st.metric("Beleggingen einde plan", f"€ {df_avg.iloc[-1]['Investeringen']:,.0f}")
    with col3:
        st.metric("Reëel vermogen", f"€ {df_avg.iloc[-1]['Totaal (reëel)']:,.0f}")

    st.dataframe(
        df_avg[["Maand", "Investeringen", "Storting Beleggen", "Totaal (nominaal)"]],
        use_container_width=True,
    )

    if st.button("⬅️ Terug naar Home", key="back-investments"):
        st.session_state.active_page = "Home"
        st.experimental_rerun()


def render_income() -> None:
    st.header("💼 Inkomen")
    st.caption("Werk al je inkomensstromen bij.")

    st.write(
        "Gebruik de tabel hieronder om bronnen, bedragen en frequenties aan te passen. "
        "De wijzigingen worden direct opgeslagen en gebruikt in andere pagina's."
    )

    income_df = st.data_editor(
        st.session_state.data_store["income"],
        num_rows="dynamic",
        use_container_width=True,
        key="income-editor",
    )
    income_df = income_df[INCOME_COLUMNS]
    income_df["Bedrag"] = pd.to_numeric(income_df["Bedrag"], errors="coerce").fillna(0.0)
    st.session_state.data_store["income"] = income_df

    cashflow = compute_cashflow_summary()
    st.metric("Totale inkomens per maand", f"€ {cashflow['income']:,.0f}")

    if st.button("⬅️ Terug naar Home", key="back-income"):
        st.session_state.active_page = "Home"
        st.experimental_rerun()


def render_budget() -> None:
    st.header("🧮 Budget")
    st.caption("Analyseer je maandelijkse cashflow en allocatie.")

    expenses_df = st.data_editor(
        st.session_state.data_store["expenses"],
        num_rows="dynamic",
        use_container_width=True,
        key="expenses-editor",
    )
    expenses_df = expenses_df[EXPENSE_COLUMNS]
    expenses_df["Bedrag"] = pd.to_numeric(
        expenses_df["Bedrag"], errors="coerce"
    ).fillna(0.0)
    st.session_state.data_store["expenses"] = expenses_df

    cashflow = compute_cashflow_summary()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Inkomen (pm)", f"€ {cashflow['income']:,.0f}")
    with col2:
        st.metric("Uitgaven (pm)", f"€ {cashflow['expenses']:,.0f}")
    with col3:
        st.metric("Sparen (pm)", f"€ {cashflow['savings_allocation']:,.0f}")
    with col4:
        st.metric("Investeren (pm)", f"€ {cashflow['investment_allocation']:,.0f}")

    st.subheader("Cashflow overzicht")
    summary_df = pd.DataFrame(
        {
            "Categorie": ["Inkomen", "Uitgaven", "Sparen", "Investeren", "Netto"],
            "Maandbedrag": [
                cashflow["income"],
                -cashflow["expenses"],
                -cashflow["savings_allocation"],
                -cashflow["investment_allocation"],
                cashflow["net_cashflow"],
            ],
        }
    ).set_index("Categorie")
    st.bar_chart(summary_df)

    if cashflow["net_cashflow"] >= 0:
        st.success(
            f"Je houdt € {cashflow['net_cashflow']:,.0f} per maand over na sparen en investeren."
        )
    else:
        st.error(
            f"Je komt € {abs(cashflow['net_cashflow']):,.0f} per maand tekort na sparen en investeren."
        )

    st.info(
        "Wijzig inkomens, uitgaven of inleg op andere pagina's om dit overzicht direct bij te werken."
    )

    if st.button("⬅️ Terug naar Home", key="back-budget"):
        st.session_state.active_page = "Home"
        st.experimental_rerun()


def render_wishlist() -> None:
    st.header("🎯 Wishlist")
    st.caption("Organiseer spaardoelen en voortgang over de planningshorizon.")

    wishlist_df = st.data_editor(
        st.session_state.data_store["wishlist"],
        num_rows="dynamic",
        use_container_width=True,
        key="wishlist-editor",
    )
    wishlist_df = wishlist_df[WISHLIST_COLUMNS]
    wishlist_df["Doelbedrag"] = pd.to_numeric(
        wishlist_df["Doelbedrag"], errors="coerce"
    ).fillna(0.0)
    wishlist_df["Maandelijkse Bijdrage"] = pd.to_numeric(
        wishlist_df["Maandelijkse Bijdrage"], errors="coerce"
    ).fillna(0.0)
    st.session_state.data_store["wishlist"] = wishlist_df

    cashflow = compute_cashflow_summary()
    df_avg, _ = get_projection_frames()
    total_future_nominal = df_avg.iloc[-1]["Totaal (nominaal)"]

    total_goal_contrib = float(wishlist_df["Maandelijkse Bijdrage"].sum())
    st.metric("Totale maandelijkse doel-bijdrage", f"€ {total_goal_contrib:,.0f}")

    plan_months_total = cashflow["plan_months_total"]

    for _, row in wishlist_df.iterrows():
        goal = str(row["Doel"]) if not pd.isna(row["Doel"]) else "Onbenoemd doel"
        goal_amount = float(row["Doelbedrag"])
        monthly_contrib = float(row["Maandelijkse Bijdrage"])

        with st.container(border=True):
            st.subheader(goal)
            st.write(f"Doelbedrag: € {goal_amount:,.0f}")
            st.write(f"Maandelijkse bijdrage: € {monthly_contrib:,.0f}")

            if goal_amount > 0 and monthly_contrib > 0:
                months_needed = goal_amount / monthly_contrib
                if plan_months_total > 0:
                    progress = min(1.0, plan_months_total / months_needed)
                    progress_text = (
                        f"{min(plan_months_total, months_needed):.0f} van {months_needed:.0f}"
                        " geplande maanden"
                    )
                else:
                    progress = 0.0
                    progress_text = "Geen planduur ingesteld"
            elif goal_amount > 0:
                progress = 0.0
                months_needed = math.inf
                progress_text = "Geen maandelijkse bijdrage ingesteld"
            else:
                progress = 0.0
                months_needed = math.inf
                progress_text = "Voeg een doelbedrag toe"

            st.progress(progress, text=progress_text)

            if goal_amount > 0:
                coverage = min(1.0, total_future_nominal / goal_amount)
                st.caption(
                    f"Scenario dekking (gemiddeld): {coverage * 100:,.0f}% van het doel"
                )

            if not math.isinf(months_needed) and monthly_contrib > 0:
                st.caption(
                    f"Bij huidige bijdrage behaal je dit doel in ongeveer {months_needed:.0f} maanden."
                )

    if st.button("⬅️ Terug naar Home", key="back-wishlist"):
        st.session_state.active_page = "Home"
        st.experimental_rerun()


def render_home() -> None:
    st.title("📱 Toekomstbestendig Beleggen")
    st.caption(
        "Overzicht van je spaargeld, investeringen, inkomsten en doelen op één plek."
    )

    df_avg, df_good = get_projection_frames()
    final_avg = df_avg.iloc[-1]
    cashflow = compute_cashflow_summary()

    target = st.session_state.data_store["plan"]["target_savings"]
    savings_now = st.session_state.data_store["savings"]["start_balance"]
    target_progress = min(1.0, savings_now / target if target else 0.0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Spaarrekening aan einde plan", f"€ {final_avg['Spaarrekening']:,.0f}")
    with col2:
        st.metric("Investeringen aan einde plan", f"€ {final_avg['Investeringen']:,.0f}")
    with col3:
        st.metric("Netto cashflow per maand", f"€ {cashflow['net_cashflow']:,.0f}")
    with col4:
        st.metric("Doel spaarrekening", f"€ {target:,.0f}")

    st.progress(target_progress, text=f"{target_progress * 100:,.0f}% van spaardoel bereikt")

    st.markdown("---")

    cards: List[Page] = [
        Page("Spaarrekening", "💰", "Stel je noodbuffer en rente in.", render_savings),
        Page(
            "Investeringen",
            "📈",
            "Bekijk je investeringsscenario's en pas rendementen aan.",
            render_investments,
        ),
        Page(
            "Inkomen",
            "💼",
            "Beheer je inkomensstromen en upload nieuwe data.",
            render_income,
        ),
        Page(
            "Budget",
            "🧮",
            "Controleer maandelijkse cashflow en allocatie naar doelen.",
            render_budget,
        ),
        Page(
            "Wishlist",
            "🎯",
            "Organiseer spaardoelen en voortgang.",
            render_wishlist,
        ),
    ]

    st.subheader("Navigatie")
    card_columns = st.columns(3)
    for index, page in enumerate(cards):
        column = card_columns[index % 3]
        with column:
            with st.container(border=True):
                st.subheader(f"{page.icon} {page.name}")
                st.write(page.description)
                if st.button(f"Open {page.name}", key=f"card-{page.name}"):
                    st.session_state.active_page = page.name
                    st.experimental_rerun()

    st.markdown("---")
    st.subheader("📤 Financiële data uploaden")
    st.write(
        "Upload CSV-bestanden om inkomens, uitgaven of doelen bij te werken. "
        "Gebruik kolommen die overeenkomen met de voorbeeldtabellen."
    )

    dataset_choice = st.selectbox(
        "Kies dataset om te vervangen", ["Inkomen", "Uitgaven", "Wishlist"], index=0
    )
    uploaded_file = st.file_uploader("Sleep hier een CSV-bestand", type="csv")

    if uploaded_file is not None:
        try:
            new_df = pd.read_csv(uploaded_file)
            if dataset_choice == "Inkomen":
                if not set(INCOME_COLUMNS).issubset(new_df.columns):
                    st.error("CSV mist vereiste kolommen voor inkomens.")
                else:
                    st.session_state.data_store["income"] = new_df[INCOME_COLUMNS]
                    st.success("Inkomensgegevens bijgewerkt.")
            elif dataset_choice == "Uitgaven":
                if not set(EXPENSE_COLUMNS).issubset(new_df.columns):
                    st.error("CSV mist vereiste kolommen voor uitgaven.")
                else:
                    st.session_state.data_store["expenses"] = new_df[EXPENSE_COLUMNS]
                    st.success("Uitgavengegevens bijgewerkt.")
            else:
                if not set(WISHLIST_COLUMNS).issubset(new_df.columns):
                    st.error("CSV mist vereiste kolommen voor doelen.")
                else:
                    st.session_state.data_store["wishlist"] = new_df[WISHLIST_COLUMNS]
                    st.success("Spaardoelen bijgewerkt.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Kon bestand niet lezen: {exc}")

    col_export1, col_export2, col_export3 = st.columns(3)
    with col_export1:
        st.download_button(
            "⬇️ Download inkomens",
            data=st.session_state.data_store["income"].to_csv(index=False).encode("utf-8"),
            file_name="inkomen.csv",
            mime="text/csv",
        )
    with col_export2:
        st.download_button(
            "⬇️ Download uitgaven",
            data=st.session_state.data_store["expenses"].to_csv(index=False).encode("utf-8"),
            file_name="uitgaven.csv",
            mime="text/csv",
        )
    with col_export3:
        st.download_button(
            "⬇️ Download doelen",
            data=st.session_state.data_store["wishlist"].to_csv(index=False).encode("utf-8"),
            file_name="wishlist.csv",
            mime="text/csv",
        )


def render_login() -> None:
    st.title("🔐 Toekomstbestendig Beleggen")
    st.caption("Log in om je persoonlijke financiële dashboard te openen.")

    with st.form("login-form"):
        username = st.text_input("Gebruikersnaam")
        password = st.text_input("Wachtwoord", type="password")
        submitted = st.form_submit_button("Inloggen")

    if submitted:
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.success("Succesvol ingelogd!")
            st.experimental_rerun()
        else:
            st.error("Ongeldige gebruikersnaam of wachtwoord.")

    st.info("Gebruik testaccount **planner / veiligwachtwoord** om te starten.")


def main() -> None:
    init_session_state()

    if not st.session_state.authenticated:
        render_login()
        return

    pages: Dict[str, Callable[[], None]] = {
        "Home": render_home,
        "Spaarrekening": render_savings,
        "Investeringen": render_investments,
        "Inkomen": render_income,
        "Budget": render_budget,
        "Wishlist": render_wishlist,
    }

    st.sidebar.title("Navigatie")
    st.sidebar.markdown(f"**Ingelogd als:** {st.session_state.username}")

    if st.sidebar.button("🏠 Naar Home", key="sidebar-home"):
        st.session_state.active_page = "Home"
        st.experimental_rerun()

    options = list(pages.keys())
    current_index = options.index(st.session_state.active_page)
    selected_page = st.sidebar.selectbox(
        "Ga naar pagina", options, index=current_index, key="page-select"
    )
    if selected_page != st.session_state.active_page:
        st.session_state.active_page = selected_page
        st.experimental_rerun()

    if st.sidebar.button("🚪 Log uit", key="sidebar-logout"):
        logout()

    page_renderer = pages.get(st.session_state.active_page, render_home)
    page_renderer()


if __name__ == "__main__":
    main()
