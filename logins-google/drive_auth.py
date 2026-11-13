"""drive_auth.py — Autenticação OAuth2 pro Google Drive (uma vez por conta).

Gera um link → você cola no browser → autoriza → script salva o token.
Depois disso, drive_upload_api.py usa o token salvo (refresh automático, sem browser).

Uso:
    python drive_auth.py <email>

Tokens salvos em: D:/logins-google/drive_tokens/<email>.json
"""
import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

TOKENS_DIR = Path("D:/logins-google/drive_tokens")
TOKENS_DIR.mkdir(exist_ok=True)

SCOPES = ["https://www.googleapis.com/auth/drive"]

# Client ID público (tipo Desktop) — precisa criar um no Google Cloud Console
# OU usar o client ID do rclone (público, funciona pra qualquer conta)
CLIENT_CONFIG = {
    "installed": {
        "client_id": "202264815644.apps.googleusercontent.com",
        "client_secret": "<SEGREDO_REMOVIDO>",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "<SEGREDO_REMOVIDO>",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
    }
}


def auth_account(email):
    token_path = TOKENS_DIR / f"{email.split('@')[0]}.json"

    if token_path.exists():
        print(f"Token já existe: {token_path}")
        print("Para re-autenticar, delete o arquivo e rode novamente.")
        return

    flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)

    # Tenta localhost primeiro (abre browser automaticamente)
    # Se falhar, usa console flow (cola a URL manualmente)
    try:
        creds = flow.run_local_server(port=8090, prompt="consent")
    except Exception:
        print("\nNão conseguiu abrir browser. Use o link abaixo:")
        creds = flow.run_console()

    # Salva o token
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
        "email": email,
    }
    token_path.write_text(json.dumps(token_data, indent=2), encoding="utf-8")
    print(f"\nToken salvo: {token_path}")
    print("Agora pode usar drive_upload_api.py com essa conta.")


def main():
    if len(sys.argv) < 2:
        print("Uso: python drive_auth.py <email>")
        print("\nContas sugeridas:")
        print("  solarmundo195@gmail.com")
        print("  fabricadeautomacoes0@gmail.com")
        print("  vendeafiliados3@gmail.com")
        return

    email = sys.argv[1]
    if "@" not in email:
        email = f"{email}@gmail.com"

    auth_account(email)


if __name__ == "__main__":
    main()
