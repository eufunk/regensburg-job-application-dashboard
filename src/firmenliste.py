"""Parst die handgepflegte Firmenliste (ASCII-Tabelle) aus dem OneDrive-Ordner und
verknüpft sie mit den bereits geparsten Bewerbungen (Firma/Stelle/Datum), um pro Firma
zu zeigen, wie oft und wofür schon beworben wurde.
"""

import re

import pandas as pd

SOURCE_PATH = r"C:\Users\funke\OneDrive\Bewerbungen\Bewerbungen\Anschreiben_Alt\Firmen_Softwareentwicklung.txt"

COLUMNS = ["status", "datum", "firma", "ort", "art", "schwerpunkt", "notizen", "rueckmeldung"]


def _split_row(line: str):
    parts = [p.strip() for p in line.strip().split("|")]
    return parts[1:-1]


def parse_firmenliste(path: str = SOURCE_PATH) -> pd.DataFrame:
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    entries = []
    current = None

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("+") or not stripped.startswith("|"):
            continue

        parts = _split_row(stripped)
        if len(parts) == len(COLUMNS) - 1:
            parts.append("")  # fehlendes Trennzeichen am Zeilenende tolerieren
        if len(parts) != len(COLUMNS):
            continue  # Abschnittstitel wie "REMOTE / BUNDESWEIT" ueberspringen

        if parts[0] == "Status" and parts[1] == "Datum":
            continue  # Kopfzeile

        if parts[1]:  # Datum gesetzt -> neue Firma beginnt
            if current:
                entries.append(current)
            current = dict(zip(COLUMNS, parts))
        elif current:
            for key, value in zip(COLUMNS, parts):
                if value:
                    current[key] = f"{current[key]} {value}".strip() if current[key] else value

    if current:
        entries.append(current)

    df = pd.DataFrame(entries)
    df["datum"] = df["datum"].replace("--", "")
    return df


LOKALE_ORTE = {"regensburg", "neutraubling", "wackersdorf"}


def classify_grund(status: str, ort: str, notizen: str) -> str:
    """Nur für Status 'NICHT WEITER VERFOLGEN' relevant: warum wird die Firma nicht
    weiterverfolgt? Wird aus Ort + Notizen abgeleitet (Reihenfolge = Priorität)."""
    if "NICHT WEITER" not in status:
        return ""

    if ort.strip().lower() not in LOKALE_ORTE:
        return "Falscher Standort"

    n = notizen.lower()
    if "abgelehnt" in n:
        return "Bereits mehrfach abgelehnt"
    if "karriereseite" in n or "karrierebereich" in n:
        return "Kein Karriereportal"
    if "nicht dein bereich" in n:
        return "Fachlich nicht passend"
    if "passt nicht zum profil" in n or "erfahrung fehlt" in n or "anspruchs" in n:
        return "Profil passt nicht"
    if "priorität" in n:
        return "Keine Priorität"
    return "Kein aktueller Bedarf"


def _normalize(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^a-zäöüß0-9\s]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def _firmen_matchen(firmenliste_name: str, bewerbung_name: str) -> bool:
    a, b = _normalize(firmenliste_name), _normalize(bewerbung_name)
    if not a or not b:
        return False
    return a in b or b in a


def build_firmenliste(df_bewerbungen: pd.DataFrame, path: str = SOURCE_PATH) -> pd.DataFrame:
    firmen = parse_firmenliste(path)

    anzahl, jobs = [], []
    for firma in firmen["firma"]:
        treffer = df_bewerbungen[
            df_bewerbungen["firma"].apply(lambda b: _firmen_matchen(firma, b))
        ].sort_values("datum")
        anzahl.append(len(treffer))
        jobs.append("; ".join(f"{r.stelle} ({r.datum_str})" for r in treffer.itertuples()))

    firmen["anzahl_bewerbungen"] = anzahl
    firmen["beworbene_stellen"] = jobs
    firmen["grund"] = firmen.apply(
        lambda r: classify_grund(r["status"], r["ort"], r["notizen"]), axis=1
    )
    return firmen


def weitere_bewerbungen(df_bewerbungen: pd.DataFrame, path: str = SOURCE_PATH) -> pd.DataFrame:
    """Firmen, an die bereits beworben wurde, die aber (noch) nicht in der
    handgepflegten Firmenliste stehen - z.B. weil die Bewerbung vor Beginn der
    Liste war. Ergänzt die Firmenliste um die vollständige Bewerbungshistorie."""
    firmenliste_df = parse_firmenliste(path)

    bereits_erfasst = df_bewerbungen["firma"].apply(
        lambda b: any(_firmen_matchen(f, b) for f in firmenliste_df["firma"])
    )
    rest = df_bewerbungen[~bereits_erfasst]

    rows = []
    for firma, gruppe in rest.groupby("firma"):
        gruppe = gruppe.sort_values("datum")
        rows.append({
            "firma": firma,
            "ort": gruppe["region"].iloc[0],
            "erste_bewerbung": gruppe["datum_str"].iloc[0],
            "letzte_bewerbung": gruppe["datum_str"].iloc[-1],
            "anzahl_bewerbungen": len(gruppe),
            "beworbene_stellen": "; ".join(f"{r.stelle} ({r.datum_str})" for r in gruppe.itertuples()),
        })

    return pd.DataFrame(rows).sort_values("firma", key=lambda s: s.str.lower())
