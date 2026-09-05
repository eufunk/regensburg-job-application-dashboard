"""Firmenliste Regensburg & Umgebung - zweite Seite des Dashboards.

Zeigt die handgepflegte Firmenliste (Firmen_Softwareentwicklung.txt) inkl. Ort,
Einschätzung/Notizen und - verknüpft mit den erfassten Bewerbungen - wie oft und
für welche Stellen bei jeder Firma bereits beworben wurde.

Je Status (Beworben / Noch nicht beworben / Nicht weiter verfolgen) ein eigener Tab
mit nur den dort relevanten Spalten, damit die Tabelle übersichtlich bleibt.
"""

import os

import pandas as pd
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIRMENLISTE_CSV = os.path.join(PROJECT_ROOT, "data", "firmenliste.csv")
WEITERE_CSV = os.path.join(PROJECT_ROOT, "data", "weitere_bewerbungen.csv")

st.set_page_config(page_title="Firmenliste", page_icon="🏢", layout="wide")

st.title("🏢 Firmenliste Regensburg & Umgebung")


@st.cache_data
def get_firmen():
    return pd.read_csv(FIRMENLISTE_CSV).fillna("")


@st.cache_data
def get_weitere_bewerbungen():
    if not os.path.exists(WEITERE_CSV):
        return pd.DataFrame()
    return pd.read_csv(WEITERE_CSV).fillna("")


df = get_firmen()
weitere = get_weitere_bewerbungen()

if df.empty:
    st.warning("Keine Firmen gefunden. Bitte zuerst `python export_firmenliste.py` ausführen.")
    st.stop()

RENAME = {
    "datum": "Datum",
    "firma": "Firma",
    "ort": "Adresse",
    "art": "Art",
    "schwerpunkt": "Schwerpunkt",
    "notizen": "Notizen",
    "rueckmeldung": "Rückmeldung",
    "anzahl_bewerbungen": "Anzahl Bewerbungen",
    "beworbene_stellen": "Beworbene Stellen (Datum)",
    "grund": "Grund",
    "erste_bewerbung": "Erste Bewerbung",
    "letzte_bewerbung": "Letzte Bewerbung",
}

# --- KPIs --------------------------------------------------------------------
beworben = df[df["status"] == "BEWORBEN"]
noch_nicht = df[df["status"] == "NOCH NICHT"]
nicht_weiter = df[df["status"].str.contains("NICHT WEITER")]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Firmen in der Liste", len(df))
col2.metric("Beworben", len(beworben))
col3.metric("Noch nicht beworben", len(noch_nicht))
col4.metric("Nicht weiter verfolgt", len(nicht_weiter))
col5.metric("Weitere Bewerbungen", len(weitere))

st.divider()

tab_beworben, tab_noch_nicht, tab_nicht_weiter, tab_weitere = st.tabs([
    f"✅ Beworben ({len(beworben)})",
    f"🕓 Noch nicht beworben ({len(noch_nicht)})",
    f"🚫 Nicht weiter verfolgen ({len(nicht_weiter)})",
    f"📋 Weitere Bewerbungen ({len(weitere)})",
])

with tab_beworben:
    spalten = ["datum", "firma", "ort", "art", "schwerpunkt", "notizen",
               "rueckmeldung", "anzahl_bewerbungen", "beworbene_stellen"]
    anzeige = beworben[spalten].rename(columns=RENAME)
    st.dataframe(anzeige, use_container_width=True, hide_index=True)

with tab_noch_nicht:
    spalten = ["firma", "ort", "art", "schwerpunkt", "notizen"]
    anzeige = noch_nicht[spalten].rename(columns=RENAME)
    st.dataframe(anzeige, use_container_width=True, hide_index=True)

with tab_nicht_weiter:
    gruende = ["Alle"] + sorted(nicht_weiter["grund"].unique())
    gewaehlter_grund = st.selectbox("Grund", gruende)
    gefiltert = nicht_weiter if gewaehlter_grund == "Alle" else nicht_weiter[nicht_weiter["grund"] == gewaehlter_grund]

    spalten = ["firma", "ort", "grund", "notizen"]
    anzeige = gefiltert[spalten].rename(columns=RENAME)
    st.dataframe(anzeige, use_container_width=True, hide_index=True)

with tab_weitere:
    st.caption(
        "Firmen, an die bereits beworben wurde, die aber (noch) nicht in der "
        "handgepflegten Firmenliste stehen - z.B. weil die Bewerbung vor Beginn der Liste war."
    )
    if weitere.empty:
        st.info("Keine weiteren Bewerbungen gefunden.")
    else:
        spalten = ["firma", "ort", "erste_bewerbung", "letzte_bewerbung", "anzahl_bewerbungen", "beworbene_stellen"]
        anzeige = weitere[spalten].rename(columns=RENAME)
        st.dataframe(anzeige, use_container_width=True, hide_index=True)
