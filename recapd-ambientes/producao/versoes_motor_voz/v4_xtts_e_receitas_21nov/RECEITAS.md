# Receitas das versões aprovadas (21/11) — como refazer cada uma

Todas usam o código desta pasta (cópia de `bin\` de 21/11 02h). O liga/desliga é por variável de ambiente
(no pedido do longo: `longo_override` com as mesmas chaves, ou no job de teste em `envs`).

| versão | o que a dona achou | receita (variáveis) |
|---|---|---|
| **xtts2_6** | escolhida ("4 e 6 iguais ao meu ouvido; a 5 inferior"); mais natural que o Kitten, erra bem menos que o Fish | `MOTOR_VOZ=xtts XTTS_VERSAO=6` (frase a frase sem ponto, ref normal+sub-voz, temp 0,6, melhor de 3, microcortes, velocidade por frase 0,8, cadência do Q3, S do respeito) |
| xtts2_4 | igual à 6 pra ela | `MOTOR_VOZ=xtts XTTS_VERSAO=4` (frase inteira sem ponto, temp 0,75, velocidade 0,5) |
| xtts2_5 | inferior | `XTTS_VERSAO=5` |
| teste num longo | — | `XTTS_VERSAO=tercos` (1º terço 4, 2º 5, 3º 6) |
| **Q / Q3 / Q4v3** | única SEM erros (Kitten) | `MOTOR_VOZ=antigo VOZ_MODO=kitten_tudo KITTEN_SUBVOZ=1 KITTEN_SUBVOZ_FORCA=1.5 KITTEN_CADENCIA=1 KITTEN_MICROCORTES=1 KITTEN_VEL=auto KITTEN_VEL_FORCA=0.6 FISH_GOL=1 FISH_RITMO=1` |
| K8 | entre as melhores (Kitten) | Q sem `KITTEN_VEL_FORCA` (=1) |
| K9 | idem | K8 + `KITTEN_SUBVOZ_FORCA=1 KITTEN_SUBVOZ_TOM=0 KITTEN_SUBVOZ_FIM=0` |
| K10 | idem | K9 com `KITTEN_SUBVOZ_FIM=1` |
| A2v3 / A2v4 | Fish acelerando no código, 1 tentativa | `MOTOR_VOZ=fish FISH_ACELERA_NO_CODIGO=1 FISH_TENTATIVAS=1` |
| A4v3 / A4v4 | Fish melhor de 3 | `MOTOR_VOZ=fish FISH_ACELERA_NO_CODIGO=1 FISH_TENTATIVAS=3` |
| R4v3 | mistura (Fish nas piadas/mulher/personagem, Kitten na briga e no gol) — resolveu a velocidade | `MOTOR_VOZ=fish MISTURA_MODO=por_tipo MISTURA_GOL_NO_FISH=0 FISH_RVC=1 FISH_TENTATIVAS=3` + as do Kitten da Q (sem `KITTEN_CADENCIA`) |

Testes (jobs): `job_motores_outros.py` (XTTS/Higgs/F5 etc.), `job_modelos_novos.py` (Fish S1-mini/S2-Pro/Drama 3),
`job_drama3_llamacpp.py` (Drama 3 / S2-Pro pelo llama.cpp), `job_auditor.py` (Whisper + ECAPA + tom: confere antes da
dona ouvir). Os testes ficam em `manhwa-drive:colab_recap/fila_teste_voz/voz_fish_2011_*` e o arquivo dos antigos em
`manhwa-drive:arquivo_testes_voz/20nov/`.

**Modelo reserva (sem Kaggle):** p3 continua até medir o XTTS nos PCs. Regra da dona: se o XTTS (versão 6) for até 5x
mais lento que o p3 no PC, ele vira o reserva; mais que 5x, fica o p3.
**Licença:** XTTS v2 = Coqui Public Model License (não comercial; a Coqui fechou em jan/2024). Fish, Higgs e F5
também são não comerciais. Comerciais: Qwen3-TTS e VoxCPM2 (Apache-2.0), Pocket TTS (CC-BY-4.0). Decisão da dona.
