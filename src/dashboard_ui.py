"""Gemeinsame Anzeige-Bausteine für beide Dashboard-Seiten.

Status-Farben sind die feste Status-Palette (gut/warnung/kritisch) - "Sonstige"
und "Keine Antwort" sind keine echten Status, daher neutrales Grau statt Ampelfarbe.
Grund-Farben sind eine feste kategoriale Zuordnung (Identität, nicht Zustand) -
jede Kategorie behält ihre Farbe unabhängig davon, welche anderen gerade gefiltert
sichtbar sind.
"""

from st_aggrid import JsCode

STATUS_FARBEN = {
    "Einladung": "#0ca30c",
    "Zwischenbescheid": "#fab219",
    "Absage": "#d03b3b",
    "Sonstige": "#898781",
    "Keine Antwort": "#c3c2b7",
}
STATUS_REIHENFOLGE = ["Keine Antwort", "Sonstige", "Zwischenbescheid", "Absage", "Einladung"]

GRUND_FARBEN = {
    "Bereits mehrfach abgelehnt": "#2a78d6",
    "Kein Karriereportal": "#eb6834",
    "Fachlich nicht passend": "#1baf7a",
    "Profil passt nicht": "#eda100",
    "Falscher Standort": "#e87ba4",
    "Keine Priorität": "#008300",
    "Kein aktueller Bedarf": "#4a3aa7",
}

# Icon + Text statt Farbe allein (Warnung/Kritisch-Text sonst zu kontrastarm) -
# leichte Tönung der Status-Farbe als Hintergrund für die AG-Grid-Badges.
ANTWORT_ICON_FORMATTER = JsCode(
    """
    function(params) {
        const icons = {'Absage': '❌', 'Einladung': '✅', 'Zwischenbescheid': '⏳',
                       'Sonstige': '❔', 'Keine Antwort': '➖'};
        const icon = icons[params.value];
        return icon ? (icon + ' ' + params.value) : params.value;
    }
    """
)
ANTWORT_CELL_STYLE = JsCode(
    """
    function(params) {
        const farben = {
            'Absage':           {bg: '#F8E2E2', color: '#B42318'},
            'Einladung':        {bg: '#DBF1DB', color: '#0ca30c'},
            'Zwischenbescheid': {bg: '#FEF3DD', color: '#52514e'},
            'Sonstige':         {bg: '#F3F4F6', color: '#52514e'},
            'Keine Antwort':    {bg: '#F1F5F9', color: '#898781'},
        };
        const f = farben[params.value] || {};
        return {backgroundColor: f.bg || '', color: f.color || '', fontWeight: '600'};
    }
    """
)
