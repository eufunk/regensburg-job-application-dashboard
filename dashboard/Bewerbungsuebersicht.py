"""Streamlit-Dashboard zur Analyse der Bewerbungen.

Start mit: streamlit run Bewerbungsuebersicht.py
"""

import os
import sys

import plotly.express as px
import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, JsCode

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_bewerbungen
from src.dashboard_ui import (
    STATUS_FARBEN, STATUS_REIHENFOLGE, ANTWORT_ICON_FORMATTER, ANTWORT_CELL_STYLE,
)

st.set_page_config(page_title="Bewerbungsdashboard", page_icon="📄", layout="wide")

st.title("📄 Bewerbungsdashboard Regensburg")

EMAIL_STATUS_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "email_status.csv"
)


@st.cache_data
def get_data():
    df = load_bewerbungen()
    if os.path.exists(EMAIL_STATUS_CSV):
        import pandas as pd
        status = pd.read_csv(EMAIL_STATUS_CSV)
        df = df.merge(status, on="firma", how="left")
    else:
        df["status"] = None
        df["letzte_antwort"] = None
    df["status"] = df["status"].fillna("Keine Antwort")
    df["letzte_antwort"] = df["letzte_antwort"].fillna("")
    return df


df = get_data()

if df.empty:
    st.warning("Keine Bewerbungen gefunden.")
    st.stop()

# --- Sidebar-Filter ---------------------------------------------------------
st.sidebar.header("Filter")

monate = ["Alle"] + sorted(df["monat"].unique())
gewaehlter_monat = st.sidebar.selectbox("Monat", monate)

firmen = ["Alle"] + sorted(df["firma"].unique())
gewaehlte_firma = st.sidebar.selectbox("Firma", firmen)

gefiltert = df if gewaehlter_monat == "Alle" else df[df["monat"] == gewaehlter_monat]
if gewaehlte_firma != "Alle":
    gefiltert = gefiltert[gefiltert["firma"] == gewaehlte_firma]

# --- KPIs --------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Gesamtanzahl Bewerbungen", len(gefiltert))
if not gefiltert.empty:
    col2.metric("Erste Bewerbung", gefiltert["datum"].min().strftime("%d.%m.%Y"))
    col3.metric("Letzte Bewerbung", gefiltert["datum"].max().strftime("%d.%m.%Y"))
col4.metric("Absagen", int((gefiltert["status"] == "Absage").sum()))

st.divider()

# --- Bewerbungen pro Monat, nach Antwort-Status --------------------------------
st.subheader("Bewerbungen pro Monat, nach Antwort-Status")

pro_monat_status = gefiltert.groupby(["monat", "status"]).size().reset_index(name="anzahl")

fig = px.bar(
    pro_monat_status,
    x="monat",
    y="anzahl",
    color="status",
    color_discrete_map=STATUS_FARBEN,
    category_orders={"monat": sorted(gefiltert["monat"].unique()), "status": STATUS_REIHENFOLGE},
)
fig.update_traces(marker_line_color="white", marker_line_width=1)
fig.update_layout(
    xaxis_title="Monat", yaxis_title="Anzahl Bewerbungen",
    legend_title_text="Antwort-Status", barmode="stack",
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Firmen pro Monat ----------------------------------------------------------
st.subheader("Firmen pro Monat")
for monat, gruppe in gefiltert.sort_values(["monat", "datum"]).groupby("monat"):
    with st.expander(f"{monat} – {len(gruppe)} Bewerbung(en)"):
        for row in gruppe.itertuples():
            st.markdown(f"- **{row.firma}** ({row.datum_str})")

st.divider()

# --- Detailtabelle ---------------------------------------------------------
st.subheader("Alle Bewerbungen im Detail")
detail = gefiltert[["datum_str", "firma", "stelle", "kategorie", "region", "status", "letzte_antwort"]].rename(columns={
    "datum_str": "Datum",
    "firma": "Firma",
    "stelle": "Stelle",
    "kategorie": "Kategorie",
    "region": "Ort",
    "status": "Antwort",
    "letzte_antwort": "Antwort-Datum",
})
kategorie_optionen = sorted(gefiltert["kategorie"].unique())

# Kategorie-Filter als natives <select> in der Floating-Filter-Zeile des Spalten-Headers.
# Steuert den eingebauten Textfilter der Spalte via 'equals', daher ohne AG Grid Enterprise nutzbar.
kategorie_floating_filter = JsCode(
    """
    class KategorieFloatingFilter {
        init(params) {
            this.params = params;
            this.eGui = document.createElement('select');
            this.eGui.style.width = '100%';
            const options = [''].concat(""" + str(kategorie_optionen) + """);
            options.forEach((opt) => {
                const el = document.createElement('option');
                el.value = opt;
                el.text = opt === '' ? '(alle)' : opt;
                this.eGui.appendChild(el);
            });
            this.eGui.addEventListener('change', () => {
                const value = this.eGui.value;
                params.parentFilterInstance((instance) => {
                    if (value === '') {
                        instance.onFloatingFilterChanged(null, null);
                    } else {
                        instance.onFloatingFilterChanged('equals', value);
                    }
                });
            });
        }
        getGui() {
            return this.eGui;
        }
        onParentModelChanged(parentModel) {
            this.eGui.value = parentModel ? parentModel.filter : '';
        }
    }
    """
)

gb = GridOptionsBuilder.from_dataframe(detail)
gb.configure_default_column(filter="agTextColumnFilter", floatingFilter=True, sortable=True, resizable=True)
gb.configure_column("Kategorie", floatingFilterComponent=kategorie_floating_filter, suppressMenu=True)
gb.configure_column("Antwort", valueFormatter=ANTWORT_ICON_FORMATTER, cellStyle=ANTWORT_CELL_STYLE)
gb.configure_column("Stelle", flex=2)

grid_response = AgGrid(
    detail,
    gridOptions=gb.build(),
    height=420,
    theme="alpine",
    fit_columns_on_grid_load=True,
    allow_unsafe_jscode=True,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
)

st.metric("Bewerbungen nach Filter", len(grid_response["data"]))
