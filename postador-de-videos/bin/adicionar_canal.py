#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""adicionar_canal.py — cadastra um canal NOVO do YouTube no postador. Só pelo navegador: sem chave de API e sem senha.

Antes: o canal já existe no YouTube e a dona logou a conta Google dele no cofre (ela mesma digita a senha):
    python D:\\logins-google\\cofre.py logar <email>

Uso (sem --gravar só MOSTRA o que mudaria; nada é escrito):
  rede de react (o mr/rede.py do manhwa-react distribui e posta nele):
    python bin/adicionar_canal.py --projeto rede --nome "Nome" --handle @handle --email conta@gmail.com
        --channel-id UCxxxx --nicho "..." --persona "..." --tags "a,b,c" --horarios 12:00,19:00,21:30 [--gravar]
  hipercool (só o hipercool posta nele):
    python bin/adicionar_canal.py --projeto hipercool --nome "Nome" --handle @handle --email conta@gmail.com
        --channel-id UCxxxx --maiores-18 [--gravar]

--maiores-18: todo vídeo desse canal sobe com Público > Restrição de idade > "restringir a maiores de 18"
(youtube_web_poster.py; se não conseguir marcar, não sobe). Não libera nudez: a censura e a análise do vídeo pronto
continuam valendo.

Grava (cada arquivo com backup <arquivo>.bkp_AAAAMMDD_<slug>):
  - D:/credenciais-canais/youtube_canais.json  entrada SEM segredo (id, nome, email, tem_upload), se o id não existe
  - config/rede_canais.json                    o canal (status "ativo" na rede, "hipercool" no hipercool)
  - config/youtube_navegador.json              usar=true (sobe pelo Studio), email, channel_id, maiores_18
  - config/canais_reservados.json              hipercool: o id fica reservado ao projeto (fora da rotação)
"""
import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import politica  # noqa: E402

PERFIS_DIR = Path(r"D:\logins-google\chrome-profiles")
HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
CHANNEL_ID = re.compile(r"^UC[\w-]{22}$")


class Erro(Exception):
    pass


def _ler(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Erro(f"não achei {path}")
    except ValueError as ex:
        raise Erro(f"{Path(path).name} ilegível ({ex}): conserte antes de cadastrar")


def _lista(texto, sep=","):
    return [x.strip() for x in (texto or "").split(sep) if x.strip()]


def montar(a, config_dir, creds_file):
    """Valida e devolve {arquivo: (conteúdo novo, resumo do que muda)}. Não grava nada."""
    nome, handle, email, cid = a.nome.strip(), a.handle.strip(), a.email.strip().lower(), a.channel_id.strip()
    if not nome:
        raise Erro("--nome vazio")
    if not re.fullmatch(r"@[\w.-]{3,}", handle):
        raise Erro(f"--handle '{handle}' inválido (ex.: @meucanal)")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise Erro(f"--email '{email}' inválido")
    if not CHANNEL_ID.fullmatch(cid):
        raise Erro(f"--channel-id '{cid}' inválido (UC + 22 caracteres, está na URL do canal no Studio)")
    slug = (a.slug or handle.lstrip("@").replace("-", "").replace(".", "")).lower()
    if not re.fullmatch(r"[a-z0-9_]+", slug):
        raise Erro(f"slug '{slug}' inválido (use --slug só com letras minúsculas, números e _)")
    cred_id = f"novo_{slug}"
    hoje = datetime.now().strftime("%d/%m")

    rede_f = config_dir / "rede_canais.json"
    nav_f = config_dir / "youtube_navegador.json"
    res_f = config_dir / "canais_reservados.json"
    rede, nav, res, creds = _ler(rede_f), _ler(nav_f), _ler(res_f), _ler(creds_file)
    if not isinstance(creds, list):
        raise Erro(f"{creds_file} não é uma lista de canais: não mexo nele")

    canais_rede, canais_nav = rede.setdefault("canais", []), nav.setdefault("canais", {})
    for rc in canais_rede:
        if rc.get("slug") == slug:
            raise Erro(f"o slug '{slug}' já existe na rede_canais.json ({rc.get('nome')})")
        if rc.get("yt_id") == cid:
            raise Erro(f"o canal {cid} já está na rede_canais.json como '{rc.get('slug')}'")
        if cred_id in (rc.get("creds") or []):
            raise Erro(f"a credencial {cred_id} já é usada por '{rc.get('slug')}' na rede_canais.json")
    for s, e in canais_nav.items():
        if s == slug:
            raise Erro(f"o slug '{slug}' já existe no youtube_navegador.json")
        if e.get("channel_id") == cid:
            raise Erro(f"o canal {cid} já está no youtube_navegador.json como '{s}'")
    avisos = [f"a conta {email} já é usada pelo canal '{s}' no navegador (confira se ela é dona dos dois canais)"
              for s, e in canais_nav.items() if (e.get("email") or "").lower() == email]

    nota = f"{hoje}: canal novo do projeto {a.projeto} (adicionar_canal.py)" + (", restrito a maiores de 18" if a.maiores_18 else "")
    if a.projeto == "rede":
        tags, horarios = _lista(a.tags), _lista(a.horarios)
        faltam = [n for n, v in (("--nicho", a.nicho), ("--persona", a.persona), ("--tags", tags),
                                 ("--horarios", horarios)) if not v]
        if faltam:
            raise Erro(f"canal da rede precisa de {', '.join(faltam)} (o agente do canal usa isso para título e horário)")
        ruins = [h for h in horarios if not HORA.fullmatch(h)]
        if ruins:
            raise Erro(f"horário inválido: {', '.join(ruins)} (use HH:MM, horário de Brasília)")
        entrada_rede = {"slug": slug, "yt_id": cid, "nome": nome, "handle": handle, "creds": [cred_id],
                        "status": "ativo", "categoria": a.categoria or rede.get("padrao", {}).get("categoria", "24"),
                        "nicho": a.nicho.strip(), "persona": a.persona.strip(), "tags_base": tags,
                        "horarios": horarios}
        if a.cor:
            entrada_rede["cor"] = a.cor
    else:
        entrada_rede = {"slug": slug, "yt_id": cid, "nome": nome, "handle": handle, "creds": [cred_id],
                        "status": "hipercool", "idioma": "pt-BR", "pais": "BR", "categoria": a.categoria or "1"}
        if a.nicho:
            entrada_rede["nicho"] = a.nicho.strip()
    entrada_rede["nota"] = nota
    canais_rede.append(entrada_rede)

    perfil = email.split("@")[0]
    portas = [e.get("porta") for e in canais_nav.values() if isinstance(e.get("porta"), int)]
    entrada_nav = {"usar": True, "nome": nome, "handle": handle, "creds": [cred_id], "email": email,
                   "perfil": perfil, "perfil_existe": (PERFIS_DIR / perfil).is_dir(),
                   "porta": max(portas, default=9399) + 1, "channel_id": cid}
    if a.maiores_18:
        entrada_nav["maiores_18"] = True
    entrada_nav["nota"] = nota + ", só pelo navegador"
    canais_nav[slug] = entrada_nav

    mudancas = {rede_f: (rede, entrada_rede), nav_f: (nav, entrada_nav)}
    if a.projeto == "hipercool":
        ids = res.setdefault("hipercool", [])
        if cred_id not in ids:
            ids.append(cred_id)
        mudancas[res_f] = (res, {"hipercool": f"+ {cred_id}"})
    if any(c.get("id") == cred_id for c in creds if isinstance(c, dict)):
        avisos.append(f"{creds_file.name} já tem a credencial {cred_id}: fica como está")
    else:
        entrada_cred = {"id": cred_id, "nome": nome, "email": email, "tem_upload": True, "nota": nota}
        creds.append(entrada_cred)
        mudancas[creds_file] = (creds, entrada_cred)
    return slug, cred_id, mudancas, avisos


def main():
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Cadastra um canal novo do YouTube no postador (sem senha, sem API).")
    ap.add_argument("--projeto", required=True, choices=["rede", "hipercool"],
                    help="rede = rede de react do manhwa-react; hipercool = só o hipercool posta")
    ap.add_argument("--nome", required=True, help="nome do canal como aparece no YouTube")
    ap.add_argument("--handle", required=True, help="@ do canal")
    ap.add_argument("--email", required=True, help="conta Google dona do canal (a mesma logada no cofre)")
    ap.add_argument("--channel-id", required=True, help="UC... (na URL do canal no Studio)")
    ap.add_argument("--slug", help="apelido interno (padrão: o @ sem símbolos)")
    ap.add_argument("--maiores-18", action="store_true", help="todo vídeo do canal sobe restrito a maiores de 18")
    ap.add_argument("--nicho", default="", help="rede: do que o canal fala (o agente do canal usa)")
    ap.add_argument("--persona", default="", help="rede: jeito de falar do canal")
    ap.add_argument("--tags", default="", help="rede: tags base separadas por vírgula")
    ap.add_argument("--horarios", default="", help="rede: horários de Brasília separados por vírgula (ex.: 12:00,19:00)")
    ap.add_argument("--categoria", default=None, help="categoria do YouTube (padrão: a da rede; hipercool: 1)")
    ap.add_argument("--cor", default=None, help="rede: cor do @ no vídeo (ex.: #FF2D55)")
    ap.add_argument("--gravar", action="store_true", help="grava de verdade (sem isso só mostra)")
    ap.add_argument("--config-dir", default=str(politica.CONFIG_DIR), help=argparse.SUPPRESS)
    ap.add_argument("--creds", default=str(politica.CREDS_FILE), help=argparse.SUPPRESS)
    a = ap.parse_args()

    try:
        slug, cred_id, mudancas, avisos = montar(a, Path(a.config_dir), Path(a.creds))
    except Erro as ex:
        print(f"ERRO: {ex}")
        sys.exit(1)

    print(f"Canal '{a.nome}' ({a.handle}) -> projeto {a.projeto}, slug {slug}, credencial {cred_id}"
          + ("  [restrito a maiores de 18]" if a.maiores_18 else ""))
    for arq, (_, resumo) in mudancas.items():
        print(f"\n{arq}:\n{json.dumps(resumo, ensure_ascii=False, indent=2)}")
    for av in avisos:
        print(f"\nAVISO: {av}")

    if not a.gravar:
        print("\nSIMULAÇÃO: nada foi gravado. Confira acima e rode de novo com --gravar.")
        return

    sufixo = f".bkp_{datetime.now():%Y%m%d}_{slug}"
    for arq, (conteudo, _) in mudancas.items():
        shutil.copy2(arq, arq.with_name(arq.name + sufixo))
        politica.gravar_json(arq, conteudo)
    print(f"\nGRAVADO (backup de cada arquivo em *{sufixo}).")
    print("\nPRÓXIMOS PASSOS")
    print(f"  1. Se a conta ainda não está no cofre, a dona loga: python D:\\logins-google\\cofre.py logar {a.email}")
    print(f"  2. Conferir o login e o canal:  python bin\\youtube_web_poster.py --checar --canal {cred_id}")
    print(f"  3. Ensaio (preenche tudo e PARA antes de publicar; fica um rascunho privado no Studio para apagar):")
    print(f"     python bin\\youtube_web_poster.py --video <arquivo.mp4> --titulo teste --canal {cred_id} --ensaio"
          + (" --projeto hipercool" if a.projeto == "hipercool" else ""))
    if a.projeto == "rede":
        print("  4. A rede (D:\\manhwa-react, mr/rede.py) passa a distribuir para ele na próxima rodada.")
    else:
        print("  4. Falta o hipercool saber O QUE vai para este canal (config/fila.json do hipercool).")


if __name__ == "__main__":
    main()
