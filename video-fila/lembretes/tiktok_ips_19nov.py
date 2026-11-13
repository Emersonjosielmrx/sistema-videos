"""Lembrete pedido pela dona em 12/11/2026: "todas com proxy, mas tem que ter análise se as novas postadas nos canais top
ainda vão dar bem... altamente documentado e lembrete". Tarefa LembreteTikTokIPs (19/11 09:30, uma vez) manda pelo
Telegram a comparação das 5 contas boas do TikTok com a linha de base de antes de dividirem IP.
Doc: D:\\postador-de-videos\\docs\\TIKTOK_IPS_COMPARTILHADOS.md"""
import json
import sys
from datetime import date, timedelta

sys.path.insert(0, r"D:\video-fila")
sys.path.insert(0, r"D:\postador-de-videos\bin")
import avisos  # noqa: E402
import vigia_tiktok_ip as vg  # noqa: E402

est = json.loads(vg.ESTADO.read_text(encoding="utf-8"))
mapa = json.loads(vg.MAPA.read_text(encoding="utf-8"))
contas = json.loads(vg.REUSO.read_text(encoding="utf-8"))["tiktok"]["contas"]
linhas = []
for conta, ip in (mapa.get("_boas") or {}).get("contas", {}).items():
    base = est["base"].get(conta)
    if not base or base < vg.MIN_NORMAL:
        continue
    gs = [g for g in (vg.ganho(conta, date.today() - timedelta(days=i), (contas.get(conta) or {}).get("cofre")) for i in range(7)) if g is not None]
    media = round(sum(gs) / len(gs)) if gs else None
    sinal = "—" if media is None else ("✅" if media >= base * 0.8 else "⚠️" if media >= base * 0.5 else "🔴")
    linhas.append(f"{sinal} {conta} (IP {ip}): {media if media is not None else '?'} views/dia agora × {round(base)} antes")
pausadas = [c for c, r in contas.items() if "vigia_tiktok_ip" in str(r.get("pausada") or "")]
texto = ("⏰ Lembrete (você pediu em 12/11): 1 semana com TODAS as contas do TikTok dividindo os 10 IPs grátis.\n"
         "As contas boas, comparadas com antes:\n" + "\n".join(linhas)
         + (f"\n\nO vigia já pausou {len(pausadas)} conta(s) por queda: {', '.join(pausadas)[:300]}" if pausadas else
            "\n\nO vigia não precisou pausar nenhuma conta.")
         + "\nVer também se alguma conta morta voltou a ter view (TIKTOK_VISUALIZACOES.md)."
         + "\nSe as boas caíram: voltar a 1 conta por IP (como desfazer no doc TIKTOK_IPS_COMPARTILHADOS.md).")
avisos.enviar(texto, "tiktok-views", importante=True)
print(texto)
