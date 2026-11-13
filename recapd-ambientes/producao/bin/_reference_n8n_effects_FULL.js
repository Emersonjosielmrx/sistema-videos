// Extraido de node: aplica efeitos
// Data: 2026-06-28
// ╔══════════════════════════════════════════════════════════════════════╗
// ║                GUIA DE MANUTENÇÃO PARA IA                            ║
// ╠══════════════════════════════════════════════════════════════════════╣
// ║                                                                      ║
// ║   🎯 COMO ADICIONAR NOVOS EFEITOS:                                   ║
// ║       → Vá para SEÇÃO 2: EFFECTS_DATABASE                            ║
// ║       → Adicione no array correspondente                             ║
// ║       → Sistema rotaciona automaticamente                            ║
// ║                                                                      ║
// ║   ✅ ATUALIZAÇÃO V5.1 (KARAOKE & JSON AUDIO):                        ║
// ║       → Suporte nativo a legendas .ass (Karaokê)                     ║
// ║       → Detecção de áudio real a partir de referência JSON           ║
// ║       → Mantida biblioteca V5.0 Ultimate completa                    ║
// ║                                                                      ║
// ╚══════════════════════════════════════════════════════════════════════╝

// ❌ NÃO REMOVER - Dependências do Node.js necessárias
const fs = require('fs');
const fsPromises = require('fs').promises;
const { execSync } = require('child_process');
const path = require('path');
const crypto = require('crypto');

// ======================================================================
// SEÇÃO 1: ✅ CONFIGURAÇÕES GLOBAIS - EDITÁVEL V5.0
// ======================================================================
const GLOBAL_CONFIG = {
  // ✅ Marca d'água do vídeo
  watermark: "TURBINE SEUS ATENDIMENTOS E POSTS COM NOSSA AI(91)984698653",
  
  // ✅ Configurações de resolução e formato
  outputFormat: {
    workingResolution: "1280:720",
    finalResolution: "1920x1080",
    workingWidth: 1280,
    workingHeight: 720,
    finalWidth: 1920,
    finalHeight: 1080,
    fps: 25,
    videoCodec: "libx264",
    audioCodec: "aac",
    crf: 23,
    audioBitrate: "128k",
    preset: "ultrafast",
    presetFallback: "veryfast",
    upscaleFilter: "lanczos",
    upscaleCrf: 21,
    
    // NOVO: Perfis de qualidade
    qualityProfiles: {
      draft: { crf: 28, preset: "ultrafast", audioBitrate: "96k" },
      standard: { crf: 23, preset: "fast", audioBitrate: "128k" },
      high: { crf: 20, preset: "medium", audioBitrate: "192k" },
      ultra: { crf: 18, preset: "slow", audioBitrate: "256k" }
    },
    currentProfile: "standard"
  },
  
  // ✅ Timeouts de processamento
  timeouts: {
    imageProcessing: 30000,
    videoBase: 300000,
    memeNormalization: 60000,
    transition: 120000,
    finalMix: 300000,
    fallback: 240000,
    upscale: 120000,
    audioAnalysis: 15000  // NOVO
  },
  
  // ✅ Configurações de áudio PROFISSIONAL
  audio: {
    sampleRate: 24000,
    channels: 1,
    musicVolume: 0.12,
    fadeInDuration: 3,
    fadeOutDuration: 3,
    
    // NOVO: Áudio profissional
    normalization: {
      enabled: true,
      targetLUFS: -16,        // Padrão YouTube
      truePeak: -1.5          // Evita clipping
    },
    ducking: {
      enabled: true,
      narrationVolume: 1.0,   // Volume da narração (referência)
      musicDuringNarration: 0.08,  // Música quando há narração (reduzida)
      duckingSpeed: 0.3       // Velocidade da transição (segundos)
    },
    enhancement: {
      noiseReduction: true,
      noiseAmount: 0.003,     // Muito sutil para não afetar voz
      deEsser: true,          // Remove sibilância excessiva
      compression: {
        enabled: true,
        threshold: -18,       // dB
        ratio: 3,             // 3:1
        attack: 5,            // ms
        release: 50           // ms
      }
    }
  },
  
 // ✅ Configurações do meme de transição
  meme: {
    frequency: 8,               // 🆕 A cada N vídeos (2 = alterna)
    duration: 8,
    transitionDuration: 0.5,
    transitionOffset: 1.5
  },
  
  // ═══════════════════════════════════════════════════════════════════════
  // ✅ V6.20: CONFIGURAÇÕES DE EFEITOS SONOROS - AJUSTE AQUI
  // ═══════════════════════════════════════════════════════════════════════
  soundEffects: {
    enabled: true,
    
    // 🔊 Volume do efeito sonoro (0.0 a 1.0) - REDUZIDO para não sobrepor narração
    effectVolume: 0.35,
    
    // 🔊 Volume da narração durante o efeito (ducking) - 1.0 = sem redução
    narrationDuckingVolume: 0.6,
    
    // ⏱️ Duração da pausa/redução na narração (em segundos)
    narrationPauseDuration: 1.0,
    
    // Fade in/out do ducking (em segundos)
    duckingFadeIn: 0.15,
    duckingFadeOut: 0.25,
    
    // Offset: quanto tempo ANTES do efeito começa o ducking
    duckingPreOffset: 0.1,
    
    // Peso no mix final (0.0 a 1.0)
    mixWeight: 0.5,
  },
  // ═══════════════════════════════════════════════════════════════════════
  
  
  // ✅ NOVO: Sistema de legendas avançado
  subtitle: {
    defaultStyle: "Fontname=Arial,Fontsize=14,PrimaryColour=&H00FFFFFF,BackColour=&H00000000,BorderStyle=1,Outline=1,Shadow=1,MarginV=25,Alignment=2,Bold=1",
    
    // NOVO: Estilos por contexto
    contextStyles: {
      normal: "Fontsize=14,PrimaryColour=&H00FFFFFF,Bold=1,Outline=2,Shadow=1",
      emphasis: "Fontsize=16,PrimaryColour=&H00FFFF00,Bold=1,Outline=2,Shadow=2",
      whisper: "Fontsize=12,PrimaryColour=&H00CCCCCC,Italic=1,Outline=1,Shadow=1",
      shout: "Fontsize=18,PrimaryColour=&H00FFFFFF,Bold=1,Outline=3,Shadow=2",
      thought: "Fontsize=13,PrimaryColour=&H00E0E0FF,Italic=1,Outline=1,Shadow=1"
    },
    
    // NOVO: Animações de entrada/saída
    animations: {
      enabled: true,
      fadeInDuration: 0.2,
      fadeOutDuration: 0.2,
      slideIn: false  // Pode causar distração na leitura
    },
    
    // NOVO: Posicionamento inteligente
    positioning: {
      avoidTopThird: true,      // Evita área comum de rostos
      preferBottom: true,
      adaptiveMargin: true,     // Ajusta margem por tamanho de texto
      maxWidth: 80              // % da largura da tela
    },
    
    // NOVO: Outline adaptativo
    outlineAdaptive: {
      enabled: true,
      minOutline: 1,
      maxOutline: 3,
      basedOnBackground: true  // Aumenta outline em fundos claros
    }
  },
  
  // ✅ NOVO: Sistema de memória para continuidade
  memory: {
    enabled: true,
    trackColorGrading: true,       // Mantém grading similar entre páginas
    trackMovementDirection: true,  // Mantém direção de movimento
    trackPacing: true,             // Mantém ritmo de transições
    trackAtmosphere: true,         // Mantém atmosfera (dark/light/etc)
    smoothingWindow: 3,            // Páginas para calcular média
    
    // Pesos para decisões (0-1)
    weights: {
      previousPage: 0.5,
      averageLast3: 0.3,
      contextual: 0.2
    }
  },
  
  // ✅ NOVO: Análise de conteúdo
  contentAnalysis: {
    enabled: true,
    detectBrightness: true,        // Analisa brilho médio
    detectContrast: true,          // Analisa contraste
    detectColorPalette: true,      // Detecta paleta predominante
    detectTextDensity: true,       // Estima densidade de texto
    
    // Ajustes baseados em análise
    adaptiveEffects: {
      enabled: true,
      brightnessThreshold: 0.6,   // > 0.6 = imagem clara
      contrastThreshold: 0.4,     // < 0.4 = baixo contraste
      textDensityHigh: 0.3        // > 0.3 = muito texto
    }
  },
  
  // ✅ NOVO: Otimização de performance
  performance: {
    enableCaching: true,
    cacheEffects: true,            // Cache de efeitos já processados
    parallelProcessing: false,     // Mantém false para estabilidade
    gpuAcceleration: "auto",       // "auto", "nvidia", "amd", "intel", "off"
    
    // Detecção automática de recursos
    autoDetectHardware: true,
    maxMemoryUsage: "2G",          // Limite de RAM
    tmpCleanup: true               // Limpa temporários automaticamente
  }
};

// ======================================================================
// SEÇÃO 2: ✅ EFFECTS_DATABASE - V5.0 ULTIMATE READING-OPTIMIZED
// ======================================================================

// ──────────────────────────────────────────────────────────────────────
// SEÇÃO 2A: ✅ FILTROS VISUAIS - 60 FILTROS OTIMIZADOS PARA LEITURA
// ──────────────────────────────────────────────────────────────────────
const VISUAL_FILTERS = [
  // ═══ TIER 1: IDEAIS PARA LEITURA - BACKGROUNDS SUAVES (25 filtros) ═══
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8[bg_blurred];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_blurred][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Blur Suave", weight: 10, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,eq=brightness=-0.5[bg_dark];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_dark][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Dark Suave", weight: 10, readability: 10 },
  
  { filter: `scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black`, name: "Black Border", weight: 15, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8[bg_blur];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[fg_scaled]split=2[orig][shadow];[shadow]drawbox=t=fill:c=black@0.4,scale=iw*1.01:ih*1.01[shadow_layer];[bg_blur][shadow_layer]overlay=(W-w)/2:(H-h)/2[bg_w_shadow];[bg_w_shadow][orig]overlay=(W-w)/2:(H-h)/2`, name: "Shadow Suave", weight: 10, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=25:10,colorbalance=rs=0.15:gs=0.08:bs=0.15[bg_pink];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_pink][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Romantic Suave", weight: 8, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,colorbalance=bs=0.25:rs=-0.15[bg_cold];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=saturation=0.85[fg_scaled];[bg_cold][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Cold Suave", weight: 8, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=20:8,colorbalance=rs=0.15:gs=0.08:bs=-0.15[bg_gold];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_gold][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Golden Suave", weight: 8, readability: 9 },
  
  { filter: `scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=white`, name: "White Border", weight: 5, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,hue=s=0[bg_bw];[fg]scale=1280:720:force_original_aspect_ratio=decrease,hue=s=0,eq=contrast=1.05[fg_scaled];[bg_bw][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Noir Suave", weight: 7, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,colorbalance=rs=0.3:gs=-0.3:bs=-0.3,eq=contrast=1.15:brightness=-0.2[bg_red];[fg]scale=1280:720:force_original_aspect_ratio=decrease,colorbalance=rs=0.08[fg_scaled];[bg_red][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Horror Suave", weight: 6, readability: 8 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131[bg_sepia];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_sepia][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Sepia Suave", weight: 7, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,colorbalance=bs=0.3:rs=-0.15:gs=-0.08[bg_blue];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_blue][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Blue Suave", weight: 8, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=18:9[bg_blur];[fg]scale=1280:720:force_original_aspect_ratio=decrease,unsharp=5:5:0.8:5:5:0.0[fg_sharp];[bg_blur][fg_sharp]overlay=(W-w)/2:(H-h)/2`, name: "Depth Focus", weight: 9, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=12:6,eq=brightness=-0.3[bg_vignette];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_vignette][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Vignette Natural", weight: 9, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=20:10[bg_soft];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=contrast=1.08[fg_contrast];[bg_soft][fg_contrast]overlay=(W-w)/2:(H-h)/2`, name: "Soft Contrast", weight: 10, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,noise=alls=5:allf=t[bg_grain];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_grain][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Film Grain BG", weight: 8, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8[bg_blur];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2,vignette=PI/10`, name: "Cinematic Frame", weight: 9, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,eq=gamma=1.1[bg_lift];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=gamma=0.95[fg_scaled];[bg_lift][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Lifted Blacks", weight: 8, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=20:10,colorbalance=rm=0.1:gm=0.05:bm=0.15[bg_matte];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_matte][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Matte Finish", weight: 7, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,eq=contrast=1.1:brightness=-0.1[bg_manga];[fg]scale=1280:720:force_original_aspect_ratio=decrease,unsharp=3:3:0.5:3:3:0.0[fg_sharp];[bg_manga][fg_sharp]overlay=(W-w)/2:(H-h)/2`, name: "Manga Print", weight: 10, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=12:6[bg_soft];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=contrast=1.05,smartblur=lr=0.3:ls=-0.3[fg_clean];[bg_soft][fg_clean]overlay=(W-w)/2:(H-h)/2`, name: "Clean Lines", weight: 10, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,hue=s=0.7[bg_desaturate];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_desaturate][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Subtle BW", weight: 7, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=18:9,eq=brightness=-0.4,colorbalance=bs=0.2[bg_night];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=contrast=1.05[fg_scaled];[bg_night][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Night Scene", weight: 7, readability: 8 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,eq=brightness=0.15[bg_day];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_day][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Day Scene", weight: 8, readability: 9 },
  
  { filter: `scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x1a1a1a`, name: "Dark Gray Border", weight: 8, readability: 10 },
// ═══ TIER 2: CLARITY & SHARPNESS (15 filtros) ═══
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8[bg_blur];[fg]scale=1280:720:force_original_aspect_ratio=decrease,cas=0.3[fg_clarity];[bg_blur][fg_clarity]overlay=(W-w)/2:(H-h)/2`, name: "Clarity Boost", weight: 9, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,eq=saturation=0.9[bg_subtle];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=saturation=1.05[fg_pop];[bg_subtle][fg_pop]overlay=(W-w)/2:(H-h)/2`, name: "Pop Center", weight: 9, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=10:5,eq=brightness=-0.2[bg_dim];[fg]scale=1280:720:force_original_aspect_ratio=decrease,unsharp=5:5:1.0[fg_sharp];[bg_dim][fg_sharp]overlay=(W-w)/2:(H-h)/2`, name: "Ultra Sharp", weight: 8, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,eq=contrast=0.95[bg_low];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=contrast=1.1[fg_high];[bg_low][fg_high]overlay=(W-w)/2:(H-h)/2`, name: "Contrast Pop", weight: 9, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=22:11[bg_very_soft];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=contrast=1.07[fg_scaled];[bg_very_soft][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Dreamy Focus", weight: 7, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,colorbalance=rm=-0.05:gm=0.05:bm=0.05[bg_cool_dim];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_cool_dim][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Cool Dim BG", weight: 7, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,colorbalance=rm=0.08:gm=0.05:bm=-0.05[bg_warm_dim];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_warm_dim][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Warm Dim BG", weight: 7, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8[bg_blur];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=gamma=0.9:contrast=1.08[fg_punch];[bg_blur][fg_punch]overlay=(W-w)/2:(H-h)/2`, name: "Dark Punch", weight: 8, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,eq=brightness=0.1[bg_light];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=gamma=1.05[fg_lifted];[bg_light][fg_lifted]overlay=(W-w)/2:(H-h)/2`, name: "Lifted Light", weight: 8, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=14:7,hue=s=0.9[bg_muted];[fg]scale=1280:720:force_original_aspect_ratio=decrease,hue=s=1.1[fg_vibrant];[bg_muted][fg_vibrant]overlay=(W-w)/2:(H-h)/2`, name: "Vibrant Center", weight: 8, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,eq=contrast=1.12:brightness=-0.15[bg_dramatic];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_dramatic][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Dramatic Dark", weight: 7, readability: 8 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,eq=brightness=0.2:saturation=1.1[bg_bright];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_bright][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Bright Airy", weight: 7, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8[bg_blur];[fg]scale=1280:720:force_original_aspect_ratio=decrease,smartblur=lr=0.5:ls=-0.5[fg_detail];[bg_blur][fg_detail]overlay=(W-w)/2:(H-h)/2`, name: "Detail Enhance", weight: 9, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,eq=brightness=-0.25:contrast=1.05[bg_moody];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_moody][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Moody Dark", weight: 7, readability: 8 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=13:6,eq=brightness=-0.15[bg_soft_dark];[fg]scale=1280:720:force_original_aspect_ratio=decrease,cas=0.4[fg_crisp];[bg_soft_dark][fg_crisp]overlay=(W-w)/2:(H-h)/2`, name: "Crisp Focus", weight: 9, readability: 10 },

  // ═══ TIER 3: SPECIAL ATMOSPHERE (20 filtros) ═══
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,colorbalance=rs=0.05:gs=0.05:bs=0.05[bg_neutral];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=contrast=1.06[fg_scaled];[bg_neutral][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Neutral Balanced", weight: 8, readability: 10 },
  
  { filter: `scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x0a0a0a,eq=contrast=1.05`, name: "Near Black Border", weight: 7, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=17:8,colorbalance=rs=-0.1:gs=0.1:bs=0.2[bg_teal];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_teal][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Teal Mood", weight: 6, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,colorbalance=rs=0.2:gs=-0.1:bs=-0.2[bg_orange];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_orange][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Orange Mood", weight: 6, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,hue=s=0.5[bg_faded];[fg]scale=1280:720:force_original_aspect_ratio=decrease,hue=s=1.15[fg_saturated];[bg_faded][fg_saturated]overlay=(W-w)/2:(H-h)/2`, name: "Faded BG Pop FG", weight: 8, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=20:10,colorbalance=rs=0.2:gs=0.15:bs=-0.1[bg_sunset];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_sunset][fg_scaled]overlay=(W-w)/2:(H-h)/2`, name: "Sunset Mood", weight: 7, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8[bg_blur];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_scaled];[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2,pad=1280:720+40:(ow-iw)/2:20:color=black`, name: "Letterbox", weight: 6, readability: 9 },
  
  // NOVO: Efeitos adaptativos para diferentes tipos de cena
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=16:8,eq=brightness=-0.1:contrast=1.04[bg_adapt];[fg]scale=1280:720:force_original_aspect_ratio=decrease,unsharp=4:4:0.6[fg_adapt];[bg_adapt][fg_adapt]overlay=(W-w)/2:(H-h)/2`, name: "Adaptive Balanced", weight: 8, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=14:7,colorbalance=rm=0.05:gm=0.05:bm=0.05,eq=contrast=1.03[bg_natural];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=saturation=1.05[fg_natural];[bg_natural][fg_natural]overlay=(W-w)/2:(H-h)/2`, name: "Natural Enhance", weight: 9, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=18:9,eq=brightness=-0.2[bg_depth];[fg]scale=1280:720:force_original_aspect_ratio=decrease,cas=0.35[fg_depth];[bg_depth][fg_depth]overlay=(W-w)/2:(H-h)/2`, name: "Depth Enhanced", weight: 8, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,hue=s=0.85[bg_subdued];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=contrast=1.06[fg_clear];[bg_subdued][fg_clear]overlay=(W-w)/2:(H-h)/2`, name: "Subdued Background", weight: 8, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=17:8,eq=gamma=1.05[bg_lifted];[fg]scale=1280:720:force_original_aspect_ratio=decrease,unsharp=4:4:0.7[fg_crisp2];[bg_lifted][fg_crisp2]overlay=(W-w)/2:(H-h)/2`, name: "Lifted Crisp", weight: 8, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=19:9,colorbalance=rs=0.08:gs=0.08:bs=0.12[bg_cool];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_cool];[bg_cool][fg_cool]overlay=(W-w)/2:(H-h)/2`, name: "Cool Atmosphere", weight: 7, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=19:9,colorbalance=rs=0.12:gs=0.08:bs=-0.05[bg_warm];[fg]scale=1280:720:force_original_aspect_ratio=decrease[fg_warm];[bg_warm][fg_warm]overlay=(W-w)/2:(H-h)/2`, name: "Warm Atmosphere", weight: 7, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,eq=contrast=1.08[bg_contrast];[fg]scale=1280:720:force_original_aspect_ratio=decrease,smartblur=lr=0.4:ls=-0.4[fg_smart];[bg_contrast][fg_smart]overlay=(W-w)/2:(H-h)/2`, name: "Smart Contrast", weight: 8, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=16:8,noise=alls=3:allf=t[bg_texture];[fg]scale=1280:720:force_original_aspect_ratio=decrease,cas=0.3[fg_texture];[bg_texture][fg_texture]overlay=(W-w)/2:(H-h)/2`, name: "Textured Depth", weight: 7, readability: 9 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,eq=brightness=0.05:saturation=0.95[bg_mild];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=contrast=1.04[fg_mild];[bg_mild][fg_mild]overlay=(W-w)/2:(H-h)/2`, name: "Mild Enhancement", weight: 9, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=20:10,eq=gamma=0.95[bg_subtle];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=gamma=1.05[fg_subtle];[bg_subtle][fg_subtle]overlay=(W-w)/2:(H-h)/2`, name: "Subtle Gamma", weight: 8, readability: 10 },
  
  { filter: `[0:v]split=2[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=15:8,eq=saturation=0.8[bg_desaturated];[fg]scale=1280:720:force_original_aspect_ratio=decrease,eq=saturation=1.12[fg_saturated];[bg_desaturated][fg_saturated]overlay=(W-w)/2:(H-h)/2`, name: "Selective Saturation", weight: 8, readability: 9 },

  // ═══ ⚡ TIER 4: EFEITOS DE IMPACTO & AÇÃO (Adicionado V6.9) ═══
  { 
    // Separa os canais RGB: Vermelho move horizontal, Azul move vertical (Efeito Glitch/Soco)
    filter: `split=3[r][g][b];[r]crop=iw:ih:5:0,pad=iw:ih:-5:0:black[r_shift];[b]crop=iw:ih:0:5,pad=iw:ih:0:-5:black[b_shift];[r_shift][g][b_shift]mergeplanes=0x001020:format=gbrp`, 
    name: "Impacto RGB Split", 
    weight: 5, 
    readability: 7 
  },
  {
    // Simula velocidade com blur direcional vertical (Motion Blur)
    filter: `tinterlace=mode=mergex2,boxblur=0:10,tinterlace=mode=drop_even`,
    name: "Speed Blur Vertical",
    weight: 5,
    readability: 6
  },
  // ═══ EFEITO DE ATMOSFERA MÁGICA (V6.9 Add-on) ═══
  { 
    // Cria um brilho difuso (Glow) nas áreas claras, estilo anime/romance
    filter: `[0:v]split=2[a][b];[b]boxblur=20:10,curves=all='0/0 0.5/0.8 1/1',eq=saturation=1.2[b_glow];[a][b_glow]blend=all_mode=screen:all_opacity=0.6`, 
    name: "Anime Bloom (Glow)", 
    weight: 7, 
    readability: 8 
  }
];

// ──────────────────────────────────────────────────────────────────────
// SEÇÃO 2B: ✅ TRANSIÇÕES - 80+ TRANSIÇÕES (ORIGINAIS + ACTION MANHWA)
// ──────────────────────────────────────────────────────────────────────
const TRANSITIONS = [
  // ═══ ORIGINAIS SUAVES (Mantenha para momentos de calma) ═══
  'fade', 'fadeblack', 'fadewhite', 'fadegrays',
  'wipeleft', 'wiperight', 'wipeup', 'wipedown',
  'slideleft', 'slideright', 'slideup', 'slidedown',
  'smoothleft', 'smoothright', 'smoothup', 'smoothdown',
  'circlecrop', 'circleopen', 'circleclose',
  'dissolve', 'zoomin', 'fadefast', 'fadeslow',
  'rectcrop', 'distance', 'hlslice', 'hrslice',
  
  // ═══ GEOMÉTRICAS & DIAGONAIS ═══
  'diagtl', 'diagtr', 'diagbl', 'diagbr',
  'squeezeh', 'squeezev',
  'radial', 'rotate',
  
  // ═══ ARTÍSTICAS ═══
  'pixelize', 'wipetl', 'wipetr', 'wipebl', 'wipebr',
  'horzopen', 'horzclose', 'vertopen', 'vertclose',
  
  // ═══ SUAVES & SUTIS ═══
  'coverleft', 'coverright', 'coverup', 'coverdown',
  'revealleft', 'revealright', 'revealup', 'revealdown',
  
  // ═══ ⚡ NOVAS: ESTILO MANHWA ACTION (Do vídeo de referência) ═══
  // Glitch e Digital (Para cenas de Sistema/Status)
  'glitchmem', 'glitchdisplace', 'hblur', 'wblur', 'zombie',
  
  // ═══ ⚡ NOVAS ADIÇÕES: EFEITOS DE VENTO & VELOCIDADE (Estilo Anime/Manhwa) ═══
  // Simulam "speed lines" e movimentos rápidos de câmera
  'hlwind', // Vento horizontal para a esquerda (Ótimo para cortes de corrida/ataque)
  'hrwind', // Vento horizontal para a direita
  'vuwind', // Vento vertical para cima (Pulos/Voo)
  'vdwind', // Vento vertical para baixo (Quedas/Impactos no chão)

  // ═══ 🌀 DISTORÇÃO & MAGIA (Para cenas de Isekai/Poder) ═══
  'spiral',    // Torção espiral (Ótimo para portais ou confusão mental)
  'crosswarp', // Distorção cruzada (Efeito de "dobra" espacial)
  'feedback',  // Efeito de eco visual/sonho (Retardatário visual)

  // ═══ 👾 GLITCH & SISTEMA (Para telas de Status/Level Up) ═══
  'mosaic',    // Pixelização em bloco (Diferente do pixelize, mais digital)
  
  // ═══ 🔪 CORTES DE COMBATE (Para espadas e lâminas) ═══
  'hextile',   // Corte em hexágonos (Estilo barreira quebrando)

  // Impacto e Velocidade (Motion Blur simulado)
  'vuslice', 'vdslice', 'hulsice', 'hurslice', // Cortes rápidos
  'dreamy', 'kaleidoscope', // Cenas de magia/confusão
  'zoomout', // Ótimo para revelar cenários
  
  // ═══ EXTRAS PARA PROBABILIDADE (Repetidos para aparecerem mais) ═══
  'smoothdown', 'smoothup', 'fadefast', 
  'fadeslow', 'circleopen', 'circleclose', 'dissolve', 'distance'
];

// ──────────────────────────────────────────────────────────────────────
// SEÇÃO 2C: ✅ MOVIMENTOS - 85 MOVIMENTOS OTIMIZADOS COM TAGS
// ──────────────────────────────────────────────────────────────────────
const MOVEMENTS = [
  // ═══ CATEGORIA A: ⭐⭐⭐ VERTICAL PAN (Prioridade Máxima - 35 variações) ═══
  
  // --- Velocidade ULTRA LENTA (8 variações) ---
  { filter: "zoompan=z=1.25:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*3))':s=1280x720", desc: "⬇️ Vertical Glacial", priority: 1, weight: 5, tags: ["vertical", "slow", "reading", "calm"], readability: 10 },
  { filter: "zoompan=z=1.3:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*3.5))':s=1280x720", desc: "⬇️ Vertical Ultra Lento", priority: 1, weight: 5, tags: ["vertical", "slow", "reading", "calm"], readability: 10 },
  { filter: "zoompan=z=1.35:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*4))':s=1280x720", desc: "⬇️ Vertical Suave A", priority: 1, weight: 5, tags: ["vertical", "slow", "reading", "calm"], readability: 10 },
  { filter: "zoompan=z=1.28:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*3.2))':s=1280x720", desc: "⬇️ Vertical Suave B", priority: 1, weight: 5, tags: ["vertical", "slow", "reading", "calm"], readability: 10 },
  { filter: "zoompan=z=1.25:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*3))':s=1280x720", desc: "⬆️ Vertical Reverso Glacial", priority: 1, weight: 5, tags: ["vertical", "slow", "reading", "calm", "reverse"], readability: 10 },
  { filter: "zoompan=z=1.3:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*3.5))':s=1280x720", desc: "⬆️ Vertical Reverso Ultra Lento", priority: 1, weight: 5, tags: ["vertical", "slow", "reading", "calm", "reverse"], readability: 10 },
  { filter: "zoompan=z=1.35:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*4))':s=1280x720", desc: "⬆️ Vertical Reverso Suave A", priority: 1, weight: 5, tags: ["vertical", "slow", "reading", "calm", "reverse"], readability: 10 },
  { filter: "zoompan=z=1.28:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*3.2))':s=1280x720", desc: "⬆️ Vertical Reverso Suave B", priority: 1, weight: 5, tags: ["vertical", "slow", "reading", "calm", "reverse"], readability: 10 },
  
  // --- Velocidade LENTA (8 variações) ---
  { filter: "zoompan=z=1.4:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*5))':s=1280x720", desc: "⬇️ Vertical Lento A", priority: 1, weight: 6, tags: ["vertical", "slow", "reading"], readability: 10 },
  { filter: "zoompan=z=1.45:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*5.5))':s=1280x720", desc: "⬇️ Vertical Lento B", priority: 1, weight: 6, tags: ["vertical", "slow", "reading"], readability: 10 },
  { filter: "zoompan=z=1.38:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*4.8))':s=1280x720", desc: "⬇️ Vertical Lento C", priority: 1, weight: 6, tags: ["vertical", "slow", "reading"], readability: 10 },
  { filter: "zoompan=z=1.42:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*5.2))':s=1280x720", desc: "⬇️ Vertical Lento D", priority: 1, weight: 6, tags: ["vertical", "slow", "reading"], readability: 10 },
  { filter: "zoompan=z=1.4:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*5))':s=1280x720", desc: "⬆️ Vertical Reverso Lento A", priority: 1, weight: 6, tags: ["vertical", "slow", "reading", "reverse"], readability: 10 },
  { filter: "zoompan=z=1.45:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*5.5))':s=1280x720", desc: "⬆️ Vertical Reverso Lento B", priority: 1, weight: 6, tags: ["vertical", "slow", "reading", "reverse"], readability: 10 },
  { filter: "zoompan=z=1.38:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*4.8))':s=1280x720", desc: "⬆️ Vertical Reverso Lento C", priority: 1, weight: 6, tags: ["vertical", "slow", "reading", "reverse"], readability: 10 },
  { filter: "zoompan=z=1.42:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*5.2))':s=1280x720", desc: "⬆️ Vertical Reverso Lento D", priority: 1, weight: 6, tags: ["vertical", "slow", "reading", "reverse"], readability: 10 },
  
  // --- Velocidade MÉDIA (8 variações) ---
  { filter: "zoompan=z=1.5:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*6.5))':s=1280x720", desc: "⬇️ Vertical Médio A", priority: 1, weight: 7, tags: ["vertical", "medium", "reading"], readability: 9 },
  { filter: "zoompan=z=1.48:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*7))':s=1280x720", desc: "⬇️ Vertical Médio B", priority: 1, weight: 7, tags: ["vertical", "medium", "reading"], readability: 9 },
  { filter: "zoompan=z=1.52:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*6.8))':s=1280x720", desc: "⬇️ Vertical Médio C", priority: 1, weight: 7, tags: ["vertical", "medium", "reading"], readability: 9 },
  { filter: "zoompan=z=1.55:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*7.5))':s=1280x720", desc: "⬇️ Vertical Médio D", priority: 1, weight: 7, tags: ["vertical", "medium", "reading"], readability: 9 },
  { filter: "zoompan=z=1.5:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*6.5))':s=1280x720", desc: "⬆️ Vertical Reverso Médio A", priority: 1, weight: 7, tags: ["vertical", "medium", "reading", "reverse"], readability: 9 },
  { filter: "zoompan=z=1.48:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*7))':s=1280x720", desc: "⬆️ Vertical Reverso Médio B", priority: 1, weight: 7, tags: ["vertical", "medium", "reading", "reverse"], readability: 9 },
  { filter: "zoompan=z=1.52:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*6.8))':s=1280x720", desc: "⬆️ Vertical Reverso Médio C", priority: 1, weight: 7, tags: ["vertical", "medium", "reading", "reverse"], readability: 9 },
  { filter: "zoompan=z=1.55:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*7.5))':s=1280x720", desc: "⬆️ Vertical Reverso Médio D", priority: 1, weight: 7, tags: ["vertical", "medium", "reading", "reverse"], readability: 9 },
  
  // --- Velocidade RÁPIDA (6 variações) ---
  { filter: "zoompan=z=1.3:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*9))':s=1280x720", desc: "⬇️ Vertical Rápido A", priority: 1, tags: ["vertical", "fast", "dynamic"], readability: 8 },
  { filter: "zoompan=z=1.35:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*9.5))':s=1280x720", desc: "⬇️ Vertical Rápido B", priority: 1, tags: ["vertical", "fast", "dynamic"], readability: 8 },
  { filter: "zoompan=z=1.32:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*10))':s=1280x720", desc: "⬇️ Vertical Rápido C", priority: 1, tags: ["vertical", "fast", "dynamic"], readability: 8 },
  { filter: "zoompan=z=1.3:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*9))':s=1280x720", desc: "⬆️ Vertical Reverso Rápido A", priority: 1, tags: ["vertical", "fast", "dynamic", "reverse"], readability: 8 },
  { filter: "zoompan=z=1.35:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*9.5))':s=1280x720", desc: "⬆️ Vertical Reverso Rápido B", priority: 1, tags: ["vertical", "fast", "dynamic", "reverse"], readability: 8 },
  { filter: "zoompan=z=1.32:d=10000:x='iw/2-(iw/zoom/2)':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*10))':s=1280x720", desc: "⬆️ Vertical Reverso Rápido C", priority: 1, tags: ["vertical", "fast", "dynamic", "reverse"], readability: 8 },
  
  // --- Vertical com DRIFT LATERAL suave (5 variações) ---
  { filter: "zoompan=z=1.4:d=10000:x='iw/2-(iw/zoom/2)+sin(on*0.005)*15':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*5.5))':s=1280x720", desc: "⬇️ Vertical + Drift Suave A", priority: 1, tags: ["vertical", "drift", "reading"], readability: 9 },
  { filter: "zoompan=z=1.45:d=10000:x='iw/2-(iw/zoom/2)+cos(on*0.006)*12':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*6))':s=1280x720", desc: "⬇️ Vertical + Drift Suave B", priority: 1, tags: ["vertical", "drift", "reading"], readability: 9 },
  { filter: "zoompan=z=1.38:d=10000:x='iw/2-(iw/zoom/2)+sin(on*0.004)*18':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*5.5))':s=1280x720", desc: "⬆️ Vertical Reverso + Drift A", priority: 1, tags: ["vertical", "drift", "reading", "reverse"], readability: 9 },
  { filter: "zoompan=z=1.42:d=10000:x='iw/2-(iw/zoom/2)+cos(on*0.005)*14':y='if(lte(on,100),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-100)*6))':s=1280x720", desc: "⬆️ Vertical Reverso + Drift B", priority: 1, tags: ["vertical", "drift", "reading", "reverse"], readability: 9 },
  { filter: "zoompan=z=1.5:d=10000:x='iw/2-(iw/zoom/2)+sin(on*0.003)*10':y='if(lte(on,100),0,min(ih-ih/zoom,(on-100)*7))':s=1280x720", desc: "⬇️ Vertical + Drift Mínimo", priority: 1, tags: ["vertical", "drift", "reading"], readability: 9 },
  
  // ═══ CATEGORIA B: ⭐⭐ ZOOM FACIAL / CLOSE-UP (Prioridade Alta - 25 variações) ═══
  
  // --- Zoom Centro (Rosto) - Velocidades variadas (10 variações) ---
  { filter: "zoompan=z='min(zoom+0.0008,1.35)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Rosto Lento", priority: 2, tags: ["zoom", "facial", "slow"], readability: 9 },
  { filter: "zoompan=z='min(zoom+0.001,1.4)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Rosto Médio", priority: 2, tags: ["zoom", "facial", "medium"], readability: 9 },
  { filter: "zoompan=z='min(zoom+0.0012,1.45)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Rosto Rápido", priority: 2, tags: ["zoom", "facial", "fast"], readability: 8 },
  { filter: "zoompan=z='min(zoom+0.0006,1.3)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Rosto Ultra Lento", priority: 2, tags: ["zoom", "facial", "slow"], readability: 10 },
  { filter: "zoompan=z='min(zoom+0.0015,1.5)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Rosto Intenso", priority: 2, tags: ["zoom", "facial", "intense"], readability: 8 },
  { filter: "zoompan=z='min(zoom+0.0009,1.38)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3.5-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Rosto Alto A", priority: 2, tags: ["zoom", "facial", "medium"], readability: 9 },
  { filter: "zoompan=z='min(zoom+0.0011,1.42)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3.2-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Rosto Alto B", priority: 2, tags: ["zoom", "facial", "medium"], readability: 9 },
  { filter: "zoompan=z='min(zoom+0.0007,1.32)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2.8-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Rosto Baixo A", priority: 2, tags: ["zoom", "facial", "slow"], readability: 9 },
  { filter: "zoompan=z='min(zoom+0.001,1.4)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2.5-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Rosto Baixo B", priority: 2, tags: ["zoom", "facial", "medium"], readability: 9 },
  { filter: "zoompan=z='min(zoom+0.0013,1.48)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Rosto Dramático", priority: 2, tags: ["zoom", "facial", "dramatic"], readability: 8 },
  
  // --- Zoom com Delay (Suspense) (5 variações) ---
  { filter: "zoompan=z='if(lte(on,80),1.0,min(1.0+(on-80)*0.0015,1.35))':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Delay Rosto A", priority: 2, tags: ["zoom", "facial", "delay", "suspense"], readability: 9 },
  { filter: "zoompan=z='if(lte(on,100),1.0,min(1.0+(on-100)*0.002,1.4))':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Delay Rosto B", priority: 2, tags: ["zoom", "facial", "delay", "suspense"], readability: 9 },
  { filter: "zoompan=z='if(lte(on,60),1.0,min(1.0+(on-60)*0.0018,1.42))':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Delay Rosto C", priority: 2, tags: ["zoom", "facial", "delay", "suspense"], readability: 9 },
  { filter: "zoompan=z='if(lte(on,120),1.0,min(1.0+(on-120)*0.0025,1.5))':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Delay Dramático", priority: 2, tags: ["zoom", "facial", "delay", "dramatic"], readability: 8 },
  { filter: "zoompan=z='if(lte(on,90),1.0,min(1.0+(on-90)*0.0012,1.3))':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Delay Suave", priority: 2, tags: ["zoom", "facial", "delay", "calm"], readability: 10 },
  
  // --- Zoom Centro Geral (5 variações) ---
  { filter: "zoompan=z='min(zoom+0.0008,1.4)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "🔍 Zoom Centro Lento", priority: 2, tags: ["zoom", "center", "slow"], readability: 9 },
  { filter: "zoompan=z='min(zoom+0.001,1.45)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "🔍 Zoom Centro Médio", priority: 2, tags: ["zoom", "center", "medium"], readability: 9 },
  { filter: "zoompan=z='min(zoom+0.0012,1.5)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "🔍 Zoom Centro Rápido", priority: 2, tags: ["zoom", "center", "fast"], readability: 8 },
  { filter: "zoompan=z='min(zoom+0.0006,1.3)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "🔍 Zoom Centro Ultra Lento", priority: 2, tags: ["zoom", "center", "slow"], readability: 10 },
  { filter: "zoompan=z='min(zoom+0.0015,1.55)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "🔍 Zoom Centro Intenso", priority: 2, tags: ["zoom", "center", "intense"], readability: 8 },
  
  // --- Zoom com Easing (5 variações) ---
  { filter: "zoompan=z='1.0+0.4*pow((on/250),2)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Ease In Rosto", priority: 2, tags: ["zoom", "facial", "ease", "smooth"], readability: 9 },
  { filter: "zoompan=z='1.0+0.4*(1-pow(1-(on/250),2))':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Ease Out Rosto", priority: 2, tags: ["zoom", "facial", "ease", "smooth"], readability: 9 },
  { filter: "zoompan=z='1.0+0.35*(-cos(on/250*PI)+1)/2':d=10000:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':s=1280x720", desc: "🎯 Zoom Smooth Rosto", priority: 2, tags: ["zoom", "facial", "ease", "smooth"], readability: 9 },
  { filter: "zoompan=z='1.0+0.38*pow((on/250),1.5)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "🔍 Zoom Ease In Centro", priority: 2, tags: ["zoom", "center", "ease", "smooth"], readability: 9 },
  { filter: "zoompan=z='1.0+0.38*(1-pow(1-(on/250),1.5))':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "🔍 Zoom Ease Out Centro", priority: 2, tags: ["zoom", "center", "ease", "smooth"], readability: 9 },
  
  // ═══ CATEGORIA C: ⭐ KEN BURNS FOCADO (Prioridade Média - 15 variações) ═══
  { filter: "crop=iw*0.7:ih*0.7:iw*0.15:ih*0.1,scale=1280:720,zoompan=z='min(zoom+0.001,1.4)':d=200:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "📷 Ken Burns Rosto Superior", priority: 3, tags: ["kenburns", "facial", "crop"], readability: 8 },
  { filter: "crop=iw*0.6:ih*0.6:iw*0.2:ih*0.15,zoompan=z='min(zoom+0.0012,1.45)':d=180:x='iw*0.2':y='ih*0.15':s=1280x720", desc: "📷 Ken Burns Face Close A", priority: 3, tags: ["kenburns", "facial", "crop"], readability: 8 },
  { filter: "crop=iw*0.65:ih*0.65:iw*0.175:ih*0.12,zoompan=z='min(zoom+0.0008,1.35)':d=220:x='iw*0.175':y='ih*0.12':s=1280x720", desc: "📷 Ken Burns Face Close B", priority: 3, tags: ["kenburns", "facial", "crop"], readability: 8 },
  { filter: "crop=iw*0.7:ih*0.7:iw*0.15:ih*0.2,zoompan=z='min(zoom+0.001,1.4)':d=200:x='iw*0.15':y='ih*0.2':s=1280x720", desc: "📷 Ken Burns Centro A", priority: 3, tags: ["kenburns", "center", "crop"], readability: 8 },
  { filter: "crop=iw*0.75:ih*0.75:iw*0.125:ih*0.125,zoompan=z='min(zoom+0.0009,1.38)':d=210:x='iw*0.125':y='ih*0.125':s=1280x720", desc: "📷 Ken Burns Centro B", priority: 3, tags: ["kenburns", "center", "crop"], readability: 8 },
  { filter: "crop=iw*0.5:ih*0.5:iw*0.25:ih*0.1,zoompan=z='min(zoom+0.0015,1.5)':d=150:x='iw*0.25':y='ih*0.1':s=1280x720", desc: "📷 Ken Burns Close Extremo", priority: 3, tags: ["kenburns", "facial", "crop", "intense"], readability: 7 },
  { filter: "crop=iw*0.8:ih*0.6:iw*0.1:ih*0.15,zoompan=z='min(zoom+0.0007,1.32)':d=240:x='iw*0.1':y='ih*0.15':s=1280x720", desc: "📷 Ken Burns Wide Face", priority: 3, tags: ["kenburns", "facial", "crop", "wide"], readability: 8 },
  { filter: "crop=iw*0.6:ih*0.7:iw*0.2:ih*0.1,zoompan=z='min(zoom+0.0011,1.42)':d=190:x='iw*0.2':y='ih*0.1':s=1280x720", desc: "📷 Ken Burns Tall Face", priority: 3, tags: ["kenburns", "facial", "crop"], readability: 8 },
  { filter: "crop=iw*0.55:ih*0.55:iw*0.225:ih*0.15,zoompan=z='min(zoom+0.0013,1.48)':d=170:x='iw*0.225':y='ih*0.15':s=1280x720", desc: "📷 Ken Burns Tight Shot", priority: 3, tags: ["kenburns", "facial", "crop", "tight"], readability: 7 },
  { filter: "crop=iw*0.65:ih*0.65:iw*0.175:ih*0.175,zoompan=z='min(zoom+0.001,1.4)':d=200:x='iw*0.175':y='ih*0.175':s=1280x720", desc: "📷 Ken Burns Centrado", priority: 3, tags: ["kenburns", "center", "crop"], readability: 8 },
  
  // --- Ken Burns com movimento (5 variações) ---
  { filter: "crop=iw*0.7:ih*0.7:iw*0.15:ih*0.1,zoompan=z='min(zoom+0.001,1.4)':d=200:x='iw*0.15+sin(on*0.01)*10':y='ih*0.1':s=1280x720", desc: "📷 Ken Burns Drift Horizontal", priority: 3, tags: ["kenburns", "facial", "crop", "drift"], readability: 7 },
  { filter: "crop=iw*0.65:ih*0.65:iw*0.175:ih*0.12,zoompan=z='min(zoom+0.0009,1.38)':d=220:x='iw*0.175':y='ih*0.12+sin(on*0.01)*8':s=1280x720", desc: "📷 Ken Burns Drift Vertical", priority: 3, tags: ["kenburns", "facial", "crop", "drift"], readability: 7 },
  { filter: "crop=iw*0.6:ih*0.6:iw*0.2:ih*0.15,zoompan=z='min(zoom+0.0012,1.45)':d=180:x='iw*0.2+sin(on*0.008)*12':y='ih*0.15+cos(on*0.008)*8':s=1280x720", desc: "📷 Ken Burns Circular Drift", priority: 3, tags: ["kenburns", "facial", "crop", "drift", "circular"], readability: 7 },
  { filter: "crop=iw*0.68:ih*0.68:iw*0.16:ih*0.16,zoompan=z='min(zoom+0.001,1.42)':d=200:x='iw*0.16+sin(on*0.006)*15':y='ih*0.16':s=1280x720", desc: "📷 Ken Burns Wave Motion", priority: 3, tags: ["kenburns", "center", "crop", "drift"], readability: 7 },
  { filter: "crop=iw*0.72:ih*0.72:iw*0.14:ih*0.14,zoompan=z='min(zoom+0.0008,1.36)':d=210:x='iw*0.14':y='ih*0.14+sin(on*0.007)*10':s=1280x720", desc: "📷 Ken Burns Gentle Float", priority: 3, tags: ["kenburns", "center", "crop", "drift", "gentle"], readability: 8 },
  
  // ═══ CATEGORIA D: EFEITOS ESPECIAIS (Baixa Prioridade - 10 variações) ═══
  { filter: "zoompan=z='1.0+0.06*sin(on*0.02)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "💫 Breathing Micro", priority: 4, tags: ["special", "breathing", "subtle"], readability: 9 },
  { filter: "zoompan=z=1.12:d=10000:x='iw/2-(iw/zoom/2)+sin(on*0.01)*12':y='ih/2-(ih/zoom/2)+cos(on*0.01)*10':s=1280x720", desc: "💫 Parallax Suave", priority: 4, tags: ["special", "parallax", "drift"], readability: 8 },
  { filter: "zoompan=z=1.08:d=10000:x='iw/2-(iw/zoom/2)+sin(on*0.5)*8':y='ih/2-(ih/zoom/2)+cos(on*0.5)*6':s=1280x720", desc: "💫 Shake Muito Suave", priority: 4, tags: ["special", "shake", "subtle"], readability: 7 },
  { filter: "zoompan=z='1.0+sin(on*0.02)*0.15':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "💫 Pulse Suave", priority: 4, tags: ["special", "pulse", "breathing"], readability: 8 },
  { filter: "zoompan=z='max(zoom-0.0005,0.95)':d=1500:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "💫 Zoom Out Suave", priority: 4, tags: ["special", "zoomout"], readability: 8 },
  
  // Efeitos especiais adicionais (5 variações)
  { filter: "zoompan=z='1.0+0.08*sin(on*0.025)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "💫 Breathing Medium", priority: 4, tags: ["special", "breathing", "medium"], readability: 8 },
  { filter: "zoompan=z=1.1:d=10000:x='iw/2-(iw/zoom/2)+sin(on*0.008)*10':y='ih/2-(ih/zoom/2)+cos(on*0.012)*8':s=1280x720", desc: "💫 Orbital Drift", priority: 4, tags: ["special", "drift", "circular"], readability: 8 },
  { filter: "zoompan=z='1.05+0.05*sin(on*0.03)':d=10000:x='iw/2-(iw/zoom/2)+cos(on*0.01)*8':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "💫 Wave Float", priority: 4, tags: ["special", "wave", "drift"], readability: 8 },
  { filter: "zoompan=z=1.15:d=10000:x='iw/2-(iw/zoom/2)+sin(on*0.006)*14':y='ih/2-(ih/zoom/2)+sin(on*0.009)*10':s=1280x720", desc: "💫 Gentle Sway", priority: 4, tags: ["special", "sway", "drift"], readability: 7 },
  { filter: "zoompan=z='1.0+0.1*abs(sin(on*0.02))':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720", desc: "💫 Pulse Breathing", priority: 4, tags: ["special", "pulse", "breathing"], readability: 8 },
  
  // ═══ CATEGORIA E: CAMERA SHAKE - SÓ COM CONTEXTO (3 variações) ═══
  { filter: "zoompan=z=1.15:d=10000:x='iw/2-(iw/zoom/2)+sin(on*2)*8':y='ih/2-(ih/zoom/2)+cos(on*2)*6':s=1280x720", desc: "📹 Camera Shake Leve", priority: 4, tags: ["shake", "action", "impact", "light"], readability: 5 },
  { filter: "zoompan=z=1.2:d=10000:x='iw/2-(iw/zoom/2)+sin(on*3)*12':y='ih/2-(ih/zoom/2)+cos(on*3)*10':s=1280x720", desc: "📹 Camera Shake Médio", priority: 4, tags: ["shake", "action", "impact", "medium"], readability: 4 },
  { filter: "zoompan=z=1.25:d=10000:x='iw/2-(iw/zoom/2)+sin(on*4)*16':y='ih/2-(ih/zoom/2)+cos(on*4)*14':s=1280x720", desc: "📹 Camera Shake Intenso", priority: 4, tags: ["shake", "action", "impact", "heavy"], readability: 3 },
  
  // ═══ CATEGORIA F: AÇÃO EXTREMA & ROTAÇÃO (Estilo Manhwa Recap) ═══
  
  // Rotação Suave (Dutch Angle) - Ótimo para tensão
  { filter: "zoompan=z=1.2:d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',rotate=a='0.05*sin(t)':ow='iw':oh='ih'", desc: "😵 Rotação Tensa (Dutch Angle)", priority: 4, tags: ["rotation", "tension", "camera"], readability: 6 },
  
  // Rotação com Zoom Rápido (Ação)
  { filter: "zoompan=z='min(zoom+0.003,1.5)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',rotate=a='t*0.02':ow='iw':oh='ih'", desc: "😵 Zoom + Rotação Ação", priority: 4, tags: ["rotation", "action", "fast"], readability: 5 },

  // Efeito de Flash/Impacto (Strobe) - A tela pisca branco
  { filter: "zoompan=z=1.1:d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',drawbox=t=fill:c=white@0.3:enable='lt(mod(t*10,2),1)'", desc: "⚡ Flash de Impacto (Strobe)", priority: 4, tags: ["action", "flash", "impact", "fight"], readability: 4 },

  // Tremor Violento + Zoom (Terremoto/Poder)
  { filter: "zoompan=z=1.3:d=10000:x='iw/2-(iw/zoom/2)+sin(t*20)*20':y='ih/2-(ih/zoom/2)+cos(t*15)*20'", desc: "🌋 Tremor Violento", priority: 4, tags: ["shake", "heavy", "chaos"], readability: 3 },
  
  // "Heartbeat" (Pulsação com borda vermelha) - Para perigo
  { filter: "zoompan=z='1.0+0.1*abs(sin(t*3))':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',drawbox=t=20:c=red@0.5:enable='gt(sin(t*3),0.8)'", desc: "💓 Pulsação Perigo", priority: 4, tags: ["horror", "danger", "pulse"], readability: 7 },

  // ═══ NOVOS EFEITOS DE AÇÃO (V6.9 - JUICE) ═══
  
  // 1. Terremoto Caótico (Usa noise/random para tremer a câmera violentamente)
  { 
    filter: "zoompan=z='min(zoom+0.001,1.15)':d=10000:x='iw/2-(iw/zoom/2)+((random(1)-0.5)*60)*eq(mod(on,2),0)':y='ih/2-(ih/zoom/2)+((random(1)-0.5)*60)*eq(mod(on,2),0)':s=1280x720", 
    desc: "🌋 Terremoto Caótico (Random)", 
    priority: 4, 
    tags: ["shake", "chaos", "heavy", "action_heavy"], 
    readability: 2 
  },

  // 2. Flash de Poder (Strobe Branco - Aumenta brilho explosivamente)
  { 
    filter: "zoompan=z=1.1:d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',eq=brightness='0.4*sin(on*1.5)*sin(on*1.5)':contrast='1.6'", 
    desc: "⚡ Flash de Poder (Strobe)", 
    priority: 4, 
    tags: ["action", "flash", "power", "magic"], 
    readability: 5 
  },

  // 3. Impacto Rápido (Zoom in/out violento em 1 frame)
  {
    filter: "zoompan=z='if(eq(mod(on,10),0),1.4,1.1)':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720",
    desc: "🥊 Impacto Punch (Zoom Hit)",
    priority: 4,
    tags: ["action", "hit", "punch", "fight"],
    readability: 4
  },

  // 4. Vignette Pulsante (A tela escurece e clareia nas bordas - Tensão/Medo)
  { 
    filter: "zoompan=z='1.02':d=10000:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720,vignette='PI/3+sin(time*4)*0.1'", 
    desc: "💓 Vignette Pulsante (Tensão)", 
    priority: 4, 
    tags: ["tension", "fear", "danger", "monster"], 
    readability: 6 
  }
];

// ──────────────────────────────────────────────────────────────────────
// SEÇÃO 2D: ✅ EFEITOS DE COR E ATMOSFERA - 50 EFEITOS SUTIS
// ──────────────────────────────────────────────────────────────────────
const COLOR_EFFECTS = [
  // ═══ AJUSTES SUTIS (15) ═══
  "eq=contrast=1.03:brightness=0.01:saturation=1.05",
  "eq=contrast=1.04:brightness=-0.01:saturation=1.08",
  "eq=contrast=1.05:brightness=0.02:saturation=1.1",
  "eq=contrast=1.02:brightness=0.015:saturation=1.04",
  "eq=contrast=1.06:brightness=-0.02:saturation=1.07",
  "colorbalance=rs=0.03:gs=-0.01:bs=0.02",
  "colorbalance=rs=-0.02:gs=0.03:bs=0.01",
  "colorbalance=rs=0.01:gs=0.02:bs=-0.01",
  "colorbalance=rs=-0.01:gs=-0.01:bs=0.03",
  "hue=s=1.05:b=0.03",
  "hue=s=1.08:b=0.02",
  "hue=s=1.04:b=0.01",
  "hue=s=1.06:b=-0.01",
  "vibrance=intensity=0.12",
  "vibrance=intensity=0.18",
  // ═══ COLOR GRADING CINEMATICO (15) ═══
  "curves=r='0.1/0.15 0.3/0.35 0.5/0.5 0.7/0.75 0.9/0.95':g='0.1/0.15 0.3/0.35 0.5/0.5 0.7/0.75 0.9/0.95':b='0.1/0.1 0.3/0.25 0.5/0.4 0.7/0.5 0.9/0.7'",
  "curves=r='0.1/0.08 0.3/0.2 0.5/0.35 0.7/0.55 0.9/0.75':g='0.1/0.08 0.3/0.2 0.5/0.35 0.7/0.55 0.9/0.75':b='0.1/0.1 0.3/0.25 0.5/0.4 0.7/0.55 0.9/0.78'",
  "curves=r='0.1/0.3 0.3/0.5 0.5/0.7 0.7/0.82 0.9/0.95':g='0.1/0.3 0.3/0.5 0.5/0.7 0.7/0.82 0.9/0.95':b='0.1/0.3 0.3/0.5 0.5/0.7 0.7/0.82 0.9/0.95'",
  "curves=r='0.1/0.15 0.3/0.3 0.5/0.5 0.7/0.7 0.9/0.9':g='0.1/0.15 0.3/0.3 0.5/0.5 0.7/0.7 0.9/0.9':b='0.1/0.1 0.3/0.2 0.5/0.4 0.7/0.6 0.9/0.7'",
  "curves=r='0.1/0.12 0.3/0.32 0.5/0.52 0.7/0.72 0.9/0.92':g='0.1/0.12 0.3/0.32 0.5/0.52 0.7/0.72 0.9/0.92':b='0.1/0.12 0.3/0.32 0.5/0.52 0.7/0.72 0.9/0.92'",
  "curves=r='0.1/0.12 0.3/0.25 0.5/0.4 0.7/0.6 0.9/0.8':g='0.1/0.18 0.3/0.35 0.5/0.5 0.7/0.7 0.9/0.88':b='0.1/0.22 0.3/0.45 0.5/0.65 0.7/0.82 0.9/0.96'",
  "curves=r='0.1/0.12 0.3/0.32 0.5/0.52 0.7/0.72 0.9/0.92':g='0.1/0.18 0.3/0.38 0.5/0.58 0.7/0.78 0.9/0.96':b='0.1/0.28 0.3/0.48 0.5/0.68 0.7/0.88 0.9/1.0'",
  "curves=r='0.1/0.08 0.3/0.28 0.5/0.52 0.7/0.82 0.9/0.96':g='0.1/0.18 0.3/0.38 0.5/0.58 0.7/0.78 0.9/0.96':b='0.1/0.28 0.3/0.48 0.5/0.68 0.7/0.88 0.9/1.0'",
  "curves=r='0.1/0.18 0.3/0.35 0.5/0.52 0.7/0.72 0.9/0.92':g='0.1/0.18 0.3/0.35 0.5/0.52 0.7/0.72 0.9/0.92':b='0.1/0.08 0.3/0.2 0.5/0.35 0.7/0.45 0.9/0.65'",
  "curves=r='0.1/0.1 0.3/0.3 0.5/0.48 0.7/0.68 0.9/0.88':g='0.1/0.12 0.3/0.32 0.5/0.52 0.7/0.72 0.9/0.92':b='0.1/0.15 0.3/0.35 0.5/0.58 0.7/0.78 0.9/0.98'",
  "curves=r='0.1/0.13 0.3/0.33 0.5/0.53 0.7/0.73 0.9/0.93':g='0.1/0.13 0.3/0.33 0.5/0.53 0.7/0.73 0.9/0.93':b='0.1/0.13 0.3/0.33 0.5/0.53 0.7/0.73 0.9/0.93'",
  "curves=r='0.1/0.14 0.3/0.28 0.5/0.45 0.7/0.65 0.9/0.85':g='0.1/0.16 0.3/0.32 0.5/0.5 0.7/0.7 0.9/0.9':b='0.1/0.2 0.3/0.4 0.5/0.6 0.7/0.8 0.9/0.95'",
  "curves=r='0.1/0.11 0.3/0.31 0.5/0.51 0.7/0.71 0.9/0.91':g='0.1/0.12 0.3/0.32 0.5/0.52 0.7/0.72 0.9/0.92':b='0.1/0.14 0.3/0.34 0.5/0.54 0.7/0.74 0.9/0.94'",
  "curves=r='0.1/0.16 0.3/0.36 0.5/0.56 0.7/0.76 0.9/0.94':g='0.1/0.15 0.3/0.35 0.5/0.55 0.7/0.75 0.9/0.93':b='0.1/0.12 0.3/0.32 0.5/0.52 0.7/0.72 0.9/0.9'",
  "curves=r='0.1/0.2 0.3/0.38 0.5/0.55 0.7/0.75 0.9/0.92':g='0.1/0.18 0.3/0.36 0.5/0.54 0.7/0.74 0.9/0.91':b='0.1/0.15 0.3/0.32 0.5/0.5 0.7/0.7 0.9/0.88'",

  // ═══ SATURATION & TONE (20) ═══
  "eq=saturation=1.15",
  "eq=saturation=1.12",
  "eq=saturation=0.95",
  "eq=saturation=1.08:brightness=0.02",
  "eq=saturation=0.98:brightness=0.01",
  "eq=saturation=1.06:contrast=1.03",
  "eq=saturation=1.1:gamma=1.02",
  "eq=saturation=1.04:gamma=0.98",
  "format=rgb,geq=r='(r+g+b)/3':g='(r+g+b)/3':b='(r+g+b)/3',eq=contrast=1.05",
  "unsharp=luma_msize_x=7:luma_msize_y=7:luma_amount=0.8:chroma_msize_x=7:chroma_msize_y=7:chroma_amount=0.4",
  "unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=0.6:chroma_msize_x=5:chroma_msize_y=5:chroma_amount=0.3",
  "format=rgb,noise=all=8:allf=t",
  
  // NOVO: Efeitos de tom adicionais (8)
  "eq=gamma=1.05:saturation=1.06",
  "eq=gamma=0.95:saturation=1.04",
  "eq=gamma=1.02:contrast=1.04:saturation=1.05",
  "colorbalance=rm=0.02:gm=0.02:bm=0.02,eq=saturation=1.06",
  "colorbalance=rs=0.04:gs=0.02:bs=-0.02,eq=contrast=1.03",
  "colorbalance=rs=-0.02:gs=0.02:bs=0.04,eq=contrast=1.03",
  "hue=s=1.07:h=0",
  "hue=s=1.09:b=0.02"
];

// ──────────────────────────────────────────────────────────────────────
// SEÇÃO 2E: ✅ EFEITOS DE BLUR - 12 EFEITOS SUTIS
// ──────────────────────────────────────────────────────────────────────
const BLUR_EFFECTS = [
  "gblur=sigma=0.2:steps=1",
  "gblur=sigma=0.3:steps=1",
  "gblur=sigma=0.25:steps=1",
  "gblur=sigma=0.15:steps=1",
  "gblur=sigma=0.18:steps=1",
  "boxblur=1:1",
  "boxblur=2:1",
  "boxblur=1.5:1",
  "avgblur=sizeX=2",
  "avgblur=sizeX=3",
  "avgblur=sizeX=1",
  "avgblur=sizeX=2:sizeY=1"
];

// ──────────────────────────────────────────────────────────────────────
// SEÇÃO 2F: ✅ EFEITOS DE VINHETA - 10 EFEITOS
// ──────────────────────────────────────────────────────────────────────
const VIGNETTE_EFFECTS = [
  "vignette=PI/8",
  "vignette=PI/10:mode=forward",
  "vignette=angle=PI/12",
  "vignette=PI/9:mode=forward",
  "vignette=PI/11",
  "vignette=PI/7:mode=forward",
  "vignette=angle=PI/13",
  "vignette=PI/8.5",
  "vignette=PI/9.5:mode=forward",
  "vignette=angle=PI/11.5"
];

// ──────────────────────────────────────────────────────────────────────
// SEÇÃO 2G: ✅ EFEITOS DE RUÍDO - 8 EFEITOS
// ──────────────────────────────────────────────────────────────────────
const NOISE_EFFECTS = [
  "noise=alls=2:allf=t+u",
  "noise=alls=3:allf=t",
  "noise=alls=1:allf=t+u",
  "noise=alls=2.5:allf=t",
  "noise=alls=1.5:allf=t+u",
  "noise=alls=4:allf=t",
  "noise=alls=3.5:allf=t+u",
  "noise=alls=1.8:allf=t"
];

// ──────────────────────────────────────────────────────────────────────
// SEÇÃO 2H: ✅ EFEITOS DE SHARPEN - 12 EFEITOS
// ──────────────────────────────────────────────────────────────────────
const SHARPEN_EFFECTS = [
  "unsharp=3:3:0.8:3:3:0.0",
  "unsharp=5:5:1.0:5:5:0.0",
  "unsharp=4:4:0.9:4:4:0.0",
  "unsharp=3:3:0.6:3:3:0.0",
  "unsharp=5:5:0.7:5:5:0.0",
  "unsharp=4:4:0.75:4:4:0.0",
  "cas=0.3",
  "cas=0.4",
  "cas=0.35",
  "cas=0.25",
  "smartblur=lr=0.5:ls=-0.5",
  "smartblur=lr=0.4:ls=-0.4"
];

// ======================================================================
// SEÇÃO 3: ✅ PADRÕES CONTEXTUAIS - DETECÇÃO INTELIGENTE V5.0 EXPANDIDO
// ======================================================================
const CONTEXTUAL_PATTERNS = {
  // ═══ PADRÕES DE AÇÃO COM CAMERA SHAKE ═══
  action_heavy: {
    regex: /explosão|destruição|estrondo|violento|crash|desaba|terramoto|tremor|impacto forte|colisão/i,
    effectType: "shake_heavy",
    name: "Camera Shake Intenso (Ação Pesada)",
    intensity: "INTENSA",
    type: "acao_pesada",
    forceEffect: true
  },
  action_medium: {
    regex: /soco|chute|golpe|impacto|bam|pow|batida|choque|desce o sarrafo|murro|pancada|esmagado|esmaga/i,
    effectType: "shake_medium",
    name: "Camera Shake Médio (Ação)",
    intensity: "MÉDIA",
    type: "acao_media",
    forceEffect: true
  },
  action_light: {
    regex: /tombo|cai|tropeç|escorrega|batida leve|empurr|puxa|empurrão|trombada/i,
    effectType: "shake_light",
    name: "Camera Shake Leve (Ação Leve)",
    intensity: "LEVE",
    type: "acao_leve",
    forceEffect: true
  },
  
  // ═══ PADRÕES QUE SEMPRE USAM VERTICAL PAN (LEITURA) ═══
  reading_slow: {
    regex: /leitura|texto|carta|papel|documento|livro|lê|ler|escrito|manuscrito|bilhete/i,
    effectType: "vertical_slow",
    name: "Vertical Pan Lento (Leitura)",
    intensity: "SUAVE",
    type: "leitura",
    forceEffect: true
  },
  dialogue_calm: {
    regex: /conversa|fala|diz|responde|pergunta|comenta|explica|conta|relata/i,
    effectType: "vertical_medium",
    name: "Vertical Pan Médio (Diálogo)",
    intensity: "MODERADA",
    type: "dialogo",
    forceEffect: false // Permite variação
  },
  narration: {
    regex: /narrador|narrando|contando|história|relato|descrição/i,
    effectType: "vertical_slow",
    name: "Vertical Pan Lento (Narração)",
    intensity: "SUAVE",
    type: "narracao",
    forceEffect: true
  },
  
  // ═══ PADRÕES EMOCIONAIS ═══
  suspense: {
    regex: /medo|terror|surpresa|choque|assustado|grito|perigo|ameaça|tenso|apreensivo/i,
    effectType: "zoom_suspense",
    name: "Zoom Face Impact (Suspense)",
    intensity: "DRAMÁTICA",
    type: "suspense",
    forceEffect: true
  },
  dramatic: {
    regex: /revelação|verdade|descoberta|segredo|confissão|admite|revela|descobr/i,
    effectType: "zoom_delay",
    name: "Zoom Delay (Revelação)",
    intensity: "DRAMÁTICA",
    type: "revelacao",
    forceEffect: true
  },
  romance: {
    regex: /amor|beijo|abraço|carinho|coração|paixão|romântico|ternura|confiss|apaixon|crush/i,
    effectType: "soft_float",
    name: "Soft Float (Romance)",
    intensity: "SUAVE",
    type: "romance",
    forceEffect: true
  },
  tension: {
    regex: /tenso|nervoso|ansioso|preocupado|inquieto|apreensivo|pressão|estress/i,
    effectType: "breathing_heavy",
    name: "Breathing Heavy (Tensão)",
    intensity: "INTENSA",
    type: "tensao",
    forceEffect: true
  },
  calm: {
    regex: /calmo|paz|tranquilo|sereno|silêncio|quieto|relaxado|pacífico/i,
    effectType: "vertical_glacial",
    name: "Vertical Glacial (Calmo)",
    intensity: "SUAVE",
    type: "calmo",
    forceEffect: true
  },
  
  // ═══ PADRÕES DE MOVIMENTO ═══
  speed: {
    regex: /corre|foge|rápido|veloz|escapar|perseguir|corrida|velocidade|sprint|disparada/i,
    effectType: "vertical_fast",
    name: "Vertical Rápido (Velocidade)",
    intensity: "DINÂMICA",
    type: "velocidade",
    forceEffect: true
  },
  memory: {
    regex: /lembr|passado|flashback|memória|antigamente|recordar|nostalgia|lembrança/i,
    effectType: "breathing",
    name: "Breathing (Flashback)",
    intensity: "EMOCIONAL",
    type: "memoria",
    forceEffect: true
  },
  battle: {
    regex: /batalha|combate|guerra|duelo|enfrentamento|luta final|confronto/i,
    effectType: "vertical_fast",
    name: "Vertical Rápido (Batalha)",
    intensity: "INTENSA",
    type: "batalha",
    forceEffect: true
  },
  mystery: {
    regex: /mistério|enigma|suspeito|investigação|pista|dúvida|intriga/i,
    effectType: "kenburns_drift",
    name: "Ken Burns Circular (Mistério)",
    intensity: "INTRIGANTE",
    type: "misterio",
    forceEffect: true
  }
};

// ═══ MAPEAMENTO DE EFFECT TYPE PARA TAGS (ATUALIZADO V6.9 + ROMANCE/TENSÃO) ═══
const EFFECT_TYPE_MAP = {
  // Ação e Caos
  "shake_light": { tags: ["shake", "action", "light"], minReadability: 5 },
  "shake_medium": { tags: ["shake", "action", "medium"], minReadability: 4 },
  "shake_heavy": { tags: ["shake", "chaos", "heavy"], minReadability: 2 }, // Terremoto
  
  // Movimentos de Câmera
  "vertical_glacial": { tags: ["vertical", "slow", "reading", "calm"], minReadability: 10 },
  "vertical_slow": { tags: ["vertical", "slow", "reading"], minReadability: 9 },
  "vertical_medium": { tags: ["vertical", "medium", "reading"], minReadability: 8 },
  "vertical_fast": { tags: ["vertical", "fast", "dynamic"], minReadability: 6 },
  
  // Emoção e Zoom
  "zoom_suspense": { tags: ["zoom", "facial", "suspense"], minReadability: 8 },
  "zoom_delay": { tags: ["zoom", "facial", "delay", "dramatic"], minReadability: 8 },
  
  // Especiais & Atmosfera
  "breathing": { tags: ["special", "breathing", "subtle"], minReadability: 9 },
  "breathing_heavy": { tags: ["flash", "power"], minReadability: 5 }, // Flash
  
  // 🔥 NOVOS VÍNCULOS (V6.9)
  "soft_float": { tags: ["special", "drift", "gentle"], minReadability: 9 }, // Para Romance
  "tension": { tags: ["tension", "fear", "danger"], minReadability: 6 }, // Para Monstros/Medo
  "kenburns_drift": { tags: ["kenburns", "drift", "circular"], minReadability: 7 }
};

// ======================================================================
// SEÇÃO 4: ✅ SISTEMA DE MEMÓRIA - CONTINUIDADE INTELIGENTE V5.0
// ======================================================================
class MemorySystem {
  constructor() {
    this.history = {
      colorGrading: [],
      movementDirection: [],
      atmosphere: [],
      brightness: [],
      pacing: []
    };
    this.maxHistorySize = GLOBAL_CONFIG.memory.smoothingWindow || 3;
  }
  
  // Adiciona informação ao histórico
  record(category, value) {
    if (!this.history[category]) {
      this.history[category] = [];
    }
    
    this.history[category].push(value);
    
    // Mantém apenas últimos N itens
    if (this.history[category].length > this.maxHistorySize) {
      this.history[category].shift();
    }
  }
  
  // Obtém tendência baseada no histórico
  getTrend(category) {
    if (!GLOBAL_CONFIG.memory.enabled) return null;
    
    const hist = this.history[category];
    if (!hist || hist.length === 0) return null;
    
    // Retorna o mais recente
    return hist[hist.length - 1];
  }
  
  // Obtém média dos últimos valores
  getAverage(category) {
    if (!GLOBAL_CONFIG.memory.enabled) return null;
    
    const hist = this.history[category];
    if (!hist || hist.length === 0) return null;
    
    const sum = hist.reduce((a, b) => a + b, 0);
    return sum / hist.length;
  }
  
  // Verifica se deve manter continuidade
  shouldMaintainContinuity(category) {
    if (!GLOBAL_CONFIG.memory.enabled) return false;
    
    const trackingKey = `track${category.charAt(0).toUpperCase() + category.slice(1)}`;
    return GLOBAL_CONFIG.memory[trackingKey] || false;
  }
  
  // Sugestão baseada em histórico
  suggestBasedOnHistory(category, options) {
    if (!this.shouldMaintainContinuity(category)) return null;
    
    const trend = this.getTrend(category);
    if (!trend) return null;
    
    // Encontra opção mais similar ao histórico
    let bestMatch = null;
    let bestScore = -1;
    
    for (const option of options) {
      const score = this._calculateSimilarity(trend, option);
      if (score > bestScore) {
        bestScore = score;
        bestMatch = option;
      }
    }
    
    return bestMatch;
  }
  
  _calculateSimilarity(a, b) {
    // Implementação simples - pode ser refinada
    if (typeof a === 'string' && typeof b === 'string') {
      return a === b ? 1.0 : 0.0;
    }
    if (typeof a === 'number' && typeof b === 'number') {
      const diff = Math.abs(a - b);
      return 1.0 - Math.min(diff, 1.0);
    }
    return 0.0;
  }
  
  // Reset do histórico
  reset() {
    for (const key in this.history) {
      this.history[key] = [];
    }
  }
}

// ======================================================================
// SEÇÃO 5: ✅ ANÁLISE DE CONTEÚDO - DETECÇÃO AUTOMÁTICA V5.0
// ======================================================================
class ContentAnalyzer {
  // Analisa brilho médio da imagem
  static analyzeBrightness(imagePath) {
    if (!GLOBAL_CONFIG.contentAnalysis.enabled || !GLOBAL_CONFIG.contentAnalysis.detectBrightness) {
      return 0.5; // Valor neutro
    }
    
    try {
      const result = execSync(
        `ffmpeg -i "${imagePath}" -vf "signalstats" -f null - 2>&1 | grep "lavfi.signalstats.YAVG" | tail -1 | awk '{print $NF}'`,
        { timeout: 5000 }
      ).toString().trim();
      
      const brightness = parseFloat(result) / 255 || 0.5;
      return Math.max(0, Math.min(1, brightness));
    } catch(e) {
      return 0.5;
    }
  }
  
  // Analisa contraste da imagem
  static analyzeContrast(imagePath) {
    if (!GLOBAL_CONFIG.contentAnalysis.enabled || !GLOBAL_CONFIG.contentAnalysis.detectContrast) {
      return 0.5; // Valor neutro
    }
    
    try {
      const result = execSync(
        `ffmpeg -i "${imagePath}" -vf "signalstats" -f null - 2>&1 | grep "lavfi.signalstats.YDIF" | tail -1 | awk '{print $NF}'`,
        { timeout: 5000 }
      ).toString().trim();
      
      const contrast = parseFloat(result) / 100 || 0.5;
      return Math.max(0, Math.min(1, contrast));
    } catch(e) {
      return 0.5;
    }
  }
  
  // Detecta paleta de cores predominante
  static analyzeColorPalette(imagePath) {
    if (!GLOBAL_CONFIG.contentAnalysis.enabled || !GLOBAL_CONFIG.contentAnalysis.detectColorPalette) {
      return { type: 'neutral', warmth: 0.5 };
    }
    
    try {
      // Análise simplificada de temperatura de cor
      const result = execSync(
        `ffmpeg -i "${imagePath}" -vf "signalstats" -f null - 2>&1 | grep "lavfi.signalstats.UAVG\\|lavfi.signalstats.VAVG" | tail -2`,
        { timeout: 5000 }
      ).toString();
      
      const lines = result.split('\n');
      const uAvg = parseFloat((lines[0] || '').split(' ').pop()) || 128;
      const vAvg = parseFloat((lines[1] || '').split(' ').pop()) || 128;
      
      // U < 128 = azul, U > 128 = amarelo
      // V < 128 = verde, V > 128 = vermelho
      const warmth = (vAvg / 255 + (uAvg / 255)) / 2;
      
      let type = 'neutral';
      if (warmth > 0.6) type = 'warm';
      else if (warmth < 0.4) type = 'cool';
      
      return { type, warmth };
    } catch(e) {
      return { type: 'neutral', warmth: 0.5 };
    }
  }
  
  // Ajustes adaptativos baseados na análise
  static getAdaptiveAdjustments(imagePath) {
    if (!GLOBAL_CONFIG.contentAnalysis.enabled || !GLOBAL_CONFIG.contentAnalysis.adaptiveEffects.enabled) {
      return {
        brightnessAdjust: 0,
        contrastAdjust: 1.0,
        recommendedFilter: null
      };
    }
    
    const brightness = this.analyzeBrightness(imagePath);
    const contrast = this.analyzeContrast(imagePath);
    const palette = this.analyzeColorPalette(imagePath);
    
    const thresholds = GLOBAL_CONFIG.contentAnalysis.adaptiveEffects;
    
    let brightnessAdjust = 0;
    let contrastAdjust = 1.0;
    let recommendedFilter = null;
    
    // Ajuste de brilho
    if (brightness > thresholds.brightnessThreshold) {
      brightnessAdjust = -0.05; // Imagem muito clara, escurece um pouco
    } else if (brightness < (1 - thresholds.brightnessThreshold)) {
      brightnessAdjust = 0.05; // Imagem muito escura, clareia um pouco
    }
    
    // Ajuste de contraste
    if (contrast < thresholds.contrastThreshold) {
      contrastAdjust = 1.08; // Baixo contraste, aumenta
    }
    
    // Recomendação de filtro baseado em paleta
    if (palette.type === 'warm') {
      recommendedFilter = 'warm_atmosphere';
    } else if (palette.type === 'cool') {
      recommendedFilter = 'cool_atmosphere';
    }
    
    return {
      brightness,
      contrast,
      palette,
      brightnessAdjust,
      contrastAdjust,
      recommendedFilter
    };
  }
}
// ======================================================================
// SEÇÃO 5B: ✅ SISTEMA DE EFEITOS SONOROS CONTEXTUAIS - V1.0
// ======================================================================

// ──────────────────────────────────────────────────────────────────────
// MAPEAMENTO: Palavras-chave → Arquivos de efeitos sonoros
// ──────────────────────────────────────────────────────────────────────
const SOUND_EFFECTS_MAP = {
  // ═══ AÇÃO E COMBATE ═══
  tiro: { files: ['10 - Arma 1.mp3', '11 - Arma 2.mp3', 'Tiro - Efeitos Sonoros Nerzinho.mp3', 'Tiro de Rifle - Efeitos sonoros Nerzinho.mp3'], volume: 0.7, priority: 1 },
  arma: { files: ['10 - Arma 1.mp3', '11 - Arma 2.mp3', 'Gun Reload - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 2 },
  pistola: { files: ['10 - Arma 1.mp3', '11 - Arma 2.mp3'], volume: 0.7, priority: 2 },
  explosão: { files: ['Cinematic Boom 1.mp3', 'Cinematic Boom 2.mp3', 'Impacto de Cinema - Efeitos sonoros Nerzinho.mp3'], volume: 0.8, priority: 1 },
  explodiu: { files: ['Cinematic Boom 1.mp3', 'Cinematic Boom 2.mp3'], volume: 0.8, priority: 1 },
  bomba: { files: ['Bomb Timer Sound Effect.mp3', 'Cinematic Boom 1.mp3'], volume: 0.7, priority: 1 },
  soco: { files: ['Punch 1.mp3', 'Punch 2.mp3', 'Soco 1 - Efeitos sonoros Nerzinho.mp3', 'Gta San Andreas - Punch Sound Effects.mp3'], volume: 0.6, priority: 1 },
  murro: { files: ['Punch 1.mp3', 'Punch 2.mp3', 'Soco 1 - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 1 },
  pancada: { files: ['Punch 1.mp3', 'Hard slap _ Short Meme for edit.mp3', 'Slap.mp3'], volume: 0.6, priority: 1 },
  tapa: { files: ['Slap.mp3', 'Hard slap _ Short Meme for edit.mp3', 'Cartoon Slap - Efeitos sonoros Nerzinho.mp3', 'Som de Tapa Na Cara Audio TAPAS e Murros EFEITO SONORO (128 kbps).mp3'], volume: 0.6, priority: 1 },
  chute: { files: ['Punch 2.mp3', 'Cartoon Bonk Sound Effect.mp3'], volume: 0.6, priority: 1 },
  golpe: { files: ['Punch 1.mp3', 'Punch 2.mp3', 'som de espada para edit   som de katana aumentado(MP3_320K).mp3'], volume: 0.6, priority: 1 },
  espada: { files: ['som de espada para edit   som de katana aumentado(MP3_320K).mp3', 'Knife Slash - Efeitos sonoros Nerzinho.mp3'], volume: 0.7, priority: 1 },
  luta: { files: ['Punch 1.mp3', 'Punch 2.mp3'], volume: 0.5, priority: 2 },
  ataque: { files: ['Punch 1.mp3', 'Whoosh 1.mp3', 'air-woosh-1.mp3'], volume: 0.6, priority: 2 },
  chicote: { files: ['Chicote - Efeitos sonoros Nerzinho.mp3', '37- Chicote.mp3'], volume: 0.6, priority: 1 },
  
  // ═══ MOVIMENTO E VELOCIDADE ═══
  correr: { files: ['Whoosh 1.mp3', 'Whoosh 2.mp3', 'air-woosh-1.mp3'], volume: 0.4, priority: 3 },
  correndo: { files: ['Whoosh 1.mp3', 'Whoosh 2.mp3'], volume: 0.4, priority: 3 },
  velocidade: { files: ['Whoosh 3.mp3', 'Fireball Whoosh.mp3', 'Cinematic Whoosh.mp3'], volume: 0.5, priority: 2 },
  rápido: { files: ['Whoosh 1.mp3', 'Fast woosh - Efeitos sonoros Nerzinho.wav'], volume: 0.4, priority: 3 },
  fugir: { files: ['Whoosh 2.mp3', 'air-woosh-2.mp3'], volume: 0.4, priority: 3 },
  escapar: { files: ['Whoosh 1.mp3', 'Whoosh 2.mp3'], volume: 0.4, priority: 3 },
  pular: { files: ['EFEITO SONORO - PULO DO MÁRIO(MP3_320K).mp3', 'Efeito do Som do mario pulando (128 kbps).mp3', 'Cartoon Boing 2 - Efeitos sonoros Nerzinho.mp3'], volume: 0.5, priority: 2 },
  pulou: { files: ['EFEITO SONORO - PULO DO MÁRIO(MP3_320K).mp3', 'Cartoon Boing 2 - Efeitos sonoros Nerzinho.mp3'], volume: 0.5, priority: 2 },
  salto: { files: ['EFEITO SONORO - PULO DO MÁRIO(MP3_320K).mp3', 'Whoosh 1.mp3'], volume: 0.5, priority: 2 },
  
  // ═══ IMPACTO E QUEDAS ═══
  caiu: { files: ['Falling.mp3', 'Cartoon Slip - Efeitos sonoros Nerzinho.mp3', 'Cartoon Slip _ Sound Effect ( 256kbps cbr ).mp3'], volume: 0.6, priority: 1 },
  cair: { files: ['Falling.mp3', 'Cartoon Slip - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 2 },
  queda: { files: ['Falling.mp3', 'Cartoon Slip - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 1 },
  tropeçou: { files: ['Cartoon Slip - Efeitos sonoros Nerzinho.mp3', 'Cartoon Slip _ Sound Effect ( 256kbps cbr ).mp3'], volume: 0.5, priority: 1 },
  escorregou: { files: ['Cartoon Slip - Efeitos sonoros Nerzinho.mp3', '64- Cartoon Slip - Gaming Sound Effect (HD).mp3'], volume: 0.5, priority: 1 },
  bateu: { files: ['Punch 1.mp3', 'Cartoon Bonk Sound Effect.mp3', 'Efeito Sonoro Bonk.mp3'], volume: 0.6, priority: 1 },
  colidiu: { files: ['Cartoon Bonk Sound Effect.mp3', 'Cinematic Boom 1.mp3'], volume: 0.6, priority: 1 },
  impacto: { files: ['Cinematic Boom 1.mp3', 'Impacto de Cinema - Efeitos sonoros Nerzinho.mp3'], volume: 0.7, priority: 1 },
  quebrou: { files: ['Glass Breaking.mp3', 'Vidro Quebrando -  Efeito Sonoro.mp3', 'Copo quebrando - Efeitos sonoros Nerzinho.wav', 'Bone Crack Sound Effect.mp3'], volume: 0.6, priority: 1 },
  vidro: { files: ['Glass Breaking.mp3', 'Vidro Quebrando -  Efeito Sonoro.mp3'], volume: 0.6, priority: 1 },
  osso: { files: ['Bone Crack Sound Effect.mp3'], volume: 0.6, priority: 1 },
  
  // ═══ EMOÇÕES E REAÇÕES ═══
  grito: { files: ['Grito - Efeitos sonoros Nerzinho.mp3', 'Man Screaming Sound Effect.mp3', '50- Female Scream - Sound Effect.mp3', 'Sr pelo Screaming.mp3'], volume: 0.6, priority: 1 },
  gritou: { files: ['Grito - Efeitos sonoros Nerzinho.mp3', 'Man Screaming Sound Effect.mp3'], volume: 0.6, priority: 1 },
  berrou: { files: ['Man screaming meme sound effect.mp3', 'Grito - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 1 },
  risada: { files: ['Risada de Fundo Chaves.mp3', 'Risadas de Fundo da Estúdios Gábia.mp3', '[Efeito Sonoro] Risada de Criança de Desenho Animado(MP3_320K).mp3'], volume: 0.5, priority: 2 },
  riso: { files: ['Risada de Fundo Chaves.mp3', 'Risadas de Fundo da Estúdios Gábia.mp3'], volume: 0.5, priority: 2 },
  riu: { files: ['Risada de Fundo Chaves.mp3', 'Risadas de Fundo da Estúdios Gábia.mp3'], volume: 0.5, priority: 2 },
  chorou: { files: ['Sad Music 1.mp3', '5- Triste.mp3'], volume: 0.4, priority: 2 },
  chorando: { files: ['Sad Music 1.mp3', 'Sad 2 - Efeitos sonoros Nerzinho.mp3'], volume: 0.4, priority: 2 },
  triste: { files: ['5- Triste.mp3', 'Sad Music 1.mp3', 'Sad 2 - Efeitos sonoros Nerzinho.mp3'], volume: 0.4, priority: 2 },
  feliz: { files: ['Children Yay   Sound Effect.mp3', 'Kids Cheering.mp3'], volume: 0.5, priority: 2 },
  surpresa: { files: ['36- !.mp3', '! - Efeitos sonoros Nerzinho.mp3', 'Suspense 1.mp3'], volume: 0.5, priority: 1 },
  surpreso: { files: ['36- !.mp3', '! - Efeitos sonoros Nerzinho.mp3'], volume: 0.5, priority: 1 },
  chocado: { files: ['36- !.mp3', 'Suspense 1.mp3', 'Dun Dun Dun.mp3'], volume: 0.6, priority: 1 },
  medo: { files: ['Suspense 1.mp3', 'Suspense 2.mp3', 'Long Suspense 1.mp3'], volume: 0.5, priority: 1 },
  assustou: { files: ['Suspense 1.mp3', '36- !.mp3', 'Scary Suspense.mp3'], volume: 0.6, priority: 1 },
  susto: { files: ['36- !.mp3', 'Suspense 1.mp3'], volume: 0.6, priority: 1 },
  raiva: { files: ['Angry Sound.mp3', 'Suspense - Efeitos sonoros Nerzinho.mp3'], volume: 0.5, priority: 2 },
  nervoso: { files: ['Suspense - Efeitos sonoros Nerzinho.mp3', 'Heartbeat.mp3'], volume: 0.4, priority: 2 },
  
  // ═══ SUSPENSE E DRAMA ═══
  suspense: { files: ['Suspense 1.mp3', 'Suspense 2.mp3', 'Suspense 3.mp3', 'Long Suspense 1.mp3', 'Long Suspense 2.mp3', 'Suspense - Efeitos sonoros Nerzinho.mp3', '9- Suspense 2.mp3'], volume: 0.5, priority: 1 },
  tensão: { files: ['Suspense 1.mp3', 'Long Suspense 1.mp3', 'Heartbeat.mp3'], volume: 0.5, priority: 1 },
  perigo: { files: ['Danger Alarm Sound Effect.mp3', 'Suspense 1.mp3', 'Emergencia - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 1 },
  morte: { files: ['39- MORRI.mp3', 'MORRI - Efeitos sonoros Nerzinho.mp3', '51- E Morreu - Didi.mp3', 'Roblox Death Sound  Sound Effect HD.mp3'], volume: 0.6, priority: 1 },
  morreu: { files: ['39- MORRI.mp3', '51- E Morreu - Didi.mp3', 'Roblox Death Sound  Sound Effect HD.mp3', 'GTA Wasted - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 1 },
  matar: { files: ['Suspense 1.mp3', 'Danger Alarm Sound Effect.mp3'], volume: 0.5, priority: 2 },
  revelação: { files: ['Dun Dun Dun.mp3', 'Suspense 1.mp3', 'Inception.mp3'], volume: 0.6, priority: 1 },
  segredo: { files: ['Suspense 1.mp3', 'Suspense 2.mp3'], volume: 0.5, priority: 2 },
  mistério: { files: ['Suspense 1.mp3', 'Long Suspense 1.mp3'], volume: 0.5, priority: 2 },
  
  // ═══ SONS AMBIENTES ═══
  água: { files: ['34- Água 1.mp3', '35- Água 2.mp3', 'Bubbles.mp3', 'Splat.mp3'], volume: 0.5, priority: 2 },
  chuva: { files: ['34- Água 1.mp3', '35- Água 2.mp3'], volume: 0.4, priority: 3 },
  trovão: { files: ['Trovão - Efeitos Sonoros Nerzinho.mp3'], volume: 0.7, priority: 1 },
  raio: { files: ['15- Raio Logo.mp3', 'Trovão - Efeitos Sonoros Nerzinho.mp3'], volume: 0.7, priority: 1 },
  vento: { files: ['4- Vento Lento.mp3', 'air-woosh-1.mp3'], volume: 0.4, priority: 3 },
  fogo: { files: ['Fireball Whoosh.mp3', 'Cinematic Boom 1.mp3'], volume: 0.6, priority: 2 },
  silêncio: { files: ['60- Grilos.mp3', 'Grilos - Efeitos sonoros Nerzinho.mp3', 'Crickets.mp3', 'GRILO CRI CRI _ EFEITO SONORO(MP3_320K).mp3'], volume: 0.3, priority: 3 },
  noite: { files: ['60- Grilos.mp3', 'Crickets.mp3'], volume: 0.3, priority: 3 },
  
  // ═══ OBJETOS E AÇÕES ═══
  porta: { files: ['Batendo na Porta - Efeitos sonoros Nerzinho.mp3', 'Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3'], volume: 0.5, priority: 2 },
  campainha: { files: ['Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3', 'Bell Transition.mp3'], volume: 0.5, priority: 1 },
  telefone: { files: ['Phone Ringing.mp3', 'Samsung Notification Sound Effect.mp3', 'Z Iphone SMS Sound - Efeitos Sonoros Nerzinho.mp3'], volume: 0.5, priority: 1 },
  celular: { files: ['Samsung Notification Sound Effect.mp3', 'Z Iphone SMS Sound - Efeitos Sonoros Nerzinho.mp3', 'iPhone Piano Riff Sound Effect.mp3'], volume: 0.5, priority: 1 },
  mensagem: { files: ['Samsung Notification Sound Effect.mp3', 'Discord Join Sound Effect.mp3', 'som de notificação discord - Efeitos Sonoros HD (128 kbps).mp3'], volume: 0.5, priority: 1 },
  notificação: { files: ['Samsung Notification Sound Effect.mp3', 'Discord Join Sound Effect.mp3'], volume: 0.5, priority: 1 },
  click: { files: ['29- Click.mp3', 'Click mouse - Efeitos sonoros Nerzinho.mp3', 'Mouse Click.mp3'], volume: 0.4, priority: 2 },
  clicou: { files: ['29- Click.mp3', 'Click mouse - Efeitos sonoros Nerzinho.mp3'], volume: 0.4, priority: 2 },
  digitando: { files: ['Digitando teclado - Efeitos sonoros Nerzinho.mp3', 'efeito sonoro teclado de computador 2020 (320 kbps).mp3', 'Typewriter.mp3'], volume: 0.4, priority: 2 },
  moeda: { files: ['SMB Adquirindo moeda - Efeitos sonoros Nerzinho.mp3', 'Sonic Ring Sound Effect.mp3', 'Cash Register.mp3'], volume: 0.5, priority: 1 },
  dinheiro: { files: ['26- Dinheiro 2.mp3', '27- Dinheiro 1.mp3', 'Cash Register.mp3', 'Caixa Registradora - Efeitos Sonoros Nerzinho.mp3'], volume: 0.5, priority: 1 },
  carro: { files: ['Carro Buzinando - Efeitos sonoros Nerzinho.mp3', '30- Buzina.mp3'], volume: 0.5, priority: 2 },
  buzina: { files: ['30- Buzina.mp3', 'Carro Buzinando - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 1 },
  foto: { files: ['Camera Shot _[Efeito sonoro](MP3_320K).mp3', 'Camera Shutter - Efeitos Sonoros Nerzinho.mp3', 'Shutter Click.mp3', 'Taking Photos.mp3'], volume: 0.5, priority: 1 },
  fotografia: { files: ['Camera Shutter - Efeitos Sonoros Nerzinho.mp3', 'Shutter Click.mp3'], volume: 0.5, priority: 1 },
  
  // ═══ COMIDA E BEBIDA ═══
  bebendo: { files: ['Abrindo Latinha - Efeitos sonoros Nerzinho.mp3', 'GULP sound effect.mp3', 'Cartoon Gulp Sound Effect.mp3'], volume: 0.5, priority: 2 },
  bebeu: { files: ['GULP sound effect.mp3', 'Cartoon Gulp Sound Effect.mp3'], volume: 0.5, priority: 2 },
  comendo: { files: ['Minecraft eating sound effect.mp3', 'Som de Mordida de Desenho Animado 1  - Efeitos Sonoros Nerzinho.mp3'], volume: 0.5, priority: 2 },
  comeu: { files: ['Minecraft eating sound effect.mp3', 'Som de Mordida de Desenho Animado 1  - Efeitos Sonoros Nerzinho.mp3'], volume: 0.5, priority: 2 },
  mordida: { files: ['Som de Mordida de Desenho Animado 1  - Efeitos Sonoros Nerzinho.mp3'], volume: 0.5, priority: 1 },
  garrafa: { files: ['Abrindo garrafa - Efeitos Sonoros Nerzinho.mp3', 'Cork-Pop - Efeitos sonoros Nerzinho.mp3'], volume: 0.5, priority: 2 },
  
  // ═══ ANIMAIS ═══
  cavalo: { files: ['CAVALO - Efeitos sonoros Nerzinho.mp3', 'Cavalo Correndo - Efeitos Sonoros Nerzinho.mp3', 'Cavalo vinhetas.mp3'], volume: 0.5, priority: 2 },
  galinha: { files: ['Galinha efeito sonoro.mp3'], volume: 0.5, priority: 2 },
  golfinho: { files: ['Dolphin.mp3', 'Golfinho efeito sonoro.mp3'], volume: 0.5, priority: 2 },
  pato: { files: ['Pato - Efeitos sonoros Nerzinho.mp3', 'Rubber Duck.mp3', 'Patinho de borracha - Efeitos sonoros Nerzinho.mp3'], volume: 0.5, priority: 2 },
  macaco: { files: ['Macaco gritando - Efeitos sonoros Nerzinho.mp3', 'MACACO GRITANDO EFEITO SONORO(MP3_320K).mp3'], volume: 0.5, priority: 2 },
  passaro: { files: ['audio de bem te vi.mp3'], volume: 0.4, priority: 3 },
  
  // ═══ MAGIA E FANTASIA ═══
  magia: { files: ['21- Mágica.mp3', 'Brilho Mágico - Efeitos sonoros Nerzinho.mp3', 'Magic_Wand_1.wav', 'Angel  Sound Effect HD.mp3'], volume: 0.6, priority: 1 },
  mágica: { files: ['21- Mágica.mp3', 'Brilho Mágico - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 1 },
  poder: { files: ['21- Mágica.mp3', 'Brilho Mágico - Efeitos sonoros Nerzinho.mp3', 'Cinematic Boom 1.mp3'], volume: 0.6, priority: 1 },
  transformação: { files: ['21- Mágica.mp3', 'Brilho Mágico - Efeitos sonoros Nerzinho.mp3', 'Titan Transformation Lightning WITH SOUND EFFECTS - Attack on Titan.mp3'], volume: 0.7, priority: 1 },
  transformou: { files: ['21- Mágica.mp3', 'Titan Transformation Lightning WITH SOUND EFFECTS - Attack on Titan.mp3'], volume: 0.7, priority: 1 },
  teleporte: { files: ['Enderman Teleport - Minecraft Gaming Sound Effect (HD) ( 256kbps cbr ).mp3', 'Enderman Teleport Minecraft Gaming Sound Effect Hd.mp3', 'Sonido de desaparecer.mp3'], volume: 0.6, priority: 1 },
  desapareceu: { files: ['Sonido de desaparecer.mp3', 'SUMIU!!! - Efeitos sonoros Nerzinho.mp3', 'Poof sound Naruto.mp3'], volume: 0.6, priority: 1 },
  apareceu: { files: ['Poof sound Naruto.mp3', '21- Mágica.mp3'], volume: 0.6, priority: 1 },
  
  // ═══ COMUNICAÇÃO ═══
  falou: { files: [], volume: 0, priority: 10 }, // Não adiciona som para fala normal
  disse: { files: [], volume: 0, priority: 10 },
  perguntou: { files: [], volume: 0, priority: 10 },
  
  // ═══ VITÓRIA E DERROTA ═══
  vitória: { files: ['Children Yay   Sound Effect.mp3', 'Kids Cheering.mp3', 'People Clapping.mp3', 'Multidão Aplaudindo - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 1 },
  ganhou: { files: ['Children Yay   Sound Effect.mp3', 'Resposta Certa - Efeitos sonoros Nerzinho.mp3', 'Minecraft Level Up Sound Effect Free _ Download Link.mp3'], volume: 0.6, priority: 1 },
  venceu: { files: ['Children Yay   Sound Effect.mp3', 'People Clapping.mp3'], volume: 0.6, priority: 1 },
  perdeu: { files: ['Fail 1.mp3', 'Fail 2.mp3', 'Resposta Errada - Efeitos sonoros Nerzinho.mp3', '49- The Price is Right Losing Horn - Gaming Sound Effect (HD).mp3', 'Wrong Answer.mp3'], volume: 0.6, priority: 1 },
  derrota: { files: ['Fail 1.mp3', '49- The Price is Right Losing Horn - Gaming Sound Effect (HD).mp3', 'Sad Music 1.mp3'], volume: 0.6, priority: 1 },
  errou: { files: ['25- Errou.mp3', 'Resposta Errada - Efeitos sonoros Nerzinho.mp3', 'Wrong Answer.mp3', 'Fail 1.mp3'], volume: 0.5, priority: 1 },
  acertou: { files: ['Resposta Certa - Efeitos sonoros Nerzinho.mp3', 'Sonic Ring Sound Effect.mp3'], volume: 0.5, priority: 1 },
  aplausos: { files: ['People Clapping.mp3', 'Multidão Aplaudindo - Efeitos sonoros Nerzinho.mp3', 'Kids Cheering.mp3'], volume: 0.5, priority: 1 },
  
  // ═══ REAÇÕES CÔMICAS ═══
  constrangedor: { files: ['Crickets.mp3', '60- Grilos.mp3'], volume: 0.4, priority: 2 },
  vergonha: { files: ['Crickets.mp3', 'Fail 1.mp3'], volume: 0.4, priority: 2 },
  piada: { files: ['Ba Dum Tss - Efeitos sonoros Nerzinho.mp3', 'Badum Tsss.mp3', 'Drum Roll.mp3'], volume: 0.5, priority: 1 },
  engraçado: { files: ['Risada de Fundo Chaves.mp3', 'Ba Dum Tss - Efeitos sonoros Nerzinho.mp3'], volume: 0.5, priority: 2 },
  peido: { files: ['57- PEIDO.mp3', 'Fart 1.mp3', 'Fart 2.mp3', 'Efeito Sonoro de Peido  Efeito Sonoro HD.mp3', 'Reverb fart sound effect.mp3'], volume: 0.5, priority: 1 },
  peidou: { files: ['57- PEIDO.mp3', 'Fart 1.mp3', 'Fart 2.mp3'], volume: 0.5, priority: 1 },
  arroto: { files: ['GULP sound effect.mp3'], volume: 0.5, priority: 2 },
  espirro: { files: ['Espirro de Bebê - Efeitos sonoros Nerzinho.mp3'], volume: 0.5, priority: 1 },
  ronco: { files: ['[Efeito Sonoro] Desenho Animado Roncando e Assobiando (128 kbps).mp3', 'efeito sonoro roncando 🥱🥱.mp3', 'maluko roncando estourado (128 kbps).mp3'], volume: 0.4, priority: 2 },
  dormindo: { files: ['[Efeito Sonoro] Desenho Animado Roncando e Assobiando (128 kbps).mp3', 'efeito sonoro roncando 🥱🥱.mp3'], volume: 0.4, priority: 2 },
  
  // ═══ INTERJEIÇÕES E EXPRESSÕES ═══
  uau: { files: ['45- Whaaat - Sound Effect.mp3', 'Anime Wow - Efeitos sonoros Nerzinho.mp3'], volume: 0.5, priority: 2 },
  wow: { files: ['Anime Wow - Efeitos sonoros Nerzinho.mp3', '45- Whaaat - Sound Effect.mp3'], volume: 0.5, priority: 2 },
  ops: { files: ['56- Ops.mp3', 'Fail 1.mp3'], volume: 0.5, priority: 2 },
  eita: { files: ['Meme - EITA EITA EITAAAAAAAA.mp3', '36- !.mp3'], volume: 0.5, priority: 1 },
  aleluia: { files: ['Aleluia - Efeitos sonoros Nerzinho.mp3', 'Angel  Sound Effect HD.mp3', 'Angels Singing.mp3'], volume: 0.5, priority: 1 },
  
  // ═══ GAME RELATED ═══
  level: { files: ['Minecraft Level Up Sound Effect Free _ Download Link.mp3', 'SMB Power-up - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 1 },
  levelup: { files: ['Minecraft Level Up Sound Effect Free _ Download Link.mp3', 'SMB Power-up - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 1 },
  powerup: { files: ['SMB Power-up - Efeitos sonoros Nerzinho.mp3', 'Minecraft Level Up Sound Effect Free _ Download Link.mp3'], volume: 0.6, priority: 1 },
  game: { files: ['GTA Wasted - Efeitos sonoros Nerzinho.mp3', 'Minecraft Level Up Sound Effect Free _ Download Link.mp3'], volume: 0.5, priority: 2 },
  wasted: { files: ['GTA Wasted - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 1 },
  
  // ═══ CORAÇÃO/AMOR ═══
  coração: { files: ['Heartbeat.mp3', 'Coração batendo - Efeitos sonoros Nerzinho.mp3'], volume: 0.4, priority: 2 },
  amor: { files: ['Heartbeat.mp3', 'Angel  Sound Effect HD.mp3'], volume: 0.4, priority: 3 },
  beijo: { files: ['Som de Beijo - Efeitos Sonoros Nerzinho.mp3'], volume: 0.5, priority: 1 },
  beijou: { files: ['Som de Beijo - Efeitos Sonoros Nerzinho.mp3'], volume: 0.5, priority: 1 },
  
  // ═══ TEMPO ═══
  relógio: { files: ['Relógio - Efeitos sonoros Nerzinho.wav', 'Bomb Timer Sound Effect.mp3'], volume: 0.4, priority: 2 },
  tempo: { files: ['Relógio - Efeitos sonoros Nerzinho.wav'], volume: 0.3, priority: 3 },
  rewind: { files: ['Rewind.mp3'], volume: 0.5, priority: 1 },
  flashback: { files: ['Flashback.mp3', 'Rewind.mp3'], volume: 0.5, priority: 1 },
  
  // ═══ NOTÍCIAS/BREAKING ═══
  notícia: { files: ['Breaking News - Efeitos sonoros Nerzinho.mp3', 'My New News Intro.mp3'], volume: 0.5, priority: 1 },
  urgente: { files: ['Breaking News - Efeitos sonoros Nerzinho.mp3', 'Emergencia - Efeitos sonoros Nerzinho.mp3'], volume: 0.6, priority: 1 },
  alerta: { files: ['Emergencia - Efeitos sonoros Nerzinho.mp3', 'Danger Alarm Sound Effect.mp3'], volume: 0.6, priority: 1 }
};

// ──────────────────────────────────────────────────────────────────────
// CONFIGURAÇÃO: Pasta base dos efeitos sonoros - V6.20 VOLUME CORRIGIDO
// ──────────────────────────────────────────────────────────────────────
const SOUND_EFFECTS_CONFIG = {
  basePath: '/tmp/youtubevideos/efeitos_sonoros',
  
  // ═══════════════════════════════════════════════════════════════
  // 🔊 VOLUME PADRÃO - REDUZIDO PARA NÃO SOBREPOR NARRAÇÃO
  // ═══════════════════════════════════════════════════════════════
  defaultVolume: 0.35,          // Era 0.5, agora 0.35
  
  maxEffectsPerPage: 10,
  minTimeBetweenEffects: 0.5,
  effectDurationBuffer: 0.1,
  enabled: true
};

// ──────────────────────────────────────────────────────────────────────
// CLASSE: SubtitleParser - Parse de legendas SRT e ASS
// ──────────────────────────────────────────────────────────────────────
class SubtitleParser {
  /**
   * Converte timestamp SRT (00:00:01,500) para segundos
   */
  static srtTimeToSeconds(timeStr) {
    if (!timeStr) return 0;
    
    const parts = timeStr.replace(',', '.').split(':');
    if (parts.length !== 3) return 0;
    
    const hours = parseFloat(parts[0]) || 0;
    const minutes = parseFloat(parts[1]) || 0;
    const seconds = parseFloat(parts[2]) || 0;
    
    return hours * 3600 + minutes * 60 + seconds;
  }
  
  /**
   * Converte timestamp ASS (0:00:01.50) para segundos
   */
  static assTimeToSeconds(timeStr) {
    if (!timeStr) return 0;
    
    const parts = timeStr.split(':');
    if (parts.length !== 3) return 0;
    
    const hours = parseFloat(parts[0]) || 0;
    const minutes = parseFloat(parts[1]) || 0;
    const seconds = parseFloat(parts[2]) || 0;
    
    return hours * 3600 + minutes * 60 + seconds;
  }
  
  /**
   * Remove tags ASS do texto (ex: {\k50}, {\fad(200,200)})
   */
  static cleanAssText(text) {
    if (!text) return '';
    return text
      .replace(/\{[^}]*\}/g, '')  // Remove tags {}
      .replace(/\\N/g, ' ')        // Substitui quebras de linha
      .replace(/\\n/g, ' ')
      .trim();
  }
  
  /**
   * Parse de arquivo SRT
   * Retorna array de { start, end, text }
   */
  static parseSRT(content) {
    const entries = [];
    const blocks = content.split(/\n\s*\n/);
    
    for (const block of blocks) {
      const lines = block.trim().split('\n');
      if (lines.length < 3) continue;
      
      // Linha de tempo: 00:00:01,500 --> 00:00:03,000
      const timeLine = lines[1];
      const timeMatch = timeLine.match(/(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})/);
      
      if (!timeMatch) continue;
      
      const start = this.srtTimeToSeconds(timeMatch[1]);
      const end = this.srtTimeToSeconds(timeMatch[2]);
      const text = lines.slice(2).join(' ').trim();
      
      entries.push({ start, end, text });
    }
    
    return entries;
  }
  
  /**
   * Parse de arquivo ASS
   * Retorna array de { start, end, text }
   */
  static parseASS(content) {
    const entries = [];
    const lines = content.split('\n');
    
    let inEvents = false;
    let formatFields = [];
    
    for (const line of lines) {
      const trimmed = line.trim();
      
      // Detecta seção [Events]
      if (trimmed === '[Events]') {
        inEvents = true;
        continue;
      }
      
      // Detecta nova seção
      if (trimmed.startsWith('[') && trimmed !== '[Events]') {
        inEvents = false;
        continue;
      }
      
      if (!inEvents) continue;
      
      // Parse Format line
      if (trimmed.startsWith('Format:')) {
        formatFields = trimmed.substring(7).split(',').map(f => f.trim().toLowerCase());
        continue;
      }
      
      // Parse Dialogue line
      if (trimmed.startsWith('Dialogue:')) {
        const values = trimmed.substring(9).split(',');
        
        // Encontra índices dos campos
        const startIdx = formatFields.indexOf('start');
        const endIdx = formatFields.indexOf('end');
        const textIdx = formatFields.indexOf('text');
        
        if (startIdx === -1 || endIdx === -1 || textIdx === -1) continue;
        
        const start = this.assTimeToSeconds(values[startIdx]?.trim());
        const end = this.assTimeToSeconds(values[endIdx]?.trim());
        // Texto pode conter vírgulas, então junta tudo após o índice de texto
        const text = this.cleanAssText(values.slice(textIdx).join(','));
        
        entries.push({ start, end, text });
      }
    }
    
    return entries;
  }
  
  /**
   * Parse automático baseado na extensão
   */
  static parse(filePath) {
    try {
      if (!fs.existsSync(filePath)) {
        console.warn(`⚠️ [SFX] Arquivo de legenda não encontrado: ${filePath}`);
        return [];
      }
      
      const content = fs.readFileSync(filePath, 'utf8');
      
      if (filePath.toLowerCase().endsWith('.ass')) {
        console.log(`📝 [SFX] Parseando legenda ASS: ${filePath}`);
        return this.parseASS(content);
      } else if (filePath.toLowerCase().endsWith('.srt')) {
        console.log(`📝 [SFX] Parseando legenda SRT: ${filePath}`);
        return this.parseSRT(content);
      } else {
        console.warn(`⚠️ [SFX] Formato de legenda não suportado: ${filePath}`);
        return [];
      }
    } catch (e) {
      console.error(`❌ [SFX] Erro ao parsear legenda: ${e.message}`);
      return [];
    }
  }
}

// ──────────────────────────────────────────────────────────────────────
// CLASSE: SoundEffectsDetector - Detecta palavras-chave e seus timestamps
// ──────────────────────────────────────────────────────────────────────
class SoundEffectsDetector {
  /**
   * Detecta efeitos sonoros baseado nas entradas de legenda
   * @param {Array} subtitleEntries - Array de { start, end, text }
   * @returns {Array} - Array de { timestamp, keyword, effectFile, volume }
   */
  static detectEffects(subtitleEntries) {
    if (!SOUND_EFFECTS_CONFIG.enabled) {
      console.log(`⚠️ [SFX] Sistema de efeitos sonoros desabilitado`);
      return [];
    }
    
    const detectedEffects = [];
    const usedEffects = new Map(); // Para variar efeitos do mesmo tipo
    
    console.log(`\n🔊 ════════════════════════════════════════════`);
    console.log(`🔊 DETECTANDO EFEITOS SONOROS`);
    console.log(`🔊 ════════════════════════════════════════════`);
    console.log(`📝 Total de entradas de legenda: ${subtitleEntries.length}`);
    
    for (const entry of subtitleEntries) {
      const text = (entry.text || '').toLowerCase();
      const words = text.split(/\s+/);
      
      for (const word of words) {
        // Remove pontuação para matching
        const cleanWord = word.replace(/[.,!?;:'"()]/g, '');
        
        // Busca palavra-chave no mapa
        for (const [keyword, config] of Object.entries(SOUND_EFFECTS_MAP)) {
          // Verifica se a palavra contém a keyword (para palavras compostas)
          if (cleanWord.includes(keyword) || keyword.includes(cleanWord)) {
            // Ignora se não tem arquivos ou prioridade muito baixa
            if (!config.files || config.files.length === 0 || config.priority > 5) {
              continue;
            }
            
            // Calcula timestamp estimado (início da entrada + posição da palavra)
            const wordPosition = words.indexOf(word);
            const entryDuration = entry.end - entry.start;
            const wordFraction = words.length > 1 ? wordPosition / words.length : 0;
            const timestamp = entry.start + (entryDuration * wordFraction) - SOUND_EFFECTS_CONFIG.effectDurationBuffer;
            
            // Seleciona arquivo (rotaciona entre os disponíveis)
            const usedCount = usedEffects.get(keyword) || 0;
            const fileIndex = usedCount % config.files.length;
            const selectedFile = config.files[fileIndex];
            usedEffects.set(keyword, usedCount + 1);
            
            // Verifica se o arquivo existe
            const fullPath = `${SOUND_EFFECTS_CONFIG.basePath}/${selectedFile}`;
            if (!fs.existsSync(fullPath)) {
              console.warn(`   ⚠️ Arquivo não encontrado: ${selectedFile}`);
              continue;
            }
            
            detectedEffects.push({
              timestamp: Math.max(0, timestamp),
              keyword: keyword,
              matchedWord: cleanWord,
              effectFile: selectedFile,
              effectPath: fullPath,
              volume: config.volume || SOUND_EFFECTS_CONFIG.defaultVolume,
              priority: config.priority || 5,
              entryStart: entry.start,
              entryEnd: entry.end
            });
            
            console.log(`   ✅ "${cleanWord}" → ${selectedFile} @ ${timestamp.toFixed(2)}s`);
            break; // Só um efeito por palavra
          }
        }
      }
    }
    
    // Ordena por timestamp
    detectedEffects.sort((a, b) => a.timestamp - b.timestamp);
    
    // Remove efeitos muito próximos (mantém o de maior prioridade)
    const filteredEffects = this._filterCloseEffects(detectedEffects);
    
    // Limita quantidade de efeitos
    const finalEffects = filteredEffects.slice(0, SOUND_EFFECTS_CONFIG.maxEffectsPerPage);
    
    console.log(`\n📊 RESUMO:`)
    console.log(`   Total detectado: ${detectedEffects.length}`);
    console.log(`   Após filtro de proximidade: ${filteredEffects.length}`);
    console.log(`   Final (limitado): ${finalEffects.length}`);
    console.log(`🔊 ════════════════════════════════════════════\n`);
    
    return finalEffects;
  }
  
  /**
   * Filtra efeitos muito próximos uns dos outros
   */
  static _filterCloseEffects(effects) {
    if (effects.length < 2) return effects;
    
    const filtered = [effects[0]];
    
    for (let i = 1; i < effects.length; i++) {
      const current = effects[i];
      const last = filtered[filtered.length - 1];
      
      const timeDiff = current.timestamp - last.timestamp;
      
      if (timeDiff >= SOUND_EFFECTS_CONFIG.minTimeBetweenEffects) {
        filtered.push(current);
      } else if (current.priority < last.priority) {
        // Substitui se o novo tem maior prioridade (número menor)
        filtered[filtered.length - 1] = current;
      }
    }
    
    return filtered;
  }
}

// ──────────────────────────────────────────────────────────────────────
// CLASSE: SoundEffectsMixer V6.20 - Gera comando FFmpeg para mixar efeitos
// ──────────────────────────────────────────────────────────────────────
class SoundEffectsMixer {
  /**
   * Gera o filtro FFmpeg para adicionar efeitos sonoros
   * @param {Array} effects - Array de efeitos detectados
   * @param {number} videoDuration - Duração do vídeo em segundos
   * @returns {Object} - { inputs: string[], filterComplex: string, outputLabel: string }
   */
  static buildMixFilter(effects, videoDuration = 60) {
    if (!effects || effects.length === 0) {
      return { inputs: [], filterComplex: '', outputLabel: '', hasEffects: false };
    }
    
    console.log(`\n🎛️ ════════════════════════════════════════════`);
    console.log(`🎛️ CONSTRUINDO MIXER DE EFEITOS SONOROS V6.20`);
    console.log(`🎛️ ════════════════════════════════════════════`);
    
    // ═══════════════════════════════════════════════════════════════════════
    // 🔊 V6.20: USA CONFIGURAÇÃO GLOBAL DE VOLUME
    // ═══════════════════════════════════════════════════════════════════════
    const sfxConfig = GLOBAL_CONFIG.soundEffects || {
      effectVolume: 0.35,
      mixWeight: 0.5
    };
    const volumeMultiplier = sfxConfig.effectVolume || 0.35;
    
    console.log(`📊 Volume multiplier: ${volumeMultiplier}`);
    // ═══════════════════════════════════════════════════════════════════════
    
    const inputs = [];
    const filterParts = [];
    let currentAudioLabel = '[a_base]'; // Assume que o áudio base já está como [a_base]
    
    for (let i = 0; i < effects.length; i++) {
      const effect = effects[i];
      const inputIndex = i + 10; // Offset para evitar conflito com inputs existentes
      const effectLabel = `[sfx_${i}]`;
      const mixedLabel = `[a_mix_${i}]`;
      
      // Adiciona input do arquivo de efeito
      inputs.push(`-i "${effect.effectPath}"`);
      
      // 🔊 V6.20: Aplica volume REDUZIDO (original * multiplier)
      const finalVolume = (effect.volume || 0.5) * volumeMultiplier;
      
      // Prepara o efeito: ajusta volume e adiciona delay
      const delayMs = Math.round(effect.timestamp * 1000);
      filterParts.push(`[${inputIndex}:a]volume=${finalVolume.toFixed(2)},adelay=${delayMs}|${delayMs},apad=whole_dur=${videoDuration}${effectLabel}`);
      
      // Mixa com o áudio anterior
      filterParts.push(`${currentAudioLabel}${effectLabel}amix=inputs=2:duration=first:dropout_transition=0${mixedLabel}`);
      
      currentAudioLabel = mixedLabel;
      
      console.log(`   [${i + 1}] ${effect.keyword} @ ${effect.timestamp.toFixed(2)}s → ${effect.effectFile} (vol original: ${effect.volume}, final: ${finalVolume.toFixed(2)})`);
    }
    
    console.log(`\n   📊 Total de inputs adicionais: ${inputs.length}`);
    console.log(`🎛️ ════════════════════════════════════════════\n`);
    
    return {
      inputs: inputs,
      filterComplex: filterParts.join(';'),
      outputLabel: currentAudioLabel,
      hasEffects: true
    };
  }
  
  /**
   * Método simplificado: Cria um arquivo de áudio com todos os efeitos pré-mixados
   * Isso evita comandos FFmpeg muito complexos
   * @param {Array} effects - Array de efeitos detectados
   * @param {string} outputPath - Caminho do arquivo de saída
   * @param {number} duration - Duração total em segundos
   * @returns {Object} - { success: boolean, outputPath: string }
   */
  static createEffectsTrack(effects, outputPath, duration = 60) {
    if (!effects || effects.length === 0) {
      return { success: false, outputPath: null, hasEffects: false };
    }
    
    console.log(`\n🎵 ════════════════════════════════════════════`);
    console.log(`🎵 CRIANDO TRILHA DE EFEITOS SONOROS V6.20`);
    console.log(`🎵 ════════════════════════════════════════════`);
    console.log(`📁 Output: ${outputPath}`);
    console.log(`⏱️ Duração: ${duration}s`);
    console.log(`🔊 Efeitos: ${effects.length}`);
    
    // ═══════════════════════════════════════════════════════════════════════
    // 🔊 V6.20: USA CONFIGURAÇÃO GLOBAL DE VOLUME
    // ═══════════════════════════════════════════════════════════════════════
    const sfxConfig = GLOBAL_CONFIG.soundEffects || {
      effectVolume: 0.35
    };
    const volumeMultiplier = sfxConfig.effectVolume || 0.35;
    
    console.log(`📊 Volume multiplier configurado: ${volumeMultiplier}`);
    // ═══════════════════════════════════════════════════════════════════════
    
    try {
      // Cria um arquivo de silêncio base
      const silenceCmd = `ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=stereo -t ${duration} -c:a pcm_s16le "${outputPath.replace('.mp3', '_silence.wav')}" 2>&1`;
      
      try {
        execSync(silenceCmd, { timeout: 10000 });
      } catch (e) {
        console.warn(`⚠️ Erro ao criar silêncio base: ${e.message}`);
      }
      
      // Constrói comando para mixar todos os efeitos
      let inputs = [`-i "${outputPath.replace('.mp3', '_silence.wav')}"`];
      let filterParts = [];
      let currentLabel = '[0:a]';
      
      for (let i = 0; i < effects.length; i++) {
        const effect = effects[i];
        const inputIdx = i + 1;
        const delayMs = Math.round(effect.timestamp * 1000);
        
        inputs.push(`-i "${effect.effectPath}"`);
        
        const effectLabel = `[sfx${i}]`;
        const mixLabel = `[mix${i}]`;
        
        // 🔊 V6.20: Aplica volume REDUZIDO (original * multiplier)
        const finalVolume = (effect.volume || 0.5) * volumeMultiplier;
        
        // Aplica volume e delay ao efeito
        filterParts.push(`[${inputIdx}:a]volume=${finalVolume.toFixed(2)},adelay=${delayMs}|${delayMs},apad=whole_dur=${duration}${effectLabel}`);
        
        // Mixa com o áudio anterior
        if (i === 0) {
          filterParts.push(`${currentLabel}${effectLabel}amix=inputs=2:duration=first${mixLabel}`);
        } else {
          filterParts.push(`${currentLabel}${effectLabel}amix=inputs=2:duration=first${mixLabel}`);
        }
        
        currentLabel = mixLabel;
        
        console.log(`   [${i + 1}] ${effect.keyword} @ ${effect.timestamp.toFixed(2)}s → vol original: ${effect.volume}, final: ${finalVolume.toFixed(2)}`);
      }
      
      // 🔊 V6.20: Normalização mais suave para não amplificar demais
      filterParts.push(`${currentLabel}dynaudnorm=p=0.7:s=3[sfx_final]`);
      
      const filterComplex = filterParts.join(';');
      const mixCmd = `ffmpeg -y ${inputs.join(' ')} -filter_complex "${filterComplex}" -map "[sfx_final]" -c:a libmp3lame -b:a 128k "${outputPath}" 2>&1`;
      
      console.log(`\n🔧 Executando mixagem...`);
      
      const result = execSync(mixCmd, { timeout: 60000 }).toString();
      
      // Limpa arquivo de silêncio temporário
      const silenceFile = outputPath.replace('.mp3', '_silence.wav');
      if (fs.existsSync(silenceFile)) {
        fs.unlinkSync(silenceFile);
      }
      
      if (fs.existsSync(outputPath) && fs.statSync(outputPath).size > 0) {
        const fileSize = fs.statSync(outputPath).size;
        console.log(`\n✅ Trilha de efeitos criada com sucesso!`);
        console.log(`📊 Tamanho: ${(fileSize / 1024).toFixed(2)} KB`);
        console.log(`🎵 ════════════════════════════════════════════\n`);
        
        return { success: true, outputPath: outputPath, hasEffects: true };
      } else {
        throw new Error('Arquivo de saída não foi criado');
      }
      
    } catch (e) {
      console.error(`❌ Erro ao criar trilha de efeitos: ${e.message}`);
      console.log(`🎵 ════════════════════════════════════════════\n`);
      
      return { success: false, outputPath: null, hasEffects: false, error: e.message };
    }
  }
}

// ──────────────────────────────────────────────────────────────────────
// CLASSE: SoundEffectsProcessor - Orquestrador principal
// ──────────────────────────────────────────────────────────────────────
class SoundEffectsProcessor {
  /**
   * Processa uma página e retorna informações sobre efeitos sonoros
   * @param {string} subtitlePath - Caminho da legenda
   * @param {string} outputDir - Diretório de saída
   * @param {number} numPagina - Número da página
   * @param {number} estimatedDuration - Duração estimada do vídeo
   * @returns {Object} - { hasEffects, effectsTrackPath, effects }
   */
  static process(subtitlePath, outputDir, numPagina, estimatedDuration = 60) {
    console.log(`\n🎬 ════════════════════════════════════════════`);
    console.log(`🎬 PROCESSADOR DE EFEITOS SONOROS - PÁGINA ${numPagina}`);
    console.log(`🎬 ════════════════════════════════════════════`);
    
    // Verifica se sistema está habilitado
    if (!SOUND_EFFECTS_CONFIG.enabled) {
      console.log(`⚠️ Sistema de efeitos sonoros desabilitado`);
      return { hasEffects: false, effectsTrackPath: null, effects: [] };
    }
    
    // Verifica se pasta de efeitos existe
    if (!fs.existsSync(SOUND_EFFECTS_CONFIG.basePath)) {
      console.warn(`⚠️ Pasta de efeitos não encontrada: ${SOUND_EFFECTS_CONFIG.basePath}`);
      return { hasEffects: false, effectsTrackPath: null, effects: [] };
    }
    
    // Parse da legenda
    const subtitleEntries = SubtitleParser.parse(subtitlePath);
    
    if (subtitleEntries.length === 0) {
      console.log(`⚠️ Nenhuma entrada de legenda encontrada`);
      return { hasEffects: false, effectsTrackPath: null, effects: [] };
    }
    
    // Detecta efeitos
    const effects = SoundEffectsDetector.detectEffects(subtitleEntries);
    
    if (effects.length === 0) {
      console.log(`ℹ️ Nenhum efeito sonoro detectado para esta página`);
      return { hasEffects: false, effectsTrackPath: null, effects: [] };
    }
    
    // Cria trilha de efeitos
    const effectsTrackPath = `${outputDir}/audio/temp/sfx_track_pag${numPagina}.mp3`;
    
    // Garante que o diretório existe
    const audioDir = `${outputDir}/audio/temp`;
    if (!fs.existsSync(audioDir)) {
      fs.mkdirSync(audioDir, { recursive: true });
    }
    
    const mixResult = SoundEffectsMixer.createEffectsTrack(effects, effectsTrackPath, estimatedDuration);
    
    if (mixResult.success) {
      console.log(`✅ Processamento de efeitos concluído com sucesso`);
      console.log(`🎬 ════════════════════════════════════════════\n`);
      
      return {
        hasEffects: true,
        effectsTrackPath: effectsTrackPath,
        effects: effects,
        effectsCount: effects.length
      };
    } else {
      console.warn(`⚠️ Falha ao criar trilha de efeitos: ${mixResult.error}`);
      console.log(`🎬 ════════════════════════════════════════════\n`);
      
      return { hasEffects: false, effectsTrackPath: null, effects: effects, error: mixResult.error };
    }
  }
  
  /**
   * Gera o comando FFmpeg modificado para incluir a trilha de efeitos
   * @param {string} originalAudioFilter - Filtro de áudio original
   * @param {string} effectsTrackPath - Caminho da trilha de efeitos
   * @param {number} sfxVolume - Volume dos efeitos (0-1)
   * @returns {Object} - { additionalInput, modifiedFilter }
   */
  static getModifiedAudioCommand(originalAudioFilter, effectsTrackPath, sfxVolume = 0.7) {
    if (!effectsTrackPath || !fs.existsSync(effectsTrackPath)) {
      return { additionalInput: '', modifiedFilter: originalAudioFilter, hasSfx: false };
    }
    
    // O filtro original termina com [a_out]
    // Precisamos interceptar e adicionar os efeitos
    const modifiedFilter = originalAudioFilter.replace(
      /\[a_out\]$/,
      `[a_pre_sfx];[a_pre_sfx][SFX_INPUT:a]amix=inputs=2:duration=first:weights=1 ${sfxVolume}[a_out]`
    );
    
    return {
      additionalInput: `-i "${effectsTrackPath}"`,
      modifiedFilter: modifiedFilter,
      hasSfx: true
    };
  }
}
// ======================================================================
// SEÇÃO 6: ✅ GERENCIADOR DE EFEITOS - V6.10 (COMPLETO)
// ======================================================================

// ──────────────────────────────────────────────────────────────────────
// CLASSE: EffectsManager - NOVO: Gerenciamento centralizado de efeitos
// ──────────────────────────────────────────────────────────────────────
class EffectsManager {
  constructor() {
    this.used = {
      movimentos: [],
      transicoes: [],
      blur: [],
      sharpen: [],
      vinheta: [],
      cores: [],
      ruido: []
    };
    
    this.currentIndices = {
      blur: 0,
      sharpen: 0,
      vinheta: 0,
      cores: 0,
      ruido: 0,
      transicoes: 0
    };
    
    this.memory = new MemorySystem();
  }
  
  // Obtém próximo efeito de uma categoria
  getNext(category) {
    const categoryMap = {
      'blur': BLUR_EFFECTS,
      'sharpen': SHARPEN_EFFECTS,
      'vinheta': VIGNETTE_EFFECTS,
      'cores': COLOR_EFFECTS,
      'ruido': NOISE_EFFECTS,
      'transicoes': TRANSITIONS
    };
    
    const effects = categoryMap[category];
    if (!effects || effects.length === 0) {
      return '';
    }
    
    // Rotação simples
    const index = this.currentIndices[category] || 0;
    const selected = effects[index % effects.length];
    
    this.currentIndices[category] = (index + 1) % effects.length;
    
    // Registra uso
    if (!this.used[category]) {
      this.used[category] = [];
    }
    this.used[category].push(selected);
    
    return selected;
  }
  
  // Reset de categoria específica
  reset(category) {
    if (this.used[category]) {
      this.used[category] = [];
    }
    if (this.currentIndices[category] !== undefined) {
      this.currentIndices[category] = 0;
    }
  }
  
  // Reset completo
  resetAll() {
    for (const key in this.used) {
      this.used[key] = [];
    }
    for (const key in this.currentIndices) {
      this.currentIndices[key] = 0;
    }
    this.memory.reset();
  }
}

// ──────────────────────────────────────────────────────────────────────
// CLASSE: ContextualSelector V5.0 - INTELIGENTE COM TAGS E CONTEXTO
// ──────────────────────────────────────────────────────────────────────
class ContextualSelector {
  constructor(effectsManager) {
    this.effects = effectsManager;
    this.patterns = CONTEXTUAL_PATTERNS;
    this.memory = effectsManager.memory;
  }
  
  select(narrationText, dimensions, manualEffect = null, imagePath = null) {
    // Manual override
    if (manualEffect) {
      return {
        filtro: manualEffect,
        nome: "Manual Override",
        intensidade: "PERSONALIZADO",
        tipo: "manual"
      };
    }
    
    const text = (narrationText || "").toLowerCase();
    
    // PASSO 1: Prioriza detecção contextual
    const contextualMatch = this._detectContext(text);
    
    if (contextualMatch && contextualMatch.forceEffect) {
      const movement = this._selectByEffectType(contextualMatch.effectType);
      
      if (movement) {
        this.memory.record('atmosphere', contextualMatch.type);
        this.memory.record('movementDirection', contextualMatch.effectType);
        
        console.log(`🎯 Efeito contextual forçado: ${contextualMatch.name}`);
        
        return {
          filtro: movement.filter,
          nome: `${movement.desc} (Contextual: ${contextualMatch.name})`,
          intensidade: contextualMatch.intensity,
          tipo: contextualMatch.type,
          contextDetected: true
        };
      }
    }
    
    // PASSO 2: Análise de conteúdo da imagem
    if (imagePath && GLOBAL_CONFIG.contentAnalysis.enabled) {
      const analysis = ContentAnalyzer.getAdaptiveAdjustments(imagePath);
      this.memory.record('brightness', analysis.brightness);
      
      if (analysis.brightness < 0.3) {
        console.log(`🌙 Imagem escura detectada, usando movimento lento`);
        return this._selectVerticalSlow();
      }
    }
    
    // PASSO 3: Vertical images (manhwa) - SEMPRE prioriza vertical pan
    if (dimensions.ehAlongado) {
      console.log(`📜 Imagem alongada detectada (Manhwa), usando vertical pan`);
      return this._selectVertical();
    }
    
    // PASSO 4: Fallback com forte viés para vertical
    console.log(`🔄 Seleção por prioridade com viés vertical`);
    return this._selectByPriorityWithVerticalBias();
  }
  
  // ═══ NOVO: Detecta contexto da narração (ordem de especificidade) ═══
  _detectContext(text) {
    // Ordena patterns por especificidade (mais específico primeiro)
    const orderedPatterns = [
      // Ação (mais específico primeiro)
      'action_heavy', 'action_medium', 'action_light',
      // Emocionais dramáticos
      'suspense', 'dramatic', 'romance',
      // Movimento
      'speed', 'battle',
      // Memória e atmosfera
      'memory', 'tension', 'mystery',
      // Leitura e diálogo (menos específico)
      'reading_slow', 'narration', 'calm', 'dialogue_calm'
    ];
    
    for (const key of orderedPatterns) {
      const pattern = this.patterns[key];
      if (pattern && text.match(pattern.regex)) {
        console.log(`✅ Contexto detectado: ${pattern.name}`);
        return pattern;
      }
    }
    
    console.log(`ℹ️ Nenhum contexto específico detectado`);
    return null;
  }
  
  // ═══ NOVO: Seleciona movimento por tipo de efeito (baseado em tags) ═══
  _selectByEffectType(effectType) {
    const effectConfig = EFFECT_TYPE_MAP[effectType];
    if (!effectConfig) {
      console.log(`⚠️ Effect type não encontrado: ${effectType}`);
      return null;
    }
    
    // Filtra movimentos que têm as tags necessárias
    const candidates = MOVEMENTS.filter(m => {
      if (!m.tags) return false;
      
      // Deve ter pelo menos uma tag em comum
      const hasTag = effectConfig.tags.some(tag => m.tags.includes(tag));
      
      // Deve ter readability mínima
      const hasReadability = !m.readability || m.readability >= (effectConfig.minReadability || 0);
      
      return hasTag && hasReadability;
    });
    
    if (candidates.length === 0) {
      console.log(`⚠️ Nenhum movimento encontrado para ${effectType}, usando fallback`);
      return null;
    }
    
    console.log(`📊 ${candidates.length} candidatos encontrados para ${effectType}`);
    
    // Filtra já usados
    const used = this.effects.used.movimentos || [];
    const available = candidates.filter(m => !used.includes(m.filter));
    
    if (available.length === 0) {
      console.log(`🔄 Resetando categoria ${effectType} (todos já usados)`);
      // Reset apenas desta categoria
      const candidateFilters = candidates.map(c => c.filter);
      this.effects.used.movimentos = used.filter(f => !candidateFilters.includes(f));
    }
    
    const finalCandidates = available.length > 0 ? available : candidates;
    const selected = finalCandidates[Math.floor(Math.random() * finalCandidates.length)];
    
    this.effects.used.movimentos.push(selected.filter);
    console.log(`✅ Movimento selecionado: ${selected.desc}`);
    
    return selected;
  }
  
  // ═══ Seleciona vertical pan lento (para imagens escuras) ═══
  _selectVerticalSlow() {
    const slowMovements = MOVEMENTS.filter(m => 
      m.tags && m.tags.includes('vertical') && m.tags.includes('slow')
    );
    
    if (slowMovements.length === 0) {
      console.log(`⚠️ Nenhum movimento vertical lento encontrado, usando fallback`);
      return this._selectVertical();
    }
    
    const used = this.effects.used.movimentos || [];
    const available = slowMovements.filter(m => !used.includes(m.filter));
    
    if (available.length === 0) {
      const slowFilters = slowMovements.map(s => s.filter);
      this.effects.used.movimentos = used.filter(f => !slowFilters.includes(f));
    }
    
    const finalCandidates = available.length > 0 ? available : slowMovements;
    const selected = finalCandidates[Math.floor(Math.random() * finalCandidates.length)];
    
    this.effects.used.movimentos.push(selected.filter);
    
    return {
      filtro: selected.filter,
      nome: selected.desc + " (Adaptado Escuro)",
      intensidade: "SUAVE",
      tipo: "vertical_adaptado_escuro"
    };
  }
  
  // ═══ Seleciona vertical pan (para manhwas) ═══
  _selectVertical() {
    // Filtra movimentos verticais com alta legibilidade
    const verticals = MOVEMENTS.filter(m => 
      m.tags && m.tags.includes('vertical') && m.readability >= 8
    );
    
    if (verticals.length === 0) {
      console.log(`⚠️ Nenhum movimento vertical encontrado, usando prioridade 1`);
      // Fallback para movimentos com prioridade 1
      const priority1 = MOVEMENTS.filter(m => m.priority === 1);
      const selected = priority1[Math.floor(Math.random() * priority1.length)];
      this.effects.used.movimentos.push(selected.filter);
      
      return {
        filtro: selected.filter,
        nome: selected.desc,
        intensidade: "PADRÃO",
        tipo: "vertical"
      };
    }
    
    const used = this.effects.used.movimentos || [];
    const available = verticals.filter(m => !used.includes(m.filter));
    
    if (available.length === 0) {
      console.log(`🔄 Resetando movimentos verticais (todos já usados)`);
      const verticalFilters = verticals.map(v => v.filter);
      this.effects.used.movimentos = used.filter(f => !verticalFilters.includes(f));
    }
    
    const finalCandidates = available.length > 0 ? available : verticals;
    const selected = finalCandidates[Math.floor(Math.random() * finalCandidates.length)];
    
    this.effects.used.movimentos.push(selected.filter);
    this.memory.record('movementDirection', 'vertical');
    
    return {
      filtro: selected.filter,
      nome: selected.desc + " (Manhwa)",
      intensidade: "ADAPTATIVO",
      tipo: "vertical"
    };
  }
  
  // ═══ Seleção por prioridade com forte viés para vertical ═══
  _selectByPriorityWithVerticalBias() {
    const rand = Math.random() * 100;
    
    let targetPriority;
    // AUMENTA chance de vertical (de 40% para 60%)
    if (rand < 60) {
      targetPriority = 1; // 60% - Vertical Pans
    } else if (rand < 80) {
      targetPriority = 2; // 20% - Zoom Facial
    } else if (rand < 95) {
      targetPriority = 3; // 15% - Ken Burns
    } else {
      targetPriority = 4; // 5% - Especiais (inclui shake, mas raro)
    }
    
    const priorityMovements = MOVEMENTS.filter(m => m.priority === targetPriority);
    
    // Se prioridade 4, filtra APENAS não-shake (shake só com contexto)
    let filteredMovements = priorityMovements;
    if (targetPriority === 4) {
      filteredMovements = priorityMovements.filter(m => 
        !m.tags || !m.tags.includes('shake')
      );
      
      console.log(`🚫 Prioridade 4: Filtrando shake (${priorityMovements.length} -> ${filteredMovements.length})`);
      
      if (filteredMovements.length === 0) {
        console.log(`⚠️ Nenhum movimento especial sem shake, voltando para vertical`);
        // Se não sobrou nada, volta para prioridade 1 (vertical)
        return this._selectVertical();
      }
    }
    
    const priorityFilters = filteredMovements.map(m => m.filter);
    const used = this.effects.used.movimentos || [];
    const available = priorityFilters.filter(f => !used.includes(f));
    
    if (available.length === 0) {
      console.log(`🔄 Resetando prioridade ${targetPriority} (todos já usados)`);
      this.effects.used.movimentos = used.filter(m => !priorityFilters.includes(m));
    }
    
    const finalCandidates = available.length > 0 ? available : priorityFilters;
    const selected = finalCandidates[Math.floor(Math.random() * finalCandidates.length)];
    
    this.effects.used.movimentos.push(selected);
    
    const movement = filteredMovements.find(m => m.filter === selected);
    this.memory.record('movementDirection', this._getTypeName(targetPriority));
    
    return {
      filtro: selected,
      nome: movement ? movement.desc : "Movimento Priorizado",
      intensidade: this._getIntensityName(targetPriority),
      tipo: this._getTypeName(targetPriority)
    };
  }
  
  _getIntensityName(priority) {
    const names = {
      1: "VERTICAL",
      2: "FOCAL",
      3: "KEN BURNS",
      4: "ESPECIAL"
    };
    return names[priority] || "PADRÃO";
  }
  
  _getTypeName(priority) {
    const types = {
      1: "vertical_pan",
      2: "zoom_facial",
      3: "ken_burns",
      4: "especial"
    };
    return types[priority] || "padrao";
  }
}
// ──────────────────────────────────────────────────────────────────────
// FUNÇÃO: ensureFolders - Garante estrutura de pastas
// ──────────────────────────────────────────────────────────────────────
function ensureFolders(pastaDestino) {
  const fs = require('fs');
  
  const pastasNecessarias = [
    pastaDestino,
    `${pastaDestino}/videos`,
    `${pastaDestino}/videos/temp`,
    `${pastaDestino}/audio`,
    `${pastaDestino}/audio/temp`,
    `${pastaDestino}/reports`
  ];
  
  for (const pasta of pastasNecessarias) {
    try {
      if (!fs.existsSync(pasta)) {
        fs.mkdirSync(pasta, { recursive: true });
        console.log(`📁 Pasta criada: ${pasta}`);
      }
    } catch (e) {
      console.warn(`⚠️ Erro ao criar pasta ${pasta}: ${e.message}`);
    }
  }
}


// ──────────────────────────────────────────────────────────────────────
// CLASSE: MissingPagesHandler V6.29 - Verifica apenas intervalo até último vídeo
// ──────────────────────────────────────────────────────────────────────
class MissingPagesHandler {

  static checkMissingPreviousPages(currentPage, processedPages, pastaRaizObra, maxPagesToInclude = 5) {
    console.log(`\n🔍 ════════════════════════════════════════════`);
    console.log(`🔍 VERIFICANDO PÁGINAS ANTERIORES FALTANTES V6.29`);
    console.log(`🔍 ════════════════════════════════════════════`);
    console.log(`📄 Página atual: ${currentPage}`);
    
    const missingPages = [];
    const imagePaths = [];
    
    for (let page = currentPage - 1; page >= 1 && missingPages.length < maxPagesToInclude; page--) {
      
      // 🔥 V6.29: Se encontrar vídeo, PARA - páginas anteriores já foram incorporadas
      if (processedPages && processedPages.has(page)) {
        console.log(`   ✅ Página ${page} já tem vídeo - PARANDO VERIFICAÇÃO`);
        break;
      }
      
      const imgCandidates = [
        `${pastaRaizObra}/${page}_editado.jpg`,
        `${pastaRaizObra}/i/${page}.jpg`,
        `${pastaRaizObra}/${page}.jpg`,
        `${pastaRaizObra}/images/original/${page}.jpg`
      ];
      
      let foundImage = null;
      for (const imgPath of imgCandidates) {
        if (fs.existsSync(imgPath)) {
          foundImage = imgPath;
          break;
        }
      }
      
      if (foundImage) {
        missingPages.unshift(page);
        imagePaths.unshift(foundImage);
        console.log(`   ⚠️ Página ${page} sem vídeo - Será incluída`);
      } else {
        console.log(`   ❌ Página ${page} sem vídeo - Imagem NÃO encontrada`);
      }
    }
    
    const result = {
      hasMissing: missingPages.length > 0,
      missingPages: missingPages,
      imagePaths: imagePaths,
      count: missingPages.length
    };
    
    if (result.hasMissing) {
      console.log(`\n📊 RESULTADO:`);
      console.log(`   Páginas a incluir: [${missingPages.join(', ')}]`);
      console.log(`   Total: ${missingPages.length} página(s)`);
    } else {
      console.log(`\n✅ Todas as páginas anteriores já têm vídeo`);
    }
    console.log(`🔍 ════════════════════════════════════════════\n`);
    
    return result;
  }
  
  static calculateDurations(totalPages, totalDuration, currentPageWeight = 0.6) {
    if (totalPages <= 1) {
      return { missingPageDuration: 0, currentPageDuration: totalDuration };
    }
    const missingPagesCount = totalPages - 1;
    const missingPagesTotalWeight = 1 - currentPageWeight;
    const missingPageDuration = (totalDuration * missingPagesTotalWeight) / missingPagesCount;
    const currentPageDuration = totalDuration * currentPageWeight;
    
    console.log(`📊 Cálculo de durações:`);
    console.log(`   Total de páginas: ${totalPages}`);
    console.log(`   Duração total: ${totalDuration.toFixed(2)}s`);
    console.log(`   Duração por página faltante: ${missingPageDuration.toFixed(2)}s`);
    console.log(`   Duração da página atual: ${currentPageDuration.toFixed(2)}s`);
    
    return { missingPageDuration, currentPageDuration };
  }
  
  static buildSlideshowFilter(imagePaths, durations, transition = 'fade', transitionDuration = 0.5) {
    if (!imagePaths || imagePaths.length === 0) {
      return { inputs: '', filterComplex: '', outputLabel: '[v_final]', hasSlideshow: false };
    }
    if (imagePaths.length === 1) {
      return { inputs: `-loop 1 -i "${imagePaths[0]}"`, filterComplex: '', outputLabel: '1:v', hasSlideshow: false };
    }
    
    console.log(`\n🎬 ════════════════════════════════════════════`);
    console.log(`🎬 CONSTRUINDO SLIDESHOW COM ${imagePaths.length} IMAGENS`);
    console.log(`🎬 ════════════════════════════════════════════`);
    
    let inputs = [];
    let filterParts = [];
    
    for (let i = 0; i < imagePaths.length; i++) {
      const duration = durations[i] || 3;
      inputs.push(`-loop 1 -t ${duration + transitionDuration} -i "${imagePaths[i]}"`);
      filterParts.push(`[${i + 1}:v]scale=${GLOBAL_CONFIG.outputFormat.workingWidth}:${GLOBAL_CONFIG.outputFormat.workingHeight}:force_original_aspect_ratio=decrease,pad=${GLOBAL_CONFIG.outputFormat.workingWidth}:${GLOBAL_CONFIG.outputFormat.workingHeight}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=${GLOBAL_CONFIG.outputFormat.fps}[img${i}]`);
      console.log(`   [${i + 1}] ${imagePaths[i].split('/').pop()} - ${duration.toFixed(2)}s`);
    }
    
    let currentLabel = '[img0]';
    for (let i = 1; i < imagePaths.length; i++) {
      const offset = durations.slice(0, i).reduce((a, b) => a + b, 0) - (transitionDuration * (i - 1));
      const nextLabel = i === imagePaths.length - 1 ? '[v_slideshow]' : `[slide${i}]`;
      filterParts.push(`${currentLabel}[img${i}]xfade=transition=${transition}:duration=${transitionDuration}:offset=${offset.toFixed(2)}${nextLabel}`);
      currentLabel = nextLabel;
    }
    
    console.log(`   Transição: ${transition} (${transitionDuration}s)`);
    console.log(`🎬 ════════════════════════════════════════════\n`);
    
    return { inputs: inputs.join(' '), filterComplex: filterParts.join(';'), outputLabel: '[v_slideshow]', hasSlideshow: true };
  }
  
  static modifyCommandsForMissingPages(originalCommands, missingPagesInfo, currentImagePath, audioDuration) {
    if (!missingPagesInfo.hasMissing) {
      return { ...originalCommands, hasMissingPages: false, missingPagesIncluded: [] };
    }
    
    console.log(`\n🔧 ════════════════════════════════════════════`);
    console.log(`🔧 MODIFICANDO COMANDO PARA INCLUIR PÁGINAS FALTANTES`);
    console.log(`🔧 ════════════════════════════════════════════`);
    
    const allImages = [...missingPagesInfo.imagePaths, currentImagePath];
    const totalPages = allImages.length;
    const durationInfo = this.calculateDurations(totalPages, audioDuration);
    const durations = [...Array(missingPagesInfo.count).fill(durationInfo.missingPageDuration), durationInfo.currentPageDuration];
    const slideshowFilter = this.buildSlideshowFilter(allImages, durations, 'fade', 0.5);
    
    console.log(`📊 Resumo:`);
    console.log(`   Páginas anteriores incluídas: ${missingPagesInfo.missingPages.join(', ')}`);
    console.log(`   Total de imagens no vídeo: ${allImages.length}`);
    console.log(`🔧 ════════════════════════════════════════════\n`);
    
    return {
      ...originalCommands,
      hasMissingPages: true,
      missingPagesIncluded: missingPagesInfo.missingPages,
      slideshowInputs: slideshowFilter.inputs,
      slideshowFilter: slideshowFilter.filterComplex,
      slideshowOutputLabel: slideshowFilter.outputLabel,
      hasSlideshow: slideshowFilter.hasSlideshow,
      allImagePaths: allImages,
      imageDurations: durations
    };
  }
}


// ──────────────────────────────────────────────────────────────────────
// CLASSE: AudioProcessor V5.0 - NOVO: Processamento Profissional
// ──────────────────────────────────────────────────────────────────────
class AudioProcessor {
  // Normaliza áudio para padrão LUFS
  static normalizeAudio(inputPath, outputPath) {
    if (!GLOBAL_CONFIG.audio.normalization.enabled) {
      return { success: true, normalized: false };
    }
    
    try {
      const targetLUFS = GLOBAL_CONFIG.audio.normalization.targetLUFS;
      const truePeak = GLOBAL_CONFIG.audio.normalization.truePeak;
      
      const cmd = `ffmpeg -y -i "${inputPath}" -af "loudnorm=I=${targetLUFS}:TP=${truePeak}:LRA=11" "${outputPath}"`;
      execSync(cmd, { timeout: GLOBAL_CONFIG.timeouts.audioAnalysis });
      
      return { success: true, normalized: true };
    } catch(e) {
      return { success: false, error: e.message };
    }
  }
  
  // Aplica ducking (abaixa música quando há narração)
  static buildDuckingFilter(narrationPath, musicPath) {
    if (!GLOBAL_CONFIG.audio.ducking.enabled) {
      return null;
    }
    
    const musicVol = GLOBAL_CONFIG.audio.musicVolume;
    const duckVol = GLOBAL_CONFIG.audio.ducking.musicDuringNarration;
    const duckSpeed = GLOBAL_CONFIG.audio.ducking.duckingSpeed;
    
    // Usa sidechaincompress para ducking automático
    return `[1:a]asplit=2[music][music_side];[0:a]asplit=2[narr][narr_side];[music][narr_side]sidechaincompress=threshold=0.02:ratio=4:attack=${duckSpeed}:release=${duckSpeed * 2}:makeup=2[music_ducked];[narr][music_ducked]amix=inputs=2:duration=first[a_out]`;
  }
  
  // Aplica compressão e de-esser
  static buildEnhancementFilter() {
    if (!GLOBAL_CONFIG.audio.enhancement.compression.enabled) {
      return "";
    }
    
    const comp = GLOBAL_CONFIG.audio.enhancement.compression;
    let filters = [];
    
    // Compressor
    filters.push(`acompressor=threshold=${comp.threshold}dB:ratio=${comp.ratio}:attack=${comp.attack}:release=${comp.release}`);
    
    // De-esser (remove sibilância)
    if (GLOBAL_CONFIG.audio.enhancement.deEsser) {
      filters.push("deesser=i=0.1:m=0.5:f=0.5:s=o");
    }
    
    // Noise reduction suave
    if (GLOBAL_CONFIG.audio.enhancement.noiseReduction) {
      const noiseAmount = GLOBAL_CONFIG.audio.enhancement.noiseAmount;
      filters.push(`afftdn=nr=${noiseAmount}:nf=-25`);
    }
    
    return filters.join(",");
  }
}

// ──────────────────────────────────────────────────────────────────────
// CLASSE: SubtitleProcessor V5.0 - NOVO: Legendas Avançadas
// ──────────────────────────────────────────────────────────────────────
class SubtitleProcessor {
  // Detecta contexto da narração para aplicar estilo apropriado
  static detectContext(text) {
    const lower = text.toLowerCase();
    
    if (lower.includes('!') || /grito|berro|alto/i.test(text)) {
      return 'shout';
    }
    if (lower.includes('...') || /sussurr|baixo|murmur/i.test(text)) {
      return 'whisper';
    }
    if (lower.includes('*') || /pensa|imagin|reflet/i.test(text)) {
      return 'thought';
    }
    if (lower.includes('!!') || /important|crítico|vital/i.test(text)) {
      return 'emphasis';
    }
    
    return 'normal';
  }
  
  // Constrói estilo de legenda baseado no contexto
  static buildContextualStyle(text, baseStyle) {
    const context = this.detectContext(text);
    const contextStyle = GLOBAL_CONFIG.subtitle.contextStyles[context];
    
    if (!contextStyle) return baseStyle;
    
    // Merge base style com context style
    let style = baseStyle || GLOBAL_CONFIG.subtitle.defaultStyle;
    
    // Substitui parâmetros do contexto
    const params = contextStyle.split(',');
    for (const param of params) {
      const [key, value] = param.split('=');
      const regex = new RegExp(`${key}=[^,]+`, 'g');
      if (style.match(regex)) {
        style = style.replace(regex, `${key}=${value}`);
      } else {
        style += `,${key}=${value}`;
      }
    }
    
    return style;
  }
  
  // Ajusta outline baseado em análise de fundo
  static getAdaptiveOutline(imagePath, baseOutline = 2) {
    if (!GLOBAL_CONFIG.subtitle.outlineAdaptive.enabled) {
      return baseOutline;
    }
    
    try {
      const brightness = ContentAnalyzer.analyzeBrightness(imagePath);
      
      const min = GLOBAL_CONFIG.subtitle.outlineAdaptive.minOutline;
      const max = GLOBAL_CONFIG.subtitle.outlineAdaptive.maxOutline;
      
      // Quanto mais claro o fundo, maior o outline
      const outline = min + (max - min) * brightness;
      return Math.round(outline);
    } catch(e) {
      return baseOutline;
    }
  }
  
 // Adiciona animações de fade e POP-IN (Kinetic) para gritos/impacto
  static addFadeAnimations(subtitleContent) {
    if (!GLOBAL_CONFIG.subtitle.animations.enabled) {
      return subtitleContent;
    }
    
    const fadeIn = GLOBAL_CONFIG.subtitle.animations.fadeInDuration;
    const fadeOut = GLOBAL_CONFIG.subtitle.animations.fadeOutDuration;
    
    // Parse SRT e adiciona tags ASS
    const lines = subtitleContent.split('\\n');
    let result = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Detecta linha de tempo (formato: 00:00:01,000 --> 00:00:03,000)
      if (line.includes('-->')) {
        const [start, end] = line.split('-->').map(t => t.trim());
        
        // Calcula tempo de fade
        const startMs = this._timeToMs(start);
        const endMs = this._timeToMs(end);
        const duration = endMs - startMs;
        const fadeInMs = Math.min(fadeIn * 1000, duration / 4);
        const fadeOutMs = Math.min(fadeOut * 1000, duration / 4);
        
        result.push(line);
        
        // Verifica a próxima linha (o texto) para decidir a animação
        if (i + 1 < lines.length) {
          const textLine = lines[i + 1];
          let animTags = `{\\fad(${fadeInMs},${fadeOutMs})}`; // Tag base (Fade)
          
          // 🔥 LÓGICA KINETIC: Se tiver "!" ou for todo MAIÚSCULO -> Aplica POP-IN (Zoom rápido)
          const isShout = textLine.includes('!') || (textLine === textLine.toUpperCase() && textLine.length > 3);
          
          if (isShout) {
            // \fscx80\fscy80 = Começa com 80% do tamanho
            // \t(0,150,...) = Em 150ms, transforma para...
            // \fscx110\fscy110 = ...110% do tamanho (Leve exagero para impacto)
            animTags = `{\\fad(80,150)\\fscx80\\fscy80\\t(0,150,\\fscx110\\fscy110)}`;
          }
          
          const animatedText = `${animTags}${textLine}`;
          result.push(animatedText);
          i++; // Pula a linha de texto original pois já processamos
          continue;
        }
      }
      
      result.push(line);
    }
    
    return result.join('\\n');
  }
  
  static _timeToMs(timeStr) {
    const [time, ms] = timeStr.split(',');
    const [h, m, s] = time.split(':').map(n => parseInt(n));
    return (h * 3600 + m * 60 + s) * 1000 + parseInt(ms || 0);
  }
}
  
// ──────────────────────────────────────────────────────────────────────
// CLASSE: FileValidator (mantida do original)
// ──────────────────────────────────────────────────────────────────────
class FileValidator {
  static isValid(path) {
    try {
      if (!fs.existsSync(path)) return false;
      const stats = fs.statSync(path);
      return stats.size > 0;
    } catch(e) {
      return false;
    }
  }
  
  static validate(files) {
    const errors = [];
    
    for (const [name, path] of Object.entries(files)) {
      if (!this.isValid(path)) {
        errors.push(`${name} não encontrado: ${path}`);
      }
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  static ensureDirectory(path) {
    try {
      if (!fs.existsSync(path)) {
        fs.mkdirSync(path, { recursive: true });
      }
      return true;
    } catch(e) {
      return false;
    }
  }
}

// ──────────────────────────────────────────────────────────────────────
// CLASSE: ImageProcessor V5.0 - Com Análise de Conteúdo
// ──────────────────────────────────────────────────────────────────────
class ImageProcessor {
  static detectDimensions(imagePath) {
    try {
      if (!FileValidator.isValid(imagePath)) {
        return { largura: 1920, altura: 1080, ratio: 1.78, ehAlongado: false };
      }
      
      const probe = execSync(
        `ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 \"${imagePath}\" 2>/dev/null || echo \"1920x1080\"`
      ).toString().trim();
      
      const [largura, altura] = probe.split('x').map(n => parseInt(n) || 1920);
      const ratio = largura / altura;
      const ehAlongado = altura > (largura * 1.5);
      
      return { largura, altura, ratio, ehAlongado };
    } catch(e) {
      return { largura: 1920, altura: 1080, ratio: 1.78, ehAlongado: false };
    }
  }
  
  static applyVisualEffect(inputPath, outputPath, fileName) {
    // Seleciona filtro baseado em hash do nome do arquivo
    let hash = 0;
    for (let i = 0; i < fileName.length; i++) {
      hash = ((hash << 5) - hash) + fileName.charCodeAt(i);
      hash |= 0;
    }
    
    const index = Math.abs(hash) % VISUAL_FILTERS.length;
    const selectedFilter = VISUAL_FILTERS[index];
    const filter = selectedFilter.filter;
    
    // Análise de conteúdo para ajustes adaptativos
    let adaptiveFilter = filter;
    if (GLOBAL_CONFIG.contentAnalysis.enabled && GLOBAL_CONFIG.contentAnalysis.adaptiveEffects.enabled) {
      const analysis = ContentAnalyzer.getAdaptiveAdjustments(inputPath);
      
      // Ajusta filtro baseado na análise
      if (analysis.brightnessAdjust !== 0) {
        adaptiveFilter = `${filter},eq=brightness=${analysis.brightnessAdjust}`;
      }
      if (analysis.contrastAdjust !== 1.0) {
        adaptiveFilter = `${adaptiveFilter},eq=contrast=${analysis.contrastAdjust}`;
      }
    }
    
    const filterType = (selectedFilter.name === "White Border") ? "-vf" : "-filter_complex";
    
    const cmd = `ffmpeg -y -i \"${inputPath}\" ${filterType} \"${adaptiveFilter}\" \"${outputPath}\"`;
    
    try {
      execSync(cmd, { timeout: GLOBAL_CONFIG.timeouts.imageProcessing });
      return {
        success: FileValidator.isValid(outputPath),
        filterName: selectedFilter.name,
        readability: selectedFilter.readability || 10
      };
    } catch(e) {
      return { success: false, error: e.message };
    }
  }
}

// ──────────────────────────────────────────────────────────────────────
// CLASSE: CommandBuilder V6.10 - 🔥 FIX CRÍTICO: Escape Correto ASS
// ──────────────────────────────────────────────────────────────────────
class CommandBuilder {
  static escapeBash(str) {
    if (!str) return '';
    return str.replace(/'/g, "'\\''").replace(/"/g, '\\"').replace(/`/g, '\\`');
  }
  
  // 🔥 NOVO: Escape especial para paths dentro de filtros FFmpeg
  static escapeFFmpegPath(path) {
    if (!path) return '';
    // No filtro, escapa ':' e '\' 
    return path.replace(/\\/g, '\\\\\\\\').replace(/:/g, '\\\\:');
  }
  
  static buildFilterChain(effects, movement) {
    const filters = [
      // 🔥 FIX V6.15: Usa force_original_aspect_ratio para imagens verticais (manhwa)
      `scale=${GLOBAL_CONFIG.outputFormat.workingWidth}:${GLOBAL_CONFIG.outputFormat.workingHeight}:force_original_aspect_ratio=decrease`,
      `pad=${GLOBAL_CONFIG.outputFormat.workingWidth}:${GLOBAL_CONFIG.outputFormat.workingHeight}:(ow-iw)/2:(oh-ih)/2:color=black`,
      movement,
      effects.getNext('blur'),
      effects.getNext('sharpen'),
      effects.getNext('vinheta'),
      effects.getNext('cores'),
      effects.getNext('ruido'),
      "format=yuv420p"
    ];
    
    return filters.join(",");
  }
  
  static buildWatermark() {
    return `drawtext=text='${this.escapeBash(GLOBAL_CONFIG.watermark)}':fontcolor=white@0.5:fontsize=24:x=w-tw-30:y=30:shadowcolor=black@0.5:shadowx=2:shadowy=2`;
  }
  
  static buildFooter() {
    return `drawbox=x=0:y=h-6:w=iw:h=6:color=red@0.8:t=fill`;
  }
  
  static buildSubtitleStyle(rawStyle, narrationText, imagePath) {
    let style = SubtitleProcessor.buildContextualStyle(narrationText || "", rawStyle);
    
    if (imagePath) {
      const outline = SubtitleProcessor.getAdaptiveOutline(imagePath);
      style = style.replace(/Outline=\d+/, `Outline=${outline}`);
    }
    
    style = style.replace(/Fontsize=\d+/, "Fontsize=14");
    style = style.replace(/MarginV=\d+/, "MarginV=25");
    style = style.replace(/BorderStyle=\d+/, "BorderStyle=1");
    style = style.replace(/BackColour=&H\w+/, "BackColour=&H00000000");
    
    return `force_style='${this.escapeBash(style)}'`;
  }
  
  static buildAudioFilter(narrationPath, trilhaPath, duration) {
    const musicVol = GLOBAL_CONFIG.audio.musicVolume;
    const fadeIn = GLOBAL_CONFIG.audio.fadeInDuration;
    const fadeOut = GLOBAL_CONFIG.audio.fadeOutDuration;
    
    const enhancement = AudioProcessor.buildEnhancementFilter();
    
    if (GLOBAL_CONFIG.audio.ducking.enabled) {
      const duckingFilter = AudioProcessor.buildDuckingFilter(narrationPath, trilhaPath);
      if (duckingFilter) {
        return duckingFilter;
      }
    }
    
    return `[0:a]${enhancement ? enhancement + ',' : ''}volume=1.0[a_narr];[1:a]afade=t=in:st=0:d=${fadeIn},volume=${GLOBAL_CONFIG.audio.musicVolume},afade=t=out:st=$((${duration}-${fadeOut})):d=${fadeOut},aloop=loop=-1:size=2e+09[a_music];[a_narr][a_music]amix=inputs=2:duration=first:dropout_transition=2[a_out]`;
  }
  
  static buildCommand(params) {
    const {
  folderPath, numPagina, imagePath, subtitlePath, subtitleStyle,
  audioFinalPath, audioFormat, trilhaPath, memePath, outputPath,
  filterChain, transitionEffect, narrationText,
  pastaDestinoFinal, soundEffectsPath  // ← ADICIONE AQUI
} = params;
    
    // Pasta temporária
    const pastaTemp = `${pastaDestinoFinal}/videos/temp`;
    const mkdirCmd = `mkdir -p "${pastaTemp}"`;

    // Arquivos temporários
    const videoBaseTemp = `${pastaTemp}/temp_base_pag_${numPagina}.mp4`;
    const memeNormalizado = `${pastaTemp}/meme_norm_${numPagina}.mp4`;
    const videoComTransicaoInicio = `${pastaTemp}/temp_trans_inicio_${numPagina}.mp4`;
    
    const watermark = this.buildWatermark();
    const footer = this.buildFooter();
    const subStyle = this.buildSubtitleStyle(subtitleStyle, narrationText, imagePath);
    
    // Validação de áudio simplificada
    const audioMergeCmd = `ls "${audioFinalPath}" > /dev/null`;
    
    // 🔥 FIX CRÍTICO V6.9: Detecção de formato de áudio
    let audioInputFlags = '';
    
    if (audioFormat === 'lpcm') {
      // PCM raw precisa dos parâmetros de formato
      audioInputFlags = `-f s16le -ar ${GLOBAL_CONFIG.audio.sampleRate} -ac ${GLOBAL_CONFIG.audio.channels}`;
      console.log(`🎵 Formato detectado: LPCM (raw PCM) - usando flags: ${audioInputFlags}`);
    } else {
      // MP3 e outros formatos não precisam de flags especiais
      audioInputFlags = '';
      console.log(`🎵 Formato detectado: ${audioFormat.toUpperCase()} - sem flags de formato`);
    }
    
    // ═══════════════════════════════════════════════════════════════════════
    // 🔥 V6.20 FIX: ESCAPE CORRETO PARA LEGENDAS ASS/SRT - SINCRONIZAÇÃO
    // ═══════════════════════════════════════════════════════════════════════
    let subtitleFilter = '';
    
    if (subtitlePath.endsWith('.ass')) {
        // 🔥 FIX: Para ASS, usa filtro 'ass' que preserva timing e estilos karaoke
        // Escapa apenas os caracteres problemáticos para FFmpeg
        const escapedPath = subtitlePath
            .replace(/\\/g, '/')
            .replace(/:/g, '\\\\:')
            .replace(/'/g, "'\\''");
        
        subtitleFilter = `ass='${escapedPath}'`;
        console.log(`📝 V6.20: Usando legenda ASS via filtro 'ass': ${subtitlePath}`);
    } else {
        // Para SRT, usa subtitles com estilo
        const escapedPath = subtitlePath
            .replace(/\\/g, '/')
            .replace(/:/g, '\\\\:')
            .replace(/'/g, "'\\''");
        
        subtitleFilter = `subtitles='${escapedPath}':${subStyle}`;
        console.log(`📝 V6.20: Usando legenda SRT: ${subtitlePath}`);
    }
    // ═══════════════════════════════════════════════════════════════════════
    // ═══════════════════════════════════════════════════════════════════════
    // 🔥 V6.21: SUPORTE A MÚLTIPLAS IMAGENS (PÁGINAS ANTERIORES FALTANTES)
    // ═══════════════════════════════════════════════════════════════════════
    let filterComplexBase;
    let videoInputCmd;
    
    if (params.missingPagesInfo && params.missingPagesInfo.hasMissing) {
      // Modo slideshow: múltiplas imagens (páginas faltantes + atual)
      const allImages = [...params.missingPagesInfo.imagePaths, imagePath];
      const durations = params.missingPagesInfo.imageDurations || [];
      const transitionDuration = 0.5;
      
      console.log(`🎬 Modo SLIDESHOW ativado: ${allImages.length} imagens`);
      console.log(`   Páginas incluídas: ${params.missingPagesInfo.missingPages.join(', ')} + ${numPagina} (atual)`);
      
      // 🔥 V6.25 FIX: Extrai zoompan COMPLETO usando indexOf (regex /[^,]+/ falhava com vírgulas internas)
      let zoompanFilter = 'zoompan=z=1.2:d=10000:s=1280x720';
      let postXfadeFilters = filterChain;
      
      const zoompanStart = filterChain.indexOf('zoompan=');
      if (zoompanStart !== -1) {
        let zoompanEnd = filterChain.length;
        const afterZoompan = filterChain.substring(zoompanStart + 8);
        const nextFilterMatch = afterZoompan.match(/,([a-z]+)=/);
        if (nextFilterMatch) {
          zoompanEnd = zoompanStart + 8 + nextFilterMatch.index;
        }
        
        zoompanFilter = filterChain.substring(zoompanStart, zoompanEnd);
        console.log(`   🎥 Zoompan extraído (${zoompanFilter.length} chars): ${zoompanFilter.substring(0, 80)}...`);
        
        postXfadeFilters = filterChain.substring(0, zoompanStart) + filterChain.substring(zoompanEnd);
        postXfadeFilters = postXfadeFilters.replace(/^,|,$/g, '').replace(/,,+/g, ',').replace(/^,|,$/g, '');
      }
      
      if (!postXfadeFilters || postXfadeFilters.match(/^[,\s]*$/)) {
        postXfadeFilters = `scale=${GLOBAL_CONFIG.outputFormat.workingWidth}:${GLOBAL_CONFIG.outputFormat.workingHeight}:force_original_aspect_ratio=decrease,pad=${GLOBAL_CONFIG.outputFormat.workingWidth}:${GLOBAL_CONFIG.outputFormat.workingHeight}:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p`;
      } else {
        // 🔥 V6.26 FIX: Garante resolução final 1280x720 após qualquer crop/scale
        postXfadeFilters = `${postXfadeFilters},scale=${GLOBAL_CONFIG.outputFormat.workingWidth}:${GLOBAL_CONFIG.outputFormat.workingHeight}:force_original_aspect_ratio=decrease,pad=${GLOBAL_CONFIG.outputFormat.workingWidth}:${GLOBAL_CONFIG.outputFormat.workingHeight}:(ow-iw)/2:(oh-ih)/2:color=black`;
      }
      
      console.log(`   🎨 Post-xfade: ${postXfadeFilters.substring(0, 60)}...`);
      
      let imgInputs = [];
      let imgFilters = [];
      
      for (let i = 0; i < allImages.length; i++) {
        const dur = durations[i] || 5;
        imgInputs.push(`-loop 1 -t ${(dur + transitionDuration).toFixed(2)} -i "${allImages[i]}"`);
        imgFilters.push(`[${i + 1}:v]scale=${GLOBAL_CONFIG.outputFormat.workingWidth}:${GLOBAL_CONFIG.outputFormat.workingHeight}:force_original_aspect_ratio=decrease,pad=${GLOBAL_CONFIG.outputFormat.workingWidth}:${GLOBAL_CONFIG.outputFormat.workingHeight}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=${GLOBAL_CONFIG.outputFormat.fps},${zoompanFilter}[img${i}]`);
        console.log(`   [${i + 1}] ${allImages[i].split('/').pop()} - ${dur.toFixed(2)}s`);
      }
      
      let concatParts = [];
      let currentLabel = '[img0]';
      let offsetAccum = 0;
      
      for (let i = 1; i < allImages.length; i++) {
        offsetAccum += (durations[i - 1] || 5);
        const nextLabel = i === allImages.length - 1 ? '[v_concat]' : `[concat${i}]`;
        concatParts.push(`${currentLabel}[img${i}]xfade=transition=fade:duration=${transitionDuration}:offset=${offsetAccum.toFixed(2)}${nextLabel}`);
        currentLabel = nextLabel;
        console.log(`   🔀 Transição ${i}: offset=${offsetAccum.toFixed(2)}s`);
      }
      
      videoInputCmd = imgInputs.join(' ');
      const slideshowFilter = imgFilters.join(';') + ';' + concatParts.join(';');
      filterComplexBase = `${slideshowFilter};[v_concat]${postXfadeFilters}[v_filt];[v_filt]${subtitleFilter}[v_sub];[v_sub]${watermark},${footer}[v_final]`;
      
      console.log(`✅ Slideshow V6.25 configurado com ${allImages.length} imagens`);
      
    } else {
      // Modo normal: única imagem
      videoInputCmd = `-loop 1 -i "${imagePath}"`;
      filterComplexBase = `[1:v]${filterChain},tpad=stop_mode=clone:stop_duration=2[v_filt];[v_filt]${subtitleFilter}[v_sub];[v_sub]${watermark},${footer},fade=t=out:st=FADE_START_PLACEHOLDER:d=1.5[v_final]`;
    }

    // 🔥 V6.30 FIX: Validação robusta de variáveis para evitar erro 234
    const endBufferSeconds = 0;
    const createBaseCmd = `
# ═══════════════════════════════════════════════════════════════════════
# 🔥 V6.30: DETECÇÃO DE DURAÇÃO COM MÚLTIPLOS FALLBACKS
# ═══════════════════════════════════════════════════════════════════════

# Método 1: format duration
AUDIO_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${audioFinalPath}" 2>/dev/null)

# Validação rigorosa com regex
if [ -z "$AUDIO_DUR" ] || [ "$AUDIO_DUR" = "N/A" ] || ! echo "$AUDIO_DUR" | grep -qE '^[0-9]+\\.?[0-9]*$'; then
  echo "⚠️ Método 1 falhou, tentando stream duration..." >&2
  # Método 2: stream duration
  AUDIO_DUR=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 "${audioFinalPath}" 2>/dev/null)
  
  # Validação do método 2
  if [ -z "$AUDIO_DUR" ] || [ "$AUDIO_DUR" = "N/A" ] || ! echo "$AUDIO_DUR" | grep -qE '^[0-9]+\\.?[0-9]*$'; then
    echo "⚠️ Método 2 falhou, usando fallback 30s..." >&2
    AUDIO_DUR="30"
  fi
fi

echo "✅ Duração detectada: $AUDIO_DUR segundos"

# Cálculo de TARGET_DUR com validação
TARGET_DUR=$(echo "$AUDIO_DUR + ${endBufferSeconds}" | bc 2>/dev/null)
if [ -z "$TARGET_DUR" ] || ! echo "$TARGET_DUR" | grep -qE '^[0-9]+\\.?[0-9]*$'; then
  TARGET_DUR="$AUDIO_DUR"
fi

# ═══════════════════════════════════════════════════════════════════════
# 🔥 V6.30: CÁLCULO SEGURO DE FADE_START
# ═══════════════════════════════════════════════════════════════════════

FADE_START=$(echo "$TARGET_DUR - 1.5" | bc 2>/dev/null)

# Validação de FADE_START
if [ -z "$FADE_START" ] || ! echo "$FADE_START" | grep -qE '^-?[0-9]+\\.?[0-9]*$'; then
  echo "⚠️ bc falhou para FADE_START, usando awk..." >&2
  FADE_START=$(awk "BEGIN {printf \\"%.2f\\", $TARGET_DUR * 0.8}")
  
  # Se awk também falhar, valor fixo
  if [ -z "$FADE_START" ] || ! echo "$FADE_START" | grep -qE '^[0-9]+\\.?[0-9]*$'; then
    echo "⚠️ awk falhou, usando fallback 80% de $TARGET_DUR..." >&2
    FADE_START="28.5"
  fi
fi

# Garante que FADE_START seja >= 1 segundo (evita fade negativo)
FADE_INT=\${FADE_START%.*}
if [ -z "$FADE_INT" ]; then FADE_INT=0; fi
if [ "$FADE_INT" -lt 1 ] 2>/dev/null; then
  echo "⚠️ FADE_START muito baixo ($FADE_START), ajustando para 1..." >&2
  FADE_START="1"
fi

echo "✅ FADE_START calculado: $FADE_START (TARGET_DUR: $TARGET_DUR)"

# ═══════════════════════════════════════════════════════════════════════
# 🔥 V6.30: VALIDAÇÃO DE ARQUIVOS DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════

if [ ! -f "${imagePath}" ]; then
  echo "❌ ERRO CRÍTICO: Imagem não encontrada: ${imagePath}" >&2
  exit 1
fi

if [ ! -f "${audioFinalPath}" ] || [ ! -s "${audioFinalPath}" ]; then
  echo "❌ ERRO CRÍTICO: Áudio final não existe ou está vazio: ${audioFinalPath}" >&2
  exit 1
fi

echo "✅ Arquivos de entrada validados"

# ═══════════════════════════════════════════════════════════════════════
# COMANDO FFMPEG PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════

timeout ${GLOBAL_CONFIG.timeouts.videoBase / 1000} ffmpeg -y ${audioInputFlags} -i "${audioFinalPath}" ${videoInputCmd} -filter_complex "${filterComplexBase.replace('FADE_START_PLACEHOLDER', '$FADE_START')}" -map "[v_final]" -map 0:a -c:v ${GLOBAL_CONFIG.outputFormat.videoCodec} -preset ${GLOBAL_CONFIG.outputFormat.preset} -tune stillimage -crf ${GLOBAL_CONFIG.outputFormat.crf} -c:a ${GLOBAL_CONFIG.outputFormat.audioCodec} -b:a ${GLOBAL_CONFIG.outputFormat.audioBitrate} -t $TARGET_DUR "${videoBaseTemp}" 2>&1 | tail -20
`;

    const normalizaMemeCmd = `timeout ${GLOBAL_CONFIG.timeouts.memeNormalization / 1000} ffmpeg -y -i \"${memePath}\" -t ${GLOBAL_CONFIG.meme.duration} -vf \"scale=${GLOBAL_CONFIG.outputFormat.workingWidth}:${GLOBAL_CONFIG.outputFormat.workingHeight}:force_original_aspect_ratio=decrease,pad=${GLOBAL_CONFIG.outputFormat.workingWidth}:${GLOBAL_CONFIG.outputFormat.workingHeight}:(ow-iw)/2:(oh-ih)/2:color=black,fps=${GLOBAL_CONFIG.outputFormat.fps},setsar=1\" -c:v ${GLOBAL_CONFIG.outputFormat.videoCodec} -preset ${GLOBAL_CONFIG.outputFormat.preset} -pix_fmt yuv420p -crf ${GLOBAL_CONFIG.outputFormat.crf} -c:a ${GLOBAL_CONFIG.outputFormat.audioCodec} -ar ${GLOBAL_CONFIG.audio.sampleRate} -ac ${GLOBAL_CONFIG.audio.channels} -b:a ${GLOBAL_CONFIG.outputFormat.audioBitrate} \"${memeNormalizado}\" 2>&1 | tail -10`;

    const getDurationCmd = `DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${videoBaseTemp}" 2>/dev/null | cut -d. -f1) && [ -z "$DUR" ] && DUR=10`;
    
    const transicaoInicioCmd = `timeout ${GLOBAL_CONFIG.timeouts.transition / 1000} ffmpeg -y -i "${memeNormalizado}" -i "${videoBaseTemp}" -filter_complex "[0:v][1:v]xfade=transition=${transitionEffect}:duration=${GLOBAL_CONFIG.meme.transitionDuration}:offset=${GLOBAL_CONFIG.meme.transitionOffset}[v_temp]" -map "[v_temp]" -map 1:a -c:v ${GLOBAL_CONFIG.outputFormat.videoCodec} -preset ${GLOBAL_CONFIG.outputFormat.preset} -crf ${GLOBAL_CONFIG.outputFormat.crf} -c:a copy -shortest "${videoComTransicaoInicio}" 2>&1 | tail -10`;
    // 🔊 MODIFICAÇÃO: Adiciona trilha de efeitos sonoros se existir
    let filterComplexFinal;
    let sfxInputCmd = '';
    
    if (soundEffectsPath && fs.existsSync(soundEffectsPath)) {
      // ═══════════════════════════════════════════════════════════════════════
      // 🔊 V6.20 FIX: EFEITOS SONOROS COM VOLUME REDUZIDO
      // ═══════════════════════════════════════════════════════════════════════
      const sfxConfig = GLOBAL_CONFIG.soundEffects || { effectVolume: 0.35, mixWeight: 0.5 };
      const sfxVolume = sfxConfig.effectVolume || 0.35;
      const sfxMixWeight = sfxConfig.mixWeight || 0.5;
      
      console.log(`🔊 Incluindo trilha de efeitos sonoros: ${soundEffectsPath}`);
      console.log(`🔊 Volume SFX: ${sfxVolume}, Mix Weight: ${sfxMixWeight}`);
      sfxInputCmd = `-i "${soundEffectsPath}"`;
      
      // 🔥 V6.20: Volume de SFX REDUZIDO e mix weight ajustado
      filterComplexFinal = `[0:a]volume=1.5[a_narr];[1:a]afade=t=in:st=0:d=${GLOBAL_CONFIG.audio.fadeInDuration},volume=${GLOBAL_CONFIG.audio.musicVolume},afade=t=out:st=$FADE_OUT_ST:d=${GLOBAL_CONFIG.audio.fadeOutDuration},aloop=loop=-1:size=2e+09[a_music];[2:a]volume=${sfxVolume}[a_sfx];[a_narr][a_music]amix=inputs=2:duration=first:dropout_transition=2[a_temp];[a_temp][a_sfx]amix=inputs=2:duration=first:weights=1 ${sfxMixWeight}[a_out]`;
      // ═══════════════════════════════════════════════════════════════════════
    } else {
      // Filtro original sem efeitos sonoros
      filterComplexFinal = `[0:a]volume=1.5[a_narr];[1:a]afade=t=in:st=0:d=${GLOBAL_CONFIG.audio.fadeInDuration},volume=${GLOBAL_CONFIG.audio.musicVolume},afade=t=out:st=$FADE_OUT_ST:d=${GLOBAL_CONFIG.audio.fadeOutDuration},aloop=loop=-1:size=2e+09[a_music];[a_narr][a_music]amix=inputs=2:duration=first:dropout_transition=2[a_out]`;
    }
    const finalMixCmd = `
# 5a. Detecta duracao
DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${videoBaseTemp}" 2>/dev/null | cut -d. -f1)
[ -z "$DUR" ] && DUR=10
echo "Duracao detectada: $DUR segundos"

# 🔥 V6.32 FIX: Calcula fade out start protegido contra valores negativos
FADE_OUT_ST=$((DUR > 6 ? DUR - 3 : DUR / 2))
[ "$FADE_OUT_ST" -lt 1 ] && FADE_OUT_ST=1
echo "Fade out start: $FADE_OUT_ST segundos"

# 5b. 🔥 V6.32: Transicao video base -> meme (MEME NO FINAL)
echo "Aplicando transicao (meme no final - V6.32)..."

# Calcula offset: fim do video base - duracao da transicao
XFADE_OFFSET=$((DUR - 1))
[ "$XFADE_OFFSET" -lt 1 ] && XFADE_OFFSET=1
echo "Xfade offset: $XFADE_OFFSET segundos"

timeout 120 ffmpeg -y -i "${videoBaseTemp}" -i "${memeNormalizado}" -filter_complex "[0:v][1:v]xfade=transition=${transitionEffect}:duration=${GLOBAL_CONFIG.meme.transitionDuration}:offset=$XFADE_OFFSET[v_temp];[0:a][1:a]acrossfade=d=${GLOBAL_CONFIG.meme.transitionDuration}:c1=tri:c2=tri[a_out]" -map "[v_temp]" -map "[a_out]" -c:v ${GLOBAL_CONFIG.outputFormat.videoCodec} -preset ${GLOBAL_CONFIG.outputFormat.preset} -crf ${GLOBAL_CONFIG.outputFormat.crf} -c:a ${GLOBAL_CONFIG.outputFormat.audioCodec} -b:a ${GLOBAL_CONFIG.outputFormat.audioBitrate} "${videoComTransicaoInicio}" 2>&1 | tail -10

RETCODE_TRANS=\\$?

if [ \\$RETCODE_TRANS -ne 0 ] || [ ! -f "${videoComTransicaoInicio}" ] || [ ! -s "${videoComTransicaoInicio}" ]; then
  echo "ERRO: Transicao falhou (code: \\$RETCODE_TRANS)" >&2
  exit 1
fi
echo "Transicao OK"

# 5c. Mix com trilha sonora
echo "Mixando trilha sonora..."
timeout ${GLOBAL_CONFIG.timeouts.finalMix / 1000} ffmpeg -y -i "${videoComTransicaoInicio}" -stream_loop -1 -i "${trilhaPath}" ${sfxInputCmd} -filter_complex "${filterComplexFinal}" -map 0:v -map "[a_out]" -c:v ${GLOBAL_CONFIG.outputFormat.videoCodec} -preset ${GLOBAL_CONFIG.outputFormat.preset} -crf ${GLOBAL_CONFIG.outputFormat.crf} -c:a ${GLOBAL_CONFIG.outputFormat.audioCodec} -b:a ${GLOBAL_CONFIG.outputFormat.audioBitrate} -shortest "${outputPath}" 2>&1
`;
    return {
      mkdirCmd,
      audioMergeCmd,
      createBaseCmd,
      normalizaMemeCmd,
      finalMixCmd,
      videoBaseTemp,
      memeNormalizado,
      videoComTransicaoInicio,
      trilhaPath,
      filterComplexFinal,
      imagePath,
      filterComplexBase,
      audioInputFlags, // Retorna flags usadas
      sfxInputCmd
    };
  }
  
  static buildFinalScript(commands, params) {
    const { audioFinalPath, audioFormat, videoBaseTemp, outputPath, numPagina, contextualEffect } = params;
    const { mkdirCmd, audioMergeCmd, createBaseCmd, finalMixCmd, trilhaPath, videoComTransicaoInicio, filterComplexFinal, memeNormalizado, imagePath, filterComplexBase, audioInputFlags, sfxInputCmd } = commands;
    
    const outputPathHD = outputPath.replace('.mp4', '_HD.mp4');
    const outputSemTrilha = outputPath.replace('.mp4', '_sem_trilha.mp4');
      
    const finalMixCmdHD = finalMixCmd.replace(outputPath, outputPathHD);
    
    // 🔥 Comando de retry com flags corretas E escape correto
    const retryFlags = audioInputFlags || '';
    
    return `
# 1. Garante estrutura de pastas (Multi-Idioma)
${mkdirCmd}
set -o pipefail

# 2. Validacao inicial
if [ ! -f "${audioFinalPath}" ] || [ ! -s "${audioFinalPath}" ]; then 
  ${audioMergeCmd}; 
fi

if [ ! -f "${audioFinalPath}" ] || [ ! -s "${audioFinalPath}" ]; then 
  echo "ERRO: Audio final nao gerado" >&2; 
  exit 1; 
fi

# 🔥 V6.10: Detecta formato de áudio automaticamente
echo "Detectando formato do áudio: ${audioFinalPath}"
AUDIO_FORMAT="${audioFormat}"
echo "Formato identificado: $AUDIO_FORMAT"

# 3. Criacao do video base HD (com retry e escape correto)
${createBaseCmd}
RETCODE=$?

if [ $RETCODE -eq 124 ]; then
  echo "TIMEOUT no video base, tentando com preset mais rapido..." >&2
  timeout ${GLOBAL_CONFIG.timeouts.fallback / 1000} ffmpeg -y ${retryFlags} -i "${audioFinalPath}" -loop 1 -i "${imagePath}" -filter_complex "${filterComplexBase}" -map "[v_final]" -map 0:a -c:v ${GLOBAL_CONFIG.outputFormat.videoCodec} -preset ${GLOBAL_CONFIG.outputFormat.presetFallback} -tune stillimage -crf 25 -c:a ${GLOBAL_CONFIG.outputFormat.audioCodec} -b:a ${GLOBAL_CONFIG.outputFormat.audioBitrate} -shortest "${videoBaseTemp}" 2>&1 | tail -10
  RETCODE=$?
fi

if [ $RETCODE -ne 0 ] || [ ! -f "${videoBaseTemp}" ] || [ ! -s "${videoBaseTemp}" ]; then
  echo "ERRO: Video base nao criado (code: $RETCODE)" >&2
  exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 🔥 V6.27 FIX: ADICIONE ESTAS 7 LINHAS AQUI (entre passo 3 e passo 4)
# ═══════════════════════════════════════════════════════════════════════════════
DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${videoBaseTemp}" 2>/dev/null | cut -d. -f1)
[ -z "$DUR" ] && DUR=10
echo "Duracao detectada: $DUR segundos"

FADE_OUT_ST=$((DUR > 6 ? DUR - 3 : DUR / 2))
[ "$FADE_OUT_ST" -lt 1 ] && FADE_OUT_ST=1
echo "Fade out start: $FADE_OUT_ST segundos"
# ═══════════════════════════════════════════════════════════════════════════════



# 4. Normalizacao do meme (SE APLICÁVEL - frequency: ${GLOBAL_CONFIG.meme.frequency})
if [ $((${numPagina} % ${GLOBAL_CONFIG.meme.frequency})) -eq 1 ]; then
  echo "🎭 Página ${numPagina}: COM MEME"
  ${commands.normalizaMemeCmd}

  if [ ! -f "${memeNormalizado}" ] || [ ! -s "${memeNormalizado}" ]; then
    echo "ERRO: Meme nao normalizado" >&2
    exit 1
  fi

  # 5. Mix final HD COM MEME
  ${finalMixCmdHD}
  RETCODE=$?
else
  echo "🎭 Página ${numPagina}: SEM MEME"
  # 5. Mix final HD SEM MEME (pula transição)
  cp "${videoBaseTemp}" "${videoComTransicaoInicio}"
  
  timeout ${GLOBAL_CONFIG.timeouts.finalMix / 1000} ffmpeg -y -i "${videoComTransicaoInicio}" -stream_loop -1 -i "${trilhaPath}" ${sfxInputCmd} -filter_complex "${filterComplexFinal}" -map 0:v -map "[a_out]" -c:v ${GLOBAL_CONFIG.outputFormat.videoCodec} -preset ${GLOBAL_CONFIG.outputFormat.preset} -crf ${GLOBAL_CONFIG.outputFormat.crf} -c:a ${GLOBAL_CONFIG.outputFormat.audioCodec} -b:a ${GLOBAL_CONFIG.outputFormat.audioBitrate} -shortest "${outputPathHD}" 2>&1
  RETCODE=$?
fi

if [ $RETCODE -eq 124 ]; then
  echo "TIMEOUT no mix final, tentando versao simplificada..." >&2
  timeout ${GLOBAL_CONFIG.timeouts.fallback / 1000} ffmpeg -y -i "${videoComTransicaoInicio}" -stream_loop -1 -i "${trilhaPath}" ${sfxInputCmd} -filter_complex "${filterComplexFinal}" -map 0:v -map "[a_out]" -c:v ${GLOBAL_CONFIG.outputFormat.videoCodec} -preset ${GLOBAL_CONFIG.outputFormat.presetFallback} -crf 25 -c:a ${GLOBAL_CONFIG.outputFormat.audioCodec} -b:a ${GLOBAL_CONFIG.outputFormat.audioBitrate} -shortest "${outputPathHD}" 2>&1 | tail -10
  RETCODE=$?
fi

if [ $RETCODE -ne 0 ] || [ ! -f "${outputPathHD}" ] || [ ! -s "${outputPathHD}" ]; then
  echo "ERRO: Video HD nao criado (code: $RETCODE)" >&2
  exit 1
fi


# ✅ NOVO: Salva versao SEM TRILHA (so narracao + efeitos visuais) em HD
echo "Salvando versao sem trilha musical (HD)..."
cp "${videoComTransicaoInicio}" "${outputSemTrilha}" 2>/dev/null
if [ -f "${outputSemTrilha}" ]; then
  echo "✅ Versao sem trilha salva: ${outputSemTrilha}"
else
  echo "⚠️ Falha ao salvar versao sem trilha" >&2
fi

# 6. UPSCALE FINAL HD -> FULL HD
echo "Upscaling HD (1280x720) para Full HD (1920x1080)..."
timeout ${GLOBAL_CONFIG.timeouts.upscale / 1000} ffmpeg -y -i "${outputPathHD}" -vf "scale=${GLOBAL_CONFIG.outputFormat.finalWidth}:${GLOBAL_CONFIG.outputFormat.finalHeight}:flags=${GLOBAL_CONFIG.outputFormat.upscaleFilter}" -c:v ${GLOBAL_CONFIG.outputFormat.videoCodec} -preset ${GLOBAL_CONFIG.outputFormat.preset} -crf ${GLOBAL_CONFIG.outputFormat.upscaleCrf} -c:a copy "${outputPath}" 2>&1 | tail -10
RETCODE=$?

if [ $RETCODE -ne 0 ] || [ ! -f "${outputPath}" ] || [ ! -s "${outputPath}" ]; then
  echo "ERRO: Upscale para Full HD falhou (code: $RETCODE)" >&2
  echo "FALLBACK: Mantendo versao HD como final..." >&2
  mv "${outputPathHD}" "${outputPath}"
fi

# 7. Gera relatorio
${commands.createRelatorioCmd}

# 8. Limpeza de temporarios incluindo HD (NAO deleta versao sem trilha)
rm -f "${videoBaseTemp}" "${memeNormalizado}" "${videoComTransicaoInicio}" "${outputPathHD}" 2>/dev/null

echo "Sucesso: Pagina ${numPagina} processada com efeito contextual '${contextualEffect.nome}' (V6.10 Ultimate)"
`.trim();
  }
}

// ──────────────────────────────────────────────────────────────────────
// CLASSE: ReportGenerator V5.0 - NOVO: Relatórios Detalhados
// ──────────────────────────────────────────────────────────────────────
class ReportGenerator {
  static generate(params) {
    const {
      numPagina, outputPath, dimensoes, contextualEffect, effects,
      imagePath, audioFinalPath, subtitlePath, trilhaPath, memePath,
      movement, narrationText
    } = params;
    
    const timestamp = new Date().toISOString();
    const movementType = this._identifyMovementType(movement);
    
    return `
╔═══════════════════════════════════════════════════════════════════════╗
║                   RELATÓRIO DE PROCESSAMENTO V6.9                     ║
║                          PÁGINA ${numPagina}                                    ║
╚═══════════════════════════════════════════════════════════════════════╝

📅 TIMESTAMP: ${timestamp}
📁 OUTPUT: ${outputPath}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📐 DIMENSÕES DA IMAGEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Largura: ${dimensoes.largura}px
   Altura: ${dimensoes.altura}px
   Aspect Ratio: ${dimensoes.ratio.toFixed(2)}
   Alongado: ${dimensoes.ehAlongado ? 'SIM (Manhwa)' : 'NÃO'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 EFEITO CONTEXTUAL APLICADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Nome: ${contextualEffect.nome}
   Tipo: ${contextualEffect.tipo}
   Intensidade: ${contextualEffect.intensidade}
   Gatilho: "${narrationText ? narrationText.substring(0, 100).trim() + '...' : 'Sem narração'}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ EFEITOS VISUAIS APLICADOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Movimento: ${movementType}
   Blur: ${effects.blur || 'N/A'}
   Sharpen: ${effects.sharpen || 'N/A'}
   Vinheta: ${effects.vignette || 'N/A'}
   Cores: ${effects.color ? effects.color.substring(0, 50) + '...' : 'N/A'}
   Ruído: ${effects.noise || 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎵 CONFIGURAÇÃO DE ÁUDIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Narração: ${audioFinalPath}
   Trilha: ${trilhaPath}
   Volume Música: ${GLOBAL_CONFIG.audio.musicVolume}
   Fade In: ${GLOBAL_CONFIG.audio.fadeInDuration}s
   Fade Out: ${GLOBAL_CONFIG.audio.fadeOutDuration}s
   Ducking: ${GLOBAL_CONFIG.audio.ducking.enabled ? 'ATIVO' : 'DESATIVADO'}
   Normalização: ${GLOBAL_CONFIG.audio.normalization.enabled ? `ATIVO (${GLOBAL_CONFIG.audio.normalization.targetLUFS} LUFS)` : 'DESATIVADO'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 LEGENDAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Arquivo: ${subtitlePath}
   Contexto Detectado: ${SubtitleProcessor.detectContext(narrationText || '')}
   Animações: ${GLOBAL_CONFIG.subtitle.animations.enabled ? 'ATIVO' : 'DESATIVADO'}
   Outline Adaptativo: ${GLOBAL_CONFIG.subtitle.outlineAdaptive.enabled ? 'ATIVO' : 'DESATIVADO'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎭 MEME DE TRANSIÇÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Arquivo: ${memePath}
   Duração: ${GLOBAL_CONFIG.meme.duration}s
   Transição: ${GLOBAL_CONFIG.meme.transitionDuration}s
   Offset: ${GLOBAL_CONFIG.meme.transitionOffset}s

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ CONFIGURAÇÕES TÉCNICAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Working Resolution: ${GLOBAL_CONFIG.outputFormat.workingResolution}
   Final Resolution: ${GLOBAL_CONFIG.outputFormat.finalResolution}
   FPS: ${GLOBAL_CONFIG.outputFormat.fps}
   Codec: ${GLOBAL_CONFIG.outputFormat.videoCodec}
   CRF: ${GLOBAL_CONFIG.outputFormat.crf}
   Preset: ${GLOBAL_CONFIG.outputFormat.preset}
   Upscale Filter: ${GLOBAL_CONFIG.outputFormat.upscaleFilter}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 SISTEMA DE MEMÓRIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Status: ${GLOBAL_CONFIG.memory.enabled ? 'ATIVO' : 'DESATIVADO'}
   Color Grading: ${GLOBAL_CONFIG.memory.trackColorGrading ? 'TRACKING' : 'OFF'}
   Movement Direction: ${GLOBAL_CONFIG.memory.trackMovementDirection ? 'TRACKING' : 'OFF'}
   Atmosphere: ${GLOBAL_CONFIG.memory.trackAtmosphere ? 'TRACKING' : 'OFF'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 ANÁLISE DE CONTEÚDO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Status: ${GLOBAL_CONFIG.contentAnalysis.enabled ? 'ATIVO' : 'DESATIVADO'}
   Brightness Detection: ${GLOBAL_CONFIG.contentAnalysis.detectBrightness ? 'ON' : 'OFF'}
   Contrast Detection: ${GLOBAL_CONFIG.contentAnalysis.detectContrast ? 'ON' : 'OFF'}
   Color Palette: ${GLOBAL_CONFIG.contentAnalysis.detectColorPalette ? 'ON' : 'OFF'}
   Adaptive Effects: ${GLOBAL_CONFIG.contentAnalysis.adaptiveEffects.enabled ? 'ON' : 'OFF'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ STATUS: PROCESSAMENTO CONCLUÍDO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Versão do Sistema: V6.9 ULTIMATE AUDIO-FORMAT-FIX
Arquitetura: MODULAR HD WORKFLOW
Banco de Efeitos: 200+ efeitos otimizados para leitura
`;
  }
  
  static _identifyMovementType(movement) {
    if (movement.includes('lte(on,100),0,min')) return '⬇️ VERTICAL PAN DOWN';
    if (movement.includes('ih-ih/zoom,max')) return '⬆️ VERTICAL PAN UP';
    if (movement.includes('min(zoom+0.0')) return '🎯 ZOOM IN';
    if (movement.includes('max(zoom-0.0')) return '💫 ZOOM OUT';
    if (movement.includes('sin(on*') || movement.includes('cos(on*')) return '💫 DRIFT/PARALLAX';
    if (movement.includes('crop=')) return '📷 KEN BURNS';
    return '🔄 MOVIMENTO ESPECIAL';
  }
}

// ======================================================================
// SEÇÃO 7: ✅ FUNÇÃO PRINCIPAL - V6.8 (FIX CRÍTICO: FORMATO DE ÁUDIO CORRETO)
// ======================================================================

// ──────────────────────────────────────────────────────────────────────
// CONFIGURAÇÃO: Ative/desative organização de pastas aqui
// ──────────────────────────────────────────────────────────────────────
const ORGANIZE_FOLDERS = true; 

// ──────────────────────────────────────────────────────────────────────
// CLASSE: AudioConverter V6.7 - Conversão Direta MP3 (SEM DUPLICAÇÃO) + FIX CHIADO
// ──────────────────────────────────────────────────────────────────────
class AudioConverter {
  /**
   * Converte arquivo .json com áudio Base64 MP3 para arquivo MP3 funcional
   * V6.7: Identifica MP3 válido, salva direto sem reprocessamento e elimina chiado
   */
  static convertJsonToMp3(jsonPath) {
    try {
      console.log(`🔄 Iniciando conversão V6.7: ${jsonPath}`);
      
      if (!fs.existsSync(jsonPath)) {
        throw new Error(`Arquivo não encontrado: ${jsonPath}`);
      }
      
      const rawContent = fs.readFileSync(jsonPath, 'utf8');
      const outputPath = jsonPath.replace(/\.json$/, '_converted.mp3');
      
      // PASSO 1: Parse do JSON
      let jsonData;
      try {
        jsonData = JSON.parse(rawContent);
        console.log('✅ JSON parseado com sucesso');
        console.log('📋 Campos disponíveis:', Object.keys(jsonData));
      } catch (parseError) {
        throw new Error(`Erro ao parsear JSON: ${parseError.message}`);
      }
      
      // PASSO 2: Extrai o Base64 (compatível com seu formato)
      let base64Data = null;
      
      // 🔥 ORDEM DE PRIORIDADE PARA EXTRAÇÃO (igual ao seu script Node.js)
      if (jsonData.data) {
        base64Data = jsonData.data;
        console.log('✅ Campo "data" encontrado (formato padrão)');
      } else if (jsonData.success && jsonData.data) {
        base64Data = jsonData.data;
        console.log('✅ Campo "data" encontrado (success=true)');
      } else if (jsonData.audioContent) {
        base64Data = jsonData.audioContent;
        console.log('✅ Campo "audioContent" encontrado');
      } else if (jsonData.audio) {
        base64Data = jsonData.audio;
        console.log('✅ Campo "audio" encontrado');
      } else if (jsonData.content) {
        base64Data = jsonData.content;
        console.log('✅ Campo "content" encontrado');
      } else {
        // Busca qualquer campo com string longa (possível Base64)
        for (const [key, value] of Object.entries(jsonData)) {
          if (typeof value === 'string' && value.length > 1000) {
            base64Data = value;
            console.log(`✅ Base64 encontrado no campo "${key}"`);
            break;
          }
        }
      }
      
      if (!base64Data) {
        throw new Error('Nenhum campo com Base64 de áudio encontrado no JSON');
      }
      
      console.log(`📦 Base64 extraído: ${base64Data.length} caracteres`);
      
      // PASSO 3: Limpa o Base64 (remove prefixos data:audio e whitespace)
      let cleanBase64 = base64Data.replace(/^data:audio\/[^;]+;base64,/, '');
      cleanBase64 = cleanBase64.replace(/[\s\r\n]/g, '');
      
      console.log(`🧹 Base64 limpo: ${cleanBase64.length} caracteres`);
      
      // PASSO 4: Decodifica Base64 para Buffer
      let audioBuffer;
      try {
        audioBuffer = Buffer.from(cleanBase64, 'base64');
        console.log(`✅ Buffer decodificado: ${audioBuffer.length} bytes (${(audioBuffer.length / 1024).toFixed(2)} KB)`);
      } catch (decodeError) {
        throw new Error(`Erro ao decodificar Base64: ${decodeError.message}`);
      }
      
      // PASSO 5: Valida se é MP3
      const validation = this._validateMP3Buffer(audioBuffer);
      console.log(`🔍 Validação MP3: ${validation.isValid ? '✅ VÁLIDO' : '❌ INVÁLIDO'}`);
      console.log(`   Tipo detectado: ${validation.type}`);
      console.log(`   Magic bytes: ${validation.magicBytes}`);
      
      if (validation.isValid) {
        // ✅ MP3 VÁLIDO - Salva direto sem reprocessamento
        console.log('💾 Salvando MP3 diretamente (sem reprocessamento para evitar chiado)...');
        fs.writeFileSync(outputPath, audioBuffer);
        
        if (!fs.existsSync(outputPath)) {
          throw new Error('Arquivo não foi salvo');
        }
        
        const savedSize = fs.statSync(outputPath).size;
        if (savedSize < 1000) {
          throw new Error(`Arquivo muito pequeno: ${savedSize} bytes`);
        }
        
        console.log(`✅ MP3 salvo com sucesso: ${outputPath}`);
        console.log(`📊 Tamanho: ${(savedSize / 1024).toFixed(2)} KB`);
        
        // Validação final com FFprobe
        try {
          const probeCmd = `ffprobe -v error -show_format -show_streams "${outputPath}" 2>&1 | grep -E "(codec_name|duration|bit_rate|sample_rate)"`;
          const probeResult = execSync(probeCmd, { timeout: 5000 }).toString();
          console.log('🔍 FFprobe validação:');
          console.log(probeResult.trim());
        } catch (probeError) {
          console.warn('⚠️ FFprobe não conseguiu validar (mas arquivo pode estar OK)');
        }
        
        return {
          success: true,
          outputPath: outputPath,
          originalPath: jsonPath,
          size: savedSize,
          method: 'direct_mp3_save',
          format: validation.type,
          audioFormat: 'mp3',
          note: 'MP3 válido salvo diretamente sem conversão (sem chiado)'
        };
        
      } else {
        // ❌ NÃO É MP3 - Converte com FFmpeg (PODE CAUSAR CHIADO)
        console.log('⚠️ Buffer não é MP3 válido, tentando conversão com FFmpeg...');
        console.log('⚠️ AVISO: Conversão pode introduzir chiado se sample rate estiver incorreto');
        
        const tempPath = outputPath.replace('.mp3', '_temp.bin');
        fs.writeFileSync(tempPath, audioBuffer);
        console.log(`💾 Buffer temporário salvo: ${tempPath}`);
        
        try {
          // 🔥 FIX CHIADO: Detecta sample rate correto antes de converter
          let sampleRate = GLOBAL_CONFIG.audio.sampleRate;
          
          try {
            const probeCmd = `ffprobe -v error -select_streams a:0 -show_entries stream=sample_rate -of default=noprint_wrappers=1:nokey=1 "${tempPath}" 2>&1`;
            const detectedRate = execSync(probeCmd, { timeout: 5000 }).toString().trim();
            
            if (detectedRate && !isNaN(parseInt(detectedRate))) {
              sampleRate = parseInt(detectedRate);
              console.log(`🔍 Sample rate detectado: ${sampleRate} Hz`);
            }
          } catch(probeErr) {
            console.warn(`⚠️ Não foi possível detectar sample rate, usando padrão: ${sampleRate} Hz`);
          }
          
          // 🔥 CONVERSÃO COM SAMPLE RATE CORRETO (evita chiado)
          const convertCmd = `ffmpeg -y -i "${tempPath}" -acodec libmp3lame -ar ${sampleRate} -ac 1 -b:a 128k "${outputPath}" 2>&1 | tail -20`;
          const ffmpegOutput = execSync(convertCmd, { timeout: 30000 }).toString();
          
          console.log('📋 FFmpeg output:');
          console.log(ffmpegOutput);
          
          // Remove arquivo temporário
          if (fs.existsSync(tempPath)) {
            fs.unlinkSync(tempPath);
          }
          
          if (!fs.existsSync(outputPath)) {
            throw new Error('FFmpeg não gerou arquivo de saída');
          }
          
          const convertedSize = fs.statSync(outputPath).size;
          if (convertedSize < 1000) {
            throw new Error(`Arquivo convertido muito pequeno: ${convertedSize} bytes`);
          }
          
          console.log(`✅ Conversão FFmpeg bem-sucedida`);
          console.log(`📊 Tamanho: ${(convertedSize / 1024).toFixed(2)} KB`);
          console.log(`🎵 Sample rate usado: ${sampleRate} Hz`);
          
          return {
            success: true,
            outputPath: outputPath,
            originalPath: jsonPath,
            size: convertedSize,
            sampleRate: sampleRate,
            method: 'ffmpeg_conversion',
            audioFormat: 'mp3',
            note: 'Convertido para MP3 via FFmpeg com sample rate correto'
          };
          
        } catch (ffmpegError) {
          console.error(`❌ Erro no FFmpeg: ${ffmpegError.message}`);
          
          // FALLBACK: Salva buffer direto mesmo sem validação
          if (fs.existsSync(tempPath)) {
            fs.copyFileSync(tempPath, outputPath);
            fs.unlinkSync(tempPath);
          } else {
            fs.writeFileSync(outputPath, audioBuffer);
          }
          
          console.log(`💾 FALLBACK: Buffer salvo como MP3: ${outputPath}`);
          console.warn(`⚠️ AVISO: Arquivo pode ter problemas de compatibilidade ou chiado`);
          
          return {
            success: true,
            outputPath: outputPath,
            originalPath: jsonPath,
            size: audioBuffer.length,
            method: 'fallback_raw_save',
            audioFormat: 'mp3',
            warning: 'FFmpeg falhou, buffer salvo direto (pode ter problemas de compatibilidade ou chiado)'
          };
        }
      }
      
    } catch (error) {
      console.error(`❌ ERRO na conversão: ${error.message}`);
      console.error(error.stack);
      
      return {
        success: false,
        error: error.message,
        originalPath: jsonPath
      };
    }
  }
  
  /**
   * Valida se o buffer é um arquivo MP3 válido
   * Detecta ID3v2 tags e MPEG Audio Frame Sync
   */
  static _validateMP3Buffer(buffer) {
    if (!buffer || buffer.length < 10) {
      return { isValid: false, type: 'too_small', magicBytes: '' };
    }
    
    const firstBytes = buffer.slice(0, 16);
    const hexStr = this._bufferToHex(firstBytes);
    
    // ID3v2 tag (49 44 33 = "ID3")
    if (buffer[0] === 0x49 && buffer[1] === 0x44 && buffer[2] === 0x33) {
      return {
        isValid: true,
        type: 'MP3 with ID3v2 tag',
        magicBytes: hexStr,
        offset: 0
      };
    }
    
    // MPEG Audio Frame Sync (FF Ex)
    if (buffer[0] === 0xFF && (buffer[1] & 0xE0) === 0xE0) {
      return {
        isValid: true,
        type: 'MP3 with MPEG frame sync',
        magicBytes: hexStr,
        offset: 0
      };
    }
    
    // Busca nos primeiros 2KB (pode ter lixo no início)
    for (let i = 0; i < Math.min(buffer.length - 1, 2048); i++) {
      // Frame sync
      if (buffer[i] === 0xFF && (buffer[i + 1] & 0xE0) === 0xE0) {
        if (this._validateMPEGFrame(buffer, i)) {
          return {
            isValid: true,
            type: 'MP3 with MPEG frame sync (offset)',
            magicBytes: this._bufferToHex(buffer.slice(i, i + 16)),
            offset: i
          };
        }
      }
      
      // ID3 tag
      if (buffer[i] === 0x49 && buffer[i + 1] === 0x44 && buffer[i + 2] === 0x33) {
        return {
          isValid: true,
          type: 'MP3 with ID3v2 tag (offset)',
          magicBytes: this._bufferToHex(buffer.slice(i, i + 16)),
          offset: i
        };
      }
    }
    
    return {
      isValid: false,
      type: 'unknown_format',
      magicBytes: hexStr
    };
  }
  
  /**
   * Valida se é um frame MPEG válido
   */
  static _validateMPEGFrame(buffer, offset) {
    if (offset + 4 > buffer.length) return false;
    
    const header = buffer.readUInt32BE(offset);
    
    // Frame sync (11 bits = 1)
    if ((header & 0xFFE00000) !== 0xFFE00000) return false;
    
    // Version (2 bits)
    const version = (header >> 19) & 0x3;
    if (version === 1) return false; // Reservado
    
    // Layer (2 bits)
    const layer = (header >> 17) & 0x3;
    if (layer === 0) return false; // Reservado
    
    // Bitrate (4 bits)
    const bitrate = (header >> 12) & 0xF;
    if (bitrate === 0xF) return false; // Inválido
    
    // Sample rate (2 bits)
    const sampleRate = (header >> 10) & 0x3;
    if (sampleRate === 3) return false; // Reservado
    
    return true;
  }
  
  /**
   * Converte buffer para string hexadecimal
   */
  static _bufferToHex(buffer) {
    return Array.from(buffer)
      .map(b => b.toString(16).padStart(2, '0'))
      .join(' ');
  }
  
  /**
   * Limpa arquivos temporários antigos (mais de 1 hora)
   */
  static cleanupOldTempFiles(directory) {
    try {
      if (!fs.existsSync(directory)) return;
      
      const files = fs.readdirSync(directory);
      const now = Date.now();
      const oneHour = 60 * 60 * 1000;
      let cleaned = 0;
      
      for (const file of files) {
        if (file.includes('_temp.bin') || file.includes('_raw.bin')) {
          const filePath = path.join(directory, file);
          
          try {
            const stats = fs.statSync(filePath);
            
            if (now - stats.mtimeMs > oneHour) {
              fs.unlinkSync(filePath);
              cleaned++;
            }
          } catch(e) {
            // Ignora erros de arquivos específicos
          }
        }
      }
      
      if (cleaned > 0) {
        console.log(`🗑️ ${cleaned} arquivo(s) temporário(s) antigo(s) removido(s)`);
      }
      
    } catch (e) {
      console.warn(`⚠️ Erro ao limpar temporários: ${e.message}`);
    }
  }
}

function processItems(items) {
  console.log(`🔍 Iniciando processItems V6.9 (Cache + Auto Next) com ${items.length} itens`);
  
  const effectsManager = new EffectsManager();
  const contextualSelector = new ContextualSelector(effectsManager);
  const validItems = [];
  
  // ══════════════════════════════════════════════════════════════════════
  // 🔥 NOVO: CACHE + BUSCA AUTOMÁTICA DA PRÓXIMA PÁGINA
  // ══════════════════════════════════════════════════════════════════════
  
  // 1. Recupera nome da obra e total de páginas
  let nomeObraCache = "My_Fake_Girlfriend";
  let totalPaginasEsperadas = 24; // Padrão
  
  try {
    const configNode = $('Start').first().json.Configura_Obra1_firstItem_firstItem_firstItem;
    if (configNode?.json?.nome_obra) nomeObraCache = configNode.json.nome_obra;
    else if (configNode?.nome_obra) nomeObraCache = configNode.nome_obra;
    
    // Tenta descobrir total de páginas
    const contentParts = $('Start').first().json.content_parts_firstItem_firstItem;
    if (Array.isArray(contentParts)) {
      totalPaginasEsperadas = contentParts.length;
    }
    
    console.log(`📚 Cache - Obra: ${nomeObraCache} (${totalPaginasEsperadas} páginas)`);
  } catch(e) {
    console.warn(`⚠️ Cache - Usando padrões`);
  }
  
  // 2. Configuração de múltiplas pastas raiz
  const PASTAS_RAIZ_POSSIVEIS = [
    '/tmp/youtubevideos',
    '/root/209.145.60.53/root/n8n_videos',
  ];
  
  let pastaRaizCache = null;
  for (const pastaBase of PASTAS_RAIZ_POSSIVEIS) {
    const caminhoCompleto = `${pastaBase}/${nomeObraCache}`;
    if (fs.existsSync(caminhoCompleto)) {
      pastaRaizCache = caminhoCompleto;
      break;
    }
  }
  
  if (!pastaRaizCache) {
    pastaRaizCache = `${PASTAS_RAIZ_POSSIVEIS[0]}/${nomeObraCache}`;
  }
  
  // 3. CACHE - Detecta vídeos já existentes
const IDIOMAS_ATIVOS = [
  { code: 'PT_BR', pasta: 'PT', is_root: true },
  { code: 'EN_US', pasta: 'EN', is_root: false },
];

const cacheVideos = {};

IDIOMAS_ATIVOS.forEach(lang => {
  cacheVideos[lang.code] = new Set();
  
  PASTAS_RAIZ_POSSIVEIS.forEach(pastaBase => {
    const pastaObra = `${pastaBase}/${nomeObraCache}`;
    
    let locaisDeBusca = [];
    
    if (lang.is_root) {
      locaisDeBusca.push(pastaObra);
      locaisDeBusca.push(`${pastaObra}/videos`);
    } else {
      locaisDeBusca.push(`${pastaObra}/${lang.pasta}`);
      locaisDeBusca.push(`${pastaObra}/${lang.pasta}/videos`);
    }
    
    locaisDeBusca.forEach(local => {
      try {
        if (fs.existsSync(local)) {
          const arquivos = fs.readdirSync(local);
          arquivos
            .filter(nome => nome.startsWith('video_pag_') && nome.endsWith('.mp4'))
            .forEach(nome => {
              const match = nome.match(/video_pag_(\d+)\.mp4/);
              if (match) {
                const numPagina = parseInt(match[1], 10);
                cacheVideos[lang.code].add(numPagina);
              }
            });
        }
      } catch (e) { /* Ignora */ }
    });
  });
  
  if (cacheVideos[lang.code].size > 0) {
    console.log(`📊 Cache [${lang.code}]: ${cacheVideos[lang.code].size} vídeos`);
  }
});

// 4. 🔥 FIX CRÍTICO V6.14: EXTRAÇÃO CORRETA DO IDIOMA E PÁGINA DOS ITEMS
console.log(`\n🔍 ════════════════════════════════════════════`);
console.log(`🔍 VERIFICAÇÃO DE IDIOMA E PÁGINA V6.14`);
console.log(`🔍 ════════════════════════════════════════════`);
console.log(`📦 Total de items recebidos: ${items.length}`);

// 🔥 PRIMEIRO: Extrair o idioma do PRIMEIRO item ANTES de qualquer verificação
let langCodePrincipal = 'PT_BR'; // Fallback absoluto

if (items.length > 0) {
  const primeiroItem = items[0].json || {};
  
  console.log(`\n📋 DEBUG - Campos do primeiro item (RAW):`);
  console.log(`   lang_code = "${primeiroItem.lang_code}" (tipo: ${typeof primeiroItem.lang_code})`);
  console.log(`   target_language = "${primeiroItem.target_language}"`);
  console.log(`   pasta_lingua = "${primeiroItem.pasta_lingua}"`);
  console.log(`   is_root_lang = ${primeiroItem.is_root_lang}`);
  console.log(`   pagina = ${primeiroItem.pagina}`);
  console.log(`   pagina_numero = ${primeiroItem.pagina_numero}`);
  console.log(`   pagina_atual = ${primeiroItem.pagina_atual}`);
  
  // Extração com prioridade clara
  if (primeiroItem.lang_code && primeiroItem.lang_code !== '') {
    langCodePrincipal = primeiroItem.lang_code;
    console.log(`   ✅ USANDO lang_code: "${langCodePrincipal}"`);
  } else if (primeiroItem.target_language === 'English') {
    langCodePrincipal = 'EN_US';
    console.log(`   ✅ USANDO target_language=English → "EN_US"`);
  } else if (primeiroItem.pasta_lingua === 'EN') {
    langCodePrincipal = 'EN_US';
    console.log(`   ✅ USANDO pasta_lingua=EN → "EN_US"`);
  } else if (primeiroItem.is_root_lang === false) {
    langCodePrincipal = primeiroItem.pasta_lingua ? `${primeiroItem.pasta_lingua}_${primeiroItem.pasta_lingua}` : 'EN_US';
    console.log(`   ⚠️ is_root_lang=false, assumindo: "${langCodePrincipal}"`);
  } else {
    console.log(`   ⚠️ Nenhum indicador encontrado, usando fallback: "PT_BR"`);
  }
}

console.log(`\n🌐 ══════════════════════════════════════════`);
console.log(`🌐 IDIOMA PRINCIPAL DEFINIDO: ${langCodePrincipal}`);
console.log(`🌐 ══════════════════════════════════════════`);

// Mostra estado do cache para ESTE idioma
console.log(`\n📊 ESTADO DO CACHE PARA [${langCodePrincipal}]:`);
if (cacheVideos[langCodePrincipal]) {
  const videosNocache = Array.from(cacheVideos[langCodePrincipal]).sort((a,b) => a-b);
  console.log(`   Total de vídeos: ${videosNocache.length}`);
  console.log(`   Páginas: [${videosNocache.join(', ')}]`);
} else {
  console.log(`   ⚠️ NENHUM vídeo no cache para este idioma!`);
}

// 5. VERIFICAR QUAIS PÁGINAS FALTAM PARA ESTE IDIOMA (APENAS INFORMATIVO)
console.log(`\n🔍 VERIFICANDO PÁGINAS FALTANTES [${langCodePrincipal}] (INFORMATIVO):`);

let paginasFaltantes = [];
for (let pag = 1; pag <= totalPaginasEsperadas; pag++) {
  if (!cacheVideos[langCodePrincipal] || !cacheVideos[langCodePrincipal].has(pag)) {
    paginasFaltantes.push(pag);
  }
}

console.log(`   Total esperado: ${totalPaginasEsperadas}`);
console.log(`   Já feitas: ${cacheVideos[langCodePrincipal]?.size || 0}`);
console.log(`   Faltantes: ${paginasFaltantes.length}`);
if (paginasFaltantes.length > 0 && paginasFaltantes.length <= 10) {
  console.log(`   Páginas faltantes: [${paginasFaltantes.join(', ')}]`);
} else if (paginasFaltantes.length > 10) {
  console.log(`   Primeiras 10 faltantes: [${paginasFaltantes.slice(0, 10).join(', ')}...]`);
}

// 6. 🔥 FIX V6.14: PROCESSA OS ITEMS RECEBIDOS SEM REDIRECIONAR PARA OUTRAS PÁGINAS
console.log(`\n✅ ════════════════════════════════════════════`);
console.log(`✅ PROCESSANDO ITEMS RECEBIDOS [${langCodePrincipal}]`);
console.log(`✅ ════════════════════════════════════════════`);

const itensParaProcessar = [];

for (const item of items) {
  const itemData = item.json || {};
  
  // 🔥 FIX CRÍTICO V6.14: Usa 'pagina' como fonte principal (vem das falas)
  // Ordem de prioridade: pagina > pagina_numero > pagina_atual
  const numPaginaOriginal = parseInt(
    itemData.pagina || 
    itemData.pagina_numero || 
    itemData.pagina_atual || 
    1, 
    10
  );
  
  console.log(`\n📄 Item analisado:`);
  console.log(`   pagina (falas) = ${itemData.pagina}`);
  console.log(`   pagina_numero = ${itemData.pagina_numero}`);
  console.log(`   pagina_atual = ${itemData.pagina_atual}`);
  console.log(`   ➡️ PÁGINA REAL DETERMINADA: ${numPaginaOriginal}`);
  
  // 🔥 ATUALIZA o item com a página correta (não sobrescreve com valor errado)
  itemData.pagina_numero = numPaginaOriginal;
  itemData.pagina_atual = numPaginaOriginal;
  
  // Verifica se já existe no cache
  const jaExisteNoCache = cacheVideos[langCodePrincipal] && cacheVideos[langCodePrincipal].has(numPaginaOriginal);
  
  if (jaExisteNoCache) {
    console.log(`   ⏭️ Pág ${numPaginaOriginal} [${langCodePrincipal}]: já existe no cache`);
    itemData._already_cached = true;
    // Ainda adiciona para que o status seja retornado corretamente
  } else {
    console.log(`   ✅ Pág ${numPaginaOriginal} [${langCodePrincipal}]: SERÁ PROCESSADA`);
    itemData._already_cached = false;
  }
  
  itensParaProcessar.push(item);
}

// Verifica se há items para processar
if (itensParaProcessar.length === 0) {
  console.log(`\n⚠️ Nenhum item recebido para processar`);
  return [{
    json: {
      status: 'no_items',
      message: 'Nenhum item recebido para processar',
      lang_code: langCodePrincipal,
      cache_info: Object.fromEntries(
        IDIOMAS_ATIVOS.map(l => [l.code, cacheVideos[l.code]?.size || 0])
      )
    }
  }];
}

// Verifica se TODOS os items já estão no cache
const todosJaCacheados = itensParaProcessar.every(item => item.json._already_cached === true);

if (todosJaCacheados) {
  console.log(`\n🎉 ════════════════════════════════════════════`);
  console.log(`🎉 TODOS OS ITEMS RECEBIDOS JÁ ESTÃO NO CACHE [${langCodePrincipal}]`);
  console.log(`🎉 ════════════════════════════════════════════`);
  
  // Retorna os items com status de já processado (para que o fluxo continue)
  items = itensParaProcessar;
  
} else {
  // Há items para processar
  items = itensParaProcessar;
  
  const itemsParaProcessarReal = itensParaProcessar.filter(item => !item.json._already_cached);
  console.log(`\n📊 RESUMO:`);
  console.log(`   Total de items recebidos: ${itensParaProcessar.length}`);
  console.log(`   Items já no cache: ${itensParaProcessar.length - itemsParaProcessarReal.length}`);
  console.log(`   Items a processar: ${itemsParaProcessarReal.length}`);
}

console.log(`\n📊 ════════════════════════════════════════════`);
console.log(`📊 INICIANDO PROCESSAMENTO [${langCodePrincipal}]`);
console.log(`📊 Items a processar: ${items.length}`);
console.log(`📊 ════════════════════════════════════════════`);

  // ══════════════════════════════════════════════════════════════════════
  // 🔥 FIM DO CACHE - Continua processamento normal
  // ══════════════════════════════════════════════════════════════════════
  // ══════════════════════════════════════════════════════════════════════
  // ══════════════════════════════════════════════════════════════════════
  // 🔥 V6.18 FIX: Função para concatenar múltiplos áudios de uma página
  // ══════════════════════════════════════════════════════════════════════
  function concatenatePageAudios(audioDir, audioFiles, numPagina, langCode) {
    if (!audioFiles || audioFiles.length === 0) {
      console.error(`❌ Nenhum áudio para concatenar na página ${numPagina}`);
      return null;
    }
    
    if (audioFiles.length === 1) {
  const singleAudio = `${audioDir}/${audioFiles[0]}`;
  console.log(`📎 [${langCode}] Página ${numPagina}: Apenas 1 áudio`);
  
  // 🔥 V6.19 FIX: Mesmo com 1 áudio, converte para MP3 se necessário
  if (audioFiles[0].endsWith('.lpcm')) {
    const mp3Output = `${audioDir}/temp_audio_pag${numPagina}_CONVERTIDO.mp3`;
    try {
      const convertCmd = `ffmpeg -y -f s16le -ar ${GLOBAL_CONFIG.audio.sampleRate} -ac ${GLOBAL_CONFIG.audio.channels} -i "${singleAudio}" -c:a libmp3lame -b:a 128k "${mp3Output}" 2>&1`;
      execSync(convertCmd, { timeout: 15000 });
      
      if (fs.existsSync(mp3Output) && fs.statSync(mp3Output).size > 0) {
        console.log(`   ✅ LPCM convertido para MP3: ${mp3Output}`);
        return mp3Output;
      }
    } catch (e) {
      console.error(`   ❌ Erro ao converter LPCM: ${e.message}`);
    }
  } else if (audioFiles[0].endsWith('.json')) {
    // ... conversão JSON
  }
  
  return singleAudio;
}
    
    console.log(`\n🔗 ════════════════════════════════════════════`);
    console.log(`🔗 CONCATENANDO ${audioFiles.length} ÁUDIOS - PÁGINA ${numPagina} [${langCode}]`);
    console.log(`🔗 ════════════════════════════════════════════`);
    
    const outputConcatenated = `${audioDir}/temp_audio_pag${numPagina}_CONCATENADO.mp3`;
    
    if (fs.existsSync(outputConcatenated)) {
      fs.unlinkSync(outputConcatenated);
    }
    
    const mp3Files = [];
    
    for (let i = 0; i < audioFiles.length; i++) {
      const audioFile = audioFiles[i];
      const fullPath = `${audioDir}/${audioFile}`;
      
      console.log(`   [${i + 1}/${audioFiles.length}] Processando: ${audioFile}`);
      
      if (!fs.existsSync(fullPath)) {
        console.warn(`   ⚠️ Arquivo não encontrado: ${fullPath}`);
        continue;
      }
      
      let mp3Path = fullPath;
      
      if (audioFile.endsWith('.lpcm')) {
        mp3Path = fullPath.replace('.lpcm', '_temp.mp3');
        
        try {
          const convertCmd = `ffmpeg -y -f s16le -ar ${GLOBAL_CONFIG.audio.sampleRate} -ac ${GLOBAL_CONFIG.audio.channels} -i "${fullPath}" -c:a libmp3lame -b:a 128k "${mp3Path}" 2>&1`;
          execSync(convertCmd, { timeout: 15000 });
          
          if (fs.existsSync(mp3Path) && fs.statSync(mp3Path).size > 0) {
            console.log(`   ✅ Convertido LPCM → MP3`);
          } else {
            console.warn(`   ⚠️ Conversão falhou para: ${audioFile}`);
            continue;
          }
        } catch (e) {
          console.error(`   ❌ Erro ao converter ${audioFile}: ${e.message}`);
          continue;
        }
        
      } else if (audioFile.endsWith('.json')) {
        const convResult = AudioConverter.convertJsonToMp3(fullPath);
        if (convResult.success) {
          mp3Path = convResult.outputPath;
          console.log(`   ✅ Convertido JSON → MP3`);
        } else {
          console.warn(`   ⚠️ Conversão JSON falhou: ${convResult.error}`);
          continue;
        }
        
      } else if (audioFile.endsWith('.mp3')) {
        console.log(`   ✅ Já é MP3`);
      }
      
      mp3Files.push(mp3Path);
    }
    
    if (mp3Files.length === 0) {
      console.error(`❌ Nenhum áudio válido após conversão`);
      return null;
    }
    
    if (mp3Files.length === 1) {
      console.log(`📎 Apenas 1 áudio válido, copiando como final`);
      fs.copyFileSync(mp3Files[0], outputConcatenated);
      return outputConcatenated;
    }
    
    const listFile = `${audioDir}/concat_list_pag${numPagina}.txt`;
    const listContent = mp3Files.map(f => `file '${f}'`).join('\n');
    fs.writeFileSync(listFile, listContent);
    
    console.log(`\n📋 Lista de concatenação:`);
    mp3Files.forEach((f, i) => console.log(`   ${i + 1}. ${f.split('/').pop()}`));
    
    try {
      const concatCmd = `ffmpeg -y -f concat -safe 0 -i "${listFile}" -c:a libmp3lame -b:a 128k "${outputConcatenated}" 2>&1`;
      execSync(concatCmd, { timeout: 30000 });
      
      if (fs.existsSync(listFile)) fs.unlinkSync(listFile);
      
      mp3Files.forEach(f => {
        if (f.includes('_temp.mp3') && fs.existsSync(f)) {
          fs.unlinkSync(f);
        }
      });
      
      if (fs.existsSync(outputConcatenated) && fs.statSync(outputConcatenated).size > 0) {
        const finalSize = fs.statSync(outputConcatenated).size;
        console.log(`\n✅ CONCATENAÇÃO CONCLUÍDA! Tamanho: ${(finalSize / 1024).toFixed(2)} KB\n`);
        return outputConcatenated;
      } else {
        throw new Error('Arquivo concatenado não foi criado');
      }
      
    } catch (e) {
      console.error(`❌ Erro na concatenação: ${e.message}`);
      if (fs.existsSync(listFile)) fs.unlinkSync(listFile);
      console.warn(`⚠️ FALLBACK: Usando primeiro áudio apenas`);
      return mp3Files[0];
    }
  }
  
// ══════════════════════════════════════════════════════════════════════
  // 🔥 V6.22: Função para detectar formato de áudio pela extensão
  // ══════════════════════════════════════════════════════════════════════
  function detectAudioFormat(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const formatMap = {
      'mp3': 'mp3',
      'ogg': 'ogg',
      'wav': 'wav',
      'lpcm': 'lpcm',
      'json': 'json',
      'm4a': 'm4a',
      'aac': 'aac',
      'flac': 'flac',
      'opus': 'opus'
    };
    return formatMap[ext] || 'mp3';
  }

  // ══════════════════════════════════════════════════════════════════════
  // 🔥 V6.22: Concatenação de áudios com suporte MULTI-FORMATO
  // ══════════════════════════════════════════════════════════════════════
  function concatenatePageAudiosV622(audioDir, audioFiles, numPagina, langCode) {
    if (!audioFiles || audioFiles.length === 0) {
      console.error(`❌ Nenhum áudio para concatenar na página ${numPagina}`);
      return null;
    }
    
    console.log(`\n🔗 ════════════════════════════════════════════`);
    console.log(`🔗 CONCATENANDO ${audioFiles.length} ÁUDIOS V6.22 - PÁGINA ${numPagina} [${langCode}]`);
    console.log(`🔗 ════════════════════════════════════════════`);
    

    // 🔥 V6.23 FIX: DEDUPLICAÇÃO - Remove arquivos duplicados (mesma fala, formatos diferentes)
const PRIORIDADE_FORMATOS = ['mp3', 'ogg', 'wav', 'm4a', 'aac', 'flac', 'opus', 'lpcm', 'json'];

const falasPorNumero = new Map();

for (const audioFile of audioFiles) {
  // Extrai número da fala do nome do arquivo
  const matchFala = audioFile.match(/fala(\d+)/i);
  const numFala = matchFala ? matchFala[1] : audioFile; // Se não tem padrão, usa nome completo
  
  const ext = audioFile.split('.').pop().toLowerCase();
  const prioridade = PRIORIDADE_FORMATOS.indexOf(ext);
  
  if (!falasPorNumero.has(numFala)) {
    falasPorNumero.set(numFala, { arquivo: audioFile, prioridade: prioridade });
  } else {
    // Já existe - compara prioridade (menor = melhor)
    const existente = falasPorNumero.get(numFala);
    if (prioridade !== -1 && (existente.prioridade === -1 || prioridade < existente.prioridade)) {
      console.log(`   🔄 Substituindo ${existente.arquivo} por ${audioFile} (formato melhor)`);
      falasPorNumero.set(numFala, { arquivo: audioFile, prioridade: prioridade });
    } else {
      console.log(`   ⏭️ Ignorando ${audioFile} (duplicado de fala${numFala})`);
    }
  }
}

// Reconstrói array apenas com arquivos únicos
const audioFilesUnicos = Array.from(falasPorNumero.values())
  .map(v => v.arquivo)
  .sort((a, b) => {
    const numA = parseInt(a.match(/fala(\d+)/i)?.[1] || '0');
    const numB = parseInt(b.match(/fala(\d+)/i)?.[1] || '0');
    return numA - numB;
  });

console.log(`📊 Deduplicação: ${audioFiles.length} arquivos → ${audioFilesUnicos.length} únicos`);
audioFiles = audioFilesUnicos;


    const outputConcatenated = `${audioDir}/temp_audio_pag${numPagina}_CONCATENADO.mp3`;
    
    if (fs.existsSync(outputConcatenated)) {
      fs.unlinkSync(outputConcatenated);
    }
    
    const mp3Files = [];
    
    for (let i = 0; i < audioFiles.length; i++) {
      const audioFile = audioFiles[i];
      const fullPath = `${audioDir}/${audioFile}`;
      const ext = audioFile.split('.').pop().toLowerCase();
      
      console.log(`   [${i + 1}/${audioFiles.length}] Processando: ${audioFile} (formato: ${ext})`);
      
      if (!fs.existsSync(fullPath)) {
        console.warn(`   ⚠️ Arquivo não encontrado: ${fullPath}`);
        continue;
      }
      
      let mp3Path = fullPath;
      
      // 🔥 V6.22: Conversão baseada no formato detectado
      if (ext === 'lpcm') {
        mp3Path = fullPath.replace('.lpcm', '_temp.mp3');
        try {
          const convertCmd = `ffmpeg -y -f s16le -ar ${GLOBAL_CONFIG.audio.sampleRate} -ac ${GLOBAL_CONFIG.audio.channels} -i "${fullPath}" -c:a libmp3lame -b:a 128k "${mp3Path}" 2>&1`;
          execSync(convertCmd, { timeout: 15000 });
          
          if (fs.existsSync(mp3Path) && fs.statSync(mp3Path).size > 0) {
            console.log(`   ✅ Convertido LPCM → MP3`);
          } else {
            console.warn(`   ⚠️ Conversão LPCM falhou`);
            continue;
          }
        } catch (e) {
          console.error(`   ❌ Erro ao converter LPCM: ${e.message}`);
          continue;
        }
        
      } else if (ext === 'ogg' || ext === 'opus') {
        // 🔥 V6.22: Conversão OGG/OPUS → MP3
        mp3Path = fullPath.replace(`.${ext}`, '_temp.mp3');
        try {
          const convertCmd = `ffmpeg -y -i "${fullPath}" -c:a libmp3lame -b:a 128k "${mp3Path}" 2>&1`;
          execSync(convertCmd, { timeout: 15000 });
          
          if (fs.existsSync(mp3Path) && fs.statSync(mp3Path).size > 0) {
            console.log(`   ✅ Convertido ${ext.toUpperCase()} → MP3`);
          } else {
            console.warn(`   ⚠️ Conversão ${ext.toUpperCase()} falhou`);
            continue;
          }
        } catch (e) {
          console.error(`   ❌ Erro ao converter ${ext.toUpperCase()}: ${e.message}`);
          continue;
        }
        
      } else if (ext === 'wav' || ext === 'm4a' || ext === 'aac' || ext === 'flac') {
        // 🔥 V6.22: Conversão WAV/M4A/AAC/FLAC → MP3
        mp3Path = fullPath.replace(`.${ext}`, '_temp.mp3');
        try {
          const convertCmd = `ffmpeg -y -i "${fullPath}" -c:a libmp3lame -b:a 128k "${mp3Path}" 2>&1`;
          execSync(convertCmd, { timeout: 15000 });
          
          if (fs.existsSync(mp3Path) && fs.statSync(mp3Path).size > 0) {
            console.log(`   ✅ Convertido ${ext.toUpperCase()} → MP3`);
          } else {
            console.warn(`   ⚠️ Conversão ${ext.toUpperCase()} falhou`);
            continue;
          }
        } catch (e) {
          console.error(`   ❌ Erro ao converter ${ext.toUpperCase()}: ${e.message}`);
          continue;
        }
        
      } else if (ext === 'json') {
        const convResult = AudioConverter.convertJsonToMp3(fullPath);
        if (convResult.success) {
          mp3Path = convResult.outputPath;
          console.log(`   ✅ Convertido JSON → MP3`);
        } else {
          console.warn(`   ⚠️ Conversão JSON falhou: ${convResult.error}`);
          continue;
        }
        
      } else if (ext === 'mp3') {
        console.log(`   ✅ Já é MP3`);
      } else {
        // 🔥 V6.22: Tenta converter qualquer formato desconhecido
        console.log(`   ⚠️ Formato desconhecido (${ext}), tentando conversão genérica...`);
        mp3Path = fullPath.replace(`.${ext}`, '_temp.mp3');
        try {
          const convertCmd = `ffmpeg -y -i "${fullPath}" -c:a libmp3lame -b:a 128k "${mp3Path}" 2>&1`;
          execSync(convertCmd, { timeout: 15000 });
          
          if (fs.existsSync(mp3Path) && fs.statSync(mp3Path).size > 0) {
            console.log(`   ✅ Convertido ${ext.toUpperCase()} → MP3 (genérico)`);
          } else {
            console.warn(`   ⚠️ Conversão genérica falhou`);
            continue;
          }
        } catch (e) {
          console.error(`   ❌ Erro na conversão genérica: ${e.message}`);
          continue;
        }
      }
      
      mp3Files.push(mp3Path);
    }
    
    if (mp3Files.length === 0) {
      console.error(`❌ Nenhum áudio válido após conversão`);
      return null;
    }
    
    if (mp3Files.length === 1) {
      console.log(`📎 Apenas 1 áudio válido, copiando como final`);
      fs.copyFileSync(mp3Files[0], outputConcatenated);
      
      // Limpa temporário se foi convertido
      if (mp3Files[0].includes('_temp.mp3') && fs.existsSync(mp3Files[0])) {
        fs.unlinkSync(mp3Files[0]);
      }
      
      return outputConcatenated;
    }
    
    const listFile = `${audioDir}/concat_list_pag${numPagina}.txt`;
    const listContent = mp3Files.map(f => `file '${f}'`).join('\n');
    fs.writeFileSync(listFile, listContent);
    
    console.log(`\n📋 Lista de concatenação:`);
    mp3Files.forEach((f, i) => console.log(`   ${i + 1}. ${f.split('/').pop()}`));
    
    try {
      const concatCmd = `ffmpeg -y -f concat -safe 0 -i "${listFile}" -c:a libmp3lame -b:a 128k "${outputConcatenated}" 2>&1`;
      execSync(concatCmd, { timeout: 30000 });
      
      if (fs.existsSync(listFile)) fs.unlinkSync(listFile);
      
      // Limpa temporários
      mp3Files.forEach(f => {
        if (f.includes('_temp.mp3') && fs.existsSync(f)) {
          fs.unlinkSync(f);
        }
      });
      
      if (fs.existsSync(outputConcatenated) && fs.statSync(outputConcatenated).size > 0) {
        const finalSize = fs.statSync(outputConcatenated).size;
        console.log(`\n✅ CONCATENAÇÃO V6.22 CONCLUÍDA! Tamanho: ${(finalSize / 1024).toFixed(2)} KB\n`);
        return outputConcatenated;
      } else {
        throw new Error('Arquivo concatenado não foi criado');
      }
      
    } catch (e) {
      console.error(`❌ Erro na concatenação: ${e.message}`);
      if (fs.existsSync(listFile)) fs.unlinkSync(listFile);
      console.warn(`⚠️ FALLBACK: Usando primeiro áudio apenas`);
      return mp3Files[0];
    }
  }

    // ══════════════════════════════════════════════════════════════════════
  // 🔥 FUNÇÃO GETPATHS V6.9 - CORRIGIDA PARA MULTI-IDIOMA
function getPaths(numPagina, itemData, nomeObra) {
    const pastaRaizObra = itemData.pasta_raiz_obra || `/tmp/youtubevideos/${nomeObra}`;
    
    // 🔥 FIX: Usa a pasta_destino_final que já vem do filtro com a pasta de idioma correta
    let pastaDestinoFinal = itemData.pasta_destino_final || pastaRaizObra;
    
    // 🔥 NOVO: Detecta lang_code do item
    const langCode = itemData.lang_code || 'PT_BR';
    const pastaLingua = itemData.pasta_lingua || 'PT';
    const isRootLang = itemData.is_root_lang !== false; // Default true para PT
    
    console.log(`🌐 Idioma detectado: ${langCode} (Pasta: ${pastaLingua}, Root: ${isRootLang})`);

    // 🔥 FIX CRÍTICO: Se não veio pasta_destino_final, monta baseado no idioma
    if (!itemData.pasta_destino_final) {
        if (isRootLang) {
            pastaDestinoFinal = pastaRaizObra;
        } else {
            pastaDestinoFinal = `${pastaRaizObra}/${pastaLingua}`;
        }
        console.log(`📁 Pasta destino construída: ${pastaDestinoFinal}`);
    }

    // IMAGEM - Busca em múltiplos locais
    const imgCandidates = [
        `${pastaRaizObra}/${numPagina}_editado.jpg`,
        `${pastaRaizObra}/i/${numPagina}.jpg`,
        `${pastaRaizObra}/${numPagina}.jpg`,
        `${pastaRaizObra}/images/original/${numPagina}.jpg`,
        `${pastaDestinoFinal}/images/${numPagina}_editado.jpg`,
        `${pastaDestinoFinal}/i/${numPagina}.jpg`
    ];
    
    let imagePath = null;
    let imagePathOriginal = null;
    
    for (const cand of imgCandidates) {
        if (fs.existsSync(cand)) {
            imagePath = cand;
            imagePathOriginal = cand;
            console.log(`✅ Imagem encontrada: ${cand}`);
            break;
        }
    }
    
    if (!imagePath) {
        imagePath = imgCandidates[0];
        imagePathOriginal = imgCandidates[1];
        console.warn(`⚠️ Nenhuma imagem encontrada para página ${numPagina}, usando fallback: ${imagePath}`);
    }

    // TRILHA & MEME
    let trilhaPath = fs.existsSync(`${pastaRaizObra}/${nomeObra}_trilha.mp3`) 
      ? `${pastaRaizObra}/${nomeObra}_trilha.mp3` 
      : `${pastaRaizObra}/trilha.mp3`;
    
    if (!fs.existsSync(trilhaPath)) {
      trilhaPath = `/tmp/youtubevideos/trilha.mp3`;
      console.warn(`⚠️ Trilha não encontrada, usando padrão: ${trilhaPath}`);
    } else {
      console.log(`✅ Trilha encontrada: ${trilhaPath}`);
    }

    let memePath = fs.existsSync(`${pastaRaizObra}/${nomeObra}_meme_transicao.mp4`) 
      ? `${pastaRaizObra}/${nomeObra}_meme_transicao.mp4` 
      : `${pastaRaizObra}/meme_transicao.mp4`;
    
    if (!fs.existsSync(memePath)) {
      memePath = `/tmp/youtubevideos/meme_transicao.mp4`;
      console.warn(`⚠️ Meme não encontrado, usando padrão: ${memePath}`);
    } else {
      console.log(`✅ Meme encontrado: ${memePath}`);
    }

    // 🔥 FIX CRÍTICO: LEGENDA - Busca na pasta do idioma correto
    const subCandidates = [
        `${pastaDestinoFinal}/legenda_pag_${numPagina}.ass`,
        `${pastaDestinoFinal}/legenda_pag_${numPagina}.srt`,
        // Fallback para raiz (caso não encontre na pasta de idioma)
        `${pastaRaizObra}/legenda_pag_${numPagina}.ass`,
        `${pastaRaizObra}/legenda_pag_${numPagina}.srt`
    ];
    
    let subtitlePath = null;
    for (const cand of subCandidates) {
        if (fs.existsSync(cand)) { 
            subtitlePath = cand;
            console.log(`✅ Legenda encontrada: ${cand} (${cand.endsWith('.ass') ? 'Karaoke' : 'SRT'})`);
            break; 
        }
    }
    
    if (!subtitlePath) {
        subtitlePath = subCandidates[0];
        console.warn(`⚠️ Nenhuma legenda encontrada para página ${numPagina}, usando fallback: ${subtitlePath}`);
    }
// 🔥 FIX CRÍTICO V6.22: ÁUDIO - Busca em TODOS OS FORMATOS
    const audioDir = `${pastaDestinoFinal}/audio/temp`;
    let audioFinalPath = "";
    let todosAudiosDaPagina = [];
    let audioFormat = "mp3";

    // 🔥 V6.22: Lista de TODOS os formatos de áudio suportados
    const FORMATOS_AUDIO_SUPORTADOS = ['ogg', 'mp3', 'lpcm', 'wav', 'json', 'm4a', 'aac', 'flac', 'opus'];

    console.log(`🔍 [${langCode}] Buscando áudios da página ${numPagina} em: ${audioDir}`);
    console.log(`🔍 [${langCode}] Formatos suportados: ${FORMATOS_AUDIO_SUPORTADOS.join(', ')}`);

    if (fs.existsSync(audioDir)) {
        try {
            const files = fs.readdirSync(audioDir);
            
            // 🔥 V6.22: Regex atualizado para incluir TODOS os formatos
            const formatosRegex = FORMATOS_AUDIO_SUPORTADOS.join('|');
            
            todosAudiosDaPagina = files
                .filter(f => {
                    // Padrão 1: temp_audio_pag{N}_fala{M}.{ext}
                    const regex1 = new RegExp(`^temp_audio_pag${numPagina}_fala\\d+\\.(${formatosRegex})$`, 'i');
                    // Padrão 2: audio_pag{N}_fala{M}.{ext}
                    const regex2 = new RegExp(`^audio_pag${numPagina}_fala\\d+\\.(${formatosRegex})$`, 'i');
                    // Padrão 3: pag{N}_fala{M}.{ext}
                    const regex3 = new RegExp(`^pag${numPagina}_fala\\d+\\.(${formatosRegex})$`, 'i');
                    // Padrão 4: {N}_fala{M}.{ext} ou fala{M}_pag{N}.{ext}
                    const regex4 = new RegExp(`^${numPagina}_fala\\d+\\.(${formatosRegex})$`, 'i');
                    const regex5 = new RegExp(`^fala\\d+_pag${numPagina}\\.(${formatosRegex})$`, 'i');
                    
                    return regex1.test(f) || regex2.test(f) || regex3.test(f) || regex4.test(f) || regex5.test(f);
                })
                .sort((a, b) => {
                    const numA = parseInt(a.match(/fala(\d+)/i)?.[1] || '0');
                    const numB = parseInt(b.match(/fala(\d+)/i)?.[1] || '0');
                    return numA - numB;
                });
            
            // 🔥 V6.22: Se não encontrou com padrões específicos, busca por nome base
            if (todosAudiosDaPagina.length === 0) {
                console.log(`⚠️ [${langCode}] Nenhum áudio com padrão específico, buscando por nome base...`);
                
                // Busca qualquer arquivo que contenha o número da página
                todosAudiosDaPagina = files.filter(f => {
                    const lowerF = f.toLowerCase();
                    const temNumeroPagina = lowerF.includes(`pag${numPagina}`) || 
                                            lowerF.includes(`pag_${numPagina}`) ||
                                            lowerF.includes(`pagina${numPagina}`) ||
                                            lowerF.includes(`pagina_${numPagina}`) ||
                                            lowerF.match(new RegExp(`[_-]${numPagina}[_-]`)) ||
                                            lowerF.startsWith(`${numPagina}_`) ||
                                            lowerF.startsWith(`${numPagina}.`);
                    
                    const temExtensaoAudio = FORMATOS_AUDIO_SUPORTADOS.some(ext => lowerF.endsWith(`.${ext}`));
                    
                    return temNumeroPagina && temExtensaoAudio;
                }).sort();
                
                if (todosAudiosDaPagina.length > 0) {
                    console.log(`✅ [${langCode}] Encontrado(s) ${todosAudiosDaPagina.length} áudio(s) por busca flexível`);
                }
            }
            
            console.log(`📂 [${langCode}] Página ${numPagina}: ${todosAudiosDaPagina.length} áudio(s) encontrado(s):`);
            todosAudiosDaPagina.forEach(f => console.log(`   - ${f}`));
            
            if (todosAudiosDaPagina.length > 0) {
                // 🔥 V6.22: Concatena TODOS os áudios da página (com suporte a multi-formato)
                const concatenatedAudio = concatenatePageAudiosV622(audioDir, todosAudiosDaPagina, numPagina, langCode);
                
                if (concatenatedAudio && fs.existsSync(concatenatedAudio)) {
                    audioFinalPath = concatenatedAudio;
                    audioFormat = 'mp3'; // Sempre converte para MP3 no final
                    console.log(`🎵 [${langCode}] Áudio final: ${audioFinalPath} (Formato: ${audioFormat})`);
                } else {
                    // Fallback: usa primeiro áudio encontrado
                    audioFinalPath = `${audioDir}/${todosAudiosDaPagina[0]}`;
                    audioFormat = detectAudioFormat(todosAudiosDaPagina[0]);
                    console.warn(`⚠️ Concatenação falhou, usando primeiro áudio: ${audioFinalPath}`);
                }
            }
        } catch(e) {
            console.error(`❌ [${langCode}] Erro ao ler diretório de áudio: ${e.message}`);
        }
    } else {
        console.warn(`⚠️ [${langCode}] Diretório de áudio não existe: ${audioDir}`);
    }

    // 🔥 V6.22: Fallback MELHORADO - busca em QUALQUER formato
    if (!audioFinalPath || !fs.existsSync(audioFinalPath)) {
        console.log(`⚠️ [${langCode}] Áudio não encontrado com métodos anteriores, tentando busca direta...`);
        
        if (fs.existsSync(audioDir)) {
            const files = fs.readdirSync(audioDir);
            
            for (const ext of FORMATOS_AUDIO_SUPORTADOS) {
                // Tenta vários padrões de nome
                const candidatos = [
                    `temp_audio_pag${numPagina}_fala1.${ext}`,
                    `temp_audio_pag${numPagina}.${ext}`,
                    `audio_pag${numPagina}_fala1.${ext}`,
                    `audio_pag${numPagina}.${ext}`,
                    `pag${numPagina}_fala1.${ext}`,
                    `pag${numPagina}.${ext}`,
                    `${numPagina}_fala1.${ext}`,
                    `${numPagina}.${ext}`
                ];
                
                for (const candidato of candidatos) {
                    // Busca case-insensitive
                    const encontrado = files.find(f => f.toLowerCase() === candidato.toLowerCase());
                    if (encontrado) {
                        audioFinalPath = `${audioDir}/${encontrado}`;
                        audioFormat = detectAudioFormat(encontrado);
                        console.log(`✅ [${langCode}] Áudio encontrado via busca direta: ${audioFinalPath} (${audioFormat})`);
                        break;
                    }
                }
                
                if (audioFinalPath && fs.existsSync(audioFinalPath)) break;
            }
        }
    }

    // Fallback se nenhum áudio foi encontrado
    if (!audioFinalPath) {
        audioFinalPath = `${audioDir}/temp_audio_pag${numPagina}_fala1.lpcm`;
        audioFormat = 'lpcm';
        console.warn(`⚠️ [${langCode}] Nenhum áudio encontrado para página ${numPagina}, usando fallback: ${audioFinalPath}`);
    }

    // 🔥 FIX: Output na pasta do idioma correto
    const outputPath = `${pastaDestinoFinal}/videos/video_pag_${numPagina}.mp4`;
    const relatorioPath = `${pastaDestinoFinal}/reports/relatorio_efeitos_pag_${numPagina}.txt`;

    console.log(`📁 [${langCode}] Paths finais:`);
    console.log(`   Vídeo: ${outputPath}`);
    console.log(`   Relatório: ${relatorioPath}`);

    return {
      imagePathOriginal, imagePath, audioFinalPath, subtitlePath,
      outputPath, relatorioPath, trilhaPath, memePath,
      pastaDestinoFinal, pastaRaizObra, todosAudiosDaPagina,
      audioFormat,
      langCode, // 🔥 NOVO: Retorna lang_code
      pastaLingua, // 🔥 NOVO: Retorna pasta_lingua
      isRootLang // 🔥 NOVO: Retorna is_root_lang
    };
  }
  
  // 🔥 PROCESSAMENTO SEQUENCIAL POR PÁGINA
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (item.binary) delete item.binary; 
    
    const itemData = item.json || {};
    if (itemData.reset_loop) {
      console.log(`🔄 Reset loop detectado, pulando item ${i}`);
      continue;
    }
    
    // 🔥 EXTRAÇÃO DO NOME DA OBRA
    let nomeObra = "My_Fake_Girlfriend";
    try {
      const configNode = $('Start').first().json.Configura_Obra1_firstItem_firstItem_firstItem;
      if (configNode?.json?.nome_obra) nomeObra = configNode.json.nome_obra;
      else if (configNode?.nome_obra) nomeObra = configNode.nome_obra;
      if (itemData.pasta_id) nomeObra = itemData.pasta_id;
      console.log(`📚 Nome da obra: ${nomeObra}`);
    } catch(e) {
      console.warn(`⚠️ Erro ao extrair nome da obra, usando padrão: ${nomeObra}`);
    }
    
    // 🔥 FIX CRÍTICO: INCREMENTO CORRETO DE PÁGINA
    const numPagina = itemData.pagina_numero || (i + 1);
    
    console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    console.log(`🎬 PROCESSANDO PÁGINA ${numPagina} (Item ${i + 1}/${items.length})`);
    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    
    const textoNarracao = itemData.texto_para_tts || "";
    
    const paths = getPaths(numPagina, itemData, nomeObra);
    ensureFolders(paths.pastaDestinoFinal);
    
    // ══════════════════════════════════════════════════════════════════════
    // 🔊 PROCESSAMENTO DE EFEITOS SONOROS CONTEXTUAIS
    // ══════════════════════════════════════════════════════════════════════
    let soundEffectsResult = { hasEffects: false, effectsTrackPath: null, effects: [] };
    
    try {
      // Estima duração baseada no áudio (se disponível)
      let estimatedDuration = 30; // Fallback
      
      if (paths.audioFinalPath && fs.existsSync(paths.audioFinalPath)) {
        try {
          const durationCmd = `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${paths.audioFinalPath}" 2>&1`;
          const durationStr = execSync(durationCmd, { timeout: 5000 }).toString().trim();
          estimatedDuration = parseFloat(durationStr) || 30;
          console.log(`⏱️ Duração estimada do áudio: ${estimatedDuration.toFixed(2)}s`);
        } catch (e) {
          console.warn(`⚠️ Não foi possível detectar duração do áudio: ${e.message}`);
        }
      }
      
      // Processa efeitos sonoros
      soundEffectsResult = SoundEffectsProcessor.process(
        paths.subtitlePath,
        paths.pastaDestinoFinal,
        numPagina,
        estimatedDuration + 5 // Adiciona buffer
      );
      
      if (soundEffectsResult.hasEffects) {
        console.log(`✅ ${soundEffectsResult.effectsCount} efeitos sonoros serão adicionados`);
        
        item.json.soundEffects = {
          enabled: true,
          trackPath: soundEffectsResult.effectsTrackPath,
          count: soundEffectsResult.effectsCount,
          effects: soundEffectsResult.effects.map(e => ({
            keyword: e.keyword,
            timestamp: e.timestamp,
            file: e.effectFile,
            volume: e.volume
          }))
        };
      } else {
        item.json.soundEffects = { enabled: false, count: 0 };
      }
      
    } catch (sfxError) {
      console.error(`❌ Erro no processamento de efeitos sonoros: ${sfxError.message}`);
      item.json.soundEffects = { enabled: false, error: sfxError.message };
    }
    /// Limpa temporários antigos
AudioConverter.cleanupOldTempFiles(`${paths.pastaDestinoFinal}/audio/temp`);

// ======================================================================
// 🔥 VERIFICAÇÃO: VÍDEO JÁ EXISTE? (MODO HÍBRIDO)
// ======================================================================
const forceReprocess = itemData.force_reprocess || false;
const skipExisting = itemData.skip_existing !== false; // Default = true

if (skipExisting && FileValidator.isValid(paths.outputPath) && !forceReprocess) {
  console.log(`✅ Vídeo já existe: ${paths.outputPath}`);
  console.log(`⏭️ Pulando página ${numPagina} (já processada)`);
  
  item.json.status = 'already_processed';
  item.json.outputPath = paths.outputPath;
  item.json.pagina_numero = numPagina;
  item.json.filesUsed = {
    audio: paths.audioFinalPath,
    audioFormato: paths.audioFormat,
    legenda: paths.subtitlePath,
    imagem: paths.imagePath,
    trilha: paths.trilhaPath,
    meme: paths.memePath
  };
  
  validItems.push(item);
  continue;
}

if (forceReprocess && FileValidator.isValid(paths.outputPath)) {
  console.log(`🔄 FORÇANDO reprocessamento da página ${numPagina} (force_reprocess=true)`);
}

if (!skipExisting) {
  console.log(`🔄 Modo: processar todas as páginas (skip_existing=false)`);
}

console.log(`🔄 Iniciando processamento da página ${numPagina}...`);

// ======================================================================
// 🔥 DEBUG: Informações de paths encontrados
// ======================================================================
item.json.debugPaths = {
    paginaProcessada: numPagina,
    pasta: paths.pastaDestinoFinal,
    audioEncontrado: paths.audioFinalPath,
    audioFormato: paths.audioFormat,
    todosAudiosDaPagina: paths.todosAudiosDaPagina,
    legendaEncontrada: paths.subtitlePath,
    imagemEncontrada: paths.imagePath,
    videoJaExiste: FileValidator.isValid(paths.outputPath),
    skipExisting: skipExisting,
    forceReprocess: forceReprocess
};

// ======================================================================
// 🔥 PROCESSAMENTO DA IMAGEM
// ======================================================================
if (!FileValidator.isValid(paths.imagePath)) {
    console.log(`⚠️ Imagem não encontrada: ${paths.imagePath}`);
    if (FileValidator.isValid(paths.imagePathOriginal)) {
         console.log(`🔧 Aplicando efeito visual em: ${paths.imagePathOriginal}`);
         const visualResult = ImageProcessor.applyVisualEffect(
           paths.imagePathOriginal, 
           paths.imagePath, 
           `${numPagina}.jpg`
         );
         
         if (visualResult.success) {
           console.log(`✅ Efeito visual aplicado: ${visualResult.filterName} (Legibilidade: ${visualResult.readability}/10)`);
         } else {
           console.error(`❌ Falha ao aplicar efeito visual: ${visualResult.error}`);
         }
    }
}

// ======================================================================
// 🔥 VALIDAÇÃO GERAL DE ARQUIVOS NECESSÁRIOS
// ======================================================================
const validation = FileValidator.validate({ 
    'Imagem': paths.imagePath, 
    'Audio': paths.audioFinalPath, 
    'Legenda': paths.subtitlePath,
    'Meme': paths.memePath
});

if (!validation.valid) {
  console.log(`❌ Validação falhou para página ${numPagina}:`);
  validation.errors.forEach(err => console.log(`   - ${err}`));
  
  item.json.erro_validacao = validation.errors.join('; ');
  item.json.pagina_numero = numPagina;
  item.json.status = 'validation_failed';
  
  validItems.push(item);
  continue; 
}


    
    console.log(`✅ Todos os arquivos necessários encontrados`);
    
    // 🔥 CONVERSOR V6.8 - JSON/LPCM → MP3 (ELIMINA CHIADO)
    if (paths.audioFormat === 'json') {
        console.log(`\n🎵 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
        console.log(`🎵 ━━━ CONVERSÃO DE ÁUDIO V6.8 (JSON→MP3) ━━━`);
        console.log(`🎵 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
        console.log(`📂 Arquivo JSON: ${paths.audioFinalPath}`);
        
        const conversionResult = AudioConverter.convertJsonToMp3(paths.audioFinalPath);
        
        if (conversionResult.success) {
            console.log(`✅ ━━━ CONVERSÃO BEM-SUCEDIDA! ━━━`);
            console.log(`📁 Arquivo MP3: ${conversionResult.outputPath}`);
            console.log(`📏 Tamanho: ${(conversionResult.size / 1024).toFixed(2)} KB`);
            console.log(`⚙️ Método: ${conversionResult.method}`);
            
            if (conversionResult.sampleRate) {
              console.log(`🎵 Sample Rate: ${conversionResult.sampleRate} Hz (Fix Chiado)`);
            }
            
            if (conversionResult.note) {
              console.log(`📝 Nota: ${conversionResult.note}`);
            }
            
            // Atualiza caminho do áudio E formato
            paths.audioFinalPath = conversionResult.outputPath;
            paths.audioFormat = conversionResult.audioFormat || 'mp3';
            
            item.json.audioConversion = {
                originalFile: conversionResult.originalPath,
                convertedFile: conversionResult.outputPath,
                size: conversionResult.size,
                sampleRate: conversionResult.sampleRate || GLOBAL_CONFIG.audio.sampleRate,
                method: conversionResult.method,
                format: conversionResult.audioFormat || 'mp3',
                warning: conversionResult.warning || null,
                note: conversionResult.note || null
            };
            
        } else {
            console.error(`❌ ━━━ FALHA NA CONVERSÃO! ━━━`);
            console.error(`⚠️ Erro: ${conversionResult.error}`);
            
            item.json.audioConversion = {
                originalFile: conversionResult.originalPath,
                error: conversionResult.error,
                success: false
            };
            
            // Tenta usar arquivo mesmo com erro
            if (conversionResult.outputPath && fs.existsSync(conversionResult.outputPath)) {
                console.log(`⚠️ Usando arquivo gerado mesmo com erro...`);
                paths.audioFinalPath = conversionResult.outputPath;
                paths.audioFormat = 'mp3';
            } else {
                console.error(`❌ Conversão falhou completamente, não é possível prosseguir`);
                item.json.erro_validacao = `Conversão de áudio falhou: ${conversionResult.error}`;
                item.json.pagina_numero = numPagina;
                item.json.status = 'audio_conversion_failed';
                validItems.push(item);
                continue;
            }
        }
        
        console.log(`🎵 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);
        
    } else if (paths.audioFormat === 'lpcm') {
        console.log(`\n🎵 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
        console.log(`🎵 ━━━ CONVERSÃO DE ÁUDIO V6.8 (LPCM→MP3) ━━━`);
        console.log(`🎵 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
        console.log(`🔄 Convertendo LPCM para MP3: ${paths.audioFinalPath}`);
        
        const lpcmPath = paths.audioFinalPath;
        const mp3Path = lpcmPath.replace('.lpcm', '_converted.mp3');
        
        // 🔥 FIX CHIADO: Usa sample rate da configuração global
        const sampleRate = GLOBAL_CONFIG.audio.sampleRate;
        const channels = GLOBAL_CONFIG.audio.channels;
        
        const convertCmd = `ffmpeg -y -f s16le -ar ${sampleRate} -ac ${channels} -i "${lpcmPath}" -c:a libmp3lame -b:a 128k "${mp3Path}" 2>&1`;
        
        try {
            console.log(`⚙️ Configuração: ${sampleRate} Hz, ${channels} canal(is)`);
            
            const ffmpegOutput = execSync(convertCmd, { timeout: 10000 }).toString();
            
            if (fs.existsSync(mp3Path) && fs.statSync(mp3Path).size > 0) {
                const mp3Size = fs.statSync(mp3Path).size;
                console.log(`✅ Conversão LPCM→MP3 bem-sucedida`);
                console.log(`📁 Arquivo: ${mp3Path}`);
                console.log(`📏 Tamanho: ${(mp3Size / 1024).toFixed(2)} KB`);
                
                paths.audioFinalPath = mp3Path;
                paths.audioFormat = 'mp3';
                
                item.json.audioConversion = {
                    originalFile: lpcmPath,
                    convertedFile: mp3Path,
                    method: 'lpcm_to_mp3',
                    size: mp3Size,
                    format: 'mp3',
                    sampleRate: sampleRate,
                    channels: channels
                };
            } else {
                throw new Error('Arquivo MP3 não gerado ou vazio');
            }
        } catch (convErr) {
            console.error(`❌ Erro na conversão LPCM: ${convErr.message}`);
            console.log(`⚠️ Mantendo arquivo LPCM original (pode causar problemas)`);
            
            item.json.audioConversion = {
                originalFile: lpcmPath,
                error: convErr.message,
                method: 'lpcm_failed',
                format: 'lpcm',
                fallback: 'using_lpcm',
                warning: 'Conversão falhou, usando LPCM original (pode causar chiado)'
            };
        }
        
        console.log(`🎵 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);
        
    } else if (paths.audioFormat === 'mp3') {
        console.log(`✅ Áudio já está em MP3, sem necessidade de conversão`);
        console.log(`📁 Arquivo: ${paths.audioFinalPath}`);
        
        try {
            const mp3Size = fs.statSync(paths.audioFinalPath).size;
            console.log(`📏 Tamanho: ${(mp3Size / 1024).toFixed(2)} KB`);
            
            // Valida sample rate do MP3 existente
            try {
                const probeCmd = `ffprobe -v error -select_streams a:0 -show_entries stream=sample_rate -of default=noprint_wrappers=1:nokey=1 "${paths.audioFinalPath}" 2>&1`;
                const detectedRate = execSync(probeCmd, { timeout: 5000 }).toString().trim();
                
                if (detectedRate && !isNaN(parseInt(detectedRate))) {
                    const sampleRate = parseInt(detectedRate);
                    console.log(`🎵 Sample Rate detectado: ${sampleRate} Hz`);
                    
                    item.json.audioConversion = {
                        originalFile: paths.audioFinalPath,
                        method: 'already_mp3',
                        size: mp3Size,
                        format: 'mp3',
                        sampleRate: sampleRate,
                        note: 'Arquivo já estava em formato MP3'
                    };
                } else {
                    throw new Error('Sample rate não detectado');
                }
            } catch(probeErr) {
                console.warn(`⚠️ Não foi possível detectar sample rate: ${probeErr.message}`);
                
                item.json.audioConversion = {
                    originalFile: paths.audioFinalPath,
                    method: 'already_mp3',
                    size: mp3Size,
                    format: 'mp3',
                    note: 'Arquivo já estava em formato MP3 (sample rate não detectado)'
                };
            }
            
        } catch(statErr) {
            console.warn(`⚠️ Erro ao obter informações do arquivo: ${statErr.message}`);
            
            item.json.audioConversion = {
                originalFile: paths.audioFinalPath,
                method: 'already_mp3',
                format: 'mp3',
                warning: 'Não foi possível validar arquivo MP3'
            };
        }
    } else {
        console.warn(`⚠️ Formato de áudio desconhecido: ${paths.audioFinalPath}`);
        console.warn(`⚠️ Tentando usar arquivo mesmo assim (pode causar erros)`);
        
        item.json.audioConversion = {
            originalFile: paths.audioFinalPath,
            method: 'unknown_format',
            format: paths.audioFormat,
            warning: 'Formato de áudio não reconhecido, usando arquivo original'
        };
    }
    
    // Validação final do áudio após conversão
    if (!FileValidator.isValid(paths.audioFinalPath)) {
        console.error(`❌ ERRO CRÍTICO: Áudio final não é válido: ${paths.audioFinalPath}`);
        item.json.erro_validacao = `Áudio final inválido após conversão: ${paths.audioFinalPath}`;
        item.json.pagina_numero = numPagina;
        item.json.status = 'audio_invalid';
        validItems.push(item);
        continue;
    }
    
    console.log(`✅ Áudio validado com sucesso: ${paths.audioFinalPath}`);
    console.log(`📊 Formato final do áudio: ${paths.audioFormat.toUpperCase()}`);
   
    // Detecção de dimensões da imagem
    console.log(`\n📐 Analisando dimensões da imagem...`);
    const dimensoes = ImageProcessor.detectDimensions(paths.imagePath);
    console.log(`   Largura: ${dimensoes.largura}px`);
    console.log(`   Altura: ${dimensoes.altura}px`);
    console.log(`   Aspect Ratio: ${dimensoes.ratio.toFixed(2)}`);
    console.log(`   Tipo: ${dimensoes.ehAlongado ? 'ALONGADO (Manhwa)' : 'NORMAL'}`);
    
    // ══════════════════════════════════════════════════════════════════════
    // 🔥 V6.21: VERIFICAÇÃO DE PÁGINAS ANTERIORES FALTANTES
    // ══════════════════════════════════════════════════════════════════════
    let missingPagesInfo = { hasMissing: false, missingPages: [], imagePaths: [], count: 0 };
    
    try {
      // Usa o cache do idioma atual para verificar páginas processadas
      const cacheDoIdioma = cacheVideos[paths.langCode] || new Set();
      
      missingPagesInfo = MissingPagesHandler.checkMissingPreviousPages(
        numPagina,
        cacheDoIdioma,
        paths.pastaRaizObra,
        5 // Máximo de 5 páginas anteriores a incluir
      );
      
      if (missingPagesInfo.hasMissing) {
        console.log(`⚠️ ATENÇÃO: ${missingPagesInfo.count} página(s) anterior(es) serão incluídas neste vídeo`);
        console.log(`   Páginas: [${missingPagesInfo.missingPages.join(', ')}]`);
        
        // Salva info no item para rastreamento
        item.json.missingPagesIncluded = {
          enabled: true,
          pages: missingPagesInfo.missingPages,
          images: missingPagesInfo.imagePaths,
          count: missingPagesInfo.count
        };
      } else {
        item.json.missingPagesIncluded = { enabled: false, count: 0 };
      }
      
    } catch (missingErr) {
      console.error(`❌ Erro ao verificar páginas faltantes: ${missingErr.message}`);
      item.json.missingPagesIncluded = { enabled: false, error: missingErr.message };
    }
    
    // Seleção de efeitos visuais
    console.log(`\n🎬 Selecionando efeitos visuais...`);
    const transitionEffect = effectsManager.getNext('transicoes');
    console.log(`   Transição: ${transitionEffect}`);
    
    const contextualEffect = contextualSelector.select(
      textoNarracao, 
      dimensoes, 
      itemData.moveFilter, 
      paths.imagePath
    );
    
    console.log(`   Movimento: ${contextualEffect.nome}`);
    console.log(`   Tipo: ${contextualEffect.tipo}`);
    console.log(`   Intensidade: ${contextualEffect.intensidade}`);
    
    if (contextualEffect.contextDetected) {
      console.log(`   ✅ Contexto detectado na narração`);
    }
    
    const movement = contextualEffect.filtro;
    const filterChain = CommandBuilder.buildFilterChain(effectsManager, movement);
    

   // ══════════════════════════════════════════════════════════════════════
    // 🔥 V6.21: CALCULA DURAÇÕES SE HÁ PÁGINAS FALTANTES
    // ══════════════════════════════════════════════════════════════════════
    let missingPagesWithDurations = { ...missingPagesInfo };
    
    if (missingPagesInfo.hasMissing) {
      try {
        // Detecta duração do áudio
        let audioDuration = 30;
        if (fs.existsSync(paths.audioFinalPath)) {
          const durationCmd = `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${paths.audioFinalPath}" 2>&1`;
          const durationStr = execSync(durationCmd, { timeout: 5000 }).toString().trim();
          audioDuration = parseFloat(durationStr) || 30;
        }
        
        // Calcula durações proporcionais
        const durationInfo = MissingPagesHandler.calculateDurations(
          missingPagesInfo.count + 1, // +1 para página atual
          audioDuration,
          0.6 // 60% do tempo para página atual
        );
        
        missingPagesWithDurations.imageDurations = [
          ...Array(missingPagesInfo.count).fill(durationInfo.missingPageDuration),
          durationInfo.currentPageDuration
        ];
        
        console.log(`📊 Durações calculadas:`);
        console.log(`   Páginas anteriores: ${durationInfo.missingPageDuration.toFixed(2)}s cada`);
        console.log(`   Página atual: ${durationInfo.currentPageDuration.toFixed(2)}s`);
        
      } catch (durErr) {
        console.warn(`⚠️ Erro ao calcular durações: ${durErr.message}`);
        // Fallback: 3s por página faltante
        missingPagesWithDurations.imageDurations = [
          ...Array(missingPagesInfo.count).fill(3),
          10
        ];
      }
    }
    
    // Construção do comando FFmpeg
    console.log(`\n⚙️ Construindo comando FFmpeg...`);
    const commands = CommandBuilder.buildCommand({
      folderPath: paths.pastaDestinoFinal, 
      numPagina,
      imagePath: paths.imagePath,
      missingPagesInfo: missingPagesWithDurations, // 🔥 V6.21: Info das páginas faltantes
      subtitlePath: paths.subtitlePath, 
      subtitleStyle: itemData.subtitleStyle || GLOBAL_CONFIG.subtitle.defaultStyle,
      audioFinalPath: paths.audioFinalPath,
      audioFormat: paths.audioFormat,
      trilhaPath: paths.trilhaPath, 
      memePath: paths.memePath, 
      outputPath: paths.outputPath, 
      filterChain,
      transitionEffect,
      narrationText: textoNarracao,
      pastaDestinoFinal: paths.pastaDestinoFinal,
      pastaRaizObra: paths.pastaRaizObra,
      soundEffectsPath: soundEffectsResult.effectsTrackPath
    });
    
    console.log(`✅ Comando construído com sucesso`);
    
    // Geração do relatório
    console.log(`\n📊 Gerando relatório...`);
    const reportContent = ReportGenerator.generate({
       numPagina, 
       outputPath: paths.outputPath, 
       dimensoes, 
       contextualEffect, 
       effects: { 
         movimento: movement, 
         blur: commands.filterChain,
         transition: transitionEffect
       }, 
       imagePath: paths.imagePath, 
       audioFinalPath: paths.audioFinalPath, 
       subtitlePath: paths.subtitlePath, 
       trilhaPath: paths.trilhaPath, 
       memePath: paths.memePath, 
       movement, 
       narrationText: textoNarracao
    });
    
    const createRelatorioCmd = `cat > "${paths.relatorioPath}" << 'EOFRELATORIO'\n${reportContent}\nEOFRELATORIO`;
    commands.createRelatorioCmd = createRelatorioCmd;
    
    console.log(`✅ Relatório gerado: ${paths.relatorioPath}`);
    
    // Script final de processamento
    console.log(`\n🎬 Montando script final de processamento...`);
    const finalScript = CommandBuilder.buildFinalScript(commands, {
      audioFinalPath: paths.audioFinalPath,
      audioFormat: paths.audioFormat, // 🔥 NOVO
      videoBaseTemp: commands.videoBaseTemp,
      outputPath: paths.outputPath,
      numPagina,
      contextualEffect
    });
    
    console.log(`✅ Script final montado`);
    
    // Salva informações no item
    item.json.generatedCommand = finalScript;
    item.json.outputPath = paths.outputPath;
    item.json.outputPathHD = paths.outputPath.replace('.mp4', '_HD.mp4');
    item.json.outputPathSemTrilha = paths.outputPath.replace('.mp4', '_sem_trilha.mp4');
    item.json.folderStructure = 'ORGANIZADO_V6.8';
    item.json.status = 'ready_to_process';
    
    // 🔥 CRÍTICO: Salva número da página para próxima execução
    item.json.pagina_numero = numPagina;
    
    item.json.filesUsed = { 
        audio: paths.audioFinalPath,
        audioFormato: paths.audioFormat,
        audioOriginal: paths.todosAudiosDaPagina.length > 0 ? `${paths.pastaDestinoFinal}/audio/temp/${paths.todosAudiosDaPagina[0]}` : null,
        todosAudios: paths.todosAudiosDaPagina,
        legenda: paths.subtitlePath,
        legendaTipo: paths.subtitlePath.endsWith('.ass') ? 'ASS (Karaoke)' : 'SRT',
        imagem: paths.imagePath,
        trilha: paths.trilhaPath,
        meme: paths.memePath
    };
    
    item.json.effectsApplied = {
        visual: contextualEffect.nome,
        transition: transitionEffect,
        movement: contextualEffect.tipo,
        intensity: contextualEffect.intensidade,
        contextDetected: contextualEffect.contextDetected || false
    };
    
    item.json.videoSpecs = {
        workingResolution: GLOBAL_CONFIG.outputFormat.workingResolution,
        finalResolution: GLOBAL_CONFIG.outputFormat.finalResolution,
        fps: GLOBAL_CONFIG.outputFormat.fps,
        codec: GLOBAL_CONFIG.outputFormat.videoCodec,
        crf: GLOBAL_CONFIG.outputFormat.crf,
        preset: GLOBAL_CONFIG.outputFormat.preset
    };
    
    item.json.audioSpecs = {
        format: paths.audioFormat,
        sampleRate: item.json.audioConversion?.sampleRate || GLOBAL_CONFIG.audio.sampleRate,
        channels: GLOBAL_CONFIG.audio.channels,
        musicVolume: GLOBAL_CONFIG.audio.musicVolume,
        ducking: GLOBAL_CONFIG.audio.ducking.enabled,
        normalization: GLOBAL_CONFIG.audio.normalization.enabled
    };
    
    console.log(`\n✅ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    console.log(`✅ PÁGINA ${numPagina} CONFIGURADA COM SUCESSO`);
    console.log(`✅ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    console.log(`📊 RESUMO:`);
    console.log(`   🎵 Áudio: ${paths.audioFinalPath.split('/').pop()} (${paths.audioFormat.toUpperCase()})`);
    console.log(`   📝 Legenda: ${paths.subtitlePath.split('/').pop()}`);
    console.log(`   🖼️ Imagem: ${paths.imagePath.split('/').pop()}`);
    console.log(`   🎬 Efeito: ${contextualEffect.nome}`);
    console.log(`   🔄 Transição: ${transitionEffect}`);
    console.log(`   📹 Saída: ${paths.outputPath.split('/').pop()}`);
    
    validItems.push(item);
  }
  
  console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`🎉 PROCESSAMENTO CONCLUÍDO - V6.8`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`📊 Estatísticas:`);
  console.log(`   Total de itens processados: ${validItems.length}`);
  console.log(`   Páginas configuradas: ${validItems.filter(v => v.json.status === 'ready_to_process').length}`);
  console.log(`   Erros de validação: ${validItems.filter(v => v.json.status === 'validation_failed').length}`);
  console.log(`   Erros de conversão: ${validItems.filter(v => v.json.status === 'audio_conversion_failed').length}`);
  console.log(`\n📋 Páginas processadas: ${validItems.map(v => `#${v.json.pagina_numero}`).join(', ')}`);
  console.log(`\n🚀 Sistema: V6.8 Ultimate (Fix Formato de Áudio FFmpeg)`);
  console.log(`📅 Timestamp: ${new Date().toISOString()}`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);
  
  return validItems;
}

// ======================================================================
// SEÇÃO 9: ✅ RETORNO PARA N8N - V6.14 FIX FONTE DE DADOS
// ======================================================================

// Tenta pegar items da fonte correta
let itemsParaProcessar = [];

try {
  // PRIORIDADE 1: Node "separa vozes dos personagens e grava legenda"
  const itemsSeparaVozes = $('Start').first().json.separa_vozes_dos_personagens_e_grava_legenda_allItems;
  if (itemsSeparaVozes && itemsSeparaVozes.length > 0) {
    itemsParaProcessar = itemsSeparaVozes;
    console.log(`✅ Usando items do node "separa vozes": ${itemsParaProcessar.length} items`);
  }
} catch(e) {
  console.log(`⚠️ Não conseguiu ler "separa vozes": ${e.message}`);
}

// PRIORIDADE 2: Se não encontrou, tenta Loop Falas
if (itemsParaProcessar.length === 0) {
  try {
    const itemsLoop = $('Start').first().json.Loop_Falas_allItems;
    if (itemsLoop && itemsLoop.length > 0) {
      itemsParaProcessar = itemsLoop;
      console.log(`✅ Usando items do node "Loop Falas": ${itemsParaProcessar.length} items`);
    }
  } catch(e) {
    console.log(`⚠️ Não conseguiu ler "Loop Falas": ${e.message}`);
  }
}

// PRIORIDADE 3: Fallback para input direto
if (itemsParaProcessar.length === 0) {
  itemsParaProcessar = $input.all();
  console.log(`⚠️ Usando input direto: ${itemsParaProcessar.length} items`);
}

return processItems(itemsParaProcessar);