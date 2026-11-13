# Isca v3 (curta): texto e plano de troca

Escrito em 15/10/2026 ~12:20, antes de mexer em qualquer coisa. Nada deste arquivo foi executado.
Dois momentos de OK da dona: **(A)** o texto; **(B)** o áudio ouvido e a troca. Entre um e outro, a campanha segue como está.

## 1. Por que trocar (resumo)

Das 16 atendidas até agora, 10 não passaram da isca. Com a isca de 5,7 s, 2 desligaram no meio e 5 ouviram inteira e
desligaram 1,5–2 s depois, sem dizer uma frase completa. Com a de 9,6 s, 3 de 3 desligaram no meio. O ritmo da voz é de
~3 palavras por segundo; alvo: **até 10 palavras, 3,5 s, terminando em pergunta**.

## 2. Texto: 8 candidatos, 3 juízes (dono de imobiliária, voz sintética, vendedor por telefone)

| Nota | Texto | Palavras | Comentário dos juízes |
|---|---|---|---|
| **8,2** | Oi, é da Inovári. Vocês atendem cliente pelo WhatsApp? | 9 | Pergunta sobre o negócio dela: responde "sim" por reflexo, e a oferta ("a gente tem uma ferramenta… atendente no WhatsApp") emenda direto. Risco: parecer cliente perguntando. Ajuste sugerido: "Oi, **aqui** é da Inovári…" (10 palavras) |
| 7,5 | Oi, é da Inovári. Você que cuida do atendimento aí? | 10 | Soa gente de verdade procurando a pessoa certa; "sou eu"/"quem é?" caem bem na IA. Risco: um "não, é outra pessoa" toca a oferta para a pessoa errada |
| 7,3 | Oi, é da Inovári, sobre a sua imobiliária. Pode falar? | 10 | Motivo ligado à pessoa e "Pode falar?" é a pergunta padrão de telefone. Risco: "sobre a sua imobiliária" soar como cobrança/reclamação |
| 6,3 | Oi! É da Inovári, sobre o atendimento de vocês. Pode falar? | 11 | Passa do alvo; "sobre o atendimento de vocês" soa como queixa |
| 6,0 | Oi, é da Inovári. Posso falar um minutinho? | 8 | É o mesmo pedido de licença de telemarketing da isca antiga ("posso falar uns segundinhos"), que 5 de 13 ouviram e desligaram |
| 5,5 | Oi! É da Inovári. Você cuida do WhatsApp da imobiliária? | 10 | "Cuida do WhatsApp" tem cheiro de golpe; "não, é fulano" atrapalha |
| 5,0 | Oi, é da Inovári. Posso falar do WhatsApp da imobiliária? | 10 | Pede licença e já vende; vago |
| 4,8 | Oi, aqui é da Inovári. Posso te falar rapidinho? | 9 | "Rapidinho" = isca antiga |

**Recomendação do agente:** `Oi, aqui é da Inovári. Vocês atendem cliente pelo WhatsApp?` (10 palavras, ~3,3 s).
Alternativa se a dona achar que "parece cliente": `Oi, aqui é da Inovári. É você que cuida do atendimento aí?` (11 palavras,
no limite). Em todo caso, a duração só se sabe medindo o áudio (a v2 era estimada em 6 s e saiu com 9,6 s).

Observações da voz: "WhatsApp" sai como "uatzép" de propósito (filtro de pronúncia do Hermes, o mesmo da conversa ao
vivo); "Inovári" passa como está. O texto gravado em `request.tts_message` é o texto normal (não a grafia fonética), e é
o que a IA recebe como "o que o cliente já ouviu". O perfil "Vendas Hermes Call" não cita a isca no prompt (conferido).

## 3. Plano de troca (produção, `ssh hermes-prod`; só depois do OK A)

Tudo roda como root na VPS. `K` é o cabeçalho da chave: `K="X-API-Key: $(cat /root/.hermes-campanha-apikey)"` (nunca ecoar
a chave). Placeholders: `<TEXTO_NOVO>`, `<ID_NOVO>`, `<MS_NOVO>`, `<DATA>`.

### Passo 1. Fotografia do estado (só leitura)

```bash
sudo -u postgres psql -d wacalls_main -x -c "SELECT id, user_id, audio_ref, audio_ms, to_char(next_slot_at AT TIME ZONE 'America/Sao_Paulo','DD/MM HH24:MI') AS proximo, paused, sent_today, sent_day, request->>'audio_id' AS audio_id, request->>'tts_message' AS tts_message, request->>'audio_id_2' AS audio_id_2, left(request->>'tts_message_2',40) AS oferta, request->>'tts_voice' AS voz, request->>'profile_id' AS perfil, request->>'start_hour' AS ini, request->>'end_hour' AS fim, request->>'weekdays_only' AS uteis FROM campaigns WHERE id='8843d578ff82eee06fdc1f6198040df8'"
curl -s -H "$K" http://127.0.0.1:8080/api/auth/me | jq -r '.user.id'   # conferido em 15/10 12:11: igual a campaigns.user_id
```

### Passo 2. Gerar o áudio com a mesma voz, pelo próprio Hermes

`POST /api/tts/generate` usa o mesmo rotador de chaves ElevenLabs e o mesmo modelo da ligação. A resposta diz
`provider` pedido, não o efetivo: se a conta ficasse sem chave ElevenLabs, cairia na voz grátis em silêncio. Por isso a
conferência dos 4 primeiros bytes (MP3 = `ID3` ou `ff fb`/`ff f3`; `OggS` = voz grátis, descartar).

```bash
umask 077; cd /root
jq -n --arg t "<TEXTO_NOVO>" '{text:$t, provider:"elevenlabs", voice:"hpp4J3VqNfWAUOO0d1Us"}' > isca-v3-req.json
curl -s -m 130 -H "$K" -H 'Content-Type: application/json' --data @isca-v3-req.json http://127.0.0.1:8080/api/tts/generate > isca-v3-resp.json
jq '{provider,voice,bytes,error}' isca-v3-resp.json                      # bytes > 0, sem error
jq -r .audio_base64 isca-v3-resp.json | tr -d '\n' > isca-v3.b64 && base64 -d isca-v3.b64 > isca-v3.mp3
od -A n -t x1 -N 4 isca-v3.mp3                                            # 49 44 33 (ID3) ou ff fb/ff f3 = ElevenLabs; 4f 67 67 53 (OggS) = NÃO usar
journalctl -u hermes-call --since '-3 min' --no-pager -o cat | grep -iE 'voz grátis|edge-tts' | tail -3   # tem de vir vazio
```

### Passo 3. Medir a duração como o servidor mede

O servidor não calcula a duração ao salvar na biblioteca; `duration_ms` é o que a gente manda, e `campaigns.audio_ms` é
o que vai para os resultados das ligações sem conversa e para o cabeçalho da campanha.

```bash
B=$(ffmpeg -hide_banner -loglevel error -i /root/isca-v3.mp3 -ac 1 -ar 16000 -f f32le pipe:1 | wc -c); echo "MS_NOVO=$((B/64))"
ffprobe -v error -show_entries format=duration -of csv=p=0 /root/isca-v3.mp3   # conferência
```
Se passar de **3.600 ms**, encurtar o texto e voltar ao passo 2.

### Passo 4. A dona ouve e dá o OK B

```powershell
# no PC
scp hermes-prod:/root/isca-v3.mp3 D:\hermes\campanha\campanha-01\isca-v3.mp3
```
O agente manda o arquivo na conversa, com o texto e a duração medida. Só segue com o OK dela (texto, pronúncia de
"Inovári", duração).

### Passo 5. Salvar na biblioteca da conta da campanha

```bash
jq -n --rawfile b64 /root/isca-v3.b64 --argjson ms <MS_NOVO> '{name:"[campanha] Divulgação Hermes - imobiliárias (piloto 01) (isca v3 <DATA>)", audio_base64:($b64|rtrimstr("\n")), mime:"audio/mpeg", duration_ms:$ms, voice:"hpp4J3VqNfWAUOO0d1Us", source:"tts"}' > /root/isca-v3-lib.json
ls -l /root/isca-v3-lib.json                                               # tem de ficar abaixo de 1 MB (limite do corpo)
curl -s -H "$K" -H 'Content-Type: application/json' --data @/root/isca-v3-lib.json http://127.0.0.1:8080/api/audios | tee /root/isca-v3-lib-resp.json | jq '{id,name,duration_ms,voice,source}'
ID_NOVO=$(jq -r .id /root/isca-v3-lib-resp.json); echo "$ID_NOVO"          # 32 letras, sem traço (mesmo formato do audio_ref atual)
sudo -u postgres psql -d wacalls_main -c "SELECT (a.user_id = c.user_id) AS mesmo_dono, a.duration_ms, a.voice FROM audio_library a, campaigns c WHERE a.id='$ID_NOVO' AND c.id='8843d578ff82eee06fdc1f6198040df8'"   # mesmo_dono = t
```
Depois disso a dona também consegue ouvir no painel › biblioteca de áudios. Nada mudou na campanha ainda.

### Passo 6. Backup da campanha e script de volta prontos ANTES de trocar

```bash
F=/root/backup-campanha-8843-$(date +%Y%m%d-%H%M).json; umask 077
sudo -u postgres psql -d wacalls_main -Atc "SELECT row_to_json(c) FROM campaigns c WHERE id='8843d578ff82eee06fdc1f6198040df8'" > "$F"
jq '{audio_ref, audio_ms, next_slot_at, paused, sent_today, audio_id:.request.audio_id, tts_message:.request.tts_message, audio_id_2:.request.audio_id_2}' "$F"
ls -l "$F" /root/backup-campanha-8843-20261015-0655.json                   # o das 06:55 (isca v1) fica guardado
```
Script de volta (`/root/rollback-isca-v3.sh`, 700), no formato heredoc (o `psql -c` não substitui variáveis):
```bash
cat > /root/rollback-isca-v3.sh <<'EOF'
#!/bin/bash
set -euo pipefail
T=$(jq -er '.request.tts_message' /root/backup-campanha-8843-<DATA-HORA>.json)
sudo -u postgres psql -d wacalls_main -v ON_ERROR_STOP=1 -v t="$T" -v novo="<ID_NOVO>" <<'SQL'
UPDATE campaigns
   SET audio_ref='03012f1a15eb073880f8a702298d85d3', audio_ms=9613,
       request=jsonb_set(jsonb_set(request,'{audio_id}',to_jsonb('03012f1a15eb073880f8a702298d85d3'::text)),'{tts_message}',to_jsonb(:'t'::text))
 WHERE id='8843d578ff82eee06fdc1f6198040df8' AND audio_ref=:'novo'
 RETURNING audio_ref, audio_ms, left(request->>'tts_message',40);
SQL
EOF
chmod 700 /root/rollback-isca-v3.sh
```

### Passo 7. Segurar a campanha (nenhuma ligação sai com a isca velha no meio da troca)

`paused=true` é a trava principal (nenhum tick a sobrescreve; o cadenciador ignora campanha pausada). O `next_slot_at`
+30 min é a segunda trava: um tick que não disca reprograma para +1 min, por isso a conferência 10 s depois.

```bash
sudo -u postgres psql -d wacalls_main -Atc "UPDATE campaigns SET paused=true, next_slot_at = now() + interval '30 minutes' WHERE id='8843d578ff82eee06fdc1f6198040df8' RETURNING paused, to_char(next_slot_at AT TIME ZONE 'America/Sao_Paulo','HH24:MI:SS')"
sleep 10; sudo -u postgres psql -d wacalls_main -Atc "SELECT paused, to_char(next_slot_at AT TIME ZONE 'America/Sao_Paulo','HH24:MI:SS') FROM campaigns WHERE id='8843d578ff82eee06fdc1f6198040df8'"   # paused=t; se o horário caiu, repetir
```
Isto não segura o retorno de ligação perdida nem a ligação automática da v0.13.0 (eles não leem a isca e não precisam
do reinício; só podem estar no ar na hora do reinício, ver passo 9).

### Passo 8. Trocar a isca no banco (um comando, atômico, com trava)

```bash
sudo -u postgres psql -d wacalls_main -v ON_ERROR_STOP=1 -v id="<ID_NOVO>" -v ms=<MS_NOVO> -v t="<TEXTO_NOVO>" <<'SQL'
UPDATE campaigns
   SET audio_ref = :'id',
       audio_ms  = :ms,
       request   = jsonb_set(jsonb_set(request, '{audio_id}', to_jsonb(:'id'::text)), '{tts_message}', to_jsonb(:'t'::text))
 WHERE id = '8843d578ff82eee06fdc1f6198040df8'
   AND audio_ref = '03012f1a15eb073880f8a702298d85d3'
   AND request IS NOT NULL
 RETURNING audio_ref, audio_ms, request->>'audio_id' AS audio_id, request->>'tts_message' AS tts_message,
           request->>'audio_id_2' AS audio_id_2, left(request->>'tts_message_2',30) AS oferta, request->>'tts_voice' AS voz,
           request->>'profile_id' AS perfil, request->>'start_hour' AS ini, request->>'end_hour' AS fim, paused;
SQL
```
"0 rows" = a trava barrou, nada mudou, voltar ao passo 1. O que muda: `audio_ref` (de onde o áudio é carregado),
`audio_ms` e `request.tts_message` (o que a IA recebe); `request.audio_id` só para a linha ficar coerente. **Não muda:**
oferta (`audio_id_2`/`tts_message_2`), voz da conversa, perfil, números, nomes, `pace_config`, `sent_today`, janela.

### Passo 9. Reinício seguro (único jeito de o áudio novo valer)

O cadenciador guarda a isca em memória e não existe rota que limpe isso; pausar/retomar não limpa. O reinício derruba
qualquer ligação em curso nas duas linhas (8653 e 8288, inclusive retorno de ligação perdida e a ligação da v0.13.0),
zera a trava de 12 h da ligação por mensagem (v0.13.0) e descarta retorno de ligação perdida que esteja esperando os 45 s.
No boot: `ReapStuck` marca `failed` número preso em `ringing` há mais de 15 min (não redisca); `resumeCampaigns` não
toca em campanha espaçada; o 1º tick do cadenciador é 25 s depois e só pega a campanha quando `paused=false` e
`next_slot_at <= now()`; o cache nasce vazio e o 1º dial lê `audio_ref`/`audio_ms` novos.

Pré-condições (todas verdadeiras):
```bash
sudo -u postgres psql -d wacalls_main -c "SELECT c.id, c.mode, left(c.name,30) AS nome, count(*) FILTER (WHERE r.status='queued') AS na_fila, count(*) FILTER (WHERE r.status IN ('ringing','sending','dispatched')) AS em_voo FROM campaigns c LEFT JOIN campaign_results r ON r.campaign_id=c.id WHERE c.finished_at IS NULL GROUP BY 1,2,3"   # só a 8843 (paced), em_voo=0 (conferido 12:11: é assim)
curl -s http://127.0.0.1:8080/saude-local | jq '{linhas_conectadas, ids_fora}'       # 2 e []
curl -s -H "$K" http://127.0.0.1:8080/api/sessions/290f2fb3c1ad8d570c732d16afd41f1e/calls | jq .active   # 0 (a 8288 é de outra conta: só o log cobre)
journalctl -u hermes-call --since '-5 min' --no-pager -o cat | grep -E 'call ACTIVE|incoming call|callback:|mensagem de lead:|call terminated|ligação não atendida|entrega=' | tail -5   # a última linha tem de ser um fim, não um ACTIVE
```
Conferência e reinício numa linha só (janela de segundos):
```bash
A=$(curl -s -H "$K" http://127.0.0.1:8080/api/sessions/290f2fb3c1ad8d570c732d16afd41f1e/calls | jq .active); R=$(sudo -u postgres psql -d wacalls_main -Atc "SELECT count(*) FROM campaign_results WHERE status IN ('ringing','sending','dispatched')"); [ "$A" = 0 ] && [ "$R" = 0 ] && { date; systemctl restart hermes-call; } || echo "ligação em curso (active=$A em_voo=$R): esperar"
for i in $(seq 1 30); do curl -s -m3 http://127.0.0.1:8080/api/version | grep -q '"build"' && break; sleep 3; done; curl -s http://127.0.0.1:8080/api/version; echo
sleep 20; curl -s http://127.0.0.1:8080/saude-local | jq '{linhas_conectadas, ids_fora}'   # 2 e [] antes de liberar
journalctl -u hermes-call --since '-2 min' --no-pager -o cat | grep -E 'sessions restored|level=ERROR|presos' | tail -5
```

### Passo 10. Liberar a campanha

```bash
sudo -u postgres psql -d wacalls_main -Atc "UPDATE campaigns SET paused=false, next_slot_at = now() WHERE id='8843d578ff82eee06fdc1f6198040df8' RETURNING paused, to_char(next_slot_at AT TIME ZONE 'America/Sao_Paulo','HH24:MI:SS'), sent_today"
journalctl -u hermes-call -f -o cat | grep --line-buffered -E 'scheduler|gate pcm2|isca\) tocado|oferta\) tocado|ligação não atendida|não está no WhatsApp|WARN|ERROR'
```
A 1ª discagem sai no próximo tick (até 1 min). Em todo o processo a campanha perde um intervalo (~11 min); o serviço
fica fora do ar ~5 s e as linhas voltam em ~15 s.

### Verificação depois

| O que | Esperado |
|---|---|
| 1ª discagem NÃO atendida (`campaign_results` por `updated_at`) | `audio_ms = <MS_NOVO>` (prova de que o cadenciador leu a linha nova) |
| 1ª atendida, no log | `áudio 1 (isca) tocado durMs≈<MS_NOVO>` e `gate pcm2 … pcm2_len=373255` (oferta continua carregada) |
| Atendida que chegou à IA | `audio_ms ≈ <MS_NOVO> + 23328` (isca + oferta) e `listen_pct` sobre esse total: **não** é sinal de isca velha |
| Oferta pulada ("quem fala?"/recusa) | `audio_ms = <MS_NOVO>` |
| Log do 1º dial | sem `campanha paced sem áudio persistido`, `decode do áudio … falhou`, `oferta da campanha não encontrada`, `scheduler: falha ao discar` |
| Cadência | `next_slot_at` ≈ última ligação + ~11 min, `paused=false`, `sent_today` continuou de onde estava |
| 1ª conversa com a IA (`call_transcripts`) | a IA não repete a isca nem fala como se tivesse dito o texto antigo |
| Resultado com `updated_at` a ±1 min do reinício | anotar como "cortada pelo reinício" e não contar na comparação |
| Biblioteca (`GET /api/audios`) | v3 com o nome "(isca v3 …)" e `duration_ms=<MS_NOVO>`; v2 e v1 continuam lá (não apagar: `audio_ref` apontando para áudio apagado trava a campanha) |
| Depois de 10 atendidas | comparar "desligou na isca / depois da isca / ouviu a oferta / conversou" com a tabela de 15/10 antes de qualquer outra mudança |

Registrar no PLANO.md: hora, `<ID_NOVO>`, `<MS_NOVO>`, texto, horário do reinício, 1ª ligação, arquivo de backup.
A revisão horária (outra sessão) também escreve no PLANO.md: acrescentar, nunca sobrescrever.

### Volta (rollback)

1. `bash /root/rollback-isca-v3.sh` → "1 row" com `03012f1a…`, `9613`, texto v2.
2. Repetir o passo 9 (segurar com `paused=true`, pré-condições, reinício seguro) e o passo 10.
3. Conferir: próxima discagem com `audio_ms=9613` e, na próxima atendida, `durMs≈9600`.
4. Volta para a isca v1 (5,7 s), se quiserem: mesmo script com `faf486e5dccadebe67dffc1e05fb1d58`, `5669` e o texto de
   `jq -er '.request.tts_message' /root/backup-campanha-8843-20261015-0655.json` (a análise diz que a v1 não resolve).
5. Se o serviço não subir em 90 s: `journalctl -u hermes-call -n 80`; a campanha é só dados, então o problema seria a
   versão: `bash ops/reverter.sh` no PC (→ v0.12.0).
6. Número que ficou `ringing` por causa do reinício: deixar o `ReapStuck` marcar `failed` (até 1 h); rediscar só com OK
   (`UPDATE campaign_results SET status='queued', reply='' WHERE … AND reply LIKE 'reaped:%'`).

### Cuidados

- Uma mudança só: não aproveitar o reinício para trocar oferta, perfil ou horário.
- Texto só com letras, vírgula, ponto e interrogação; passar sempre por `jq --arg` e `psql -v` (nunca montar JSON/SQL à mão).
- Não gerar o áudio várias vezes à toa (crédito do ElevenLabs); se der 502, esperar 1 min.
- Nunca ecoar a chave da API nem colar a resposta inteira de `/api/auth/me` em documento.
- Escolher o momento logo depois de uma ligação encerrar e longe do fim da janela (18h), para medir a isca nova ainda hoje.
