
# Toekomstbestendig Beleggen (Webapp)

Een mobiele, aanpasbare Streamlit webapp om jouw woning- en beleggingsplan te simuleren.

## Functies
- Fase 1: route naar je woning (woningfonds + beleggen)
- Fase 2: lange termijn beleggen
- Scenario's: gemiddeld (5%) & goed (7%)
- Grafieken: woningfonds, belegging, totaal nominaal, totaal reëel (koopkracht)
- CSV-downloads

## Quickstart (lokaal)
1) Python 3.10+ installeren
2) In deze map:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

## Online hosten (aanbevolen)
1) Maak een **gratis Streamlit Community Cloud** account: https://streamlit.io/cloud
2) Upload deze 3 files naar een nieuwe GitHub repo (bijv. 'toekomstbestendigbeleggen').
3) In Streamlit Cloud: 'New app' → koppel je repo → kies branch 'main' → app file: `app.py`
4) Deploy. Je krijgt een URL in de vorm: `https://<jouwnaam>-toekomstbestendigbeleggen.streamlit.app`
5) Open op je telefoon en kies 'Toevoegen aan startscherm' voor app-ervaring.

## Tips
- Pas bedragen aan in de zijbalk om je eigen situatie te simuleren.
- Bewaar de link als app-icoon op je telefoon.
