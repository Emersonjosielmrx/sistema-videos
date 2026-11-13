import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import briefing from '../../../trabalhos/sintetizerisada_20261110_061444/public/briefing.json';

const {fontFamily} = loadFont('normal', {
  weights: ['600', '700', '800', '900'],
  subsets: ['latin'],
});

const COR_MARCA = briefing.cores.marca; // #FFA94D
const COR_ESCURA = briefing.cores.fundo_escuro; // #1F2937
const COR_TEXTO_MARCA = briefing.cores.texto_sobre_marca; // #1F2937

// Palavras com quebras sintáticas equilibradas (incluindo a locução final)
const PALAVRAS_KARAOOKE: PalavraK[] = briefing.palavras.map((w) => {
  const quebraAntes =
    (w.cena === 0 && w.p === 'quando') ||
    (w.cena === 0 && w.p === 'em') ||
    (w.cena === 1 && w.p === 'por') ||
    (w.cena === 1 && w.p === 'Hoje') ||
    (w.cena === 1 && w.p === 'com' && w.ini > 11) ||
    (w.cena === 2 && w.p === 'confirma') ||
    (w.cena === 2 && w.p === 'direto') ||
    (w.cena === 2 && w.p === 'vinte') ||
    (w.cena === 2 && w.p === 'sem') ||
    (w.cena === 3 && w.p === 'funcionam') ||
    (w.cena === 3 && w.p === 'sem') ||
    (w.cena === 3 && w.p === 'e' && w.ini > 27);
  return {
    p: w.p,
    ini: w.ini,
    fim: w.fim,
    quebraAntes,
  };
});

// ============================================================================
// CENA 0 — PERGUNTA (0.0s a 5.7s)
// Composição (a): Chamada de alto impacto limpa no terço superior + Card interativo
// ============================================================================
const Cena0Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps; // tempo absoluto pois inicia em 0

  // Ken Burns contínuo e perceptível no fundo + zoom de tensão na hora do cancelamento
  const bgScale = interpolate(frame, [0, 171], [1.0, 1.08], {extrapolateRight: 'clamp'});
  const bgX = interpolate(frame, [0, 171], [0, -24], {extrapolateRight: 'clamp'});

  const titleSpring = spring({frame: frame - 3, fps, config: {damping: 13, stiffness: 160}});
  const cardSpring = spring({frame: frame - 12, fps, config: {damping: 14, stiffness: 140}});

  // Quando a voz diz "desmarca" (2.78s = frame 83), o slot das 14:00 vira "DESMARCOU"
  const cancelSpring = spring({frame: frame - 82, fps, config: {damping: 11, stiffness: 190}});
  const floatY = Math.sin(frame / 9) * 8;

  // Micro-vibração (shake) na entrada do cancelamento + pulso contínuo até o fim da cena (q02->q03 vivo)
  const framesAfterCancel = Math.max(0, frame - 82);
  const shakeDecay = interpolate(framesAfterCancel, [0, 22], [1, 0], {extrapolateRight: 'clamp'});
  const badgeShakeX = framesAfterCancel > 0 ? Math.sin(framesAfterCancel * 1.9) * 8 * shakeDecay : 0;
  const badgePulse = cancelSpring > 0.2 ? 1 + Math.sin(frame / 3.2) * 0.065 : 1;
  const cardZoom = cancelSpring > 0.2 ? interpolate(frame, [82, 165], [1.0, 1.05], {extrapolateRight: 'clamp'}) : 1.0;

  // Saída suave no final da cena
  const exitOpacity = interpolate(t, [5.35, 5.68], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA, opacity: exitOpacity}}>
      {/* Foto de fundo viva com Ken Burns (zoom 1.0 -> 1.08) + pan */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale}) translateX(${bgX}px)`,
          }}
        />
        {/* Gradiente escuro apenas no topo e base para preservar a recepcionista visível e clara à esquerda */}
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(17,24,39,0.92) 0%, rgba(17,24,39,0.68) 32%, rgba(17,24,39,0.18) 62%, rgba(17,24,39,0.88) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Chamada direta única de alto impacto no terço superior (despoluída, sem excesso de caixas) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          transform: `translateY(${interpolate(titleSpring, [0, 1], [-35, 0])}px) scale(${interpolate(titleSpring, [0, 1], [0.92, 1])})`,
          opacity: titleSpring,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(17, 24, 39, 0.90)',
            borderLeft: `10px solid ${cancelSpring > 0.2 ? '#EF4444' : COR_MARCA}`,
            borderRadius: 24,
            padding: '22px 28px',
            boxShadow: '0 18px 40px rgba(0,0,0,0.55)',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 54,
              fontWeight: 900,
              lineHeight: 1.14,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: -0.5,
            }}
          >
            <span style={{color: COR_MARCA}}>Buracos na agenda</span> por{' '}
            <span
              style={{
                color: cancelSpring > 0.2 ? '#FCA5A5' : '#FFFFFF',
                textDecoration: cancelSpring > 0.2 ? 'underline' : 'none',
              }}
            >
              cancelamento?
            </span>
          </div>
        </div>
      </div>

      {/* Card de Agenda Interativa no lado direito (x=470..1020, y=640..1170) — recepcionista à esquerda livre */}
      <div
        style={{
          position: 'absolute',
          top: 640 + floatY,
          right: 60,
          width: 530,
          backgroundColor: 'rgba(17, 24, 39, 0.94)',
          borderRadius: 28,
          padding: '24px 26px',
          border: `3px solid ${cancelSpring > 0.3 ? '#EF4444' : COR_MARCA}`,
          boxShadow: cancelSpring > 0.3 ? '0 24px 55px rgba(239,68,68,0.45)' : '0 24px 50px rgba(0,0,0,0.65)',
          transform: `translateX(${interpolate(cardSpring, [0, 1], [120, 0]) + badgeShakeX * 0.5}px) scale(${cardZoom})`,
          opacity: cardSpring,
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 18,
            paddingBottom: 12,
            borderBottom: '2px solid rgba(255,255,255,0.15)',
          }}
        >
          <span style={{fontFamily, fontSize: 34, fontWeight: 800, color: '#FFFFFF', whiteSpace: 'nowrap'}}>📅 Agenda Hoje</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              color: cancelSpring > 0.3 ? '#FFFFFF' : COR_TEXTO_MARCA,
              backgroundColor: cancelSpring > 0.3 ? '#EF4444' : COR_MARCA,
              padding: '4px 14px',
              borderRadius: 999,
              whiteSpace: 'nowrap',
              transform: `scale(${badgePulse})`,
            }}
          >
            {cancelSpring > 0.3 ? '1 VAGO' : 'HOJE'}
          </span>
        </div>

        {/* Horário 1 */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: 'rgba(255,255,255,0.08)',
            padding: '14px 18px',
            borderRadius: 18,
            marginBottom: 14,
          }}
        >
          <span style={{fontFamily, fontSize: 34, fontWeight: 800, color: '#E2E8F0'}}>10:00</span>
          <span style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#34D399'}}>✓ Confirmado</span>
        </div>

        {/* Horário 2 — Desmarca em 2.78s com shake e pulso contínuo */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: cancelSpring > 0.2 ? 'rgba(239, 68, 68, 0.28)' : 'rgba(255, 169, 77, 0.18)',
            border: `3px solid ${cancelSpring > 0.2 ? '#EF4444' : COR_MARCA}`,
            padding: '16px 18px',
            borderRadius: 18,
            marginBottom: 14,
            transform: `translateX(${badgeShakeX}px) scale(${badgePulse})`,
          }}
        >
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <span style={{fontFamily, fontSize: 36, fontWeight: 900, color: '#FFFFFF'}}>14:00</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: '#FFFFFF',
                backgroundColor: cancelSpring > 0.2 ? '#DC2626' : '#D97706',
                padding: '6px 16px',
                borderRadius: 12,
                boxShadow: cancelSpring > 0.2 ? '0 6px 18px rgba(220,38,38,0.6)' : 'none',
              }}
            >
              {cancelSpring > 0.2 ? '✕ DESMARCOU' : '⏳ Em cima da hora'}
            </span>
          </div>
          {cancelSpring > 0.2 && (
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FCA5A5',
                marginTop: 8,
              }}
            >
              ⚠ Horário vago!
            </span>
          )}
        </div>

        {/* Horário 3 */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: 'rgba(255,255,255,0.08)',
            padding: '14px 18px',
            borderRadius: 18,
          }}
        >
          <span style={{fontFamily, fontSize: 34, fontWeight: 800, color: '#E2E8F0'}}>16:00</span>
          <span style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#34D399'}}>✓ Confirmado</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 1 — O PROBLEMA / A SOLUÇÃO (5.35s a 13.97s)
// Composição (c): Apresentador humano no topo + Comparativo dinâmico com cascata
// ============================================================================
const Cena1ProblemaSolucao: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const cenaIni = 5.35;
  const durFrames = Math.round((13.97 - 5.35) * fps);

  const enterSpring = spring({frame, fps, config: {damping: 14, stiffness: 140}});
  // "Hoje a IA confirma tudo com antecedência" começa em 9.18s (frame local ~115)
  const viradaFrame = Math.round((9.18 - cenaIni) * fps);
  const viradaSpring = spring({frame: frame - viradaFrame, fps, config: {damping: 14, stiffness: 135}});

  // Entrada em cascata (stagger com slide-up de 15px e fade-in linha a linha) sincronizada com a locução:
  // Item 1 ('Confirma antes'): acende com slide-up de 15px e iluminação em 10.65s (na locução 'confirma')
  const item1Spring = spring({
    frame: frame - Math.round((10.65 - cenaIni) * fps),
    fps,
    config: {damping: 12, stiffness: 170},
  });
  // Item 2 ('Trabalha 24h' / 'A partir de R$ 199'): acende com slide-up de 15px e iluminação em 11.75s (na locução 'antecedência')
  const item2Spring = spring({
    frame: frame - Math.round((11.75 - cenaIni) * fps),
    fps,
    config: {damping: 12, stiffness: 170},
  });
  // Rodapé do card Hoje ('Agenda confirmada'): acende em 12.15s
  const item3Spring = spring({
    frame: frame - Math.round((12.15 - cenaIni) * fps),
    fps,
    config: {damping: 12, stiffness: 170},
  });

  const presenterScale = interpolate(frame, [0, durFrames], [1.02, 1.12], {extrapolateRight: 'clamp'});
  const gridOffset = interpolate(frame, [0, durFrames], [0, -90]);
  const floatLeft = Math.sin(frame / 10) * 6;
  const floatRight = Math.cos(frame / 10) * 6;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0F172A',
        transform: `translateY(${interpolate(enterSpring, [0, 1], [60, 0])}px)`,
        opacity: enterSpring,
      }}
    >
      {/* Fundo tecnológico escuro com malha em movimento lento (sem repetir a foto da recepcionista) */}
      <AbsoluteFill
        style={{
          background: 'radial-gradient(circle at 50% 25%, #1E293B 0%, #0F172A 65%, #090D16 100%)',
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage:
            'linear-gradient(rgba(255, 169, 77, 0.06) 2px, transparent 2px), linear-gradient(90deg, rgba(255, 169, 77, 0.06) 2px, transparent 2px)',
          backgroundSize: '64px 64px',
          transform: `translateY(${gridOffset}px)`,
        }}
      />

      {/* Topo: Apenas a Tag do bloco e Badge temático (sem título longo concorrente) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          zIndex: 10,
        }}
      >
        <span
          style={{
            backgroundColor: viradaSpring > 0.3 ? COR_MARCA : '#EF4444',
            color: viradaSpring > 0.3 ? COR_TEXTO_MARCA : '#FFFFFF',
            fontFamily,
            fontSize: 34,
            fontWeight: 900,
            padding: '10px 26px',
            borderRadius: 999,
            textTransform: 'uppercase',
            boxShadow: '0 8px 20px rgba(0,0,0,0.45)',
          }}
        >
          {viradaSpring > 0.3 ? '✓ HOJE COM AGENDA IA' : '✕ O PROBLEMA'}
        </span>

        <span
          style={{
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            color: viradaSpring > 0.3 ? COR_MARCA : '#FCA5A5',
            fontFamily,
            fontSize: 32,
            fontWeight: 800,
            padding: '10px 22px',
            borderRadius: 999,
            border: `2px solid ${viradaSpring > 0.3 ? COR_MARCA : '#EF4444'}`,
          }}
        >
          {viradaSpring > 0.3 ? 'Confirmação 24h' : 'Cancelamento repentino'}
        </span>
      </div>

      {/* Janela circular/retrato do Apresentador (dono_3.mp4) com rosto e ombros 100% livres e visíveis antes dos 15s */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 60,
          right: 60,
          height: 365,
          borderRadius: 28,
          overflow: 'hidden',
          border: `3px solid ${viradaSpring > 0.3 ? COR_MARCA : '#EF4444'}`,
          boxShadow: '0 20px 45px rgba(0,0,0,0.65)',
          backgroundColor: '#1E293B',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        {/* Lado esquerdo: Vídeo do dono enquadrando cabeça e ombros inteiros sem nenhum texto sobreposto */}
        <div style={{width: '46%', height: '100%', overflow: 'hidden', position: 'relative'}}>
          <OffthreadVideo
            src={staticFile('dono_3.mp4')}
            muted
            style={{
              width: '100%',
              height: '190%',
              objectFit: 'cover',
              objectPosition: 'center top',
              marginTop: -120,
              transform: `scale(${presenterScale})`,
            }}
          />
        </div>

        {/* Lado direito: Síntese direta em 2 tempos (Dor -> Solução) com contraste nítido */}
        <div
          style={{
            flex: 1,
            height: '100%',
            padding: '22px 26px',
            background: 'linear-gradient(90deg, rgba(15,23,42,0.92) 0%, #0F172A 30%)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            gap: 12,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: viradaSpring > 0.3 ? COR_MARCA : '#FCA5A5',
              textTransform: 'uppercase',
            }}
          >
            {viradaSpring > 0.3 ? 'Solução Automática' : 'Prejuízo Manual'}
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.18,
            }}
          >
            {viradaSpring > 0.3
              ? 'Confirmação 24h por R$ 199/mês'
              : 'Agenda com buracos: R$ 2.500/mês'}
          </div>
        </div>
      </div>

      {/* Comparativo Dinâmico em 2 Tempos na Tela Cheia (y=640..1360) */}
      <div style={{position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none'}}>
        {/* Tempo 1: Card em Tela Cheia destacando A DOR (5.35s a 9.18s) */}
        {viradaSpring < 0.5 && (
          <div
            style={{
              position: 'absolute',
              top: 640,
              left: 60,
              right: 60,
              height: 720,
              backgroundColor: '#1E293B',
              borderRadius: 28,
              padding: '28px 30px',
              border: '3px solid #EF4444',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              transform: `translateY(${floatLeft}px) translateY(${interpolate(viradaSpring, [0, 0.35], [0, -30], {extrapolateRight: 'clamp'})}px)`,
              opacity: interpolate(viradaSpring, [0, 0.35], [1, 0], {extrapolateRight: 'clamp'}),
              boxShadow: '0 24px 50px rgba(239,68,68,0.28)',
            }}
          >
            <div>
              <div
                style={{
                  backgroundColor: '#EF4444',
                  color: '#FFFFFF',
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 900,
                  padding: '12px 20px',
                  borderRadius: 16,
                  textAlign: 'center',
                  marginBottom: 20,
                  letterSpacing: 0.5,
                }}
              >
                ✕ ANTES: AGENDA MANUAL
              </div>

              <div
                style={{
                  backgroundColor: 'rgba(15, 23, 42, 0.88)',
                  border: '2px solid rgba(239,68,68,0.6)',
                  padding: '20px 24px',
                  borderRadius: 20,
                  marginBottom: 16,
                }}
              >
                <div style={{fontFamily, fontSize: 40, fontWeight: 900, color: '#FFFFFF', marginBottom: 6}}>
                  ✕ Horários vagos
                </div>
                <div style={{fontFamily, fontSize: 34, fontWeight: 700, color: '#FCA5A5'}}>
                  Cancelamento repentino em cima da hora
                </div>
              </div>

              <div
                style={{
                  backgroundColor: 'rgba(15, 23, 42, 0.88)',
                  border: '2px solid rgba(239,68,68,0.6)',
                  padding: '20px 24px',
                  borderRadius: 20,
                }}
              >
                <div style={{fontFamily, fontSize: 34, fontWeight: 800, color: '#CBD5E1', marginBottom: 6}}>
                  Recepção humana tradicional
                </div>
                <div style={{fontFamily, fontSize: 52, fontWeight: 900, color: '#EF4444'}}>
                  R$ 2.500 / mês
                </div>
              </div>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(239,68,68,0.25)',
                border: '2px solid #EF4444',
                padding: '16px',
                borderRadius: 18,
                textAlign: 'center',
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
              }}
            >
              ⚠️ Agenda com buracos e prejuízo todo mês
            </div>
          </div>
        )}

        {/* Tempo 2: Card em Tela Cheia transicionando para A SOLUÇÃO (9.18s a 13.97s) */}
        {viradaSpring > 0.05 && (
          <div
            style={{
              position: 'absolute',
              top: 640,
              left: 60,
              right: 60,
              height: 720,
              backgroundColor: '#1E293B',
              borderRadius: 28,
              padding: '28px 30px',
              border: `4px solid ${COR_MARCA}`,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              transform: `translateY(${floatRight}px) translateY(${interpolate(viradaSpring, [0.05, 0.45], [35, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}px) scale(${interpolate(viradaSpring, [0.05, 0.45], [0.94, 1.0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})})`,
              opacity: interpolate(viradaSpring, [0.05, 0.45], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
              boxShadow: '0 24px 55px rgba(255,169,77,0.35)',
            }}
          >
            {/* Header */}
            <div
              style={{
                backgroundColor: COR_MARCA,
                color: COR_TEXTO_MARCA,
                fontFamily,
                fontSize: 36,
                fontWeight: 900,
                padding: '12px 20px',
                borderRadius: 16,
                textAlign: 'center',
                letterSpacing: 0.5,
              }}
            >
              ✓ HOJE: AGENDA IA 24H
            </div>

            {/* Tópico 1: Cascata com slide-up 15px e fade-in na locução 'confirma' (10.65s) */}
            <div
              style={{
                backgroundColor: item1Spring > 0.1 ? 'rgba(255,169,77,0.22)' : 'rgba(15, 23, 42, 0.75)',
                border: `3px solid ${item1Spring > 0.1 ? COR_MARCA : 'rgba(255,169,77,0.45)'}`,
                padding: '24px 26px',
                borderRadius: 22,
                transform: `translateY(${interpolate(item1Spring, [0, 1], [15, 0])}px) scale(${interpolate(item1Spring, [0, 1], [0.97, 1])})`,
                opacity: interpolate(item1Spring, [0, 1], [0.65, 1]),
                boxShadow: item1Spring > 0.1 ? '0 10px 25px rgba(255,169,77,0.25)' : 'none',
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 42,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  marginBottom: 8,
                }}
              >
                ✓ Confirma antes
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 800,
                  color: item1Spring > 0.1 ? '#34D399' : '#E2E8F0',
                }}
              >
                Aviso automático com antecedência
              </div>
            </div>

            {/* Tópico 2: Cascata com slide-up 15px e fade-in em 11.75s (revela destaque de preço) */}
            <div
              style={{
                backgroundColor: item2Spring > 0.1 ? 'rgba(52,211,153,0.18)' : 'rgba(15, 23, 42, 0.75)',
                border: `3px solid ${item2Spring > 0.1 ? '#34D399' : 'rgba(52,211,153,0.4)'}`,
                padding: '24px 26px',
                borderRadius: 22,
                transform: `translateY(${interpolate(item2Spring, [0, 1], [15, 0])}px) scale(${interpolate(item2Spring, [0, 1], [0.97, 1])})`,
                opacity: interpolate(item2Spring, [0, 1], [0.60, 1]),
                boxShadow: item2Spring > 0.1 ? '0 10px 25px rgba(52,211,153,0.25)' : 'none',
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 40,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  marginBottom: 8,
                }}
              >
                ✓ Trabalha 24 horas por dia
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 52,
                  fontWeight: 900,
                  color: item2Spring > 0.1 ? '#34D399' : '#A7F3D0',
                }}
              >
                A partir de R$ 199 / mês
              </div>
            </div>

            {/* Rodapé do card Hoje: entra sincronizado */}
            <div
              style={{
                backgroundColor: item3Spring > 0.1 ? COR_MARCA : 'rgba(255,169,77,0.45)',
                padding: '16px',
                borderRadius: 18,
                textAlign: 'center',
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: item3Spring > 0.1 ? COR_TEXTO_MARCA : '#FFFFFF',
                transform: `translateY(${interpolate(item3Spring, [0, 1], [15, 0])}px)`,
                opacity: interpolate(item3Spring, [0, 1], [0.65, 1]),
              }}
            >
              ✓ Agenda confirmada e sem buracos
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 2 — CONVERSA WHATSAPP (13.62s a 22.39s)
// Composição (b): Celular 3D grande + Pílulas de etapas sincronizadas
// ============================================================================
const Cena2Conversa: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const cenaIni = 13.62;
  const t = cenaIni + frame / fps;

  const phoneEnter = spring({frame, fps, config: {damping: 14, stiffness: 130}});
  const rotateY = interpolate(frame, [0, 260], [14, -8], {extrapolateRight: 'clamp'});
  const floatY = Math.sin(frame / 12) * 8;

  // Tempos de entrada das 5 mensagens do briefing (acelerados no início e container dinâmico sem espaço preto morto)
  const msgTimes = [13.72, 14.55, 15.65, 17.05, 18.45];
  const msgs = briefing.cenas[2].conversa || [];

  // Ativar '1. Reagenda' desde o primeiro momento da cena (q07)
  const badgeConfirma = t >= 13.62;
  const badge24h = t >= 19.05;
  const badgeSemConflito = t >= 20.2;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#111827',
        opacity: phoneEnter,
      }}
    >
      {/* Fundo estilizado com recorte circular e iluminação da marca */}
      <div
        style={{
          position: 'absolute',
          top: -120,
          right: -120,
          width: 640,
          height: 640,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255,169,77,0.28) 0%, rgba(255,169,77,0) 70%)',
        }}
      />

      {/* Cabeçalho e Badges Sincronizados (y=160..320) */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
          zIndex: 10,
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <span
            style={{
              backgroundColor: COR_MARCA,
              color: COR_TEXTO_MARCA,
              fontFamily,
              fontSize: 34,
              fontWeight: 900,
              padding: '8px 24px',
              borderRadius: 999,
            }}
          >
            COMO FUNCIONA
          </span>
          <span
            style={{
              backgroundColor: 'rgba(255,255,255,0.1)',
              color: '#F8FAFC',
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              padding: '8px 20px',
              borderRadius: 999,
            }}
          >
            Simulação
          </span>
        </div>

        {/* 3 Etapas que acendem com a voz */}
        <div style={{display: 'flex', gap: 12}}>
          <div
            style={{
              flex: 1,
              backgroundColor: badgeConfirma ? COR_MARCA : 'rgba(255,255,255,0.08)',
              color: badgeConfirma ? COR_TEXTO_MARCA : '#94A3B8',
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              padding: '10px 14px',
              borderRadius: 16,
              textAlign: 'center',
              transition: 'all 0.2s',
            }}
          >
            1. Reagenda
          </div>
          <div
            style={{
              flex: 1,
              backgroundColor: badge24h ? COR_MARCA : 'rgba(255,255,255,0.08)',
              color: badge24h ? COR_TEXTO_MARCA : '#94A3B8',
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              padding: '10px 14px',
              borderRadius: 16,
              textAlign: 'center',
            }}
          >
            2. Atende 24h
          </div>
          <div
            style={{
              flex: 1,
              backgroundColor: badgeSemConflito ? COR_MARCA : 'rgba(255,255,255,0.08)',
              color: badgeSemConflito ? COR_TEXTO_MARCA : '#94A3B8',
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              padding: '10px 14px',
              borderRadius: 16,
              textAlign: 'center',
            }}
          >
            3. Sem conflito
          </div>
        </div>
      </div>

      {/* Mockup de Celular em 3D proporcional aos balões (cresce conforme as mensagens entram, sem buraco preto vazio) */}
      <div
        style={{
          position: 'absolute',
          top: 340 + floatY,
          left: 70,
          right: 70,
          perspective: 1200,
        }}
      >
        <div
          style={{
            width: '100%',
            backgroundColor: '#0B141A',
            borderRadius: 42,
            border: `5px solid ${COR_MARCA}`,
            boxShadow: '0 30px 70px rgba(0,0,0,0.75)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            transform: `rotateY(${rotateY}deg) scale(${interpolate(phoneEnter, [0, 1], [0.88, 1])})`,
          }}
        >
          {/* Topo do WhatsApp */}
          <div
            style={{
              backgroundColor: '#1F2C34',
              padding: '18px 26px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid rgba(255,255,255,0.1)',
              zIndex: 5,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: '50%',
                  backgroundColor: COR_MARCA,
                  color: COR_TEXTO_MARCA,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                }}
              >
                IA
              </div>
              <div>
                <div style={{fontFamily, fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>Agenda IA</div>
                <div style={{fontFamily, fontSize: 32, fontWeight: 600, color: '#34D399'}}>● Online 24h</div>
              </div>
            </div>
            <div
              style={{
                backgroundColor: 'rgba(255,169,77,0.2)',
                color: COR_MARCA,
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                padding: '6px 16px',
                borderRadius: 12,
              }}
            >
              WhatsApp
            </div>
          </div>

          {/* Corpo das Mensagens proporcional e com indicador de digitando contínuo entre balões */}
          <div
            style={{
              padding: '22px 24px 26px 24px',
              overflow: 'hidden',
              position: 'relative',
              background: 'radial-gradient(circle at 50% 50%, #131F28 0%, #0B141A 100%)',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
              }}
            >
              {msgs.map((m, idx) => {
                const mIni = msgTimes[idx];
                const prevEnd = idx === 0 ? cenaIni : msgTimes[idx - 1] + 0.25;
                if (t < prevEnd) return null;
                const digitando = t >= prevEnd && t < mIni;
                const msgS = spring({
                  frame: frame - Math.round((mIni - cenaIni) * fps),
                  fps,
                  config: {damping: 14, stiffness: 160},
                });
                const isEmpresa = m.de === 'empresa';

                if (digitando) {
                  return (
                    <div
                      key={`dig-${idx}`}
                      style={{
                        alignSelf: isEmpresa ? 'flex-start' : 'flex-end',
                        backgroundColor: isEmpresa ? '#1F2C34' : '#005C4B',
                        border: `2px solid ${isEmpresa ? COR_MARCA : '#10B981'}`,
                        color: isEmpresa ? COR_MARCA : '#A7F3D0',
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 800,
                        padding: '14px 24px',
                        borderRadius: 20,
                      }}
                    >
                      {isEmpresa ? '💬 Agenda IA digitando...' : '💬 Cliente digitando...'}
                    </div>
                  );
                }

                return (
                  <div
                    key={idx}
                    style={{
                      alignSelf: isEmpresa ? 'flex-start' : 'flex-end',
                      maxWidth: '88%',
                      backgroundColor: isEmpresa ? '#1F2C34' : '#005C4B',
                      border: isEmpresa ? `2px solid ${COR_MARCA}` : '2px solid #10B981',
                      color: '#FFFFFF',
                      padding: '16px 22px',
                      borderRadius: isEmpresa ? '22px 22px 22px 6px' : '22px 22px 6px 22px',
                      transform: `scale(${interpolate(msgS, [0, 1], [0.85, 1])})`,
                      opacity: msgS,
                      boxShadow: '0 8px 20px rgba(0,0,0,0.35)',
                    }}
                  >
                    <div
                      style={{
                        fontFamily,
                        fontSize: 34,
                        fontWeight: 700,
                        lineHeight: 1.24,
                      }}
                    >
                      {m.texto}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 3 — DONO FALANDO (22.04s a 30.07s)
// Composição (h): Vídeo cheio com punch-in dinâmico 1.1x + HUD superior sincronizado
// ============================================================================
const Cena3Dono: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const cenaIni = 22.04;
  const t = cenaIni + frame / fps;
  const durFrames = Math.round((30.07 - 22.04) * fps);

  const enterS = spring({frame, fps, config: {damping: 15, stiffness: 140}});

  // 3 itens sincronizados com a fala do dono:
  // 1) "dia e noite" (22.5s), 2) "sem duplo agendamento" (26.24s), 3) "agenda organizada" (28.20s)
  const passo1 = t >= 22.04;
  const passo2 = t >= 26.2;
  const passo3 = t >= 28.15;

  const framePasso2 = Math.round((26.2 - cenaIni) * fps);
  const framePasso3 = Math.round((28.15 - cenaIni) * fps);
  const popPasso2 = spring({frame: frame - framePasso2, fps, config: {damping: 10, stiffness: 200}});
  const popPasso3 = spring({frame: frame - framePasso3, fps, config: {damping: 10, stiffness: 200}});

  // Punch-in digital suave para 1.1x na virada para a frase 'sem duplo agendamento' (26.2s)
  const baseScale = interpolate(frame, [0, durFrames], [1.0, 1.05], {extrapolateRight: 'clamp'});
  const punchInBonus = interpolate(popPasso2, [0, 1], [0, 0.08]);
  const videoScale = baseScale + punchInBonus;

  // Scale pop de 1.15 para 1.0 quando a pílula 02 e 03 acendem
  const scalePill2 = passo2 ? interpolate(popPasso2, [0, 0.5, 1], [0.95, 1.15, 1.03]) : 1.0;
  const scalePill3 = passo3 ? interpolate(popPasso3, [0, 0.5, 1], [0.95, 1.15, 1.03]) : 1.0;

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA, opacity: enterS}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${videoScale})`,
          }}
        />
        {/* Gradiente suave apenas no topo (y=0..430) e base da legenda, deixando o rosto (y=450..950) 100% limpo */}
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(17,24,39,0.90) 0%, rgba(17,24,39,0.55) 22%, rgba(17,24,39,0) 30%, rgba(17,24,39,0) 74%, rgba(17,24,39,0.82) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Painel Superior na Zona Segura (y=160..410) — NUNCA desce para o rosto do dono */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
          <span
            style={{
              backgroundColor: COR_MARCA,
              color: COR_TEXTO_MARCA,
              fontFamily,
              fontSize: 34,
              fontWeight: 900,
              padding: '8px 24px',
              borderRadius: 999,
            }}
          >
            O RESULTADO
          </span>
          <span
            style={{
              backgroundColor: 'rgba(17,24,39,0.88)',
              color: COR_MARCA,
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              padding: '8px 20px',
              borderRadius: 999,
              border: `2px solid ${COR_MARCA}`,
            }}
          >
            Agenda IA 24h
          </span>
        </div>

        {/* Card horizontal compacto no topo mostrando a evolução 01 -> 02 -> 03 (todos na paleta laranja da marca) */}
        <div
          style={{
            backgroundColor: 'rgba(17, 24, 39, 0.90)',
            borderRadius: 24,
            padding: '14px 16px',
            border: `2px solid ${COR_MARCA}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 10,
            boxShadow: '0 14px 32px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              flex: 1,
              backgroundColor: passo1 ? COR_MARCA : 'rgba(255,255,255,0.08)',
              color: passo1 ? COR_TEXTO_MARCA : '#94A3B8',
              padding: '12px 8px',
              borderRadius: 16,
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              textAlign: 'center',
              whiteSpace: 'nowrap',
            }}
          >
            01 • 24 Horas
          </div>
          <div
            style={{
              flex: 1,
              backgroundColor: passo2 ? COR_MARCA : 'rgba(255,255,255,0.08)',
              color: passo2 ? COR_TEXTO_MARCA : '#94A3B8',
              padding: '12px 8px',
              borderRadius: 16,
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              textAlign: 'center',
              whiteSpace: 'nowrap',
              transform: `scale(${scalePill2})`,
              boxShadow: passo2 ? '0 8px 24px rgba(255,169,77,0.45)' : 'none',
            }}
          >
            02 • Sem Conflito
          </div>
          <div
            style={{
              flex: 1,
              backgroundColor: passo3 ? COR_MARCA : 'rgba(255,255,255,0.08)',
              color: passo3 ? COR_TEXTO_MARCA : '#94A3B8',
              padding: '12px 8px',
              borderRadius: 16,
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              textAlign: 'center',
              whiteSpace: 'nowrap',
              transform: `scale(${scalePill3})`,
              boxShadow: passo3 ? '0 8px 24px rgba(255,169,77,0.45)' : 'none',
            }}
          >
            03 • Organizada
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// CENA 4 — CARTÃO FINAL CTA (29.72s a 33.72s)
// Composição (f): Fundo escuro da marca + entrada sequencial stagger 0.15s + botão pulsante
// ============================================================================
const Cena4Cartao: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.round((33.72 - 29.72) * fps);

  const enterS = spring({frame, fps, config: {damping: 13, stiffness: 140}});
  // Entrada sequencial com spring suave (stagger de 0.15s = ~5 frames)
  const sLogo = spring({frame: frame - 2, fps, config: {damping: 13, stiffness: 150}});
  const sCard = spring({frame: frame - 7, fps, config: {damping: 13, stiffness: 150}});
  const sCta = spring({frame: frame - 12, fps, config: {damping: 12, stiffness: 160}});
  const sArroba = spring({frame: frame - 17, fps, config: {damping: 13, stiffness: 150}});

  const bgScale = interpolate(frame, [0, durFrames], [1.0, 1.12], {extrapolateRight: 'clamp'});
  const btnPulse = 1 + Math.sin(frame / 4.5) * 0.045;
  const floatCard = Math.sin(frame / 9) * 8;
  const shineX = interpolate(frame % 60, [0, 60], [-300, 1100]);

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA, opacity: enterS}}>
      {/* Foto desfocada com véu escuro da marca */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale})`,
            filter: 'blur(14px) brightness(0.32)',
          }}
        />
        <AbsoluteFill
          style={{
            background:
              'radial-gradient(circle at 50% 35%, rgba(255,169,77,0.22) 0%, rgba(31,41,55,0.92) 70%)',
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo Centralizado na Safe Zone (y=195..1380) deixando espaço livre para a legenda karaokê abaixo */}
      <div
        style={{
          position: 'absolute',
          top: 195,
          left: 60,
          right: 60,
          bottom: 530,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          transform: `translateY(${floatCard}px)`,
        }}
      >
        {/* Selo superior + Nome da Marca Grande (1º no stagger) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 18,
            transform: `translateY(${interpolate(sLogo, [0, 1], [30, 0])}px) scale(${interpolate(sLogo, [0, 1], [0.9, 1])})`,
            opacity: sLogo,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(255,169,77,0.18)',
              border: `2px solid ${COR_MARCA}`,
              color: COR_MARCA,
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              padding: '10px 28px',
              borderRadius: 999,
            }}
          >
            ✓ Agendamentos Automáticos 24h
          </div>

          <div style={{textAlign: 'center'}}>
            <div
              style={{
                fontFamily,
                fontSize: 88,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: -1,
                lineHeight: 1.05,
              }}
            >
              AGENDA <span style={{color: COR_MARCA}}>IA</span>
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 700,
                color: '#F1F5F9',
                marginTop: 14,
                lineHeight: 1.22,
                maxWidth: 880,
              }}
            >
              Agenda, confirma e reagenda sozinha direto no WhatsApp, sem conflito.
            </div>
          </div>
        </div>

        {/* Card de Destaque de Valor (2º no stagger +0.15s) */}
        <div
          style={{
            backgroundColor: 'rgba(17, 24, 39, 0.90)',
            border: '2px solid rgba(255,255,255,0.18)',
            borderRadius: 28,
            padding: '22px 32px',
            width: '100%',
            display: 'flex',
            justifyContent: 'space-around',
            alignItems: 'center',
            transform: `translateY(${interpolate(sCard, [0, 1], [30, 0])}px) scale(${interpolate(sCard, [0, 1], [0.9, 1])})`,
            opacity: sCard,
          }}
        >
          <div style={{textAlign: 'center'}}>
            <div style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#94A3B8'}}>Recepção humana</div>
            <div style={{fontFamily, fontSize: 40, fontWeight: 800, color: '#FCA5A5', textDecoration: 'line-through'}}>
              R$ 2.500/mês
            </div>
          </div>
          <div style={{width: 2, height: 70, backgroundColor: 'rgba(255,255,255,0.2)'}} />
          <div style={{textAlign: 'center'}}>
            <div style={{fontFamily, fontSize: 32, fontWeight: 700, color: COR_MARCA}}>Agenda IA 24h</div>
            <div style={{fontFamily, fontSize: 44, fontWeight: 900, color: '#34D399'}}>
              A partir de R$ 199
            </div>
          </div>
        </div>

        {/* Botão CTA Pulsante com scale-up (3º no stagger +0.30s) */}
        <div
          style={{
            position: 'relative',
            overflow: 'hidden',
            backgroundColor: COR_MARCA,
            color: COR_TEXTO_MARCA,
            fontFamily,
            fontSize: 46,
            fontWeight: 900,
            padding: '24px 50px',
            borderRadius: 999,
            width: '100%',
            textAlign: 'center',
            transform: `scale(${interpolate(sCta, [0, 1], [0.82, 1]) * btnPulse})`,
            opacity: sCta,
            boxShadow: '0 20px 50px rgba(255, 169, 77, 0.45)',
          }}
        >
          <span>CHAME NO DIRECT</span>
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: shineX,
              width: 120,
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.55), transparent)',
              transform: 'skewX(-25deg)',
            }}
          />
        </div>

        {/* @arroba dentro da safe zone (4º no stagger) */}
        <div
          style={{
            backgroundColor: 'rgba(17, 24, 39, 0.9)',
            color: '#FFFFFF',
            fontFamily,
            fontSize: 36,
            fontWeight: 800,
            padding: '10px 32px',
            borderRadius: 999,
            border: '2px solid rgba(255,255,255,0.22)',
            transform: `translateY(${interpolate(sArroba, [0, 1], [20, 0])}px)`,
            opacity: sArroba,
          }}
        >
          {briefing.arroba}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// COMPOSIÇÃO PRINCIPAL
// ============================================================================
const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / fps;

  // Volume da trilha: ~0.10 com fala, fade in/out suave
  const trilhaVolume = interpolate(
    frame,
    [0, 15, durationInFrames - 25, durationInFrames],
    [0, 0.1, 0.1, 0.0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  const progresso = interpolate(frame, [0, durationInFrames], [0, 100], {extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{backgroundColor: COR_ESCURA, fontFamily}}>
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Cena 0: 0.00s a 5.70s */}
      <Sequence from={0} durationInFrames={Math.ceil(5.7 * fps)}>
        <Cena0Pergunta />
      </Sequence>

      {/* Cena 1: 5.35s a 13.97s */}
      <Sequence from={Math.floor(5.35 * fps)} durationInFrames={Math.ceil((13.97 - 5.35) * fps)}>
        <Cena1ProblemaSolucao />
      </Sequence>

      {/* Cena 2: 13.62s a 22.39s */}
      <Sequence from={Math.floor(13.62 * fps)} durationInFrames={Math.ceil((22.39 - 13.62) * fps)}>
        <Cena2Conversa />
      </Sequence>

      {/* Cena 3: 22.04s a 30.07s */}
      <Sequence from={Math.floor(22.04 * fps)} durationInFrames={Math.ceil((30.07 - 22.04) * fps)}>
        <Cena3Dono />
      </Sequence>

      {/* Cena 4: 29.72s a 33.72s */}
      <Sequence from={Math.floor(29.72 * fps)} durationInFrames={Math.ceil((33.72 - 29.72) * fps)}>
        <Cena4Cartao />
      </Sequence>

      {/* Barra de progresso fina no topo da zona segura (y=150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          backgroundColor: 'rgba(255,255,255,0.2)',
          borderRadius: 999,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            backgroundColor: COR_MARCA,
          }}
        />
      </div>

      {/* Legenda Karaokê (cenas 0 a 4, ancorada acima de y=1510 com base=415 para nunca invadir y>=1560) */}
      <Karaoke
        palavras={PALAVRAS_KARAOOKE}
        fontFamily={fontFamily}
        destaque={COR_MARCA}
        textoDestaque={COR_TEXTO_MARCA}
        tamanho={44}
        base={415}
        maxLetras={28}
      />
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={VideoPrincipal}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
