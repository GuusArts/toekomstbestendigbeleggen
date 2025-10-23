"""Financial computations shared between the pages."""
from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd


def freq_to_monthly(freq: str, amount: float) -> float:
    mapping = {
        "Maandelijks": 1.0,
        "Jaarlijks": 1.0 / 12.0,
        "Eenmalig": 1.0 / 12.0,
    }
    factor = mapping.get(freq, 1.0)
    return amount * factor


def simulate_plan(
    *,
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

    rows: list[dict] = []
    total_months = months_phase1 + months_phase2
    inflation_index = 1.0

    columns = [
        "Maand",
        "Fase",
        "Spaarrekening",
        "Investeringen",
        "Buffer",
        "Totaal (nominaal)",
        "Inflatie Index",
        "Totaal (reëel)",
        "Storting Sparen",
        "Storting Beleggen",
    ]

    if total_months <= 0:
        return pd.DataFrame(columns=columns)

    for month in range(1, total_months + 1):
        in_phase1 = month <= months_phase1
        deposit_savings = monthly_savings_phase1 if in_phase1 else 0.0
        deposit_investments = monthly_invest_phase1 if in_phase1 else monthly_invest_phase2

        savings_balance = (savings_balance + deposit_savings) * (1 + monthly_savings_interest)
        investment_balance = (investment_balance + deposit_investments) * (1 + monthly_invest_return)

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

    return pd.DataFrame(rows, columns=columns)


def get_projection_frames(data: Dict[str, object]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df_avg = simulate_plan(
        start_buffer=float(data["buffer"]["amount"]),
        start_savings=float(data["savings"]["start_balance"]),
        start_investment=float(data["investments"]["start_balance"]),
        monthly_savings_phase1=float(data["savings"]["monthly_contribution"]),
        monthly_invest_phase1=float(data["investments"]["monthly_contribution_phase1"]),
        monthly_invest_phase2=float(data["investments"]["monthly_contribution_phase2"]),
        months_phase1=int(data["plan"]["months_phase1"]),
        months_phase2=int(data["plan"]["months_phase2"]),
        savings_interest_pa=float(data["savings"]["interest_rate_pa"]),
        investment_return_pa=float(data["investments"]["avg_return_pa"]),
        inflation_pa=float(data["plan"]["inflation_pa"]),
    )
    df_good = simulate_plan(
        start_buffer=float(data["buffer"]["amount"]),
        start_savings=float(data["savings"]["start_balance"]),
        start_investment=float(data["investments"]["start_balance"]),
        monthly_savings_phase1=float(data["savings"]["monthly_contribution"]),
        monthly_invest_phase1=float(data["investments"]["monthly_contribution_phase1"]),
        monthly_invest_phase2=float(data["investments"]["monthly_contribution_phase2"]),
        months_phase1=int(data["plan"]["months_phase1"]),
        months_phase2=int(data["plan"]["months_phase2"]),
        savings_interest_pa=float(data["savings"]["interest_rate_pa"]),
        investment_return_pa=float(data["investments"]["good_return_pa"]),
        inflation_pa=float(data["plan"]["inflation_pa"]),
    )
    return df_avg, df_good


def get_value_for_month(df: pd.DataFrame, month: int, column: str) -> float:
    match = df.loc[df["Maand"] == month, column]
    if match.empty:
        return float("nan")
    return float(match.iloc[0])


def compute_cashflow_summary(data: Dict[str, object]) -> Dict[str, float]:
    income_df = data["income"].copy()
    expenses_df = data["expenses"].copy()

    income_df["Bedrag"] = pd.to_numeric(income_df.get("Bedrag"), errors="coerce").fillna(0.0)
    expenses_df["Bedrag"] = pd.to_numeric(expenses_df.get("Bedrag"), errors="coerce").fillna(0.0)

    income_df["Maandbedrag"] = income_df.apply(
        lambda row: freq_to_monthly(str(row.get("Frequentie", "")), float(row.get("Bedrag", 0.0))),
        axis=1,
    )
    expenses_df["Maandbedrag"] = expenses_df.apply(
        lambda row: freq_to_monthly(str(row.get("Frequentie", "")), float(row.get("Bedrag", 0.0))),
        axis=1,
    )

    total_income = float(income_df["Maandbedrag"].sum())
    total_expenses = float(expenses_df["Maandbedrag"].sum())

    plan = data["plan"]
    months_total = int(plan["months_phase1"]) + int(plan["months_phase2"])
    if months_total > 0:
        average_invest = (
            float(data["investments"]["monthly_contribution_phase1"]) * float(plan["months_phase1"])
            + float(data["investments"]["monthly_contribution_phase2"]) * float(plan["months_phase2"])
        ) / months_total
    else:
        average_invest = 0.0

    savings_allocation = float(data["savings"]["monthly_contribution"])

    return {
        "income": total_income,
        "expenses": total_expenses,
        "savings_allocation": savings_allocation,
        "investment_allocation": float(average_invest),
        "net_cashflow": float(total_income - total_expenses - savings_allocation - average_invest),
        "plan_months_total": months_total,
        "plan_months_phase1": int(plan["months_phase1"]),
    }
