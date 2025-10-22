
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- Page setup (mobile-friendly) ---
st.set_page_config(
    page_title="Toekomstbestendig Beleggen",
    page_icon="📱",
    layout="wide",
)

# Simple CSS tweaks for better mobile touch targets
st.markdown(
    '''
    <style>
    .stButton>button { padding: 0.8rem 1.2rem; font-size: 1rem; }
    .stNumberInput>div>div>input { font-size: 1rem; }
    .metric-container {gap: 0.75rem;}
    @media (max-width: 780px) {
        .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    }
    </style>
    ''',
    unsafe_allow_html=True
)

st.title("📱 Toekomstbestendig Beleggen")
st.caption("Simuleer jouw woning- en beleggingsplan (Fase 1: naar je woning · Fase 2: lange termijn)")

# --- Sidebar inputs ---
st.sidebar.header("🔧 Instellingen")
st.sidebar.write("Pas je aannames aan en bekijk direct de impact.")

# Startwaarden (gebaseerd op ons plan)
start_buffer = st.sidebar.number_input("Start noodbuffer (EUR)", 0, 1_000_000, 6000, 100)
start_woning = st.sidebar.number_input("Start woningfonds (EUR)", 0, 1_000_000, 10000, 100)
start_belegging = st.sidebar.number_input("Start belegging (EUR)", 0, 1_000_000, 3500, 100)

# Maandelijkse inleg
m_sparen_phase1 = st.sidebar.number_input("Maandelijkse storting woningfonds (Fase 1)", 0, 100_000, 250, 50)
m_beleggen_phase1 = st.sidebar.number_input("Maandelijkse inleg belegging (Fase 1)", 0, 100_000, 100, 50)
m_beleggen_phase2 = st.sidebar.number_input("Maandelijkse inleg belegging (Fase 2)", 0, 100_000, 250, 50)

# Duur
months_phase1 = st.sidebar.number_input("Duur Fase 1 (maanden)", 1, 120, 24, 1)
months_phase2 = st.sidebar.number_input("Duur Fase 2 (maanden)", 0, 240, 60, 1)

# Rentes & inflatie
rente_sparen_pa = st.sidebar.number_input("Rente spaarrekening (%/jaar)", 0.0, 20.0, 2.75, 0.05) / 100.0
rendement_avg_pa = st.sidebar.number_input("Rendement belegging gemiddeld (%/jaar)", 0.0, 30.0, 5.0, 0.5) / 100.0
rendement_good_pa = st.sidebar.number_input("Rendement belegging goed scenario (%/jaar)", 0.0, 30.0, 7.0, 0.5) / 100.0
inflatie_pa = st.sidebar.number_input("Inflatie (%/jaar)", 0.0, 20.0, 3.5, 0.5) / 100.0

# Doel
target_woning = st.sidebar.number_input("Doel woningfonds (EUR)", 0, 1_000_000, 27500, 500)

# --- Simulation function ---
def simulate_plan(
    start_buffer, start_woning, start_belegging,
    m_sparen_phase1, m_beleggen_phase1, m_beleggen_phase2,
    months_phase1, months_phase2,
    rente_sparen_pa, rendement_pa, inflatie_pa
):
    m_sparen_pm = (1 + rente_sparen_pa) ** (1/12) - 1
    m_rendement_pm = (1 + rendement_pa) ** (1/12) - 1
    m_inflatie_pm = (1 + inflatie_pa) ** (1/12) - 1

    woning = start_woning
    beleg = start_belegging
    buffer_val = start_buffer

    rows = []
    total_months = months_phase1 + months_phase2
    infl_idx = 1.0

    for m in range(1, total_months + 1):
        in_phase1 = m <= months_phase1
        stort_sparen = m_sparen_phase1 if in_phase1 else 0
        stort_beleg = m_beleggen_phase1 if in_phase1 else m_beleggen_phase2

        woning = (woning + stort_sparen) * (1 + m_sparen_pm)
        beleg = (beleg + stort_beleg) * (1 + m_rendement_pm)

        infl_idx *= (1 + m_inflatie_pm)
        total_nominaal = buffer_val + woning + beleg
        total_reel = total_nominaal / infl_idx

        rows.append({
            "Maand": m,
            "Fase": "Fase 1" if in_phase1 else "Fase 2",
            "Woningfonds": round(woning, 2),
            "Belegging": round(beleg, 2),
            "Buffer": round(buffer_val, 2),
            "Totaal (nominaal)": round(total_nominaal, 2),
            "Inflatie Index": infl_idx,
            "Totaal (reëel)": round(total_reel, 2),
            "Storting Sparen": stort_sparen,
            "Storting Beleggen": stort_beleg,
        })
    return pd.DataFrame(rows)

# Run both scenarios
df_avg = simulate_plan(
    start_buffer, start_woning, start_belegging,
    m_sparen_phase1, m_beleggen_phase1, m_beleggen_phase2,
    months_phase1, months_phase2,
    rente_sparen_pa, rendement_avg_pa, inflatie_pa
)
df_good = simulate_plan(
    start_buffer, start_woning, start_belegging,
    m_sparen_phase1, m_beleggen_phase1, m_beleggen_phase2,
    months_phase1, months_phase2,
    rente_sparen_pa, rendement_good_pa, inflatie_pa
)

# --- KPIs ---
c1, c2, c3, c4 = st.columns(4)
with c1:
    val = df_avg.loc[df_avg["Maand"]==months_phase1, "Woningfonds"].values[0]
    st.metric("Woningfonds maand 24 (gem.)", f"{val:,.0f} EUR")
with c2:
    val = df_avg.loc[df_avg["Maand"]==months_phase1, "Belegging"].values[0]
    st.metric("Belegging maand 24 (gem.)", f"{val:,.0f} EUR")
with c3:
    val = df_avg.loc[df_avg["Maand"]==months_phase1, "Totaal (nominaal)"].values[0]
    st.metric("Totaal nominaal maand 24 (gem.)", f"{val:,.0f} EUR")
with c4:
    gehaald = "✅" if df_avg.loc[df_avg['Maand']==months_phase1, 'Woningfonds'].values[0] >= target_woning else "❌"
    st.metric("Doel woningfonds gehaald?", gehaald)

st.divider()

# --- Charts (matplotlib, single-plot each) ---
def line_chart(x, ys, labels, title, xlabel, ylabel):
    fig, ax = plt.subplots()
    for y, label in zip(ys, labels):
        ax.plot(x, y, label=label)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    st.pyplot(fig)

st.subheader("📈 Woningfonds groei (Fase 1 + Fase 2)")
line_chart(
    df_avg["Maand"],
    [df_avg["Woningfonds"], df_good["Woningfonds"]],
    ["Gemiddeld (5%)", "Goed (7%)"],
    "Woningfonds over tijd",
    "Maand",
    "Waarde (EUR)",
)

st.subheader("📈 Beleggingsgroei (ETF)")
line_chart(
    df_avg["Maand"],
    [df_avg["Belegging"], df_good["Belegging"]],
    ["Gemiddeld (5%)", "Goed (7%)"],
    "Beleggingswaarde over tijd",
    "Maand",
    "Waarde (EUR)",
)

st.subheader("💼 Totaal vermogen (nominaal)")
line_chart(
    df_avg["Maand"],
    [df_avg["Totaal (nominaal)"], df_good["Totaal (nominaal)"]],
    ["Gemiddeld (5%)", "Goed (7%)"],
    "Totaal nominaal vermogen",
    "Maand",
    "Waarde (EUR)",
)

st.subheader("🛡️ Koopkracht (reëel, gecorrigeerd voor inflatie)")
line_chart(
    df_avg["Maand"],
    [df_avg["Totaal (reëel)"], df_good["Totaal (reëel)"]],
    ["Gemiddeld (5%)", "Goed (7%)"],
    "Totaal reëel vermogen",
    "Maand",
    "Waarde (EUR)",
)

st.divider()
st.subheader("📋 Detailtabel (Gemiddeld scenario)")
st.dataframe(df_avg, use_container_width=True)

# Downloads
st.download_button(
    "⬇️ Download data (Gemiddeld) als CSV",
    data=df_avg.to_csv(index=False).encode("utf-8"),
    file_name="planner_data_gemiddeld.csv",
    mime="text/csv"
)
st.download_button(
    "⬇️ Download data (Goed) als CSV",
    data=df_good.to_csv(index=False).encode("utf-8"),
    file_name="planner_data_goed.csv",
    mime="text/csv"
)

st.info(
    "Tip: zet deze webapp op je telefoon als 'App': open de link, "
    "druk op delen en kies 'Zet op beginscherm' (iOS) of 'Toevoegen aan startscherm' (Android)."
)
