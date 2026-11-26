#!/usr/bin/env bash
# PC1: D:\video-fila\ronda\ronda_pc1.sh   (copia de trabalho: /mnt/win-bootcamp/claude-central/ronda/ronda_pc1.sh na Omarchy)
# RONDA GERAL rodando NO PC1 (Git Bash), desde 26/11/2026. Antes rodava na Omarchy (ronda.sh); a dona pediu que
# o trabalho fique no PC1 e a Omarchy so mostre o resultado (botao "R" da barra busca ultima_ronda.txt).
# Somente leitura em todas as maquinas.
#   1) PC1 por dentro (D:\video-fila\ronda_geral.ps1 + ronda_extra.py: views e Kaggle)
#   2) notebooks (com alarme de disco/RAM/temperatura)  3) VPS (disco)  4) celulares
#   5) parte da Omarchy (creditos das IAs, chats, vigias de la): a Omarchy grava D:\video-fila\ronda\omarchy.txt
#      (ronda_omarchy.sh, leve, a cada 30 min); aqui so e anexado, com aviso se estiver velho.
# Tarefa agendada: RondaGeralPC1 (de hora em hora), via ronda_oculta.vbs (sem janela).
# Saidas em D:\video-fila\ronda\: ultima_ronda.txt, ronda_anterior.txt, novos_problemas.log, resolvidos.log,
#   ronda_historico.log, rodando.txt (existe enquanto roda).
# Automatico a cada ronda:
#   - NOVOS -> Telegram (ronda_avisar.py)       - RESOLVIDOS (sumiram) -> Telegram
#   - consertaveis sem a dona -> D:\video-fila\estado\ronda_achados.json -> vigilancia.py (med_ronda) abre caso e o
#     consertador de IA do vigia conserta (mesma dedup, revisor e teto diario dele)
#   - 9h: resumo do dia no Telegram (1x por dia)   - batida do RondaCaoGuarda
# Doc: claude-central/PAINEL_PROJETOS_ATIVOS.md (LISTA MESTRA)

AQUI=/d/video-fila/ronda
SSHQ="-o ConnectTimeout=8 -o BatchMode=yes -o LogLevel=ERROR"
PY="/c/Users/Haylla/AppData/Local/Programs/Python/Python313/python.exe"
filtro() { tr -d '\r' | grep -v -i -E 'post-quantum|store now|may need to be upgraded'; }
LIM_DISCO=85; LIM_TEMP=90; LIM_RAM_MB=500

rodar() {
echo "########## PC1"
if ! timeout 300 powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'D:\video-fila\ronda_geral.ps1' 2>&1 | filtro; then
  echo "!! ronda_geral.ps1 falhou"
fi

echo "########## NOTEBOOKS"
for h in asusx hp sti x200ma itau asus; do
  r=$(timeout 25 ssh $SSHQ "$h" "LD=$LIM_DISCO LT=$LIM_TEMP LR=$LIM_RAM_MB bash -s" 2>/dev/null <<'SONDA' | filtro
d=$(df / | awk 'NR==2{gsub("%","",$5); print $5}'); r=$(free -m | awk 'NR==2{print $7}')
echo "disco ${d}% | carga $(cut -d' ' -f1 /proc/loadavg) | ram livre ${r} MB | ligado desde $(uptime -s)"
[ "$d" -ge "$LD" ] && echo "  !! DISCO ACIMA DE ${LD}% (${d}%)"
[ "$r" -lt "$LR" ] && echo "  !! RAM LIVRE ABAIXO DE ${LR} MB (${r} MB)"
f=$(systemctl --failed --no-legend --plain 2>/dev/null | awk '{print $1}' | grep -v -E 'casper-md5check' | tr '\n' ' '); [ -n "$f" ] && echo "  !! servicos falhos: $f"
uf=$(systemctl --user --failed --no-legend --plain 2>/dev/null | awk '{print $1}' | tr '\n' ' '); [ -n "$uf" ] && echo "  !! servicos do usuario falhos: $uf"
t=$(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | sort -n | tail -1)
if [ -n "$t" ]; then t=$((t/1000)); echo "  temperatura max ${t} C"; [ "$t" -ge "$LT" ] && echo "  !! TEMPERATURA ACIMA DE ${LT} C (${t} C)"; fi
[ "$(systemctl --user is-active fabrica-fish 2>/dev/null)" = "failed" ] && echo "  !! fabrica-fish FALHOU"
true
SONDA
)
  if [ -n "$r" ]; then echo "[$h] $r"; else echo "[$h] !! FORA"; fi
done

echo "########## VPS"
for v in hermes-prod hermes-staging hermes-bloqueio; do
  r=$(timeout 60 ssh -o ConnectTimeout=10 -o BatchMode=yes "$v" bash -s < /d/video-fila/sonda_vps.sh 2>&1 | filtro)
  if echo "$r" | grep -q disco; then
    echo "[$v] $r"
    dv=$(echo "$r" | sed -n 's/^disco \([0-9]*\)%.*/\1/p' | head -1)
    [ -n "$dv" ] && [ "$dv" -ge "$LIM_DISCO" ] && echo "  !! VPS $v DISCO ACIMA DE ${LIM_DISCO}% (${dv}%)"
  else echo "[$v] !! NAO RESPONDE"; fi
done

echo "########## CELULARES"
for c in s20 s20ultra a2 a3 g20; do
  r=$(timeout 40 ssh -o ConnectTimeout=8 -o BatchMode=yes "$c" sh -s < /d/video-fila/sonda_cel.sh 2>&1 | filtro | tail -1)
  if echo "$r" | grep -q '^ok'; then echo "[$c] $r"; else echo "[$c] !! sem ssh"; fi
done

echo "########## OMARCHY (creditos das IAs, vigias, chats - gravado pela Omarchy)"
if [ -f "$AQUI/omarchy.txt" ]; then
  idade=$(( ( $(date +%s) - $(stat -c %Y "$AQUI/omarchy.txt") ) / 60 ))
  cat "$AQUI/omarchy.txt" | tr -d '\r'
  [ "$idade" -gt 90 ] && echo "  !! parte da Omarchy velha ha ${idade} min (Omarchy desligada ou timer ronda-omarchy parado)"
else
  echo "  !! omarchy.txt nunca chegou (timer ronda-omarchy na Omarchy)"
fi
}

mkdir -p "$AQUI"
exec 9>"$AQUI/ronda.lock"
flock -n 9 2>/dev/null || { [ -e "$AQUI/rodando.txt" ] && exit 0; }

SAIDA="$AQUI/ultima_ronda.txt"; ANTES="$AQUI/ronda_anterior.txt"; QUANDO=$(date '+%d/%m %H:%M')
date '+%d/%m %H:%M' > "$AQUI/rodando.txt"
trap 'rm -f "$AQUI/rodando.txt"' EXIT
[ -f "$SAIDA" ] && cp "$SAIDA" "$ANTES"
{ echo "RONDA AUTOMATICA $QUANDO (PC1)"; rodar; } > "$SAIDA.tmp" 2>&1
# 26/11: no Windows o mv falha se alguem (botao R da barra via ssh/scp) esta lendo o arquivo -> tenta 10x, e por ultimo copia por cima
for i in 1 2 3 4 5 6 7 8 9 10; do mv -f "$SAIDA.tmp" "$SAIDA" 2>/dev/null && break; sleep 3; done
[ -f "$SAIDA.tmp" ] && cat "$SAIDA.tmp" > "$SAIDA" && rm -f "$SAIDA.tmp"

# problema = "  - " (tarefa com erro), "!!" ou "FORA"; numeros e horas sao tirados antes de comparar
probl() { grep -E '^\s+- |!!|FORA' "$1" 2>/dev/null | sed -E 's/[0-9]+([.,:][0-9]+)*//g; s/ +/ /g; s/^ +//' | sort -u; }
NOVOS=$(comm -13 <(probl "$ANTES") <(probl "$SAIDA"))
RESOLV=$(comm -23 <(probl "$ANTES") <(probl "$SAIDA"))
echo "$QUANDO novos=$(echo -n "$NOVOS" | grep -c .) resolvidos=$(echo -n "$RESOLV" | grep -c .) total=$(probl "$SAIDA" | grep -c .)" >> "$AQUI/ronda_historico.log"

tg() {  # texto em stdin -> Telegram pelo portao unico avisos.py
  cat > /d/video-fila/estado/ronda_msg.txt
  timeout 60 "$PY" -X utf8 'D:\video-fila\ronda_avisar.py' 'D:\video-fila\estado\ronda_msg.txt' ronda-geral >/dev/null 2>&1
}
if [ -n "$NOVOS" ] && [ -f "$ANTES" ]; then
  { echo "=== $QUANDO NOVOS PROBLEMAS ==="; echo "$NOVOS"; } >> "$AQUI/novos_problemas.log"
  { echo "RONDA GERAL $QUANDO - problemas NOVOS:"; echo "$NOVOS" | head -25; } | tg
fi
if [ -n "$RESOLV" ] && [ -s "$ANTES" ]; then
  { echo "=== $QUANDO RESOLVIDOS ==="; echo "$RESOLV"; } >> "$AQUI/resolvidos.log"
  { echo "RONDA GERAL $QUANDO - RESOLVIDO (sumiu desde a ronda anterior):"; echo "$RESOLV" | head -25; } | tg
fi

# achados consertaveis sem a dona -> vigilancia.py (med_ronda). O que precisa da dona, mexe em conta ou e VPS/maquina
# de producao fica de fora (so Telegram). Lista em SO_DONA.
SO_DONA='S20|S20U|s20|celulares fora do adb|celular|itau|\[asus\]|asus: FORA|temas\.json|emersonjosiel|368|Limitamos|Fato|token|VigiaClientes|Carrossel MS Energy|DriveCentral|Kaggle|kaggle|canal .* com 0 v|VPS|hermes|container|backup|Redroid|redroid|sem ssh|FORA DA TOMADA|BATERIA|credito|Claude:|Antigravity|Gemini|Kiro|OpenRouter|timer|sentinela|OMARCHY|omarchy|catalogo|CATALOGO|facebook: mesmo erro|reagendar pro hor|Instagram|VIEWS'
"$PY" -X utf8 - "$(cygpath -w "$SAIDA")" "$SO_DONA" "$(cygpath -w "$AQUI/ignorar_vigia.txt")" > /d/video-fila/estado/ronda_achados.tmp <<'PYA'
import json, re, sys
saida, so_dona = sys.argv[1], re.compile(sys.argv[2])
try:
    ign = [x.strip() for x in open(sys.argv[3], encoding="utf-8", errors="ignore") if x.strip() and not x.startswith("#")]
except OSError:
    ign = []
secao, out, vistos = "", [], set()
for l in open(saida, encoding="utf-8", errors="ignore"):
    l = l.rstrip("\r\n")
    m = re.match(r"^#+ ?([A-Z].*)", l) or re.match(r"^\[([^\]]+)\]", l)
    if m:
        secao = m.group(1).strip("# ")[:40]
    if not (re.match(r"^\s+- ", l) or "!!" in l or "FORA" in l):
        continue
    if secao.startswith("ALARMES DO VIGIA") or so_dona.search(l) or so_dona.search(secao) or any(i in l for i in ign):
        continue
    chave = re.sub(r"\s+", " ", re.sub(r"[0-9]+([.,:][0-9]+)*", "", l)).strip(" -!")[:110]
    if chave in vistos:
        continue
    vistos.add(chave)
    cat = "tarefa" if "TAREFAS" in secao else (re.sub(r"[^a-z]+", "-", secao.lower()).strip("-")[:30] or "geral")
    out.append({"chave": chave, "categoria": cat, "projeto": "ronda", "titulo": f"[ronda] {secao}: {l.strip(' -')}"[:200],
                "evidencia": f"Achado pela RONDA GERAL (D:\\video-fila\\ronda\\ultima_ronda.txt), secao '{secao}': {l.strip()}"})
print(json.dumps(out, ensure_ascii=False, indent=1))
PYA
mv -f /d/video-fila/estado/ronda_achados.tmp /d/video-fila/estado/ronda_achados.json

# resumo diario das 9h (1x por dia)
if [ "$(date +%H)" = "09" ] && [ "$(cat "$AQUI/.resumo_dia" 2>/dev/null)" != "$(date +%F)" ]; then
  {
    echo "RESUMO DO DIA $(date '+%d/%m') - ronda geral"
    grep -E '^\[(MAQUINA|POSTAGEM|TAREFAS COM ERRO|LACOS|CELULARES adb|FACEBOOK|CELULARES\]|SUPERVISOR|INSTAGRAM|PRODUCAO DE VIDEO|TAREFAS ATRASADAS|INVENTARIO|VIEWS|KAGGLE)' "$SAIDA"
    echo "Problemas abertos: $(probl "$SAIDA" | grep -c .)"
    echo "Ultimas 24 h: $(tail -24 "$AQUI/ronda_historico.log" | sed -n 's/.*novos=\([0-9]*\).*/\1/p' | awk '{n+=$1} END{print n+0}') novos, $(tail -24 "$AQUI/ronda_historico.log" | sed -n 's/.*resolvidos=\([0-9]*\).*/\1/p' | awk '{n+=$1} END{print n+0}') resolvidos"
    echo "Enviados ao vigia para conserto automatico: $(grep -c '"chave"' /d/video-fila/estado/ronda_achados.json)"
  } | tg && date +%F > "$AQUI/.resumo_dia"
fi

# batida para o cao de guarda (RondaCaoGuarda avisa no Telegram se a ronda parar > 150 min)
date '+%d/%m/%Y %H:%M:%S' > /d/video-fila/estado/ronda_batida.txt
