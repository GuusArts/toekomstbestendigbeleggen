
# Toekomstbestendig Beleggen (zonder matplotlib)

Deze versie gebruikt alleen Streamlit, pandas en numpy. Zo voorkom je ModuleNotFoundErrors bij deployen.

## Deploy (Streamlit Cloud)
1) Plaats **app.py**, **requirements.txt**, **README.txt** in de **root** van je GitHub-repo.
2) Streamlit Cloud → New app → kies repo → app file: `app.py` → Deploy.

## Lokaal draaien
pip install -r requirements.txt
streamlit run app.py
