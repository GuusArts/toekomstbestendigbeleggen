from __future__ import annotations

import json

import streamlit as st

from lib import auth, data_store, finance, ui

st.set_page_config(
    page_title="Toekomstbestendig Beleggen",
    page_icon="📱",
    layout="wide",
)


CARD_DEFINITIONS = [
    {
        "title": "Spaarrekening",
        "icon": "💰",
        "description": "Beheer je noodbuffer en maandelijkse stortingen.",
        "page": "pages/01_Spaarrekening.py",
    },
    {
        "title": "Investeringen",
        "icon": "📈",
        "description": "Simuleer verschillende rendementsscenario's voor je portefeuille.",
        "page": "pages/02_Investeringen.py",
    },
    {
        "title": "Inkomen",
        "icon": "💼",
        "description": "Werk alle inkomensstromen bij in één overzicht.",
        "page": "pages/03_Inkomen.py",
    },
    {
        "title": "Budget",
        "icon": "🧮",
        "description": "Analyseer je maandelijkse cashflow en allocatie.",
        "page": "pages/04_Budget.py",
    },
    {
        "title": "Wishlist",
        "icon": "🎯",
        "description": "Zet spaardoelen uit en volg de voortgang.",
        "page": "pages/05_Wishlist.py",
    },
]


def _render_sidebar(user: auth.UserIdentity) -> None:
    with st.sidebar:
        st.header("👋 Welkom")
        st.write(user.name or user.email)
        if user.picture:
            st.image(user.picture, width=120)
        st.divider()
        st.page_link("app.py", label="🏠 Home")
        for item in CARD_DEFINITIONS:
            st.page_link(item["page"], label=f"{item['icon']} {item['title']}")
        st.divider()
        if st.button("Afmelden", use_container_width=True):
            auth.logout()

        st.caption(
            "Deze app gebruikt Single Sign-On. Configureer je identity provider in "
            "`secrets.toml` om toegang te krijgen."
        )


def _render_import_export_controls() -> None:
    col_upload, col_download = st.columns([3, 2])
    with col_upload:
        uploaded = st.file_uploader(
            "Upload een export (JSON)",
            type=["json"],
            accept_multiple_files=False,
        )
        if uploaded is not None:
            try:
                data_store.import_payload(uploaded.read())
            except json.JSONDecodeError:
                st.error("Het bestand kon niet worden gelezen. Zorg dat het JSON-formaat klopt.")
            else:
                st.success("Gegevens succesvol geïmporteerd.")
                st.experimental_rerun()

    with col_download:
        export_bytes = data_store.export_payload()
        st.download_button(
            "Download mijn data",
            data=export_bytes,
            file_name="financieel_dashboard.json",
            mime="application/json",
            use_container_width=True,
        )


def _render_summary(data: dict[str, object]) -> None:
    st.subheader("Samenvatting cashflow")
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

    net = summary["net_cashflow"]
    bar_value = 0.5 + max(min(net / 2000.0, 0.5), -0.5)
    ui.safe_progress(
        bar_value,
        text=f"Netto cashflow: € {net:,.0f} per maand",
    )


def _render_cards() -> None:
    st.subheader("Kies een onderdeel")
    rows = [CARD_DEFINITIONS[i : i + 3] for i in range(0, len(CARD_DEFINITIONS), 3)]
    for row in rows:
        columns = st.columns(len(row))
        for column, card in zip(columns, row):
            with column, ui.bordered_container(border=True):
                st.markdown(f"### {card['icon']} {card['title']}")
                st.write(card["description"])
                st.page_link(card["page"], label="Open", icon="➡️")


def main() -> None:
    user = auth.require_user()
    data_store.ensure_user_store(user.email)
    _render_sidebar(user)

    st.title("Toekomstbestendig Beleggen")
    st.caption(
        "Organiseer en analyseer je financiële huishouding. Alle gegevens blijven per gebruiker "
        "gescheiden en zijn uitsluitend toegankelijk na SSO-aanmelding."
    )

    _render_import_export_controls()
    data = data_store.get_active_store()
    _render_summary(data)
    _render_cards()


if __name__ == "__main__":
    main()
