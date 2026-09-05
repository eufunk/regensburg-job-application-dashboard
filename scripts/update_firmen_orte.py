"""Holt neue Firmen aus den OneDrive-Bewerbungen und ergänzt sie in
data/firmen_orte.csv. Bereits recherchierte Firmen bleiben unverändert.

Ausführen (vom Projekt-Root), wenn neue Bewerbungen dazugekommen sind:
python scripts/update_firmen_orte.py
Danach ggf. neue Zeilen mit quelle="zu recherchieren" von Hand/online recherchieren
und in der CSV eintragen (quelle -> "Recherche").
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bewerbungen import collect_bewerbungen
from src.firmenliste import parse_firmenliste
from src.firmen_orte import sync_firmen_orte, FIRMEN_ORTE_CSV


def main():
    rows = collect_bewerbungen()
    alle_firmen = sorted({r["firma"] for r in rows})

    # bester Adress-Hinweis pro Firma aus den Anschreiben selbst,
    # nur als unsicherer Startpunkt fuer neue, noch nicht recherchierte Firmen
    pdf_hinweise = {}
    for r in rows:
        if r["ort_hinweis"] and r["firma"] not in pdf_hinweise:
            pdf_hinweise[r["firma"]] = r["ort_hinweis"]

    firmenliste_df = parse_firmenliste()

    df = sync_firmen_orte(alle_firmen, firmenliste_df, pdf_hinweise)
    neu = (df["quelle"] == "zu recherchieren").sum()

    print(f"{len(df)} Firmen insgesamt in {FIRMEN_ORTE_CSV}")
    print(f"davon {neu} noch zu recherchieren")


if __name__ == "__main__":
    main()
