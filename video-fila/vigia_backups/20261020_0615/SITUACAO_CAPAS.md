# Situação das capas IA — 20/10/2026 06:06-06:08

## Erro
3 vídeos do parceiro falharam a capa IA e usaram frame do vídeo (fallback):
- 06:06:42, 06:07:15, 06:07:59
- Último: "Desconhecido" (título "#anime #viral #animeshorts"), traído no calabouço

## Causa raiz
**Os 3 serviços de imagem estão fora**:

1. **Cloudflare flux-2-klein-4b** (4 contas, 10k neurons/dia cada):
   - HTTP 400 "Your output has been flagged"
   - Filtro de segurança bloqueando prompts de anime de ação/fantasia
   - Palavras-gatilho prováveis: "betrayed", "dungeon", "power", "attacked"

2. **Pollinations** (flux.2-klein-4b, z-image-turbo):
   - HTTP 402 "Insufficient balance. This request costs ~0.0050 pollen"
   - Saldo grátis acabou (teste de 19/10 esgotou o crédito de boas-vindas)
   - Chave: secrets/pollinations.json (sk_8DtSMnaG80h...)

3. **Gateway OmniRoute** (Gemini, capas boas):
   - Desligado pelo dono em 20/10 (imagem_reserva.py linha 38: GATEWAY = False)
   - Motivo: 403 "Verify your account" + 429 desde 19/10

## Opções de conserto

### A) Recarregar Pollinations (mais rápido)
- Adicionar crédito em gen.pollinations.ai com a chave do secrets/pollinations.json
- flux.2-klein-4b SEM filtro de saída (faz as poses sensuais de RECUSA do hipercool)
- z-image-turbo também sem filtro restritivo

### B) Religar gateway OmniRoute
- Mudar GATEWAY = True no imagem_reserva.py (+ secrets/omniroute.json ok)
- Era a fonte das capas boas (antes de 19/10)
- Se ainda der 403/429, não adianta

### C) Ajustar prompts pro Cloudflare
- Tirar palavras-gatilho dos prompts de capa_ia_anime.py
- Imprevisível (filtro deles é caixa-preta)
- Já testado em 19/10: ~50% de rejeição até em poses aprovadas

### D) Manter como está
- Capa de frame do vídeo (fallback) funciona
- Regra do dono: "defeito pequeno não segura postagem"
- Produção não travou

## Estado atual
- Produção rodando com capa de fallback (permitido)
- Não travou nenhum canal
- Decisão de qual caminho = dono (custo × qualidade)

## Conferir saldo/cota
```bash
# Cloudflare neurons restantes (zera 00:00 UTC, próximo reset em ~15h)
curl -H "Authorization: Bearer <token>" https://api.cloudflare.com/client/v4/accounts/<id>/ai/usage

# Pollinations (precisa permissão account:usage na chave)
curl -H "Authorization: Bearer sk_8DtSMnaG80h..." https://api.pollinations.ai/v1/usage
```
