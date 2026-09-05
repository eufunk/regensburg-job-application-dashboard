"""Gemeinsame Logik für alle Postfach-Such-Skripte (Microsoft Graph, Gmail, ...):
Firmen-Abgleich per Wortgrenze und Klassifikation der Antwort (Absage / Einladung /
Zwischenbescheid / Sonstige).
"""

import json
import os
import re
from datetime import date

import pandas as pd

from src.firmenliste import _normalize

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
EIGENE_ADRESSEN_FILE = os.path.join(PROJECT_ROOT, ".eigene_email_adressen.json")

SEIT_DATUM = date(2025, 9, 29)  # Datum der ersten Bewerbung

KLASSIFIKATION_KEYWORDS = [
    ("Absage", [
        "leider", "abgesagt", "absage", "andere entscheidung", "anderen kandidat",
        "andere bewerber", "anderweitig besetzt", "nicht berücksichtigen",
        "nicht weiter berücksichtigen", "keine passende stelle", "entschieden, ihnen",
        "zu diesem zeitpunkt nicht", "nicht überzeugen", "abstand nehmen",
        "stelle bereits besetzt", "nicht in die engere auswahl",
    ]),
    ("Einladung", [
        "einladen", "vorstellungsgespräch", "kennenlernen", "gespräch vereinbaren",
        "interviewtermin", "zum interview", "video-interview", "kennenlerngespräch",
        "telefonat anbieten", "kurzes telefonat",
    ]),
    ("Zwischenbescheid", [
        "eingegangen", "eingangsbestätigung", "erhalten haben", "unterlagen erhalten",
        "bedanken uns für ihre bewerbung", "in kürze melden", "wird geprüft",
        "prüfen ihre unterlagen", "bewerbung ist bei uns eingegangen", "dank für ihre bewerbung",
        "danke für deine bewerbung", "we have received your application",
    ]),
]


def classify(subject: str, body: str) -> str:
    text = f"{subject} {body}".lower()
    for label, keywords in KLASSIFIKATION_KEYWORDS:
        if any(kw in text for kw in keywords):
            return label
    return "Sonstige"


def lade_firmen() -> list[str]:
    bew = pd.read_csv(os.path.join(DATA_DIR, "bewerbungen.csv"))
    firmen = set(bew["firma"].unique())
    orte = pd.read_csv(os.path.join(DATA_DIR, "firmen_orte.csv")).fillna("")
    firmen.update(orte["firma"].unique())
    return sorted(firmen)


# Automatisierte Job-Portal-/Newsletter-Absender: erwähnen Firmennamen nur beiläufig
# in einer Stellenliste (z.B. Indeed-Jobalerts), sind aber nie die Firma selbst.
GESPERRTE_ABSENDER = [
    "jobalert.indeed.com",
    "mail.xing.com",
    "e-mail.xing.com",
    "linkedin.com",
    "jobagent.stepstone.de",
]

def _lade_eigene_adressen() -> list[str]:
    """Eigene Adressen (eigene weitergeleitete/gesendete Mails sind keine Firmen-
    Antwort) stehen lokal in .eigene_email_adressen.json (gitignored, personenbezogen,
    z.B. ["vorname.nachname@hotmail.de", ...]). Ohne diese Datei einfach keine
    Sonderbehandlung - dann nur Newsletter-Filter aktiv."""
    if not os.path.exists(EIGENE_ADRESSEN_FILE):
        return []
    with open(EIGENE_ADRESSEN_FILE, encoding="utf-8") as f:
        return [a.strip().lower() for a in json.load(f)]


EIGENE_ADRESSEN = _lade_eigene_adressen()


def finde_firma(absender_name: str, absender_adresse: str, betreff: str, firmen: list[str]) -> str:
    """Wortgrenzen-Abgleich (nicht reine Teilzeichenkette!) - sonst matchen kurze
    Firmenkürzel wie 'ETA' oder 'RIS' auch mitten in unbeteiligten Wörtern wie
    'Sekretariat' oder 'Christian'. Job-Portal-Newsletter und eigene Adressen werden
    ausgeschlossen, auch wenn der Firmenname zufällig im Text vorkommt."""
    adresse = absender_adresse.strip().lower()
    if adresse in EIGENE_ADRESSEN or any(domain in adresse for domain in GESPERRTE_ABSENDER):
        return ""

    text = _normalize(f"{absender_name} {absender_adresse} {betreff}")
    for firma in firmen:
        norm = _normalize(firma)
        if norm and len(norm) >= 3 and re.search(rf"\b{re.escape(norm)}\b", text):
            return firma
    return ""
