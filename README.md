# regensburg-job-application-dashboard
Python-basiertes Dashboard zur Analyse und Visualisierung meiner persönlichen Bewerbungserfahrungen im Raum Regensburg – basierend auf meiner eigenen Bewerbungsdokumentation und den daraus gewonnenen Daten und Erkenntnissen.

🔗 [**Live-Demo öffnen**](https://bewerbungsuebersichtpy-wsc74kjqrwc3jt764dbqey.streamlit.app/)

## Projektstruktur

```
requirements.txt                Laufzeit-Abhängigkeiten für den Dashboard-Deploy (Streamlit Community Cloud)
.streamlit/config.toml          Theme (Root-Kopie, da Streamlit Cloud vom Repo-Root aus startet)
dashboard/                     Die Streamlit-App selbst (nichts anderes)
  Bewerbungsuebersicht.py      Streamlit-Einstiegsseite: Übersicht aller Bewerbungen
  pages/
    Firmenliste.py             Zweite Dashboard-Seite: Firmenliste Regensburg & Umgebung
  .streamlit/
    config.toml                Theme (lokale Kopie für `cd dashboard && streamlit run ...`)
src/                           Wiederverwendbare Python-Module (Datenaufbereitung + UI-Bausteine)
  bewerbungen.py                Liest Anschreiben-PDFs aus OneDrive, extrahiert Firma/Stelle/Datum/Ort
  firmenliste.py                Parst die handgepflegte Firmenliste (Firmen_Softwareentwicklung.txt)
  firmen_orte.py                Pflegt data/firmen_orte.csv (Firma -> recherchierter Ort)
  data_loader.py                Lädt data/bewerbungen.csv fürs Dashboard
  dashboard_ui.py                Gemeinsame Status-Farben/-Badges (AG-Grid) für beide Dashboard-Seiten
  email_matching.py              Gemeinsame Firmen-Abgleich-/Klassifikationslogik für alle Postfach-Skripte
  graph_auth.py                  OAuth-Login (Microsoft Graph) fürs Hotmail/Outlook-Postfach, Device-Code-Flow
scripts/                       Ausführbare Skripte zum Aktualisieren der Daten
  export_data.py                OneDrive -> data/bewerbungen.csv
  export_firmenliste.py         OneDrive -> data/firmenliste.csv + data/weitere_bewerbungen.csv
  update_firmen_orte.py         Neue Firmen in data/firmen_orte.csv ergänzen
  fetch_email_antworten.py      Hotmail-Postfächer -> data/email_antworten.csv (lokal, siehe unten!)
  fetch_gmail_antworten.py      Gmail-Postfach -> data/email_antworten.csv (lokal, siehe unten!)
  aggregate_email_status.py     data/email_antworten.csv -> data/email_status.csv (unbedenklich, committet)
  generate_bewerbungsgeschichte.py  Erzeugt docs/Bewerbungsgeschichte.docx
notebooks/
  bewerbungsanalyse.ipynb       Ursprüngliche explorative Analyse
docs/
  Bewerbungsgeschichte.docx     Erzählende Rückschau auf alle Bewerbungen
data/                           Exportierte CSVs (Datenquelle des Dashboards, keine PDFs/Pfade)
```

### Postfach-Abgleich (E-Mail-Antworten)

Drei Postfächer werden abgeglichen: zwei Hotmail-Konten (`scripts/fetch_email_antworten.py`,
via Microsoft Graph) und ein Gmail-Konto (`scripts/fetch_gmail_antworten.py`, via IMAP +
App-Passwort). Beide suchen nach E-Mails von Firmen aus der Bewerbungsliste und
klassifizieren die Antwort automatisch (Absage / Einladung / Zwischenbescheid / Sonstige).
Bekannte Job-Portal-Newsletter (Indeed, LinkedIn, Xing, StepStone) und eigene Adressen
werden dabei ausgeschlossen, auch wenn ein Firmenname darin zufällig vorkommt.

**Wird nur auf ausdrücklichen Wunsch ausgeführt, niemals automatisch** - beide Skripte
greifen auf das echte Postfach zu.

Das Ergebnis (`data/email_antworten.csv`) enthält echte E-Mail-Auszüge und
Absenderadressen und bleibt deshalb lokal (`.gitignore`). Danach
`python scripts/aggregate_email_status.py` ausführen: leitet daraus die unbedenkliche
`data/email_status.csv` ab (nur Firma/Status/Datum/Anzahl, keine Auszüge) - die wird
committet und vom Dashboard genutzt (Antwort-Spalte + Farb-Badges auf beiden Seiten).

**Lokale, gitignorete Zugangsdaten** (nie committen, jede Datei hat eine eigene
`.gitignore`-Regel):
- `.msal_token_cache_<konto>.json` - Microsoft-Graph-Login-Token, ein Konto pro Datei
  (Labels in `POSTFAECHER` in `fetch_email_antworten.py`)
- `.gmail_credentials.json` - `{"email": "...", "app_password": "..."}`,
  App-Passwort erzeugen unter https://myaccount.google.com/apppasswords (erfordert 2FA)
- `.eigene_email_adressen.json` - eigene E-Mail-Adressen als JSON-Liste, damit eigene
  (weitergeleitete/gesendete) Mails nicht als Firmen-Antwort zählen

## Starten

```
cd dashboard
streamlit run Bewerbungsuebersicht.py
```

## Öffentlich deployen (Streamlit Community Cloud)

1. https://share.streamlit.io → mit GitHub-Konto anmelden → **"New app"**
2. Repository: `eufunk/regensburg-job-application-dashboard`, Branch: `main`
3. **Main file path**: `dashboard/Bewerbungsuebersicht.py`
4. Deploy - `requirements.txt` (Repo-Root) wird automatisch erkannt

Die App liest ausschließlich `data/*.csv` (committet, keine PDFs/Postfach-Zugriff), ist
also ohne weitere Einrichtung öffentlich lauffähig.

## Daten aktualisieren

Nach neuen Bewerbungen bzw. Änderungen an der Firmenliste (vom Projekt-Root):

```
python scripts/export_data.py
python scripts/export_firmenliste.py
python scripts/update_firmen_orte.py
```

Postfächer abgleichen (nur auf eigenen Wunsch, siehe oben):

```
python scripts/fetch_email_antworten.py
python scripts/fetch_gmail_antworten.py
python scripts/aggregate_email_status.py
```
