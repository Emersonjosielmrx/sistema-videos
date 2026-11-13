# ER_06 — Números e pendências por projeto (29/10)

Views de 48–120 h, ledger `D:\postador-de-videos\logs\uploads_ledger.jsonl`. "≥500" = passou o lote de teste.
Recalcular: `python D:\video-fila\engenharia_reversa\alcance_projetos.py`.

## Cortes / recapd (Shorts de parceiro) — `D:\recapd-ambientes\producao\bin`
- 275 Shorts, mediana 4, 25% ≥500, 5 ≥2.000, 1 ≥5.000.
- Bons: esportenoturno, filmenoturno, dicasfinanceirasdaia, fiodameada (med ~1.200); parceiros futtres, xiuliamelo,
  canalutopia, papodebixo, andreu_edit1.
- Ruins: manhwa (med 1, 43% zero), dorama (med 2), doramanoturno (21 vídeos, média 3), kaijinre (79 vídeos, med 1).
- Pendências: ER_01, ER_04. Tarefas da própria linha: pasta `CORTES (recapd - shorts de parceiros)` aqui ao lado.

## hipercool — `D:\hipercool-videos`
- 27 Shorts med 1 (máx 3) + 13 longos med 1 (máx 8). Zero de 40 passou de 10 views. Ver ER_03.

## manhwa-react (Veo) — postador/manhwa-react
- 24 vídeos, mediana 5, 2 ≥500 (um de 10.789 em novo_ia_agora_h3n; um de 1.219 em novo_manhwareact_ia).
- O de 10.789 é o maior de todos os projetos: comparar com os outros 15 do mesmo canal (med 5) é a melhor pista do
  que leva ao 2º lote (ER_01 item 2).

## historias-em-frames
- No ledger, aparece como canal de Shorts de parceiro: novo_historias_em_frames, 9 Shorts med 64, 3 ≥500
  (3.686 "VOCÊ SABIA que este INSETO vira um ZUMBI vivo?", parceiro thalisshortsbr).
- Os vídeos próprios do projeto não estão no ledger com `projeto` marcado: PENDENTE descobrir onde ficam medidos.

## Claude Code Video — `D:\claude-code-video`
- Nenhum upload com `projeto` próprio no ledger com views de 48–120 h. PENDENTE: onde ele posta e se mede.
- Ferramenta útil para todos: `referencia.py` (transcrição com tempo, cortes, grade de quadros, estrutura).

## postador — `D:\postador-de-videos`
- É quem mede: medidas_48h (notificar_telegram.py) + metricas_studio (metricas_rede.py). O Studio volta sem
  impressões em 593/595 (ER_02). 128 uploads antigos (18–19/10) sem `projeto` no ledger.

## Fable — resultado
**29/10 (Fable).** Resumo numérico cruzado está em `..\FABLE_DECISOES.md` (D1–D10) e nas seções "Fable — resultado"
de cada arquivo. O que vale para todos os projetos: (1) excluir vídeos não elegíveis (continuaram 100% e views_periodo
< 10) de qualquer comparação; (2) a porta do 2º lote é % assistido ≥ 65% → vídeos de 13–24 s assistidos inteiros;
(3) conteúdo reaproveitado (manhwa de parceiro, hipercool, traduções, TikTok de datacenter) não recebe o lote —
o manhwa-react só "tem views" por 1 vídeo de 10.789 (original, Veo). Pendências desta lista (histórias-em-frames e CCV
sem `projeto` no ledger) continuam: quem posta por eles precisa gravar `projeto` no `uploads_ledger.jsonl`.
