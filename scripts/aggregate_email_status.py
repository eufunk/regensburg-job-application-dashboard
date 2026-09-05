"""Leitet aus der lokalen data/email_antworten.csv (Rohdaten mit Auszügen/Absender-
adressen, bleibt lokal) eine schlanke, unbedenkliche data/email_status.csv ab:
nur Firma, aktueller Status und Datum der letzten Antwort, Anzahl Antworten
insgesamt - keine Auszüge, keine Namen/Adressen. Diese Datei wird committet und
vom Dashboard genutzt.

Setzt voraus, dass data/email_antworten.csv bereits existiert (siehe
fetch_email_antworten.py - nur auf ausdrücklichen Wunsch der Nutzerin ausführen).

Ausführen (vom Projekt-Root): python scripts/aggregate_email_status.py
"""

import os

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
INPUT_FILE = os.path.join(DATA_DIR, "email_antworten.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "email_status.csv")

# Prioritaet, falls mehrere unterschiedliche Antworten fuer dieselbe Firma da sind:
# der chronologisch letzte Status zaehlt als aktueller Stand.


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"{INPUT_FILE} fehlt. Erst 'python scripts/fetch_email_antworten.py' ausführen "
              "(nur auf ausdrücklichen Wunsch der Nutzerin).")
        return

    df = pd.read_csv(INPUT_FILE, parse_dates=["datum"])

    rows = []
    for firma, gruppe in df.groupby("firma"):
        gruppe = gruppe.sort_values("datum")
        letzte = gruppe.iloc[-1]
        rows.append({
            "firma": firma,
            "status": letzte["klassifikation"],
            "letzte_antwort": letzte["datum"].strftime("%Y-%m-%d"),
            "anzahl_antworten": len(gruppe),
        })

    export = pd.DataFrame(rows).sort_values("firma", key=lambda s: s.str.lower())
    export.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print(f"{len(export)} Firmen exportiert nach {OUTPUT_FILE}")
    print(export["status"].value_counts().to_string())


if __name__ == "__main__":
    main()
