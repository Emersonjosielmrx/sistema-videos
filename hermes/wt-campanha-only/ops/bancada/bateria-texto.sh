#!/usr/bin/env bash
# Bateria da Etapa 1 (texto) na bancada — roda NA VPS. Resultado: /root/bateria-<data>/resumo.tsv
# Motores do vendedor: A = IA da ligação atual (Gemini, padrão da bancada); B = Groq qwen3.8 (rodízio das 3 chaves).
# Cliente + juiz: gemini-3.5-flash-lite (chave "LLM Padrão"), com pausa entre rodadas (cota grátis 15/min).
set -uo pipefail
RODADAS=${RODADAS:-3}
D=/root/bateria-$(date +%Y%m%d-%H%M)
mkdir -p "$D"
echo -e "motor\tagente\tpersona\trodada\tnota\tdisse_preco\tcurtas\tinventou\tms_ia_medio\tms_1a_frase_medio\tencerrou\tproblemas" > "$D/resumo.tsv"
AV_MOD="gemini-3.5-flash-lite"; AV_KEY="LLM Padrão"
declare -A MOTOR_MOD=( [A_gemini]="" [B_groq_qwen]="qwen/qwen3.8-27b" )
declare -A MOTOR_KEY=( [A_gemini]="" [B_groq_qwen]="Groq Whisper STT" )
casos=()
for p in curioso preco desconfiado apressado sem_interesse; do casos+=("Vendas Hermes Call|$p|vendas"); done
casos+=("Teste E (renomeado 02-10)|atendimento|atendimento")
for r in $(seq 1 "$RODADAS"); do
  for c in "${casos[@]}"; do
    IFS='|' read -r ag pe mo <<< "$c"
    for m in A_gemini B_groq_qwen; do
      out=$(/root/lab-bancada.sh rodar "$ag" "$pe" 6 false "$mo" "${MOTOR_MOD[$m]}" "${MOTOR_KEY[$m]}" "$AV_MOD" "$AV_KEY" 2>&1 | head -1)
      f="$D/${m}_${pe}_${r}.json"
      [ -f "$out" ] && mv "$out" "$f"
      python3 - "$f" "$m" "$ag" "$pe" "$r" >> "$D/resumo.tsv" <<'PY'
import json, sys
f, m, ag, pe, r = sys.argv[1:6]
try:
    d = json.load(open(f))
except Exception as e:
    print("\t".join([m, ag, pe, r, "ERRO", "", "", "", "", "", "", ("sem resultado: %s" % e)[:150]])); sys.exit()
if "error" in d and "turnos" not in d:
    print("\t".join([m, ag, pe, r, "ERRO", "", "", "", "", "", "", str(d.get("error"))[:150]])); sys.exit()
a = d.get("avaliacao") or {}
t = d.get("turnos") or []
pf = [x.get("ms_primeira_frase") for x in t if isinstance(x.get("ms_primeira_frase"), (int, float)) and x.get("ms_primeira_frase") > 0]
print("\t".join(str(v) for v in [m, ag, pe, r, a.get("nota", "?"), a.get("disse_preco", ""), a.get("respostas_curtas", ""),
      a.get("inventou_algo", ""), d.get("ms_ia_medio", ""), (int(sum(pf) / len(pf)) if pf else ""), d.get("encerrou", ""),
      " | ".join(a.get("problemas") or [])[:300].replace("\t", " ").replace("\n", " ")]))
PY
      sleep 25
    done
  done
done
echo "FIM $D"
