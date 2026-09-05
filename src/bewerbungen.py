"""Einlesen und Parsen der Bewerbungsschreiben aus dem OneDrive-Ordner.

Firmenname und Datum werden aus dem Dateinamen extrahiert (Muster
`Anschreiben_<Firma>_<TT.MM.JJ(JJ)>.pdf` bzw. `Motivationsschreiben_<Firma>_<TT.MM.JJ(JJ)>.pdf`).
Fehlt das Datum im Dateinamen, wird ersatzweise das Änderungsdatum der Datei verwendet.
"""

import os
import re
from datetime import datetime

import pandas as pd
from pypdf import PdfReader

BASE_DIR = r"C:\Users\funke\OneDrive\Bewerbungen\Bewerbungen\Anschreiben_Alt"
SUBFOLDERS = ["Alt", "Neu"]

MONTH_NAMES_DE = {
    1: "Januar", 2: "Februar", 3: "März", 4: "April", 5: "Mai", 6: "Juni",
    7: "Juli", 8: "August", 9: "September", 10: "Oktober", 11: "November", 12: "Dezember",
}

FILENAME_DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})")
FILENAME_DATE_TYPO_RE = re.compile(r"(\d{1,2})\.(\d{2})(\d{2})(?!\d)")
PREFIX_RE = re.compile(r"^(Anschreiben|Motivationsschreiben)[\s_]*", re.IGNORECASE)


def normalize_year(year: str) -> int:
    year = "20" + year if len(year) == 2 else year
    return int(year)


def parse_date(day, month, year):
    try:
        return datetime(normalize_year(year), int(month), int(day))
    except ValueError:
        return None


def extract_date_from_filename(stem: str):
    for pattern in (FILENAME_DATE_RE, FILENAME_DATE_TYPO_RE):
        m = pattern.search(stem)
        if m:
            d = parse_date(*m.groups())
            if d:
                return d
    return None


STELLE_PATTERNS = [
    r"Bewerbun\w*\s+als\s+(.+?)(?:\n[ \t]*\n|$)",
    r"Initiativbewerbung\s*[:\-]?\s*(.+?)(?:\n[ \t]*\n|$)",
    r"Bewerbung\s+(?:um|zur|f[uü]r)\s+(.+?)(?:\n[ \t]*\n|$)",
    r"Motivationsschreiben\s+(?:f[uü]r\s+)?(.+?)(?:\n[ \t]*\n|$)",
]

FALLBACK_STELLE_RE = re.compile(
    r"ausgeschriebene\w*\s+(?:Position|Stelle)\s+als\s+(.+?)(?:\s+zu\s+bewerben|[.,])",
    re.IGNORECASE,
)

SALUTATION_MARKERS = ["Sehr geehrt", "Guten Tag", "Liebe ", "Hallo "]
STOP_MARKERS = ["Eugenia Funk", "eugenia.funk@", "funkeugenia@", "93055 Regensburg", "+49"]


def get_header(text: str, fallback_len: int = 600) -> str:
    """Text bis zur Anrede (Grussformel), sonst die ersten fallback_len Zeichen."""
    indices = [text.find(m) for m in SALUTATION_MARKERS]
    indices = [i for i in indices if i > 0]
    if indices:
        return text[: min(indices)]
    return text[:fallback_len]


def clean_stelle(s: str) -> str:
    for marker in STOP_MARKERS:
        idx = s.find(marker)
        if idx != -1:
            s = s[:idx]
    s = re.sub(r"\s+", " ", s).strip(" .,-")
    s = re.sub(r"^(die|das|den|dem|des|eine|einer)\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^(Position|Stelle)\s+als\s+", "", s, flags=re.IGNORECASE)
    s = s.strip(" .,-")
    if len(s) > 180:
        s = s[:180].rsplit(" ", 1)[0] + "…"
    return s


def extract_stelle(text: str) -> str:
    header = get_header(text, fallback_len=600)

    for pattern in STELLE_PATTERNS:
        m = re.search(pattern, header, re.IGNORECASE | re.DOTALL)
        if m:
            stelle = clean_stelle(m.group(1))
            if stelle:
                return stelle

    m = FALLBACK_STELLE_RE.search(text)
    if m:
        stelle = clean_stelle(m.group(1))
        if stelle:
            return stelle

    return "(nicht erkannt)"


KATEGORIE_KEYWORDS = [
    ("Trainee", ["trainee"]),
    ("Umschulung / Ausbildung", ["umsch", "ausbildung"]),
    ("Quereinstieg", ["quereinst"]),
    ("Softwareentwicklung / IT", [
        "entwickl", "developer", "programmier", "software", "engineer",
        "informatik", "backend", "frontend", "full stack", "fullstack",
        "sps", "data analyst", "it solution", "it-support", "it consultant",
        "it-lösung",
    ]),
]


def classify_stelle(stelle: str) -> str:
    stelle_lower = stelle.lower()
    for kategorie, keywords in KATEGORIE_KEYWORDS:
        if any(kw in stelle_lower for kw in keywords):
            return kategorie
    return "Sonstige"


EIGENE_PLZ = "93055"
KEIN_ORT = {"eugenia", "funk", "e-mail", "email", "telefon", "mobil", "handy"}

ADRESSE_RE = re.compile(r"(?<!\d)(\d{5})(?!\d)\s+([A-ZÄÖÜ][\wäöüß\-\.]*)")


def extract_ort_hinweis(text: str) -> str:
    """Versucht, die Empfängerstadt aus der Anschreiben-Kopfzeile zu lesen
    (eigene Adresse 93055 Regensburg wird ausgeschlossen). Nur ein unsicherer
    Hinweis für neue, noch nicht recherchierte Firmen in firmen_orte.csv -
    NICHT die verlässliche Datenquelle (viele Anschreiben haben keine formale
    Empfängeradresse, das heißt nicht, dass die Firma remote ist)."""
    header = get_header(text, fallback_len=1000)
    for plz, ort in ADRESSE_RE.findall(header):
        ort_norm = ort.strip().lower()
        if plz == EIGENE_PLZ or ort_norm in KEIN_ORT:
            continue
        return ort.strip()
    return ""


def read_first_page_text(pdf_path: str) -> str:
    try:
        reader = PdfReader(pdf_path)
        if reader.is_encrypted:
            reader.decrypt("")
        return reader.pages[0].extract_text() or ""
    except Exception:
        return ""


def parse_filename(stem: str) -> str:
    prefix_match = PREFIX_RE.match(stem)
    rest = stem[prefix_match.end():] if prefix_match else stem

    date_match = FILENAME_DATE_RE.search(rest) or FILENAME_DATE_TYPO_RE.search(rest)
    firma_part = rest[: date_match.start()] if date_match else rest

    firma = firma_part.replace("_", " ").replace("�", "")
    firma = re.sub(r"\s+", " ", firma).strip(" -")
    return firma or "(unbekannt)"


def collect_bewerbungen(base_dir: str = BASE_DIR, subfolders=SUBFOLDERS) -> list[dict]:
    rows = []
    for folder in subfolders:
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path):
            continue
        for filename in sorted(os.listdir(folder_path)):
            if not filename.lower().endswith(".pdf"):
                continue
            stem = os.path.splitext(filename)[0]
            if not PREFIX_RE.match(stem):
                continue  # z.B. Kombizertifikat o.ä. ueberspringen

            full_path = os.path.join(folder_path, filename)
            firma = parse_filename(stem)

            date_obj = extract_date_from_filename(stem)
            datum_quelle = "Dateiname"
            if date_obj is None:
                date_obj = datetime.fromtimestamp(os.path.getmtime(full_path))
                datum_quelle = "Dateidatum"

            text = read_first_page_text(full_path)
            stelle = extract_stelle(text) if text else "(nicht erkannt)"
            ort_hinweis = extract_ort_hinweis(text) if text else ""

            rows.append({
                "ordner": folder,
                "firma": firma,
                "stelle": stelle,
                "ort_hinweis": ort_hinweis,
                "datum": date_obj,
                "datum_quelle": datum_quelle,
                "dateiname": filename,
            })
    return rows


def load_bewerbungen(base_dir: str = BASE_DIR, subfolders=SUBFOLDERS) -> pd.DataFrame:
    rows = collect_bewerbungen(base_dir, subfolders)
    df = pd.DataFrame(rows).sort_values("datum").reset_index(drop=True)
    df["jahr"] = df["datum"].dt.year
    df["monat_num"] = df["datum"].dt.month
    df["monat"] = df.apply(
        lambda r: f"{r['jahr']}-{r['monat_num']:02d} ({MONTH_NAMES_DE[r['monat_num']]})", axis=1
    )
    df["datum_str"] = df["datum"].dt.strftime("%d.%m.%Y")
    df["kategorie"] = df["stelle"].apply(classify_stelle)
    return df
