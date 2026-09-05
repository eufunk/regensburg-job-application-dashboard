"""Firmenliste Regensburg & Umgebung - zweite Seite des Dashboards.

Zeigt die handgepflegte Firmenliste (Firmen_Softwareentwicklung.txt) inkl. Ort,
Einschätzung/Notizen, dem automatisch aus den Postfächern ermittelten Antwort-
Status - und, verknüpft mit den erfassten Bewerbungen - wie oft und für welche
Stellen bei jeder Firma bereits beworben wurde.

Je Status (Beworben / Noch nicht beworben / Nicht weiter verfolgen) ein eigener Tab
mit nur den dort relevanten Spalten, damit die Tabelle übersichtlich bleibt.
"""

import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.dashboard_ui import ANTWORT_CELL_STYLE, ANTWORT_ICON_FORMATTER, GRUND_FARBEN

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIRMENLISTE_CSV = os.path.join(PROJECT_ROOT, "data", "firmenliste.csv")
WEITERE_CSV = os.path.join(PROJECT_ROOT, "data", "weitere_bewerbungen.csv")
EMAIL_STATUS_CSV = os.path.join(PROJECT_ROOT, "data", "email_status.csv")

st.set_page_config(page_title="Firmenliste", page_icon="🏢", layout="wide")

st.title("🏢 Firmenliste Regensburg & Umgebung")


def _mit_antwort_status(frame: pd.DataFrame) -> pd.DataFrame:
    if os.path.exists(EMAIL_STATUS_CSV):
        status = pd.read_csv(EMAIL_STATUS_CSV).rename(columns={
            "status": "antwort", "letzte_antwort": "antwort_datum", "anzahl_antworten": "antwort_anzahl",
        })
        frame = frame.merge(status, on="firma", how="left")
    else:
        frame["antwort"] = None
        frame["antwort_datum"] = None
    frame["antwort"] = frame["antwort"].fillna("Keine Antwort")
    frame["antwort_datum"] = frame["antwort_datum"].fillna("")
    return frame


@st.cache_data
def get_firmen():
    return _mit_antwort_status(pd.read_csv(FIRMENLISTE_CSV).fillna(""))


@st.cache_data
def get_weitere_bewerbungen():
    if not os.path.exists(WEITERE_CSV):
        return pd.DataFrame()
    return _mit_antwort_status(pd.read_csv(WEITERE_CSV).fillna(""))


df = get_firmen()
weitere = get_weitere_bewerbungen()

if df.empty:
    st.warning("Keine Firmen gefunden. Bitte zuerst `python scripts/export_firmenliste.py` ausführen.")
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
    "antwort": "Antwort",
    "antwort_datum": "Antwort-Datum",
}


def zeige_tabelle(frame: pd.DataFrame, spalten: list[str], key: str) -> None:
    """AG-Grid mit Spaltenfiltern (konsistent mit der Bewerbungsübersicht-Seite);
    Antwort-Spalte bekommt dieselben farbigen Badges, falls vorhanden."""
    anzeige = frame[spalten].rename(columns=RENAME)
    gb = GridOptionsBuilder.from_dataframe(anzeige)
    gb.configure_default_column(filter="agTextColumnFilter", floatingFilter=True, sortable=True, resizable=True)
    if "Antwort" in anzeige.columns:
        gb.configure_column("Antwort", valueFormatter=ANTWORT_ICON_FORMATTER, cellStyle=ANTWORT_CELL_STYLE)
    if "Notizen" in anzeige.columns:
        gb.configure_column("Notizen", flex=2)
    AgGrid(anzeige, gridOptions=gb.build(), height=380, theme="alpine",
           fit_columns_on_grid_load=True, allow_unsafe_jscode=True, key=key)


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
               "antwort", "antwort_datum", "anzahl_bewerbungen", "beworbene_stellen"]
    zeige_tabelle(beworben, spalten, key="grid_beworben")

with tab_noch_nicht:
    spalten = ["firma", "ort", "art", "schwerpunkt", "notizen"]
    zeige_tabelle(noch_nicht, spalten, key="grid_noch_nicht")

with tab_nicht_weiter:
    st.subheader("Gründe im Überblick")
    grund_counts = (
        nicht_weiter["grund"].value_counts().reset_index()
        .rename(columns={"count": "anzahl", "grund": "grund"})
        .sort_values("anzahl")
    )
    fig = px.bar(
        grund_counts, x="anzahl", y="grund", orientation="h",
        color="grund", color_discrete_map=GRUND_FARBEN,
    )
    fig.update_layout(
        xaxis_title="Anzahl Firmen", yaxis_title="", showlegend=False, height=320,
    )
    st.plotly_chart(fig, use_container_width=True)

    spalten = ["firma", "ort", "grund", "notizen", "antwort", "antwort_datum"]
    zeige_tabelle(nicht_weiter, spalten, key="grid_nicht_weiter")

with tab_weitere:
    st.caption(
        "Firmen, an die bereits beworben wurde, die aber (noch) nicht in der "
        "handgepflegten Firmenliste stehen - z.B. weil die Bewerbung vor Beginn der Liste war."
    )
    if weitere.empty:
        st.info("Keine weiteren Bewerbungen gefunden.")
    else:
        spalten = ["firma", "ort", "erste_bewerbung", "letzte_bewerbung",
                   "anzahl_bewerbungen", "beworbene_stellen", "antwort", "antwort_datum"]
        zeige_tabelle(weitere, spalten, key="grid_weitere")
