"""Pflegt eine eigene, dauerhafte Datei mit Firmenadressen (data/firmen_orte.csv),
getrennt von den Rohdaten in OneDrive.

`ort` ist immer entweder der konkrete Ortsname (z.B. "Regensburg", "Karlsruhe",
"Neutraubling") oder wörtlich "Remote" - keine Sammelkategorien wie "Umgebung"
oder "Anderswo".

Workflow:
1. `sync_firmen_orte()` holt neue Firmen aus den Bewerbungen (OneDrive) und ergänzt
   sie in data/firmen_orte.csv - bereits recherchierte Zeilen (quelle="Recherche")
   werden NIE überschrieben, nur neue Firmen werden hinzugefügt.
2. Unbekannte Firmen (quelle="zu recherchieren") werden manuell/online recherchiert
   und in der CSV aktualisiert (quelle -> "Recherche").
3. scripts/export_data.py verwendet data/firmen_orte.csv als primäre Quelle für die
   Ort-Spalte statt der unzuverlässigen Pro-Brief-PDF-Erkennung.
"""

import os

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRMEN_ORTE_CSV = os.path.join(PROJECT_ROOT, "data", "firmen_orte.csv")

COLUMNS = ["firma", "ort", "quelle"]


def load_firmen_orte() -> pd.DataFrame:
    if os.path.exists(FIRMEN_ORTE_CSV):
        return pd.read_csv(FIRMEN_ORTE_CSV, encoding="utf-8").fillna("")
    return pd.DataFrame(columns=COLUMNS)


def save_firmen_orte(df: pd.DataFrame) -> None:
    os.makedirs(os.path.dirname(FIRMEN_ORTE_CSV), exist_ok=True)
    df.sort_values("firma", key=lambda s: s.str.lower()).to_csv(
        FIRMEN_ORTE_CSV, index=False, encoding="utf-8"
    )


def sync_firmen_orte(alle_firmen: list[str], firmenliste_df: pd.DataFrame, pdf_hinweise: dict) -> pd.DataFrame:
    """Ergänzt neue Firmen in firmen_orte.csv. Bestehende (v.a. recherchierte)
    Zeilen bleiben unangetastet. `pdf_hinweise`: firma -> ort (roher, unsicherer
    Text-Hinweis aus dem Anschreiben, nur Startpunkt für die Recherche)."""
    bestehend = load_firmen_orte()
    bekannte_firmen = set(bestehend["firma"])

    from .firmenliste import _firmen_matchen

    neue_zeilen = []
    for firma in alle_firmen:
        if firma in bekannte_firmen:
            continue

        treffer = firmenliste_df[firmenliste_df["firma"].apply(lambda f: _firmen_matchen(firma, f))]
        if len(treffer) == 1:
            neue_zeilen.append({"firma": firma, "ort": treffer.iloc[0]["ort"], "quelle": "Firmenliste"})
            continue

        ort_hinweis = pdf_hinweise.get(firma, "")
        if ort_hinweis:
            neue_zeilen.append({"firma": firma, "ort": ort_hinweis, "quelle": "Anschreiben (unsicher, zu prüfen)"})
            continue

        neue_zeilen.append({"firma": firma, "ort": "", "quelle": "zu recherchieren"})

    if neue_zeilen:
        bestehend = pd.concat([bestehend, pd.DataFrame(neue_zeilen)], ignore_index=True)
        save_firmen_orte(bestehend)

    return bestehend
