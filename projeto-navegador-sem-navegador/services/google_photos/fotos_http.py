# -*- coding: utf-8 -*-
r"""services/google_photos/fotos_http.py — Google Fotos por HTTP com os cookies da conta do cofre (sem Chrome).

Capturado em 29/10 (tools\capturar_fotos.py, capturas\fotos_fabricadeautomacoesia.jsonl) na busca "painel solar":
  * busca = RPC EzkLib em /_/PhotosUi/data/batchexecute. Payload da grade (a que a página rola, mais nova primeiro):
    [null, null, <token da página ou null>, null, <tamanho só na 1ª>, null, 1, ["<termo>"], null, [1, 1]]
    Resposta: [ [itens], "<token da próxima página>", ... ]. Item: [id, [link_base, largura, altura, ..., [null,null,tipo],
    [bytes]], quando_ms, ..., {"146008172": [null, ?, null, "<link do vídeo>"]} só em vídeo].
  * baixar: link_base + "=w2048-h2048-no" (foto) / "=dv" (vídeo) — o mesmo que o buscar_fotos_google.py faz no Chrome.
  * (o client.py antigo deste pacote raspa HTML e usa RPCs que nunca foram capturados: não usar.)

    python -m services.google_photos.fotos_http <conta> "painel solar" [maximo] [--baixar pasta]
"""
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.cofre_cookies import pegar, salvar, sessao  # noqa: E402

BASE = "https://photos.google.com"
VIDEO = "146008172"


class FotosHTTP:
    def __init__(self, conta):
        self.conta = conta
        self.s = sessao(conta, ["google.com"], url=BASE + "/")
        if not self._entrar():
            pegar(conta, BASE + "/")  # cookie vencido: o Chrome do cofre renova 1x
            self.s = sessao(conta, ["google.com"])
            if not self._entrar():
                raise RuntimeError(f"{conta}: Google Fotos pediu login (python D:\\logins-google\\cofre.py logar {conta})")

    def _entrar(self):
        r = self.s.get(BASE + "/", timeout=30)
        at = re.search(r'"SNlM0e":"([^"]+)"', r.text)
        if "accounts.google.com" in r.url or not at:
            return False
        sid, bl = re.search(r'"FdrFJe":"([^"]+)"', r.text), re.search(r'"cfb2h":"([^"]+)"', r.text)
        if not (sid and bl):  # página mudou/meio carregada: trata como sem login em vez de AttributeError
            return False
        self.at, self.sid, self.bl = at.group(1), sid.group(1), bl.group(1)
        return True

    def rpc(self, rid, payload, origem="/"):
        """Uma chamada batchexecute; devolve o JSON decodificado (None = recusou, ver .ultimo_erro)."""
        r = self.s.post(BASE + "/_/PhotosUi/data/batchexecute", timeout=60,
                        params={"rpcids": rid, "source-path": origem, "f.sid": self.sid, "bl": self.bl, "hl": "pt-BR",
                                "soc-app": "165", "soc-platform": "1", "_reqid": str(random.randint(10000, 999999)),
                                "rt": "c"},
                        data={"f.req": json.dumps([[[rid, json.dumps(payload), None, "generic"]]]), "at": self.at},
                        headers={"X-Same-Domain": "1", "Origin": BASE, "Referer": BASE + "/",
                                 "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"})
        self.ultimo_erro = None
        for linha in r.text.splitlines():
            if linha.startswith('[["wrb.fr"'):
                try:
                    bloco = json.loads(linha)[0]
                    if bloco[2] is None:
                        self.ultimo_erro = bloco[5] if len(bloco) > 5 else bloco
                        return None
                    d = json.loads(bloco[2])
                except (ValueError, IndexError, TypeError) as ex:
                    self.ultimo_erro = f"resposta ilegível ({type(ex).__name__}): {linha[:160]}"
                    return None
                salvar(self.s)
                return d
        self.ultimo_erro = f"HTTP {r.status_code}: {r.text[:200]}"
        return None

    def buscar(self, termo, maximo=150):
        """Busca do site (entende conteúdo: "painel solar", "telhado"...). Mais nova primeiro, como a grade da página.
        Devolve [{id, link, largura, altura, quando_ms, video, link_video}]."""
        itens, token = [], None
        while len(itens) < maximo:
            d = self.rpc("EzkLib", [None, None, token, None, None if token else 50, None, 1, [termo], None, [1, 1]])
            if d is None:
                if itens:
                    break
                raise RuntimeError(f"{self.conta} '{termo}': busca recusada: {self.ultimo_erro}")
            if not isinstance(d, list) or not d:
                break
            for it in d[0] or []:
                try:
                    extra = it[-1] if isinstance(it[-1], dict) else {}
                    v = extra.get(VIDEO)
                    itens.append({"id": it[0], "link": it[1][0], "largura": it[1][1], "altura": it[1][2],
                                  "quando_ms": it[2], "video": bool(v),
                                  "link_video": v[3] if isinstance(v, list) and len(v) > 3 else None})
                except (IndexError, TypeError, AttributeError):
                    continue  # item de outro formato (álbum/sugestão): pula em vez de perder a busca inteira
            token = d[1] if len(d) > 1 else None
            if not token or not d[0]:
                break
        return itens[:maximo]

    def criar_album(self, titulo, ids=()):
        """Álbum novo (capturas/fotos_album_criar.jsonl): OXvT9d ["Sem título", null, 2] -> id; SVP9Xd [id, título]
        renomeia; E1Cajb [[ids das mídias], id] adiciona (capturas/fotos_album_add.jsonl). Devolve o id do álbum."""
        d = self.rpc("OXvT9d", ["Sem título", None, 2], "/albums")
        if not d:
            raise RuntimeError(f"criar álbum recusado: {self.ultimo_erro}")
        album = d[0][0]
        if self.rpc("SVP9Xd", [album, titulo], f"/album/{album}") is None:
            raise RuntimeError(f"renomear álbum recusado: {self.ultimo_erro}")
        if ids:
            self.adicionar_ao_album(album, ids)
        return album

    def adicionar_ao_album(self, album, ids):
        """Põe mídias (ids da busca) no álbum; devolve quantas o servidor confirmou."""
        n = 0
        for i in range(0, len(ids), 50):
            d = self.rpc("E1Cajb", [list(ids[i:i + 50]), album], f"/album/{album}")
            if d is None:
                raise RuntimeError(f"adicionar ao álbum recusado: {self.ultimo_erro}")
            n += len(d[1] or [])
        return n

    def excluir_album(self, album, qtde=0):
        """Apaga só o álbum (as fotos ficam na biblioteca): nV6Qv (capturas/fotos_album_excluir.jsonl)."""
        if self.rpc("nV6Qv", [None, None, [[album, None, qtde]]], "/albums") is None:
            raise RuntimeError(f"excluir álbum recusado: {self.ultimo_erro}")

    def baixar(self, item, destino):
        """Foto em até 2048 px (como o buscar_fotos_google.py) ou o vídeo original."""
        url = item["link"] + ("=dv" if item["video"] else "=w2048-h2048-no")
        r = self.s.get(url, timeout=300)
        r.raise_for_status()
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        tmp = destino.with_name(destino.name + ".parcial")  # 30/10: arquivo pela metade nunca com o nome final
        tmp.write_bytes(r.content)
        tmp.replace(destino)
        return destino, r.headers.get("content-type"), len(r.content)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    conta, termo = a[0], a[1]
    maximo = int(a[2]) if len(a) > 2 and a[2].isdigit() else 150
    # 29/10 (D31): conta Google logada só numa máquina -> busca/baixa LÁ e a pasta --baixar volta por scp
    from core.maquinas import ou_remoto
    pasta = a[a.index("--baixar") + 1] if "--baixar" in a else None
    if ou_remoto(conta, "services.google_photos.fotos_http", google=True, receber=[pasta] if pasta else ()) is not None:
        return
    f = FotosHTTP(conta)
    itens = f.buscar(termo, maximo)
    print(f"{len(itens)} itens ({sum(i['video'] for i in itens)} vídeos)")
    if "--baixar" in a:
        pasta = Path(a[a.index("--baixar") + 1])
        for it in itens:
            ext = ".mp4" if it["video"] else ".jpg"
            print(f.baixar(it, pasta / f"{conta}_{it['id'][-12:]}{ext}"))


if __name__ == "__main__":
    main()
