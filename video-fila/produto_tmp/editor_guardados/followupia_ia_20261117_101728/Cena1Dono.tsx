import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena1Dono: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Subtle continuous push-in zoom on video
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Badge entrance ("O PROBLEMA") at ~0.2s (frame 6)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card 1: "PROPOSTAS PARADAS NO VÁCUO" (enters at frame 22, around 5.1s absolute)
  const card1Spring = spring({
    frame: frame - 22,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Card 2 transition (when speech shifts to "não conseguia dar atenção" around frame 95, 7.5s absolute)
  const card2Spring = spring({
    frame: frame - 95,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Micro-motion floating effect for cards
  const floatY = Math.sin(frame / 15) * 4;

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', overflow: 'hidden'}}>
      {/* Full screen video with continuous subtle zoom */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Soft gradient at top strictly in safe area to guarantee readable card text without dimming face */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(180deg, rgba(17, 24, 39, 0.9) 0%, rgba(17, 24, 39, 0.6) 65%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Top area elements (y=165 to 420) — NEVER covers the face */}
      {/* Label: O PROBLEMA */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            backgroundColor: 'rgba(239, 68, 68, 0.25)',
            border: '2px solid #EF4444',
            borderRadius: 24,
            backdropFilter: 'blur(10px)',
          }}
        >
          <span style={{fontSize: 26}}>⚠️</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            O Problema Real
          </span>
        </div>
      </div>

      {/* Dynamic top information cards */}
      <div
        style={{
          position: 'absolute',
          top: 255,
          left: 60,
          right: 60,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* Phase 1 Card (Frames 22 - 95): Acumulava propostas paradas */}
        {frame < 105 && (
          <div
            style={{
              transform: `scale(${card1Spring}) translateY(${interpolate(
                card1Spring,
                [0, 1],
                [20, 0]
              )}px)`,
              opacity: interpolate(frame, [90, 102], [card1Spring, 0], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              }),
              backgroundColor: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid rgba(239, 68, 68, 0.7)',
              borderRadius: 24,
              padding: '18px 28px',
              boxShadow: '0 15px 35px rgba(0,0,0,0.6)',
              backdropFilter: 'blur(12px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 16,
                  backgroundColor: 'rgba(239, 68, 68, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                }}
              >
                📁
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                  }}
                >
                  Propostas Acumuladas
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#F87171',
                  }}
                >
                  Sem tempo de dar retorno a todos
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Phase 2 Card (Frames 95+): Não conseguia dar atenção */}
        {frame >= 95 && (
          <div
            style={{
              transform: `scale(${card2Spring}) translateY(${interpolate(
                card2Spring,
                [0, 1],
                [20, 0]
              )}px)`,
              opacity: card2Spring,
              backgroundColor: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid rgba(245, 158, 11, 0.7)',
              borderRadius: 24,
              padding: '18px 28px',
              boxShadow: '0 15px 35px rgba(0,0,0,0.6)',
              backdropFilter: 'blur(12px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 16,
                  backgroundColor: 'rgba(245, 158, 11, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                }}
              >
                ⏳
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                  }}
                >
                  Sobrecarga de Atendimento
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#FCD34D',
                  }}
                >
                  Leads frios esquecidos no WhatsApp
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
