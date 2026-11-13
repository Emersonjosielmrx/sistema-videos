#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGY Video Bridge — sistema proprio de geracao de video via Vertex AI Veo,
reaproveitando as contas Google/Antigravity (OAuth) SEM depender da cripto do OmniRoute.

Fluxo:
  1) agy_video_bridge.py link            -> gera o link OAuth (PKCE) pra autorizar
  2) usuario abre, autoriza, cola a URL final (localhost:8765/callback?code=...)
  3) agy_video_bridge.py exchange "<url colada>"  -> troca code por tokens, salva conta
  4) agy_video_bridge.py accounts        -> lista contas conectadas
  5) agy_video_bridge.py gen "prompt" ...-> gera video no Veo (refresh automatico)

Tokens ficam em secrets/agy_accounts.json (refresh_token proprio nosso).
"""
import sys, os, json, time, secrets, hashlib, base64, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS = os.path.join(BASE, "secrets")
ACCOUNTS = os.path.join(SECRETS, "agy_accounts.json")
PENDING = os.path.join(SECRETS, "agy_pkce_pending.json")

CLIENT_ID = "1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com"
CLIENT_SECRET = "<SEGREDO_REMOVIDO>"
REDIRECT = "http://localhost:8765/callback"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "<SEGREDO_REMOVIDO>"
USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/cclog",
    "https://www.googleapis.com/auth/experimentsandconfigs",
]
VEO_MODEL_DEFAULT = "veo-3.0-fast-generate-001"
VERTEX_LOCATION = "us-central1"


def _load(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _post_form(url, form):
    body = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/x-www-form-urlencoded",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def cmd_link():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "state": state,
        "scope": " ".join(SCOPES),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }
    _save(PENDING, {"verifier": verifier, "state": state, "redirect": REDIRECT})
    print(AUTH_URL + "?" + urllib.parse.urlencode(params))


def cmd_exchange(pasted):
    pend = _load(PENDING, None)
    if not pend:
        print("ERRO: nenhum link pendente. Rode 'link' primeiro.", file=sys.stderr)
        sys.exit(1)
    # aceita a URL colada inteira OU so o code
    code = pasted.strip()
    if code.startswith("http"):
        q = urllib.parse.urlparse(code).query
        qs = urllib.parse.parse_qs(q)
        if "error" in qs:
            print("ERRO OAuth:", qs["error"][0], file=sys.stderr)
            sys.exit(1)
        got_state = qs.get("state", [""])[0]
        if got_state != pend["state"]:
            print("AVISO: state diferente (segue mesmo assim).", file=sys.stderr)
        code = qs.get("code", [""])[0]
    if not code:
        print("ERRO: nao achei o 'code' na URL.", file=sys.stderr)
        sys.exit(1)

    tok = _post_form(TOKEN_URL, {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "code_verifier": pend["verifier"],
        "grant_type": "authorization_code",
        "redirect_uri": pend["redirect"],
    })
    access = tok["access_token"]
    refresh = tok.get("refresh_token")
    expires_at = time.time() + int(tok.get("expires_in", 3599))

    # pega email
    req = urllib.request.Request(USERINFO_URL, headers={"Authorization": f"Bearer {access}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        info = json.loads(r.read())
    email = info.get("email", "desconhecido")

    accts = _load(ACCOUNTS, {})
    accts[email] = {
        "email": email,
        "refresh_token": refresh,
        "access_token": access,
        "expires_at": expires_at,
        "project_id": None,  # descoberto no primeiro gen
    }
    _save(ACCOUNTS, accts)
    if os.path.exists(PENDING):
        os.remove(PENDING)
    print(f"OK conta conectada: {email}")
    if not refresh:
        print("AVISO: sem refresh_token (Google so manda no 1o consent). Se faltar, reautorize.", file=sys.stderr)


def _get_access(email=None):
    accts = _load(ACCOUNTS, {})
    if not accts:
        raise RuntimeError("Nenhuma conta. Rode 'link' e 'exchange'.")
    if email is None:
        email = next(iter(accts))
    a = accts[email]
    if a.get("access_token") and a.get("expires_at", 0) > time.time() + 120:
        return a["access_token"], a, email
    # refresh
    tok = _post_form(TOKEN_URL, {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": a["refresh_token"],
        "grant_type": "refresh_token",
    })
    a["access_token"] = tok["access_token"]
    a["expires_at"] = time.time() + int(tok.get("expires_in", 3599))
    accts[email] = a
    _save(ACCOUNTS, accts)
    return a["access_token"], a, email


def _discover_project(access):
    """Lista projetos GCP visiveis pela conta; pega o primeiro ativo."""
    url = "https://cloudresourcemanager.googleapis.com/v1/projects?pageSize=50"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    for p in data.get("projects", []):
        if p.get("lifecycleState") == "ACTIVE":
            return p["projectId"]
    return None


def cmd_accounts():
    accts = _load(ACCOUNTS, {})
    if not accts:
        print("(nenhuma conta conectada)")
        return
    for email, a in accts.items():
        rt = "sim" if a.get("refresh_token") else "NAO"
        print(f"- {email} | project={a.get('project_id')} | refresh={rt}")


def cmd_gen(prompt, model=VEO_MODEL_DEFAULT, aspect="16:9", duration=8,
            out=None, email=None):
    access, acct, email = _get_access(email)
    project = acct.get("project_id")
    if not project:
        project = _discover_project(access)
        if not project:
            raise RuntimeError(f"Sem projeto GCP ativo em {email}.")
        acct["project_id"] = project
        accts = _load(ACCOUNTS, {})
        accts[email] = acct
        _save(ACCOUNTS, accts)

    base = f"https://{VERTEX_LOCATION}-aiplatform.googleapis.com/v1"
    predict_url = (f"{base}/projects/{project}/locations/{VERTEX_LOCATION}"
                   f"/publishers/google/models/{model}:predictLongRunning")
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"aspectRatio": aspect, "durationSeconds": int(duration),
                       "sampleCount": 1},
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(predict_url, data=body, headers={
        "Authorization": f"Bearer {access}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            op = json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:800]
        raise RuntimeError(f"Vertex {e.code} em {predict_url}\n{detail}")
    op_name = op.get("name")
    if not op_name:
        raise RuntimeError(f"Sem operation name: {json.dumps(op)[:400]}")
    print(f"[{email}/{project}] operacao iniciada: {op_name}")

    # poll
    fetch_url = (f"{base}/projects/{project}/locations/{VERTEX_LOCATION}"
                 f"/publishers/google/models/{model}:fetchPredictOperation")
    deadline = time.time() + 600
    while time.time() < deadline:
        time.sleep(10)
        access, acct, email = _get_access(email)  # refresh se preciso
        fb = json.dumps({"operationName": op_name}).encode()
        fr = urllib.request.Request(fetch_url, data=fb, headers={
            "Authorization": f"Bearer {access}", "Content-Type": "application/json"})
        with urllib.request.urlopen(fr, timeout=60) as r:
            st = json.loads(r.read())
        if st.get("done"):
            resp = st.get("response", {})
            vids = resp.get("videos") or resp.get("generatedSamples") or []
            if not vids and "error" in st:
                raise RuntimeError(f"Veo falhou: {json.dumps(st['error'])[:400]}")
            if not out:
                out = os.path.join(BASE, "workspace", "assets", "agy_videos",
                                   f"veo_{int(time.time())}.mp4")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            v = vids[0]
            b64 = (v.get("bytesBase64Encoded") or v.get("video", {}).get("bytesBase64Encoded"))
            if b64:
                with open(out, "wb") as f:
                    f.write(base64.b64decode(b64))
                print(f"OK video salvo: {out}")
                return out
            uri = v.get("gcsUri") or v.get("uri")
            print(f"OK video (uri): {uri}")
            return uri
        print("  ...gerando (poll)")
    raise RuntimeError("Timeout (600s) esperando o Veo.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    c = sys.argv[1]
    if c == "link":
        cmd_link()
    elif c == "exchange":
        cmd_exchange(sys.argv[2])
    elif c == "accounts":
        cmd_accounts()
    elif c == "gen":
        prompt = sys.argv[2]
        kw = {}
        for arg in sys.argv[3:]:
            if "=" in arg:
                k, v = arg.split("=", 1)
                kw[k] = v
        cmd_gen(prompt, **kw)
    else:
        print(f"Comando desconhecido: {c}")
        print(__doc__)


if __name__ == "__main__":
    main()
