import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const VERDE = '#22C55E';
const ESCURO = '#111827';
const TEXTO_ESCURO = '#121216';

export const Cena0Pergunta: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps; // 0 a 4.76s

  // Ken Burns contínuo e suave (slow zoom in de 1.00 para 1.05 + pan lento)
  const bgScale = interpolate(frame, [0, 143], [1.0, 1.05], {extrapolateRight: 'clamp'});
  const bgY = interpolate(frame, [0, 143], [0, -12], {extrapolateRight: 'clamp'});

  const topPop = spring({frame, fps, config: {damping: 14, stiffness: 160}});
  const cardPop = spring({frame, fps, config: {damping: 15, stiffness: 150}});

  // Sincronia exata com a locução:
  // "Consigo falar" -> 0.32s..1.11s
  // "com toda a minha base" -> 1.135s..2.241s
  // "sem mandar um por um" -> 2.241s..3.287s (acende linha 3 exatamente aos 2.241s)
  const line2Highlight = t >= 1.135 && t < 2.241;
  const line3Highlight = t >= 2.241;

  const ganchoPop = spring({
    frame: frame - Math.round(2.241 * fps),
    fps,
    config: {damping: 13, stiffness: 150},
  });

  const floatY = Math.sin(frame * 0.14) * 5;
  const pulseScale = 1 + Math.sin(frame * 0.2) * 0.02;

  const exitOp = interpolate(t, [4.42, 4.74], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: ESCURO, opacity: exitOp}}>
      {/* Camada de fundo fotográfico vivo com Ken Burns contínuo cobrindo a tela */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center 12%',
            transform: `scale(${bgScale}) translateY(${bgY}px)`,
          }}
        />
        {/* Véu suave preservando o rosto da apresentadora e garantindo alto contraste no terço inferior */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(17,24,39,0.5) 0%, rgba(17,24,39,0.02) 20%, rgba(17,24,39,0.2) 48%, rgba(17,24,39,0.92) 68%, rgba(17,24,39,0.98) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Topo dentro da Safe Zone (y=168) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          transform: `translateY(${interpolate(topPop, [0, 1], [-30, 0])}px)`,
          opacity: topPop,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            background: 'rgba(17, 24, 39, 0.92)',
            border: `2px solid ${VERDE}`,
            borderRadius: 999,
            padding: '10px 24px',
            boxShadow: '0 10px 28px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              width: 16,
              height: 16,
              borderRadius: '50%',
              background: VERDE,
              boxShadow: `0 0 14px ${VERDE}`,
              transform: `scale(${1 + Math.sin(frame * 0.25) * 0.25})`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 33,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 0.5,
            }}
          >
            DISPARO EM MASSA IA
          </span>
        </div>
      </div>

      {/* Card principal da pergunta em y=660..1120 (rosto da apresentadora 100% livre acima de y=650) */}
      <div
        style={{
          position: 'absolute',
          top: 660,
          left: 60,
          right: 60,
          transform: `translateY(${interpolate(cardPop, [0, 1], [35, 0]) + floatY}px)`,
          opacity: cardPop,
        }}
      >
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.96)',
            border: `3px solid ${VERDE}`,
            borderRadius: 30,
            padding: '26px 34px',
            boxShadow: '0 24px 50px rgba(0,0,0,0.75)',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          {/* Header do card: Dúvida de Lojista + WhatsApp */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#86EFAC',
                background: 'rgba(34, 197, 94, 0.18)',
                border: '2px solid rgba(34, 197, 94, 0.5)',
                padding: '6px 18px',
                borderRadius: 999,
                textTransform: 'uppercase',
              }}
            >
              Dúvida de Lojista
            </span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                background: 'rgba(255,255,255,0.15)',
                padding: '6px 18px',
                borderRadius: 999,
              }}
            >
              WhatsApp
            </span>
          </div>

          {/* Linha 1: "Consigo falar" */}
          <div style={{display: 'flex', alignItems: 'center'}}>
            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.12,
              }}
            >
              “Consigo falar
            </span>
          </div>

          {/* Linha 2: "com toda a minha base" - 100% legível desde 0s com contraste alto */}
          <div style={{display: 'flex', alignItems: 'center'}}>
            <span
              style={{
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: line2Highlight ? TEXTO_ESCURO : '#FFFFFF',
                background: line2Highlight ? VERDE : 'rgba(255, 255, 255, 0.22)',
                border: `2px solid ${line2Highlight ? VERDE : 'rgba(255, 255, 255, 0.45)'}`,
                padding: '10px 22px',
                borderRadius: 16,
                lineHeight: 1.12,
                boxShadow: line2Highlight ? '0 8px 24px rgba(34,197,94,0.5)' : 'none',
                transform: `scale(${line2Highlight ? 1.02 : 1})`,
                transformOrigin: 'left center',
              }}
            >
              com toda a minha base
            </span>
          </div>

          {/* Linha 3: "sem mandar um por um?" - 100% legível desde 0s, acende aos 2.20s exatos */}
          <div style={{display: 'flex', alignItems: 'center'}}>
            <span
              style={{
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: line3Highlight ? TEXTO_ESCURO : '#FFFFFF',
                background: line3Highlight ? VERDE : 'rgba(255, 255, 255, 0.22)',
                border: `2px solid ${line3Highlight ? VERDE : 'rgba(255, 255, 255, 0.45)'}`,
                padding: '10px 22px',
                borderRadius: 16,
                lineHeight: 1.12,
                boxShadow: line3Highlight ? '0 8px 24px rgba(34,197,94,0.5)' : 'none',
                transform: `scale(${line3Highlight ? 1.02 : 1})`,
                transformOrigin: 'left center',
              }}
            >
              sem mandar um por um?”
            </span>
          </div>
        </div>

        {/* Elementos no terço inferior eliminando qualquer vazio escuro antes da legenda */}
        <div style={{marginTop: 18}}>
          {t < 2.20 ? (
            /* Badge de contexto dinâmico nos primeiros 2.2 segundos */
            <div
              style={{
                background: 'rgba(17, 24, 39, 0.92)',
                border: '2px solid rgba(34, 197, 94, 0.45)',
                borderRadius: 22,
                padding: '14px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                boxShadow: '0 12px 30px rgba(0,0,0,0.5)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <div
                  style={{
                    width: 14,
                    height: 14,
                    borderRadius: '50%',
                    background: VERDE,
                  }}
                />
                <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#E2E8F0'}}>
                  Envio para múltiplos contatos
                </span>
              </div>
              <span style={{fontFamily, fontSize: 32, fontWeight: 900, color: '#86EFAC'}}>
                1 Clique
              </span>
            </div>
          ) : (
            /* Selo Gancho entrando com spring e pulso vivo a partir de 2.20s */
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                transform: `scale(${ganchoPop * pulseScale}) translateY(${interpolate(ganchoPop, [0, 1], [16, 0])}px)`,
                opacity: ganchoPop,
              }}
            >
              <div
                style={{
                  background: VERDE,
                  color: TEXTO_ESCURO,
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 900,
                  padding: '14px 32px',
                  borderRadius: 999,
                  boxShadow: '0 14px 30px rgba(34, 197, 94, 0.55)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                }}
              >
                <span>✓</span>
                <span>Sem copiar e colar mensagens</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
