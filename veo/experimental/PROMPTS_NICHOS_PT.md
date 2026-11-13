# Prompts por nicho — Shorts Veo 3.1 (fala PT-BR nativa)

> Regra do PT-BR no Veo: sempre dar a **fala exata entre aspas** + a instrução
> `spoken in Brazilian Portuguese`. O Veo respeita muito mais a fala quando ela
> vem literal e curta. Frase curta (1 linha), 8s, 9:16. Validar áudio no ffprobe.
> Se sair em inglês/embolado → refazer com a fala ainda mais curta e explícita.

Todos são pensados pra **short vertical 9:16, ~8s, com áudio**.

---

## 1) COMÉDIA / humor
```
A clumsy office cat in a tiny business suit knocks a coffee mug off a desk in slow motion, then looks at the camera and says in Brazilian Portuguese: "Nao fui eu, juro." Comedic timing, exaggerated cartoon reaction, bright lighting, vertical 9:16.
```

## 2) MÚSICA / clipe curto
```
A cozy lofi bedroom at night, neon rain on the window, a girl with headphones nodding to a chill beat, soft synth melody playing, dreamy vibe. On-screen mood, no speech, just warm lofi music. Vertical 9:16, cinematic.
```
(música pode não ter fala; se quiser voz, trocar por locução PT-BR por cima depois.)

## 3) CURIOSIDADES / você sabia
```
Cinematic close-up of the deep ocean with bioluminescent creatures glowing in the dark water. A warm narrator says in Brazilian Portuguese: "Voce sabia? O fundo do mar e menos explorado que a Lua." Documentary style, vertical 9:16, ambient underwater sound.
```

## 4) TERROR / creepypasta
```
A dark empty hallway lit by a single flickering light, camera slowly pushing in toward a half-open door. A whispering voice says in Brazilian Portuguese: "Tem alguem na sua casa." Cold blue tones, fog, eerie ambient sound, horror short, vertical 9:16.
```

## 5) MOTIVAÇÃO / superação
```
An athlete running alone at sunrise on an empty road, sweat and determination, cinematic slow motion. A strong narrator says in Brazilian Portuguese: "Ninguem vai fazer por voce. Levanta." Inspirational, golden light, vertical 9:16, uplifting music.
```

## 6) FATO HISTÓRICO / espaço
```
A breathtaking view of Earth from orbit, stars and the sun rising over the horizon, NASA-style cinematic space footage. A calm narrator says in Brazilian Portuguese: "A Terra vista do espaco cabe no seu polegar." Ambient space music, vertical 9:16.
```

## 7) SATISFATÓRIO / ASMR visual
```
Extreme close-up of colorful kinetic sand being sliced cleanly by a knife, crisp crunchy sound, super satisfying, soft studio lighting. No speech, only the crunchy ASMR sound. Vertical 9:16, slow motion.
```

---

---

## 🔥 LOTE VIRAL (formatos que engajam em Shorts BR — gerados 03/07/2026)

### V1) POV / "reaja isso" (comédia relatável)
```
POV shot from a person's perspective waking up late for work, phone alarm screaming, jumping over a messy room in a panic. A frustrated voice says in Brazilian Portuguese: "Nao acredito que dormi de novo." Fast comedic cuts, handheld, vertical 9:16, morning light.
```

### V2) Fato chocante / "ninguém te contou" (curiosidade viral)
```
Cinematic macro shot of a honeybee in slow motion, pollen glowing in golden light. A warm narrator says in Brazilian Portuguese: "Sem as abelhas, a humanidade tinha 4 anos de vida." Documentary style, vertical 9:16, soft ambient music.
```

### V3) Transformação satisfatória (before/after, alto retention)
```
A dirty old pair of sneakers being cleaned, dramatic before-and-after, foam and water, super satisfying close-ups, crisp cleaning sounds. No speech, only satisfying ASMR. Vertical 9:16, bright studio light.
```

### V4) Frase de impacto / mindset (motivação viral)
```
A lone wolf standing on a snowy cliff at dawn, breath visible in the cold, epic and cinematic. A deep narrator says in Brazilian Portuguese: "Enquanto voce dormia, alguem treinava pra te vencer." Vertical 9:16, epic orchestral music.
```

### V5) "Você consegue?" / desafio visual (engajamento por comentário)
```
An optical illusion of endless stairs that loop impossibly, camera moving through them, mind-bending Escher-style architecture. A curious voice says in Brazilian Portuguese: "Quantos degraus voce consegue contar?" Vertical 9:16, dreamy synth.
```

---

## Como usar (troca só o texto do prompt):
```bash
cd D:/hipercool-inferior-fix/roteador-veo-api-fake
PYTHONUTF8=1 D:/hipercool-videos/venv/Scripts/python.exe -u gera_auto.py \
  "<PROMPT DAQUI>" videos/nichos/<nicho>/v1.mp4 > logs/<nicho>.log 2>&1
```
Depois validar com ffprobe (ver COMO_GERAR_VIDEO_VEO_PASSO_A_PASSO.md, PASSO 4).
