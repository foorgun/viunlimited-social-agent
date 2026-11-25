"""Prüft, ob ein vorhandener Token (z. B. aus n8n) für den Agenten taugt.

Aufruf:  python3 scripts/check_token.py
Der Token wird verdeckt abgefragt und nirgends gespeichert oder ausgegeben.
Ausgabe: Token-Art, Instagram-Account, IG_USER_ID und Ablaufdatum (falls bekannt).
"""
import getpass
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

V = "v23.0"


def get(host, path, params):
    url = f"https://{host}/{V}/{path}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        try:
            return None, json.load(e).get("error", {}).get("message", str(e))
        except Exception:
            return None, str(e)


def main():
    token = getpass.getpass("Token einfügen (unsichtbar) und Enter: ").strip()
    if not token:
        raise SystemExit("Kein Token eingegeben.")

    if token.startswith("IG"):
        data, err = get("graph.instagram.com", "me", {"fields": "user_id,username,account_type", "access_token": token})
        if err:
            raise SystemExit(f"Token ungültig oder abgelaufen: {err}")
        print("Token-Art:     Instagram-Login (graph.instagram.com)")
        print(f"Account:       @{data.get('username')} ({data.get('account_type')})")
        print(f"IG_USER_ID:    {data.get('user_id')}")
        print("Ablauf:        60 Tage ab Erzeugung, verlängerbar über refresh_access_token.")
        print("               Falls n8n ihn regelmäßig erneuert, wird die Kopie bei GitHub trotzdem ablaufen.")
        return

    data, err = get("graph.facebook.com", "me/accounts",
                    {"fields": "name,instagram_business_account{id,username}", "access_token": token})
    if err is None and data.get("data"):
        print("Token-Art:     Facebook-Login, Nutzer-Token (graph.facebook.com)")
        for page in data["data"]:
            ig = page.get("instagram_business_account") or {}
            print(f"Seite:         {page.get('name')}  ->  @{ig.get('username', '-')}  IG_USER_ID {ig.get('id', '-')}")
        print("Hinweis:       Für GitHub besser den Page-Token aus me/accounts nehmen, der läuft nicht ab.")
        return

    data, err2 = get("graph.facebook.com", "me",
                     {"fields": "name,instagram_business_account{id,username}", "access_token": token})
    if err2:
        raise SystemExit(f"Token ungültig oder abgelaufen: {err or err2}")
    ig = data.get("instagram_business_account") or {}
    print("Token-Art:     Facebook-Login, Page-Token (graph.facebook.com)")
    print(f"Seite:         {data.get('name')}")
    print(f"Account:       @{ig.get('username', '-')}")
    print(f"IG_USER_ID:    {ig.get('id', '-')}")
    if not ig:
        print("Achtung:       Mit dieser Seite ist kein Instagram-Business-Account verbunden.")


if __name__ == "__main__":
    main()
