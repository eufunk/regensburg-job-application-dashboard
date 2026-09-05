# regensburg-job-application-dashboard
Python-basiertes Dashboard zur Analyse und Visualisierung meiner persönlichen Bewerbungserfahrungen im Raum Regensburg – basierend auf meiner eigenen Bewerbungsdokumentation und den daraus gewonnenen Daten und Erkenntnissen.

## Projektstruktur

```
dashboard/                     Die Streamlit-App selbst (nichts anderes)
  Bewerbungsübersicht.py       Streamlit-Einstiegsseite
  pages/
    Firmenliste.py             Zweite Dashboard-Seite (Streamlit-Konvention: "pages/" neben der Einstiegsseite)
  .streamlit/
    config.toml                Theme-Einstellungen
src/                           Wiederverwendbare Python-Module (Datenaufbereitung)
  bewerbungen.py                Liest Anschreiben-PDFs aus OneDrive, extrahiert Firma/Stelle/Datum/Ort
  firmenliste.py                Parst die handgepflegte Firmenliste (Firmen_Softwareentwicklung.txt)
  firmen_orte.py                Pflegt data/firmen_orte.csv (Firma -> recherchierter Ort)
  data_loader.py                Lädt data/bewerbungen.csv fürs Dashboard
  graph_auth.py                 OAuth-Login (Microsoft Graph) fürs Postfach, Device-Code-Flow
scripts/                       Ausführbare Skripte zum Aktualisieren der Daten
  export_data.py                OneDrive -> data/bewerbungen.csv
  export_firmenliste.py         OneDrive -> data/firmenliste.csv + data/weitere_bewerbungen.csv
  update_firmen_orte.py         Neue Firmen in data/firmen_orte.csv ergänzen
  fetch_email_antworten.py      Postfach -> data/email_antworten.csv (lokal, siehe unten!)
  aggregate_email_status.py     data/email_antworten.csv -> data/email_status.csv (unbedenklich, committet)
  generate_bewerbungsgeschichte.py  Erzeugt docs/Bewerbungsgeschichte.docx
notebooks/
  bewerbungsanalyse.ipynb       Ursprüngliche explorative Analyse
docs/
  Bewerbungsgeschichte.docx     Erzählende Rückschau auf alle Bewerbungen
data/                           Exportierte CSVs (Datenquelle des Dashboards, keine PDFs/Pfade)
```

### Postfach-Abgleich (E-Mail-Antworten)

`scripts/fetch_email_antworten.py` durchsucht das Hotmail-Postfach nach Antworten
der Firmen aus der Bewerbungsliste. **Wird nur auf ausdrücklichen Wunsch ausgeführt,
niemals automatisch.** Das Ergebnis (`data/email_antworten.csv`) enthält echte
E-Mail-Auszüge und Absenderadressen und bleibt deshalb lokal (`.gitignore`).

`scripts/aggregate_email_status.py` leitet daraus die unbedenkliche
`data/email_status.csv` ab (nur Firma/Status/Datum, keine Auszüge) - die wird
committet und vom Dashboard genutzt.

## Starten

```
cd dashboard
streamlit run "Bewerbungsübersicht.py"
```

## Daten aktualisieren

Nach neuen Bewerbungen bzw. Änderungen an der Firmenliste (vom Projekt-Root):

```
python scripts/export_data.py
python scripts/export_firmenliste.py
python scripts/update_firmen_orte.py
```
