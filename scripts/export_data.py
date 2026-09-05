"""Exportiert die geparsten Bewerbungsdaten aus dem OneDrive-Ordner nach data/bewerbungen.csv.

Nur die unkritischen, bereits extrahierten Felder (Datum, Firma, Stelle, Kategorie, Region)
werden exportiert - keine Original-PDFs oder Pfade. Diese CSV ist die Datenquelle für das
Dashboard und kann damit auch öffentlich deployt werden, ohne dass ein Zugriff auf den
lokalen OneDrive-Ordner nötig ist.

Die Region ist immer ein konkreter Ortsname (aus der eigenen, dauerhaft gepflegten
data/firmen_orte.csv) oder "Remote" (wenn die Stelle selbst als Remote ausgeschrieben war) -
keine Sammelkategorien wie "Umgebung" oder "Anderswo". Neue Firmen werden dabei automatisch
in firmen_orte.csv ergänzt (quelle="zu recherchieren") und müssen anschließend recherchiert
werden.

Ausführen (vom Projekt-Root): python scripts/export_data.py
Nach neuen Bewerbungen erneut ausführen.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bewerbungen import collect_bewerbungen, load_bewerbungen
from src.firmenliste import parse_firmenliste
from src.firmen_orte import sync_firmen_orte

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "bewerbungen.csv")

REMOTE_RE = re.compile(r"remote|homeoffice|home office", re.IGNORECASE)


def main():
    df = load_bewerbungen()

    rows = collect_bewerbungen()
    pdf_hinweise = {}
    for r in rows:
        if r["ort_hinweis"] and r["firma"] not in pdf_hinweise:
            pdf_hinweise[r["firma"]] = r["ort_hinweis"]

    firmen_orte = sync_firmen_orte(sorted(df["firma"].unique()), parse_firmenliste(), pdf_hinweise)
    zu_recherchieren = firmen_orte[firmen_orte["quelle"] == "zu recherchieren"]["firma"].tolist()

    df = df.merge(firmen_orte[["firma", "ort"]], on="firma", how="left")
    df["ort"] = df["ort"].fillna("")

    kein_ort = df["ort"] == ""
    ist_remote_stelle = df["stelle"].str.contains(REMOTE_RE)

    df["region"] = df["ort"]
    df.loc[kein_ort & ist_remote_stelle, "region"] = "Remote"
    df.loc[kein_ort & ~ist_remote_stelle, "region"] = "(noch zu recherchieren)"

    export = df[["datum", "firma", "stelle", "kategorie", "region"]].copy()
    export["datum"] = export["datum"].dt.strftime("%Y-%m-%d")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    export.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"{len(export)} Bewerbungen exportiert nach {OUTPUT_FILE}")
    if zu_recherchieren:
        print(f"Noch zu recherchieren ({len(zu_recherchieren)}): {', '.join(zu_recherchieren)}")


if __name__ == "__main__":
    main()
