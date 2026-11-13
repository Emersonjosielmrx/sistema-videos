# Linha PRODUTOS — testes A/B abertos (as views decidem)

Medição: `produto\variacoes.py medir` (views do Reel pela API, ≥ 48 h, sucesso = ≥ mediana da conta), Thompson.
Contas sem token (navegador) ainda NÃO são medidas -> ver como medir pelo navegador (pendente).

| fator | versões | início | vídeos por versão | decisão |
|---|---|---|---|---|
| formato do dono/Veo | dono_uma_cena (1 Veo) · dono_abre_fecha · dono_mesma_foto · dono_e_cena_veo (2) · dono_tres · dono_abre_fecha_veo_meio (3) · dono_tres_veo_final · quatro_veo (4) · cinco_veo (5) · sem_dono | 25–26/10 | <6 em todas | aberto — dono 26/10: "2 Veo ficou bom" (VPS = 3 Veo, na verdade). 27/10 17:30: todas as variantes reaproveitam a foto da 1ª cena do dono -> dono_mesma_foto = dono_abre_fecha (juntar no placar) |

| MODELO de quem cria (dono 27/10: "mude o Gemini 3.8 pelo Argon e meça") | Gemini 3.8 (até 27/10 13:00) · Argon: roteiro `gemini-4-argon`, editor/corretor `argon-gemini` (desde 13:00) | 27/10 13:00 | Gemini 6 (base) · Argon 0 | aberto — medir 4–6 vídeos |

### Medição Gemini 3.8 x Argon (régua igual: júri e revisor de fatos seguem no Gemini 3.8)
- Roteiro: nota roteiro_marca e diretor do MOLDE, tentativas até aprovar, tempo do roteirista (`roteiro.modelo_roteiro`
  no json do vídeo diz quem escreveu; se o Argon falhar cai no Gemini e conta à parte).
- Editor: GANHO = nota editada − nota do molde NO MESMO vídeo (tira o efeito das melhorias de código), edição
  terminou?, tempo.
- Confusão: o código melhorou em 27/10 (movimento) -> a nota do molde sobe sozinha; por isso o editor é medido em ganho.

| | Gemini 3.8 (base, 26–27/10) | Argon (desde 27/10 13:00) |
|---|---|---|
| vídeos | 6 | 0 |
| nota do molde (média) | 5,88 | — |
| roteiro_marca (média) | 7,0 | — |
| diretor (média) | 5,0 | — |
| ganho do editor (mesmo vídeo) | +0,08 (+0,25 · +0,25 · 0 · +0,12) | — |
| edições que terminaram | 4/6 (Hermes 27/10: 2 x timeout 1 h) | — |
| tempo do roteirista | ~10–30 s | teste 13:00: Argon estourou 600 s e caiu no Gemini = 653 s (+10 min) |
| tempo do editor (molde pronto -> fila) | Hermes 120 min (2 timeouts) · Cardápio 122 min | (1º = Agenda IA 27/10 ~14:40) |
| tempo total a mais por vídeo | — | medir: soma roteiro + editor vs base |
Dono 27/10: medir também QUANTO TEMPO o Argon acrescenta na produção de cada vídeo. `roteiro.tempo_roteiro_s` e
`tentativas_roteiro` agora vão no json do vídeo; o editor pelo log (material pronto -> [OK]). O roteiro Argon só
começa na próxima rodada do diário (o processo atual carregou o código às 07:28); o editor já vale a partir da Agenda.
Roteiro: Argon falhou 1x = segue Gemini nas outras tentativas (não soma 4 x 10 min).
Voltar: `config\produto_lapidar.antes_argon.json` + agentes.MODELO_ROTEIRO = Gemini.

Próximos (no máximo 2–3 abertos): voz clonada Francisca x edge; CTA no meio x só no fim.
