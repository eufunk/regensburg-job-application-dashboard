"""Lädt die exportierten Bewerbungsdaten aus data/bewerbungen.csv.

Diese Datei ist die einzige Datenquelle für Bewerbungsuebersicht.py - kein Zugriff auf den
lokalen OneDrive-Ordner oder pypdf zur Laufzeit nötig, damit das Dashboard auch öffentlich
(z.B. Streamlit Community Cloud) deploybar ist. Aktualisiert wird die CSV mit
`python scripts/export_data.py`.
"""

import os

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(PROJECT_ROOT, "data", "bewerbungen.csv")

MONTH_NAMES_DE = {
    1: "Januar", 2: "Februar", 3: "März", 4: "April", 5: "Mai", 6: "Juni",
    7: "Juli", 8: "August", 9: "September", 10: "Oktober", 11: "November", 12: "Dezember",
}


def load_bewerbungen(path: str = DATA_FILE) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["datum"])
    df = df.sort_values("datum").reset_index(drop=True)
    df["jahr"] = df["datum"].dt.year
    df["monat_num"] = df["datum"].dt.month
    df["monat"] = df.apply(
        lambda r: f"{r['jahr']}-{r['monat_num']:02d} ({MONTH_NAMES_DE[r['monat_num']]})", axis=1
    )
    df["datum_str"] = df["datum"].dt.strftime("%d.%m.%Y")
    return df
