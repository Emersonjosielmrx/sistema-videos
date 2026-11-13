"""Casos do filtro de contato da rede (mr/rede.py PROIBIDO_CONTATO), 16/10.
LIMPOS nao podem ser barrados (numero que nao e telefone, assunto WhatsApp); CONVITES tem que ser pegos.
Uso: python testes/teste_filtro_contato.py   (sai 1 se algum caso falhar)"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mr import rede  # noqa: E402

LIMPOS = ["Capítulo 120 - 125 do manhwa", "1.000.000 de views em 2026", "Temporada 2025 - 2026 chegou",
          "Ep. 1 - 12 (2023) completo", "Placar 3 x 1 no final", "Atendimento 24/7 com IA", "Top 10 (2024)",
          "IA que vende sozinha no WhatsApp funciona?", "O que acontece quando IA AUTOMATIZA vendas no WhatsApp",
          "Temporada 2025-2026", "R$ 1.500,00 por mês", "Ele entra no grupo dos mais fortes", "Ela fala no final",
          "veja o vídeo https://youtu.be/abc123", "Capítulos 1100-1120", "Nível 9999 9999 de poder"]
CONVITES = ["me chama no whats", "chama no pv", "manda um oi no zap", "fala comigo no WhatsApp", "siga no tiktok",
            "WhatsApp (91) 98469-8653", "zap 91984698653", "wa.me/5591984698653", "bit.ly/promo", "me segue no insta",
            "contato: 91 98469 8653", "+55 91 98469-8653", "98469-8653", "link na bio", "chama no direct",
            "manda mensagem no telegram", "acesse www.site.com.br"]


def main():
    falhas = [("LIMPO barrado", t, rede._acha_contato(t)) for t in LIMPOS if rede._acha_contato(t)]
    falhas += [("CONVITE passou", t, None) for t in CONVITES if not rede._acha_contato(t)]
    reais = []
    pub = Path(r"D:/hipercool-materiais/_postados/react/publicados.json")
    if pub.exists():
        d = json.loads(pub.read_text("utf-8"))
        for x in (d.values() if isinstance(d, dict) else d):
            if isinstance(x, dict):
                reais += [str(x[k]) for k in ("titulo", "descricao", "comentario_texto") if x.get(k)]
    falhas += [("REAL barrado", t[:80], rede._acha_contato(t)) for t in reais if rede._acha_contato(t)]
    for f in falhas:
        print(*f, sep=" | ")
    print(f"limpos {len(LIMPOS)}, convites {len(CONVITES)}, reais {len(reais)}: {len(falhas)} falha(s)")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
