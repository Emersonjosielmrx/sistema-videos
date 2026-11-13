# Claude Code Video ADICIONAL (25/10/2026)

Claude Code (Opus 5.5, contas pagas do OmniRoute) como **motor extra** dos projetos (hipercool, manhwa-react,
produto, ms-energy). Nunca é dependência: sem cota/desligado/falhou → `None` e o projeto segue como sempre.

- `adicional.Sessao(projeto, video_id)` decide UMA vez, antes do vídeo, se liga (`cota_claude.decidir`, sem
  certeza, custo `custo_por_video`). Cota acabou no meio → a sessão se desliga e o resto do vídeo segue sem ele.
- `s.olhar(imagens, pergunta)` / `s.revisar_video(mp4, contexto)` → dict ou None. Nunca levanta exceção.
- Liga/desliga: `python adicional.py ligar|desligar [projeto]`; `status` mostra cota e últimas decisões
  (`estado/decisoes.jsonl`).
- Cota e motor vêm de `D:\claude-code-video` (cota_claude.py, motor.py) — uma versão só.

## Ainda NÃO ligado em nenhum projeto
Ligar num projeto = 3 linhas no ponto de "vídeo pronto" dele. Antes: `aprendizado.py aprovados` + ler
`aprendizado\PARA_IMPLEMENTAR.md` (regra do dono). Começar só avisando (resultado vai pro json do vídeo), sem travar.
