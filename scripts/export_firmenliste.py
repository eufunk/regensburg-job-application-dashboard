"""Exportiert die Firmenliste (Regensburg & Umgebung) inkl. Verknüpfung mit den
bereits gestellten Bewerbungen nach data/firmenliste.csv, sowie alle übrigen
Bewerbungen (nicht in der handgepflegten Liste) nach data/weitere_bewerbungen.csv.

Quelle: C:\\Users\\funke\\OneDrive\\Bewerbungen\\Bewerbungen\\Anschreiben_Alt\\Firmen_Softwareentwicklung.txt
Setzt voraus, dass data/bewerbungen.csv bereits existiert (python scripts/export_data.py).

Ausführen (vom Projekt-Root): python scripts/export_firmenliste.py
Nach Änderungen an der Firmenliste erneut ausführen.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_bewerbungen
from src.firmenliste import build_firmenliste, weitere_bewerbungen

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FIRMENLISTE_FILE = os.path.join(DATA_DIR, "firmenliste.csv")
WEITERE_FILE = os.path.join(DATA_DIR, "weitere_bewerbungen.csv")


def main():
    df_bewerbungen = load_bewerbungen()

    firmenliste = build_firmenliste(df_bewerbungen)
    weitere = weitere_bewerbungen(df_bewerbungen)

    os.makedirs(DATA_DIR, exist_ok=True)
    firmenliste.to_csv(FIRMENLISTE_FILE, index=False, encoding="utf-8")
    weitere.to_csv(WEITERE_FILE, index=False, encoding="utf-8")

    print(f"{len(firmenliste)} Firmen (Liste) exportiert nach {FIRMENLISTE_FILE}")
    print(f"{len(weitere)} weitere Firmen (nicht in der Liste) exportiert nach {WEITERE_FILE}")


if __name__ == "__main__":
    main()
