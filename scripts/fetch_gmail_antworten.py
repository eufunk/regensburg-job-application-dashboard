"""Durchsucht das Gmail-Postfach (via IMAP + App-Passwort) nach E-Mails von Firmen
aus der Bewerbungsliste und ergänzt sie in data/email_antworten.csv (enthält echte
Auszüge/Absenderadressen - bleibt lokal, ist in .gitignore).

Voraussetzung: `.gmail_credentials.json` im Projekt-Root (gitignored):
{"email": "...@gmail.com", "app_password": "..."}
App-Passwort erzeugen: https://myaccount.google.com/apppasswords (erfordert 2FA).

WICHTIG: Dieses Skript greift auf das echte Postfach zu. NUR auf ausdrücklichen
Wunsch der Nutzerin ausführen - niemals automatisch/proaktiv.

Nach einem Lauf `python scripts/aggregate_email_status.py` ausführen, um daraus
die unbedenkliche, fürs Dashboard committete data/email_status.csv abzuleiten.

Ausführen (vom Projekt-Root, nur auf Wunsch der Nutzerin!): python scripts/fetch_gmail_antworten.py
"""

import email
import imaplib
import json
import os
import re
import sys
from email.header import decode_header
from email.utils import parsedate_to_datetime

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.email_matching import classify, finde_firma, lade_firmen, DATA_DIR, SEIT_DATUM

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, ".gmail_credentials.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "email_antworten.csv")

IMAP_HOST = "imap.gmail.com"
SEIT_IMAP = SEIT_DATUM.strftime("%d-%b-%Y")


def _sonderordner(imap: imaplib.IMAP4_SSL) -> list[str]:
    """Findet die Sonderordner '[Gmail]/All Mail' (deckt Posteingang + alle Labels
    ab), Spam und Papierkorb über ihre IMAP-Kennzeichnung (\\All/\\Junk/\\Trash)
    statt über feste Namen - die sind je nach Oberflächensprache unterschiedlich
    (z.B. 'Alle Nachrichten' statt 'All Mail' bei deutscher Gmail-Oberfläche)."""
    status, folders = imap.list()
    gefunden = {}
    for roh in folders:
        zeile = roh.decode("utf-8", errors="replace") if isinstance(roh, bytes) else roh
        treffer = re.match(r'^\(([^)]*)\)\s+"[^"]*"\s+(.+)$', zeile)
        if not treffer:
            continue
        flags, name = treffer.group(1), treffer.group(2).strip()
        if name.startswith('"') and name.endswith('"'):
            name = name[1:-1]
        if "\\All" in flags:
            gefunden["all"] = name
        elif "\\Junk" in flags:
            gefunden["junk"] = name
        elif "\\Trash" in flags:
            gefunden["trash"] = name
    return list(gefunden.values())


def _decode(value: str) -> str:
    if not value:
        return ""
    teile = decode_header(value)
    out = []
    for text, enc in teile:
        if isinstance(text, bytes):
            out.append(text.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def _text_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            disposition = str(part.get("Content-Disposition", ""))
            if part.get_content_type() == "text/plain" and "attachment" not in disposition:
                charset = part.get_content_charset() or "utf-8"
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(charset, errors="replace")
        return ""
    charset = msg.get_content_charset() or "utf-8"
    payload = msg.get_payload(decode=True)
    return payload.decode(charset, errors="replace") if payload else ""


def durchsuche_gmail(firmen: list[str]) -> list[dict]:
    with open(CREDENTIALS_FILE, encoding="utf-8") as f:
        creds = json.load(f)

    imap = imaplib.IMAP4_SSL(IMAP_HOST)
    imap.login(creds["email"], creds["app_password"])

    ordner_liste = _sonderordner(imap)
    print(f"[gmail] Sonderordner gefunden: {ordner_liste}")

    treffer = []
    for ordner in ordner_liste:
        status, _ = imap.select(f'"{ordner}"', readonly=True)
        if status != "OK":
            print(f"[gmail] Ordner '{ordner}' nicht gefunden, überspringe.")
            continue

        status, data = imap.search(None, f'(SINCE "{SEIT_IMAP}")')
        ids = data[0].split() if status == "OK" and data[0] else []
        print(f"[gmail] Ordner '{ordner}': {len(ids)} E-Mails seit {SEIT_IMAP}")

        for msg_id in ids:
            status, msg_data = imap.fetch(msg_id, "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            msg = email.message_from_bytes(msg_data[0][1])

            absender_roh = _decode(msg.get("From", ""))
            treffer_match = re.match(r"^(.*?)<(.+?)>$", absender_roh)
            if treffer_match:
                absender_name = treffer_match.group(1).strip(' "')
                absender_adresse = treffer_match.group(2).strip()
            else:
                absender_name, absender_adresse = "", absender_roh.strip()

            betreff = _decode(msg.get("Subject", ""))

            firma = finde_firma(absender_name, absender_adresse, betreff, firmen)
            if not firma:
                continue

            body_clean = re.sub(r"\s+", " ", _text_body(msg)).strip()

            try:
                datum = parsedate_to_datetime(msg.get("Date", ""))
                if datum and datum.tzinfo is not None:
                    datum = datum.astimezone(tz=None).replace(tzinfo=None)
            except (TypeError, ValueError):
                datum = None

            treffer.append({
                "postfach": "gmail",
                "firma": firma,
                "datum": datum,
                "ordner": ordner,
                "absender_name": absender_name,
                "absender_adresse": absender_adresse,
                "betreff": betreff,
                "klassifikation": classify(betreff, body_clean),
                "auszug": body_clean[:500],
            })

    imap.logout()
    print(f"[gmail] {len(treffer)} passende E-Mails gefunden.")
    return treffer


def main():
    firmen = lade_firmen()
    print(f"{len(firmen)} bekannte Firmen zum Abgleich geladen.")

    neu = pd.DataFrame(durchsuche_gmail(firmen))
    if not neu.empty:
        neu["datum"] = pd.to_datetime(neu["datum"])

    if os.path.exists(OUTPUT_FILE):
        bestehend = pd.read_csv(OUTPUT_FILE, parse_dates=["datum"])
        bestehend = bestehend[bestehend["postfach"] != "gmail"]  # alten Gmail-Stand ersetzen
        df = pd.concat([bestehend, neu], ignore_index=True)
    else:
        df = neu

    if not df.empty:
        df = df.sort_values("datum")

    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print(f"\n{len(df)} passende E-Mails insgesamt (alle Postfächer), exportiert nach {OUTPUT_FILE}")
    if not df.empty:
        print(df["klassifikation"].value_counts().to_string())


if __name__ == "__main__":
    main()
