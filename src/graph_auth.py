"""OAuth2-Anmeldung bei Microsoft Graph für den Zugriff auf ein privates
Outlook.com/Hotmail-Postfach (Device-Code-Flow, kein Passwort nötig/möglich).

Nutzt die von Microsoft selbst bereitgestellte öffentliche Client-ID "Microsoft
Graph Command Line Tools" (dieselbe, die auch das Connect-MgGraph PowerShell-Cmdlet
verwendet) - keine eigene Azure-App-Registrierung nötig. Diese ID ist nicht geheim,
sie ist bei allen Microsoft-Graph-PowerShell-Nutzern weltweit identisch.

Unterstützt mehrere Postfächer: jedes Konto bekommt über `account_label` seinen
eigenen, separaten Token-Cache (`.msal_token_cache_<label>.json`, gitignored,
enthält den echten geheimen Token!). Beim ersten Login pro Konto erscheint ein
Device-Code, danach läuft der Login automatisch im Hintergrund.
"""

import os

import msal

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# "Microsoft Graph Command Line Tools" - offizielle, öffentliche Microsoft-Client-ID
CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"

# "consumers" = nur private Microsoft-Konten (hotmail.com/outlook.com/live.com)
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["Mail.Read"]


def _token_cache_file(account_label: str) -> str:
    return os.path.join(PROJECT_ROOT, f".msal_token_cache_{account_label}.json")


def _load_cache(token_cache_file: str) -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if os.path.exists(token_cache_file):
        with open(token_cache_file, encoding="utf-8") as f:
            cache.deserialize(f.read())
    return cache


def _save_cache(cache: msal.SerializableTokenCache, token_cache_file: str) -> None:
    if cache.has_state_changed:
        with open(token_cache_file, "w", encoding="utf-8") as f:
            f.write(cache.serialize())


def get_access_token(account_label: str = "default") -> str:
    """Liefert einen gültigen Access-Token für das Postfach mit dem gegebenen Label
    (frei wählbarer Name zur Unterscheidung mehrerer Konten, z.B. "hauptkonto",
    "absagen"). Beim allerersten Aufruf pro Label (oder wenn der gespeicherte Token
    abgelaufen/ungültig ist) wird ein Device-Code angezeigt: die angezeigte URL im
    Browser öffnen und den Code eingeben, um sich mit dem jeweiligen Hotmail-Konto
    einzuloggen. Alle weiteren Aufrufe für dasselbe Label laufen automatisch im
    Hintergrund (stiller Refresh über den lokalen Token-Cache)."""
    token_cache_file = _token_cache_file(account_label)
    cache = _load_cache(token_cache_file)

    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)

    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise RuntimeError(f"Device-Flow konnte nicht gestartet werden: {flow}")
        print(f"[{account_label}] {flow['message']}")
        result = app.acquire_token_by_device_flow(flow)

    _save_cache(cache, token_cache_file)

    if "access_token" not in result:
        raise RuntimeError(
            f"Login fehlgeschlagen ({account_label}): "
            f"{result.get('error')} - {result.get('error_description')}"
        )
    return result["access_token"]
