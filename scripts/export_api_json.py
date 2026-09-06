"""Exportiert die Bewerbungsdaten als statische JSON-Dateien für den Zugriff aus
anderen Projekten (kein Server nötig - einfach per HTTP-GET auf die rohe
GitHub-URL abrufen, z.B.
https://raw.githubusercontent.com/eufunk/regensburg-job-application-dashboard/main/data/api/bewerbungen.json).

Enthält nur, was ohnehin schon in den committeten data/*.csv öffentlich ist -
keine E-Mail-Auszüge, keine Adressen/Namen.

Ausführen (vom Projekt-Root, nachdem export_data.py / aggregate_email_status.py
aktuell sind): python scripts/export_api_json.py
"""

import json
import os
from datetime import date

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
API_DIR = os.path.join(DATA_DIR, "api")

BEWERBUNGEN_JSON = os.path.join(API_DIR, "bewerbungen.json")
FIRMEN_JSON = os.path.join(API_DIR, "firmen.json")


def main():
    bew = pd.read_csv(os.path.join(DATA_DIR, "bewerbungen.csv"), parse_dates=["datum"])
    status_datei = os.path.join(DATA_DIR, "email_status.csv")
    status = pd.read_csv(status_datei) if os.path.exists(status_datei) else pd.DataFrame(
        columns=["firma", "status", "letzte_antwort", "anzahl_antworten"]
    )

    df = bew.merge(status, on="firma", how="left")
    df["status"] = df["status"].fillna("Keine Antwort")
    df["letzte_antwort"] = df["letzte_antwort"].where(df["letzte_antwort"].notna(), None)

    stand = date.today().isoformat()
    os.makedirs(API_DIR, exist_ok=True)

    # --- Pro Bewerbung ---------------------------------------------------------
    bewerbungen = [
        {
            "datum": r.datum.strftime("%Y-%m-%d"),
            "firma": r.firma,
            "stelle": r.stelle,
            "kategorie": r.kategorie,
            "region": r.region,
            "antwort": r.status,
            "antwort_datum": r.letzte_antwort,
        }
        for r in df.itertuples()
    ]
    with open(BEWERBUNGEN_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "stand": stand,
            "gesamt_anzahl": len(bewerbungen),
            "bewerbungen": bewerbungen,
        }, f, ensure_ascii=False, indent=2)

    # --- Pro Firma ---------------------------------------------------------------
    firmen = []
    for firma, gruppe in df.groupby("firma"):
        erste = status[status["firma"] == firma]
        firmen.append({
            "firma": firma,
            "anzahl_bewerbungen": len(gruppe),
            "antwort": erste["status"].iloc[0] if len(erste) else "Keine Antwort",
            "letzte_antwort": erste["letzte_antwort"].iloc[0] if len(erste) else None,
        })
    firmen.sort(key=lambda f: f["firma"].lower())

    with open(FIRMEN_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "stand": stand,
            "gesamt_anzahl_firmen": len(firmen),
            "firmen": firmen,
        }, f, ensure_ascii=False, indent=2)

    print(f"{len(bewerbungen)} Bewerbungen -> {BEWERBUNGEN_JSON}")
    print(f"{len(firmen)} Firmen -> {FIRMEN_JSON}")


if __name__ == "__main__":
    main()
