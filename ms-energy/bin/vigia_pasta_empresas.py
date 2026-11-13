# -*- coding: utf-8 -*-
r"""Vigia das pastas do Drive das empresas clientes (dona 31/10/2026: "crie uma verificação pra ver quando o cliente vai
colocar as fotos na pasta"). A cada rodada lista entrada/ e fotos_base/ de cada conta (pelo colab649, que enxerga o que
o cliente sobe pelo link) e avisa no Telegram o que é NOVO. Na 1ª vez só marca o que já existe (não avisa coisa velha).
Estado em cache\vigia_pastas.json. Tarefa EmpresasPastas_Vigia (a cada 30 min, sem janela).
    python vigia_pasta_empresas.py                 # contas padrão
    python vigia_pasta_empresas.py globosolarenergiag
"""
import html
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\postador-de-videos\bin")
import pastas_empresas as pe  # noqa: E402

CONTAS = ["globosolarenergiag", "advance_novoestrela"]
ESTADO = Path(r"D:\ms-energy\cache\vigia_pastas.json")
SUBS = {"entrada": "fotos/vídeos para postar", "fotos_base": "fotos do rosto para o avatar"}


def main(contas):
    st = json.loads(ESTADO.read_text("utf-8")) if ESTADO.exists() else {}
    avisos = []
    for conta in contas:
        m = pe.marcas().get(conta) or {}
        for sub, o_que in SUBS.items():
            chave = f"{conta}/{sub}"
            try:
                nomes = sorted(i["Name"] for i in pe._arquivos(conta, sub))
            except Exception as e:  # noqa: BLE001
                print(f"{chave}: não listou ({e})")
                continue
            if chave not in st:  # 1ª vez: só marca
                st[chave] = nomes
                print(f"{chave}: 1ª checagem, {len(nomes)} arquivo(s) marcados")
                continue
            novos = [n for n in nomes if n not in st[chave]]
            st[chave] = sorted(set(st[chave]) | set(nomes))
            print(f"{chave}: {len(nomes)} arquivo(s), novos {len(novos)}")
            if novos:
                extra = ""
                if sub == "fotos_base":
                    extra = f"\nTotal em fotos_base: {len(nomes)} (o avatar precisa de pelo menos 3)"
                avisos.append(f"📥 <b>{html.escape(m.get('marca', conta))}</b> colocou {len(novos)} arquivo(s) em "
                              f"<b>{sub}</b> ({o_que}):\n" + "\n".join(html.escape(n) for n in novos[:10]) + extra +
                              f"\n{m.get('link', '')}")
    st["_ultima"] = datetime.now().isoformat(timespec="seconds")
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1), "utf-8")
    tmp.replace(ESTADO)
    if avisos:
        sys.path.insert(0, r"D:\video-fila")
        import avisos as portao
        for a in avisos:
            portao.enviar(a, "empresas-pastas", importante=True)
    print(f"{datetime.now():%d/%m %H:%M} avisos: {len(avisos)}")
    try:  # 31/10: placar dos estilos/cenas/formatos dos Reels (1x por dia; bin\placar_estilos.py)
        import placar_estilos
        placar_estilos.rodar()
    except Exception as e:  # noqa: BLE001
        print(f"placar de estilos falhou: {type(e).__name__}: {e}")


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:] or CONTAS)
