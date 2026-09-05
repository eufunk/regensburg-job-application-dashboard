# -*- coding: utf-8 -*-
"""Erzeugt eine erzählende Bewerbungsgeschichte als Word-Dokument (docs/Bewerbungsgeschichte.docx)
aus den exportierten Bewerbungsdaten (data/bewerbungen.csv, data/firmenliste.csv).

Ausführen (vom Projekt-Root): python scripts/generate_bewerbungsgeschichte.py
"""

import os

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
OUTPUT_FILE = os.path.join(DOCS_DIR, "Bewerbungsgeschichte.docx")


def add_paragraph(doc, text, size=11):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(10)
    for run in p.runs:
        run.font.size = Pt(size)
    return p


def main():
    bew = pd.read_csv(os.path.join(DATA_DIR, "bewerbungen.csv"), parse_dates=["datum"])
    fl = pd.read_csv(os.path.join(DATA_DIR, "firmenliste.csv")).fillna("")

    gesamt = len(bew)
    start = bew["datum"].min().strftime("%d.%m.%Y")
    ende = bew["datum"].max().strftime("%d.%m.%Y")
    regensburg_anteil = (bew["region"] == "Regensburg").sum()

    beworben = (fl["status"] == "BEWORBEN").sum()
    noch_nicht = (fl["status"] == "NOCH NICHT").sum()
    nicht_weiter = fl["status"].str.contains("NICHT WEITER").sum()
    absagen_liste = fl["rueckmeldung"].str.contains("Absage").sum()

    doc = Document()

    title = doc.add_heading("Meine Bewerbungsgeschichte", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT

    add_paragraph(
        doc,
        f"Regensburg, {ende} – ein Rückblick auf {gesamt} Bewerbungen zwischen dem "
        f"{start} und dem {ende}.",
        size=12,
    )

    doc.add_heading("Herbst 2025 – Der Anfang", level=1)
    add_paragraph(
        doc,
        "Am 29. September 2025 verschickte ich meine ersten vier Bewerbungen: an TECVIA, Attek, "
        "Intend und FIOSYSTEMS. Ich wusste zu diesem Zeitpunkt noch nicht genau, wo die Reise "
        "hingehen würde – die Suche war breit gestreut, viele Anschreiben gingen ohne festen "
        "Orts- oder Firmenbezug hinaus, einfach dorthin, wo eine passende C#/.NET-Stelle "
        "ausgeschrieben war."
    )
    add_paragraph(
        doc,
        "Im Oktober nahm das Tempo dann deutlich zu: 17 Bewerbungen in einem einzigen Monat, "
        "unter anderem an GEFASOFT, evopro, SII Technologies und Krones – auffällig viele davon "
        "bereits mit klarem Bezug zu Regensburg und Neutraubling. Am 20. Oktober bewarb ich mich "
        "bei GFN erstmals nicht rein als Softwareentwicklerin, sondern als Trainee IT-Ausbilderin – "
        "ein erster Blick über den Tellerrand der klassischen Programmierung hinaus. Der Monat "
        "endete mit Bewerbungen quer durch die Republik: Hamburg, Karlsruhe, Frankfurt, Bochum, "
        "Remscheid, Düsseldorf, Augsburg – ich testete das Feld in alle Richtungen aus."
    )
    add_paragraph(
        doc,
        "November und Dezember beruhigten sich etwas (4 bzw. 5 Bewerbungen). Am 19. November "
        "kam mit INFOMOTION ein weiteres Trainee-Programm dazu, diesmal im Bereich Data & "
        "Analytics – die Idee, über ein Trainee den Einstieg zu finden, blieb also im Hinterkopf."
    )

    doc.add_heading("Winter 2025/2026 – Ruhigeres Fahrwasser", level=1)
    add_paragraph(
        doc,
        "Der Winter verlief geordneter und gleichmäßiger: 5 Bewerbungen im Januar, 6 im Februar. "
        "In dieser ruhigeren Phase probierte ich auch einen ganz anderen Weg aus: Am 5. Februar "
        "2026 bewarb ich mich bei InCore Bank AG auf eine Umschulung zur Fachinformatikerin "
        "Anwendungsentwicklung – ein Signal, dass mir nicht nur die klassische Direktbewerbung, "
        "sondern auch strukturierte Umschulungswege offenstanden."
    )

    doc.add_heading("Frühjahr 2026 – Der große Schub", level=1)
    add_paragraph(
        doc,
        "Ab März zog das Tempo spürbar an: 7 Bewerbungen im März, 9 im April – und dann, im Mai "
        "2026, mit 31 Bewerbungen der mit Abstand aktivste Monat der gesamten Suche. Fast ein "
        "Viertel aller Bewerbungen ging allein in diesem einen Monat hinaus."
    )
    add_paragraph(
        doc,
        "Der Mai war auch der Monat, in dem ich am konsequentesten alternative Einstiege prüfte: "
        "bei Alphatrail ein Trainee-Programm im Supply Chain Management, bei OPTITOOL und bei "
        "Tecvia gleich zwei weitere Trainee-Stellen im Bereich Anwendungsentwicklung, bei Hallo "
        "Welt ein Sales Trainee im B2B-Softwarevertrieb und bei KRONES ein Trainee im Bereich "
        "Human Resources Personalentwicklung. Gleichzeitig hatte ich schon am 20. März bei sixa "
        "AG als Quereinsteigerin im Customer Care beworben – die Bereitschaft, auch fachfremd "
        "einzusteigen, war also durchgehend da, nicht nur eine kurze Phase."
    )

    doc.add_heading("Sommer 2026 – Von der Streuung zur Strategie", level=1)
    add_paragraph(
        doc,
        "Der Juni blieb mit 14 Bewerbungen aktiv – darunter am 7. Juni eine Ausbildung zur "
        "Steuerfachangestellten bei Treukontax und am 8. Juni eine Quereinstiegs-Stelle im "
        "Versicherungsvertrieb bei Debeka. Der Juli war mit 7 Bewerbungen der ruhigste Monat "
        "des Jahres 2026 – eine kurze Verschnaufpause, bevor sich im August alles änderte."
    )
    add_paragraph(
        doc,
        "Ab dem 11. August 2026 ging ich systematischer vor: Statt einzelne Stellenanzeigen "
        "abzuklappern, legte ich mir eine eigene Liste konkreter Regensburger Firmen an, um "
        "gezielt Initiativbewerbungen zu schreiben und den Überblick zu behalten, wo ich schon "
        "war und wo nicht. Der August wurde mit 24 Bewerbungen der zweitstärkste Monat der "
        f"gesamten Suche – {regensburg_anteil} von {gesamt} Bewerbungen insgesamt gingen "
        "inzwischen an Firmen mit Sitz direkt in Regensburg."
    )
    add_paragraph(
        doc,
        "Einige dieser Initiativbewerbungen wirkten von Anfang an besonders vielversprechend: "
        "evopro systems engineering AG, System Logistics GmbH, proLogistik und Allgeier IT GmbH "
        "bewertete ich in meinen eigenen Notizen jeweils mit der Höchstpunktzahl von fünf Sternen "
        "– bei Allgeier vor allem wegen der Aussicht auf bis zu 80 % Homeoffice, bei proLogistik "
        "wegen der klaren Überschneidung mit meinem C#-Profil in der industriellen Software."
    )

    doc.add_heading("Zwischenbilanz", level=1)
    add_paragraph(
        doc,
        f"Insgesamt stehen zum {ende} {gesamt} Bewerbungen zu Buche, weit überwiegend im Bereich "
        "Softwareentwicklung/IT, ergänzt um sieben Trainee-Bewerbungen, zwei Umschulungen und "
        "zwei bewusste Quereinstiege – die Suche war also fokussiert, aber nie stur auf einen "
        "einzigen Weg beschränkt."
    )
    add_paragraph(
        doc,
        f"Von den {len(fl)} Firmen, die ich seit August 2026 aktiv auf meiner Liste führe, bin ich "
        f"bei {beworben} bereits beworben, bei {noch_nicht} steht die Bewerbung noch aus, und bei "
        f"{nicht_weiter} habe ich entschieden, sie nicht weiterzuverfolgen – meist, weil aktuell "
        "kein passender Bedarf bestand oder schlicht kein Karriereportal auffindbar war. "
        f"{absagen_liste} dieser Firmen haben bereits abgesagt."
    )

    doc.add_heading("Ausblick", level=1)
    add_paragraph(
        doc,
        "Aus anfangs unsicherem Herumtasten ist über elf Monate eine klare Richtung geworden: "
        "weg von der breiten Streuung übers ganze Land, hin zu einer gezielten, gut dokumentierten "
        "Suche direkt in Regensburg und der näheren Umgebung. Die Liste der vielversprechenden "
        "Kontakte – allen voran die mit fünf Sternen bewerteten Firmen – bleibt der nächste "
        "Ansatzpunkt."
    )

    os.makedirs(DOCS_DIR, exist_ok=True)
    doc.save(OUTPUT_FILE)
    print(f"Gespeichert unter {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
