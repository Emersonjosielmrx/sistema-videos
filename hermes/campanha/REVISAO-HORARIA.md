# Revisão horária da campanha (prompt para o agente)

Guardado em 15/10/2026 a partir da passagem entre agentes. Use em cron das 7h às 18h, dias úteis, **só se a dona pedir**.
Com a ferramenta Monitor (`journalctl -f` filtrado) o acompanhamento expira em 30 min: rearme quando expirar.

---

Revisão da campanha de divulgação do Hermes (produção: `ssh hermes-prod`, banco `wacalls_main`, campanha
`8843d578ff82eee06fdc1f6198040df8`, linha 8653 = sessão `290f2fb3c1ad8d570c732d16afd41f1e`).

Para cada ligação ATENDIDA desde a última revisão: leia a transcrição e os números de qualidade do áudio, confira no
registro (`journalctl -u hermes-call`) se a oferta tocou (linha "áudio 2 (oferta) tocado"; "gate pcm2" com
`pcm2_len > 0` só mostra que estava carregada) e se a IA errou preço/produto ou prometeu algo que não existe. Conte
também discadas, atendidas, sem WhatsApp, pedidos de "não ligar" e falhas seguidas. Mascare telefones (×1234).

Avise a dona em português simples e curto: o que foi bem, o que ajustar (uma mudança de roteiro por vez, só com o OK
dela). Se a campanha parou (parada por risco, linha desconectada, nenhuma ligação na última hora dentro das 7h–18h),
avise logo. Anote no registro de `D:\hermes\campanha\PLANO.md`. Não mude nada na produção sem o OK dela.

## Consultas que ajudam

```sql
-- discadas de hoje (o created_at é o da criação da campanha; use updated_at)
SELECT to_char(updated_at AT TIME ZONE 'America/Sao_Paulo','HH24:MI'), 'x'||right(number,4), status, duration_ms, round(listen_pct::numeric)
FROM campaign_results
WHERE campaign_id='8843d578ff82eee06fdc1f6198040df8' AND status<>'queued'
  AND (updated_at AT TIME ZONE 'America/Sao_Paulo')::date = CURRENT_DATE
ORDER BY updated_at;

-- transcrições de hoje (só as ligações em que a conversa com a IA começou)
SELECT to_char(created_at AT TIME ZONE 'America/Sao_Paulo','HH24:MI'), 'x'||right(number,4), classificacao, interested, resumo
FROM call_transcripts WHERE created_at > CURRENT_DATE ORDER BY created_at;

-- atendidas por faixa de hora (para decidir horário e rediscagem; amostra pequena até ter 100+ discadas)
SELECT extract(hour from updated_at AT TIME ZONE 'America/Sao_Paulo')::int AS hora, count(*) AS discadas,
       count(*) FILTER (WHERE status='completed') AS atendidas,
       round(100.0*count(*) FILTER (WHERE status='completed')/count(*)) AS pct
FROM campaign_results WHERE campaign_id='8843d578ff82eee06fdc1f6198040df8' AND status<>'queued'
GROUP BY 1 ORDER BY 1;

-- próximo horário de discagem e contador do dia
SELECT next_slot_at, sent_today, sent_day, paused FROM campaigns WHERE id='8843d578ff82eee06fdc1f6198040df8';
```

```bash
journalctl -u hermes-call --since "60 min ago" | grep -v 'xml=' | grep -E 'ligação não atendida|gate pcm2|isca\) tocado|oferta\) tocado|encerrou|qualidade do áudio|gravação entregue|mensagem de lead:|não está no WhatsApp|WARN|ERROR'
```
