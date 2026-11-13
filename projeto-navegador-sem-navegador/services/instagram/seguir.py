# -*- coding: utf-8 -*-
r"""services/instagram/seguir.py — segue perfis recomendados aos poucos para a conta ganhar seguidores (dona 30/10:
"pra o insta ir ganhando seguidores, vá seguindo pessoas também dos recomendados").

Fonte dos perfis: as sugestões que o próprio Instagram mostra ("chaining") a partir de perfis-semente do mesmo
público (cidade/nicho) + os seguidores recentes de quem já é da região. Por HTTP com a sessão do cofre, como o site.

Segurança (conta nova/pessoal no Instagram é sensível):
  - no máximo LIMITE_RODADA por execução e LIMITE_DIA por dia; 40-120 s aleatórios entre cada seguir;
  - pula privada sem foto, conta sem post, empresa grande (>20 mil seguidores) e quem já segue;
  - qualquer sinal de bloqueio (feedback_required, "Tente novamente mais tarde", checkpoint, 429) PARA na hora e
    marca pausa de 48 h no estado.
Estado: logs\seguir_<conta>.json (quem já foi seguido e quando, pausa).

    python -m services.instagram.seguir advance_novoestrela advanceengenhariasolar castanhal_pa ...
"""
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.arquivo import gravar_json  # noqa: E402
from services.instagram.postar import InstagramPostar  # noqa: E402

LIMITE_RODADA = 8
LIMITE_DIA = 40
PAUSA_BLOQUEIO_H = 48
SINAIS = ("feedback_required", "tente novamente", "try again later", "checkpoint", "challenge", "spam",
          "action blocked", "bloque")


class Bloqueio(RuntimeError):
    pass


class Seguidor(InstagramPostar):
    def _get(self, url):
        r = self.s.get(url, headers=self._hd(), timeout=40)
        return self._checar(r)

    def _checar(self, r):
        """Devolve o JSON; levanta Bloqueio em sinal de limite. 30/10: resposta 200 com status "ok" não é olhada por
        palavras — antes um @usuario com "spam"/"challenge" no nome, numa lista de sugestões, pausava a conta 48 h."""
        try:
            d = r.json()
        except ValueError:
            d = None
        if r.status_code == 200 and isinstance(d, dict) and d.get("status") == "ok":
            return d
        txt = r.text[:600].lower()
        if r.status_code in (400, 429) or any(s in txt for s in SINAIS):
            raise Bloqueio(f"{r.status_code} {r.text[:200]}")
        if not isinstance(d, dict):  # HTML de login/erro: não é bloqueio, mas não dá para seguir
            raise RuntimeError(f"resposta não é JSON (HTTP {r.status_code}): {r.text[:120]!r}")
        return d

    def uid_de(self, usuario):
        d = self._get(f"https://www.instagram.com/api/v1/users/web_profile_info/?username={usuario}")
        u = (d.get("data") or {}).get("user") or {}
        return u.get("id")

    def sugeridos(self, uid):
        """Perfis que o Instagram sugere a partir de `uid` (a fileira "Sugestões para você" do perfil)."""
        d = self._get(f"https://www.instagram.com/api/v1/discover/chaining/?target_id={uid}")
        return d.get("users") or []

    def seguidores(self, uid, n=50):
        d = self._get(f"https://www.instagram.com/api/v1/friendships/{uid}/followers/?count={n}&search_surface=follow_list_page")
        return d.get("users") or []

    def info(self, uid):
        return (self._get(f"https://www.instagram.com/api/v1/users/{uid}/info/").get("user") or {})

    def seguir(self, uid):
        r = self.s.post(f"https://www.instagram.com/api/v1/friendships/create/{uid}/", headers=self._hd(),
                        data={"container_module": "profile", "user_id": str(uid)}, timeout=40)
        d = self._checar(r)
        st = d.get("friendship_status") or {}
        return bool(st.get("following") or st.get("outgoing_request"))


def _estado(conta):
    arq = ROOT / "logs" / f"seguir_{conta}.json"
    try:
        return arq, json.loads(arq.read_text("utf-8"))
    except (OSError, ValueError):
        return arq, {"seguidos": {}, "pausa_ate": 0}


def rodar(conta, sementes):
    arq, est = _estado(conta)
    agora = time.time()
    if est.get("pausa_ate", 0) > agora:
        print(f"{conta}: pausado até {time.strftime('%d/%m %H:%M', time.localtime(est['pausa_ate']))} (bloqueio)")
        return 0
    hoje = time.strftime("%Y-%m-%d")
    feitos_hoje = sum(1 for t in est["seguidos"].values() if time.strftime("%Y-%m-%d", time.localtime(t)) == hoje)
    vagas = min(LIMITE_RODADA, LIMITE_DIA - feitos_hoje)
    if vagas <= 0:
        print(f"{conta}: limite do dia ({LIMITE_DIA}) já atingido")
        return 0
    ig = Seguidor(conta)
    feitos = 0
    try:
        candidatos = []
        random.shuffle(sementes)
        for sem in sementes[:3]:
            uid = sem if sem.isdigit() else ig.uid_de(sem)
            if not uid:
                continue
            candidatos += ig.sugeridos(uid)
            time.sleep(random.uniform(4, 9))
            candidatos += ig.seguidores(uid, 40)
            time.sleep(random.uniform(4, 9))
        vistos = set()
        random.shuffle(candidatos)
        for u in candidatos:
            pk = str(u.get("pk") or u.get("id") or "")
            if not pk or pk in vistos or pk in est["seguidos"] or pk == ig.uid:
                continue
            vistos.add(pk)
            if u.get("is_private") and not u.get("profile_pic_url"):
                continue
            if (u.get("friendship_status") or {}).get("following"):
                continue
            try:
                inf = ig.info(pk)
            except Bloqueio:
                raise
            except Exception:  # noqa: BLE001
                continue
            if not inf.get("media_count") or (inf.get("follower_count") or 0) > 20000:
                continue
            time.sleep(random.uniform(3, 7))
            if ig.seguir(pk):
                est["seguidos"][pk] = time.time()
                feitos += 1
                print(f"  seguiu @{u.get('username')} ({inf.get('follower_count')} seguidores)", flush=True)
                arq.parent.mkdir(exist_ok=True)
                gravar_json(arq, est)
            if feitos >= vagas:
                break
            time.sleep(random.uniform(40, 120))
    except Bloqueio as e:
        est["pausa_ate"] = time.time() + PAUSA_BLOQUEIO_H * 3600
        est["ultimo_bloqueio"] = str(e)[:300]
        print(f"{conta}: SINAL DE BLOQUEIO — parei e pausei {PAUSA_BLOQUEIO_H} h: {str(e)[:160]}", flush=True)
        try:
            sys.path.insert(0, r"D:\video-fila")
            import avisos
            avisos.enviar(f"Instagram {conta}: o Instagram limitou o 'seguir'. Parei por {PAUSA_BLOQUEIO_H} h.",
                          "instagram seguir", importante=True)
        except Exception:  # noqa: BLE001
            pass
    arq.parent.mkdir(exist_ok=True)
    gravar_json(arq, est)  # atômico: estado pela metade = perde a pausa de bloqueio e a lista de seguidos
    print(f"{conta}: seguiu {feitos} nesta rodada ({feitos_hoje + feitos} hoje)")
    return feitos


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rodar(sys.argv[1], sys.argv[2:])
