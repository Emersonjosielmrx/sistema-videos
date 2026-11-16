import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Cena1: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tRel = frame / fps;
  const tAbs = 4.15 + tRel; // 4.15s to 12.33s

  // Continuous subtle zoom on owner video (1.00 -> 1.065)
  const videoScale = interpolate(tRel, [0, 8.18], [1.0, 1.065], {
    extrapolateRight: 'clamp',
  });

  // Entrance & exit transitions
  const enterIn = spring({frame, fps, config: {damping: 15, stiffness: 150}});
  const exitOut = interpolate(tAbs, [11.98, 12.3], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Spoken timestamps in Cena 1:
  // "Eu perdia vendas quando o cliente ficava indeciso," (5.128s .. 8.328s)
  // "mas hoje" (8.748s) -> "o bot" (9.928s) -> "conhece meus produtos" (10.148s..11.448s) -> "e recomenda." (11.868s)
  const viradaAtiva = tAbs >= 8.74;
  const conheceAtivo = tAbs >= 10.14;
  const recomendaAtivo = tAbs >= 11.86;

  const flipSpring = spring({
    frame: Math.max(0, frame - Math.round((8.74 - 4.15) * fps)),
    fps,
    config: {damping: 14, stiffness: 150},
  });

  // Continuous micro-motion
  const floatY = Math.sin(tRel * 3.0) * 5;
  const pulseScale = 1 + Math.sin(tRel * 5.0) * 0.025;

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', opacity: exitOut}}>
      {/* Fullscreen owner video — no dimming over face */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${videoScale})`,
          }}
        />
      </AbsoluteFill>

      {/* Subtle top-only gradient so top HUD has crisp contrast without touching presenter's face */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 410,
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.82) 0%, rgba(17,24,39,0.42) 68%, rgba(17,24,39,0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* TOP HUD ONLY (y=155..355) — keeps presenter's head/face 100% unobstructed */}
      <div
        style={{
          position: 'absolute',
          top: 156,
          left: 60,
          right: 60,
          transform: `translateY(${interpolate(enterIn, [0, 1], [-30, 0]) + floatY}px)`,
          opacity: enterIn,
        }}
      >
        {!viradaAtiva ? (
          /* PHASE 1 (4.15s - 8.74s): O Problema */
          <div
            style={{
              backgroundColor: 'rgba(17, 24, 39, 0.93)',
              border: '2.5px solid #EF4444',
              borderRadius: 24,
              padding: '16px 24px',
              boxShadow: '0 14px 32px rgba(0,0,0,0.5)',
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
            }}
          >
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
                  color: '#FCA5A5',
                  textTransform: 'uppercase',
                  letterSpacing: 0.6,
                }}
              >
                O problema
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  backgroundColor: '#EF4444',
                  padding: '4px 16px',
                  borderRadius: 999,
                  transform: `scale(${pulseScale})`,
                }}
              >
                Perdia vendas
              </span>
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.15,
              }}
            >
              Cliente indeciso saía sem comprar
            </div>
          </div>
        ) : (
          /* PHASE 2 (8.74s - 12.33s): A Virada com o Bot Vitrine IA */
          <div
            style={{
              backgroundColor: 'rgba(17, 24, 39, 0.94)',
              border: '2.5px solid #A78BFA',
              borderRadius: 24,
              padding: '16px 24px',
              boxShadow: '0 14px 32px rgba(0,0,0,0.55)',
              transform: `scale(${interpolate(flipSpring, [0, 1], [0.9, 1])})`,
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
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
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FFFFFF',
                }}
              >
                Hoje com a <span style={{color: '#A78BFA'}}>Vitrine IA</span>
              </span>
            </div>

            {/* Two synchronized pills lighting up on "conhece meus produtos" & "recomenda" */}
            <div
              style={{
                display: 'flex',
                gap: 14,
                alignItems: 'center',
              }}
            >
              <div
                style={{
                  flex: 1,
                  padding: '10px 16px',
                  borderRadius: 16,
                  backgroundColor: conheceAtivo
                    ? '#A78BFA'
                    : 'rgba(255,255,255,0.12)',
                  color: conheceAtivo ? '#121216' : '#E2E8F0',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  textAlign: 'center',
                  transform: `scale(${conheceAtivo ? pulseScale : 1})`,
                }}
              >
                ✓ Conhece produtos
              </div>
              <div
                style={{
                  flex: 1,
                  padding: '10px 16px',
                  borderRadius: 16,
                  backgroundColor: recomendaAtivo
                    ? '#A78BFA'
                    : 'rgba(255,255,255,0.12)',
                  color: recomendaAtivo ? '#121216' : '#E2E8F0',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  textAlign: 'center',
                  transform: `scale(${recomendaAtivo ? pulseScale : 1})`,
                }}
              >
                ✓ Recomenda opções
              </div>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
