"""OAuth2-Anmeldung bei Microsoft Graph für den Zugriff auf ein privates
Outlook.com/Hotmail-Postfach (Device-Code-Flow, kein Passwort nötig/möglich).

Nutzt die von Microsoft selbst bereitgestellte öffentliche Client-ID "Microsoft
Graph Command Line Tools" (dieselbe, die auch das Connect-MgGraph PowerShell-Cmdlet
verwendet) - keine eigene Azure-App-Registrierung nötig. Diese ID ist nicht geheim,
sie ist bei allen Microsoft-Graph-PowerShell-Nutzern weltweit identisch.

Der Zugriffstoken wird nach dem ersten Login in `.msal_token_cache.json`
zwischengespeichert (gitignored, enthält den echten geheimen Token!) und bei
jedem weiteren Aufruf automatisch im Hintergrund erneuert.
"""

import os

import msal

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_CACHE_FILE = os.path.join(PROJECT_ROOT, ".msal_token_cache.json")

# "Microsoft Graph Command Line Tools" - offizielle, öffentliche Microsoft-Client-ID
CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"

# "consumers" = nur private Microsoft-Konten (hotmail.com/outlook.com/live.com)
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["Mail.Read"]


def _load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_FILE):
        with open(TOKEN_CACHE_FILE, encoding="utf-8") as f:
            cache.deserialize(f.read())
    return cache


def _save_cache(cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(cache.serialize())


def get_access_token() -> str:
    """Liefert einen gültigen Access-Token. Beim allerersten Aufruf (oder wenn der
    gespeicherte Token abgelaufen/ungültig ist) wird ein Device-Code angezeigt:
    die angezeigte URL im Browser öffnen und den Code eingeben, um sich mit dem
    Hotmail-Konto einzuloggen. Alle weiteren Aufrufe laufen automatisch im
    Hintergrund (stiller Refresh über den lokalen Token-Cache)."""
    cache = _load_cache()

    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)

    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise RuntimeError(f"Device-Flow konnte nicht gestartet werden: {flow}")
        print(flow["message"])
        result = app.acquire_token_by_device_flow(flow)

    _save_cache(cache)

    if "access_token" not in result:
        raise RuntimeError(
            f"Login fehlgeschlagen: {result.get('error')} - {result.get('error_description')}"
        )
    return result["access_token"]
