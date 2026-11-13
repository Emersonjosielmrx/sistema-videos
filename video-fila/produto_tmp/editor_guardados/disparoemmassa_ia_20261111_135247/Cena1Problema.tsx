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

const ESCURO = '#111827';
const VERMELHO = '#EF4444';

export const Cena1Problema: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  // Cena 1: ini = 4.41s, fim = 10.78s (duração local = 6.37s = 191 frames)
  const absT = 4.41 + frame / fps;

  // B-roll dinâmico de digitação manual exaustiva no notebook (img_3.jpg)
  // Enquadramento em plano médio: cabeça, mãos digitando e laptop visíveis, liberando o rosto
  const bgScale = interpolate(frame, [0, 191], [1.02, 1.07], {extrapolateRight: 'clamp'});
  const bgX = interpolate(frame, [0, 191], [10, -15], {extrapolateRight: 'clamp'});
  const bgY = interpolate(frame, [0, 191], [0, -10], {extrapolateRight: 'clamp'});

  const enterOp = interpolate(frame, [0, 9], [0, 1], {extrapolateRight: 'clamp'});
  const exitOp = interpolate(absT, [10.45, 10.76], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Animações sincronizadas exclusivamente com o processo manual:
  const headerPop = spring({frame: frame - 2, fps, config: {damping: 14}});
  const tagPop = spring({
    frame: frame - Math.round((4.85 - 4.41) * fps),
    fps,
    config: {damping: 14, stiffness: 140},
  });
  const cardAntesPop = spring({
    frame: frame - Math.round((4.95 - 4.41) * fps),
    fps,
    config: {damping: 14, stiffness: 140},
  });
  const copyTagPop = spring({
    frame: frame - Math.round((6.25 - 4.41) * fps),
    fps,
    config: {damping: 13, stiffness: 150},
  });
  const filaManualPop = spring({
    frame: frame - Math.round((7.85 - 4.41) * fps),
    fps,
    config: {damping: 14, stiffness: 140},
  });

  const floatA = Math.sin(frame * 0.15) * 5;
  const floatB = Math.cos(frame * 0.15) * 4;

  const manualBarW = interpolate(
    frame,
    [Math.round((5.2 - 4.41) * fps), Math.round((9.6 - 4.41) * fps)],
    [15, 65],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{backgroundColor: ESCURO, opacity: enterOp * exitOp}}>
      {/* Imagem do processo manual no topo (height 940) com fade gradiente suave na base */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 940,
          overflow: 'hidden',
        }}
      >
        <Img
          src={staticFile('img_3.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: '30% 22%',
            transform: `scale(${bgScale}) translate(${bgX}px, ${bgY}px)`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(17,24,39,0.6) 0%, rgba(17,24,39,0.02) 20%, rgba(17,24,39,0.06) 60%, rgba(17,24,39,0.92) 86%, rgba(17,24,39,1) 100%)',
          }}
        />
      </div>

      {/* Topo: Rótulo "O PROBLEMA" na Safe Zone (y=165) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          opacity: headerPop,
          transform: `translateY(${interpolate(headerPop, [0, 1], [-25, 0])}px)`,
        }}
      >
        <div
          style={{
            background: VERMELHO,
            color: '#FFFFFF',
            fontFamily,
            fontSize: 34,
            fontWeight: 900,
            padding: '10px 26px',
            borderRadius: 999,
            textTransform: 'uppercase',
            letterSpacing: 1,
            boxShadow: '0 10px 26px rgba(239,68,68,0.5)',
          }}
        >
          O PROBLEMA
        </div>
      </div>

      {/* Tag flutuante sobre a área livre da janela à direita (y=490, longe do rosto) */}
      <div
        style={{
          position: 'absolute',
          top: 490,
          right: 60,
          background: 'rgba(17, 24, 39, 0.92)',
          border: `2px solid ${VERMELHO}`,
          borderRadius: 20,
          padding: '12px 24px',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          opacity: tagPop,
          transform: `translateX(${interpolate(tagPop, [0, 1], [30, 0])}px)`,
          boxShadow: '0 14px 32px rgba(0,0,0,0.55)',
        }}
      >
        <span style={{fontFamily, fontSize: 32, fontWeight: 900, color: '#FCA5A5'}}>
          ✕ Ctrl+C / Ctrl+V
        </span>
      </div>

      {/* Cards de dor manual posicionados a partir de y=830 (100% abaixo do queixo e boca, sem sobreposição) */}
      <div
        style={{
          position: 'absolute',
          top: 830,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
        }}
      >
        {/* Card ANTES: MANUAL */}
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.96)',
            border: `3px solid ${VERMELHO}`,
            borderRadius: 28,
            padding: '24px 30px',
            boxShadow: '0 20px 44px rgba(0,0,0,0.7)',
            opacity: cardAntesPop,
            transform: `translateY(${interpolate(cardAntesPop, [0, 1], [30, 0]) + floatA}px)`,
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 12,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: '#FCA5A5',
                textTransform: 'uppercase',
              }}
            >
              ✕ ANTES: MANUAL
            </span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                background: 'rgba(239, 68, 68, 0.35)',
                padding: '6px 18px',
                borderRadius: 12,
              }}
            >
              Horas copiando
            </span>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 44,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.15,
            }}
          >
            Copiando e colando avisos
          </div>

          {/* Barra de lentidão manual */}
          <div
            style={{
              marginTop: 14,
              width: '100%',
              height: 12,
              background: 'rgba(255,255,255,0.12)',
              borderRadius: 999,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${manualBarW}%`,
                height: '100%',
                background: VERMELHO,
                borderRadius: 999,
              }}
            />
          </div>

          {absT >= 6.2 && (
            <div
              style={{
                marginTop: 16,
                display: 'flex',
                gap: 14,
                opacity: copyTagPop,
                transform: `scale(${interpolate(copyTagPop, [0, 1], [0.92, 1])})`,
              }}
            >
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.22)',
                  border: '2px solid rgba(248,113,113,0.65)',
                  borderRadius: 14,
                  padding: '8px 18px',
                  fontFamily,
                  fontSize: 33,
                  fontWeight: 800,
                  color: '#FECACA',
                }}
              >
                Aviso repetido
              </div>
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.22)',
                  border: '2px solid rgba(248,113,113,0.65)',
                  borderRadius: 14,
                  padding: '8px 18px',
                  fontFamily,
                  fontSize: 33,
                  fontWeight: 800,
                  color: '#FECACA',
                }}
              >
                Um por um
              </div>
            </div>
          )}
        </div>

        {/* Card exclusivo da dor manual quando a voz diz "para cada cliente no WhatsApp" (7.85s) */}
        {absT >= 7.85 && (
          <div
            style={{
              background: 'rgba(17, 24, 39, 0.96)',
              border: '3px solid rgba(239, 68, 68, 0.85)',
              borderRadius: 28,
              padding: '22px 30px',
              boxShadow: '0 20px 44px rgba(0,0,0,0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              opacity: filaManualPop,
              transform: `translateY(${interpolate(filaManualPop, [0, 1], [25, 0]) + floatB}px)`,
            }}
          >
            <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#FCA5A5',
                  textTransform: 'uppercase',
                }}
              >
                ✕ TRABALHO REPETITIVO
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                }}
              >
                Para cada cliente
              </span>
            </div>
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.28)',
                border: `2px solid ${VERMELHO}`,
                color: '#FECACA',
                fontFamily,
                fontSize: 33,
                fontWeight: 900,
                padding: '10px 20px',
                borderRadius: 16,
              }}
            >
              No WhatsApp
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
