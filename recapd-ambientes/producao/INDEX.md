# INDEX — Hipercool Inferior

> Projeto de geração automática de vídeos recap de manhwa.
> Base: edge-tts (vozes grátis) + Gemini (visão/narração) + FFmpeg (montagem).

> 📮 **POSTAR NO YOUTUBE:** ver **`POSTAGEM_YOUTUBE_PLAYBOOK.md`** (pipeline completo,
> limites reais testados, canais, postador automático do Windows, vídeos do OpenClaw).

## Estrutura do Projeto

```
D:\hipercool-inferior\
├── bin/                    ← Scripts principais (pipeline, TTS, efeitos)
├── workspace/
│   ├── panels/             ← Painéis cortados por capítulo
│   ├── videos/             ← Vídeos gerados
│   ├── assets/             ← SFX, trilhas, memes, overlays
│   ├── narration_cache/    ← Cache de narrações (JSON por capítulo)
│   └── tmp/                ← Temporários de sessão (limpos após gerar)
├── material/
│   └── tts_cache/          ← Cache de áudios TTS (WAVs reusáveis)
├── secrets/                ← Chaves API, proxies
├── codigos-legado/         ← Referência dos workflows n8n
├── BACKUP_ESTAVEL_FUNCIONAL/ ← Último estado 100% funcional
└── .git/                   ← Versionamento
```

## Scripts Principais (bin/)

| Script | Função | Dependências |
|--------|--------|-------------|
| hiper-pipeline.py | Pipeline completa (visão→narração→TTS→vídeo) | edge_tts_engine, effects_engine, gemini_llm |
| effects_engine.py | Efeitos visuais, transições, SFX, trilha, concat | FFmpeg |
| edge_tts_engine.py | TTS com edge-tts + Gemini fallback + ElevenLabs | edge-tts, gemini_tts |
| elevenlabs_tts.py | TTS ElevenLabs (14 vozes masculinas) | urllib |
| gemini_tts.py | TTS Gemini (vozes originais) | urllib, Webshare proxy |
| gemini_llm.py | Visão Gemini (descreve painéis + gera narração) | urllib |
| panel-splitter.py | Corta strips verticais em painéis individuais | PIL |
| hiper-fetcher.py | Baixa capítulos de sites (Playwright) | playwright |
| tia-fetcher.py | Baixa do tiamanhwa.com (requests simples) | urllib |
| landscape-compiler.py | Compila versão paisagem (1920x1080) | FFmpeg |
| hyperframes-from-normal.py | Gera hyperframes do vídeo normal | FFmpeg |
| auto-validate.py | Valida vídeo automaticamente (volume, sync, etc.) | FFmpeg |
| tts_cache.py | Cache híbrido de áudio por similaridade | — |
| sfx_categorizer.py | Categoriza SFX por mood | — |

## Documentação

- [CHECKLIST_PENDENCIAS_COMPLETO.md](CHECKLIST_PENDENCIAS_COMPLETO.md) — Lista mestre de TUDO pendente
- [CHECKLIST_VIDEO.md](CHECKLIST_VIDEO.md) — Como validar cada vídeo gerado
- [HANDOFF_BUGS.md](HANDOFF_BUGS.md) — Bugs conhecidos e como corrigir
- [GUIA_OPERACAO_SCRAPE_SPLIT.md](GUIA_OPERACAO_SCRAPE_SPLIT.md) — Como baixar e cortar painéis
- [codigos-legado/README_ANALISE.md](codigos-legado/README_ANALISE.md) — Viral Image Engine (n8n)
- [codigos-legado/README_AUDIO_ANALISE.md](codigos-legado/README_AUDIO_ANALISE.md) — Sistema de áudio (n8n)
- [codigos-legado/README_EFFECTS_ENGINE_ANALISE.md](codigos-legado/README_EFFECTS_ENGINE_ANALISE.md) — Effects V5.1 (n8n)

## Fluxo de Geração de Vídeo

```
1. Baixar cap (hiper-fetcher.py ou tia-fetcher.py)
2. Cortar painéis (panel-splitter.py --dark-mode --thresh 230)
3. Pipeline (hiper-pipeline.py):
   a. Visão Gemini → descreve cada painel
   b. Narração Gemini → gera locuções + título
   c. TTS (edge-tts) → gera áudio por painel
   d. Build clips (effects_engine) → Ken Burns + SFX + transição
   e. Concat + trilha dinâmica + legendas + upscale
4. Validar (auto-validate.py)
5. Hyperframes (hyperframes-from-normal.py)
6. Landscape (landscape-compiler.py)
```

## Estado Atual
- Git inicializado, estado estável commitado
- Cap 1-9 gerados (versão edge V1)
- Cap 10 em geração (87 painéis)
- Caps 11-15 pendentes (fetcher precisa correção)
- 318 trilhas, 1400+ SFX, 251 memes disponíveis
