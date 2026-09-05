"""Durchsucht mehrere Hotmail/Outlook-Postfächer (via Microsoft Graph) nach E-Mails
von Firmen aus der Bewerbungsliste und exportiert Absender, Datum, Betreff und eine
automatische Einordnung (Absage / Einladung / Zwischenbescheid / Sonstige) nach
data/email_antworten.csv (enthält echte Auszüge/Absenderadressen - bleibt lokal,
ist in .gitignore).

Jedes Postfach in POSTFAECHER bekommt einen eigenen Login (eigener lokaler Token-
Cache, siehe src/graph_auth.py) - beim ersten Lauf pro Postfach also ein eigener
Device-Code. Neues Postfach hinzufügen: einfach ein weiteres Label in die Liste.

WICHTIG: Dieses Skript greift auf das echte Postfach zu. NUR auf ausdrücklichen
Wunsch der Nutzerin ausführen - niemals automatisch/proaktiv, auch nicht als Teil
einer sonstigen Daten-Aktualisierung.

Nach einem Lauf `python scripts/aggregate_email_status.py` ausführen, um daraus
die unbedenkliche, fürs Dashboard committete data/email_status.csv abzuleiten.

Beim ersten Ausführen erscheint ein Device-Code-Login (Browser-URL + Code),
danach läuft der Login automatisch über den lokal gespeicherten Token.

Ausführen (vom Projekt-Root, nur auf Wunsch der Nutzerin!): python scripts/fetch_email_antworten.py
"""

import os
import re
import sys
import time

import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph_auth import get_access_token
from src.email_matching import classify, finde_firma, lade_firmen, DATA_DIR, SEIT_DATUM as SEIT_DATUM_DATE

OUTPUT_FILE = os.path.join(DATA_DIR, "email_antworten.csv")

GRAPH = "https://graph.microsoft.com/v1.0"
SEIT_DATUM = SEIT_DATUM_DATE.strftime("%Y-%m-%dT00:00:00Z")

# Freie Labels, eines pro Postfach - steuert nur den lokalen Token-Cache-Dateinamen,
# nicht die eigentliche Konto-Auswahl (die passiert beim Login selbst im Browser).
POSTFAECHER = ["hauptkonto", "absagen"]


def graph_get(token: str, url: str, retries: int = 3) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        # Klartext statt HTML fuer den Body, macht die Klassifikation zuverlaessiger
        "Prefer": 'outlook.body-content-type="text"',
    }
    for attempt in range(retries):
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "5"))
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()


def list_all_folders(token: str) -> list[dict]:
    folders = []

    def walk(folder_id=None):
        base = f"{GRAPH}/me/mailFolders/{folder_id}/childFolders" if folder_id else f"{GRAPH}/me/mailFolders"
        url = f"{base}?$top=100&includeHiddenFolders=true"
        while url:
            data = graph_get(token, url)
            for f in data["value"]:
                folders.append(f)
                walk(f["id"])
            url = data.get("@odata.nextLink")

    walk()
    return folders


def list_messages_in_folder(token: str, folder_id: str) -> list[dict]:
    messages = []
    select = "subject,from,receivedDateTime,body,webLink"
    url = (
        f"{GRAPH}/me/mailFolders/{folder_id}/messages"
        f"?$filter=receivedDateTime ge {SEIT_DATUM}"
        f"&$select={select}&$top=50"
    )
    while url:
        data = graph_get(token, url)
        messages.extend(data["value"])
        url = data.get("@odata.nextLink")
    return messages


def durchsuche_postfach(account_label: str, firmen: list[str]) -> list[dict]:
    print(f"=== Postfach '{account_label}': melde mich bei Microsoft Graph an ===")
    token = get_access_token(account_label)

    print(f"[{account_label}] Liste alle Postfach-Ordner auf ...")
    folders = list_all_folders(token)
    print(f"[{account_label}] {len(folders)} Ordner gefunden, durchsuche jeden nach E-Mails seit {SEIT_DATUM} ...")

    treffer = []
    for folder in folders:
        messages = list_messages_in_folder(token, folder["id"])
        for msg in messages:
            absender = msg.get("from", {}).get("emailAddress", {}) or {}
            absender_name = absender.get("name", "")
            absender_adresse = absender.get("address", "")
            betreff = msg.get("subject", "") or ""

            firma = finde_firma(absender_name, absender_adresse, betreff, firmen)
            if not firma:
                continue

            body = (msg.get("body", {}) or {}).get("content", "") or ""
            body_clean = re.sub(r"\s+", " ", body).strip()
            treffer.append({
                "postfach": account_label,
                "firma": firma,
                "datum": msg.get("receivedDateTime", ""),
                "ordner": folder.get("displayName", ""),
                "absender_name": absender_name,
                "absender_adresse": absender_adresse,
                "betreff": betreff,
                "klassifikation": classify(betreff, body_clean),
                "auszug": body_clean[:500],
            })

    print(f"[{account_label}] {len(treffer)} passende E-Mails gefunden.")
    return treffer


def main():
    firmen = lade_firmen()
    print(f"{len(firmen)} bekannte Firmen zum Abgleich geladen.")

    treffer = []
    for account_label in POSTFAECHER:
        treffer.extend(durchsuche_postfach(account_label, firmen))

    df = pd.DataFrame(treffer)
    if not df.empty:
        df["datum"] = pd.to_datetime(df["datum"]).dt.tz_localize(None)
        df = df.sort_values("datum")

    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print(f"\n{len(df)} passende E-Mails insgesamt, exportiert nach {OUTPUT_FILE}")
    if not df.empty:
        print(df["klassifikation"].value_counts().to_string())


if __name__ == "__main__":
    main()
