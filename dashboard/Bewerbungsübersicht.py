"""Streamlit-Dashboard zur Analyse der Bewerbungen.

Start mit: streamlit run Bewerbungsübersicht.py
"""

import os
import sys

import plotly.express as px
import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, JsCode

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_bewerbungen

st.set_page_config(page_title="Bewerbungsdashboard", page_icon="📄", layout="wide")

st.title("📄 Bewerbungsdashboard Regensburg")


@st.cache_data
def get_data():
    return load_bewerbungen()


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
col1, col2, col3 = st.columns(3)
col1.metric("Gesamtanzahl Bewerbungen", len(gefiltert))
if not gefiltert.empty:
    col2.metric("Erste Bewerbung", gefiltert["datum"].min().strftime("%d.%m.%Y"))
    col3.metric("Letzte Bewerbung", gefiltert["datum"].max().strftime("%d.%m.%Y"))

st.divider()

# --- Bewerbungen pro Monat -----------------------------------------------------
st.subheader("Bewerbungen pro Monat")
pro_monat = gefiltert.groupby("monat").size().reset_index(name="anzahl").sort_values("monat")

fig = px.bar(pro_monat, x="monat", y="anzahl", text="anzahl", color_discrete_sequence=["#2563EB"])
fig.update_layout(xaxis_title="Monat", yaxis_title="Anzahl Bewerbungen", showlegend=False)
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
detail = gefiltert[["datum_str", "firma", "stelle", "kategorie", "region"]].rename(columns={
    "datum_str": "Datum",
    "firma": "Firma",
    "stelle": "Stelle",
    "kategorie": "Kategorie",
    "region": "Ort",
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
