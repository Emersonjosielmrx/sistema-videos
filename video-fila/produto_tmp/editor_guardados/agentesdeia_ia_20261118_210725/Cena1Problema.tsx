import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena1Problema: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const sceneDuration = 245;

  // Scene exit fade
  const sceneOpacity = interpolate(
    frame,
    [sceneDuration - 12, sceneDuration],
    [1, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  // Top badge entrance
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Transition from "Buscando informação" to "Trabalho parado"
  // Words: "e o resto do trabalho" starts around 9.0s (scene relative: ~4.3s = frame 128)
  const isPhase2 = frame >= 128;

  // Sincronized digital punch-in zoom (corte seco para 1.25x na troca do card para enfatizar a dor com ritmo Reels)
  const videoScale = !isPhase2
    ? interpolate(frame, [0, 127], [1.05, 1.10], {extrapolateRight: 'clamp'})
    : interpolate(frame, [128, sceneDuration], [1.25, 1.30], {extrapolateRight: 'clamp'});

  // Lowered framing during punch-in to guarantee ample headroom above hair
  const videoY = !isPhase2 ? 60 : 120;

  const cardPhase1Spring = spring({
    frame: Math.max(0, frame - 15),
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const cardPhase2Spring = spring({
    frame: Math.max(0, frame - 128),
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Floating graphics springs illustrating work overload (dor de pesquisa manual e fila travada)
  const tab1Spring = spring({
    frame: Math.max(0, frame - 32),
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const tab2Spring = spring({
    frame: Math.max(0, frame - 64),
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const tab3Spring = spring({
    frame: Math.max(0, frame - 130),
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const tab4Spring = spring({
    frame: Math.max(0, frame - 160),
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Floating micro-motion for badges
  const float1 = Math.sin(frame / 10) * 4;
  const float2 = Math.cos(frame / 10) * 4;

  // Pulse for alert beacon
  const alertPulse = 1 + Math.sin(frame / 6) * 0.15;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        opacity: sceneOpacity,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Dono 1 Video with continuous motion and lowered framing for headroom */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${videoScale}) translateY(${videoY}px)`,
          transformOrigin: '50% 35%',
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
        {/* Subtle Top Gradient for text readability without darkening presenter */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(180deg, rgba(17, 24, 39, 0.85) 0%, rgba(17, 24, 39, 0.35) 70%, rgba(17, 24, 39, 0) 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Top Badge: 01 • O PROBLEMA (top: 192 ensures ≥ 34px below progress bar) */}
      <div
        style={{
          position: 'absolute',
          top: 192,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: badgeSpring,
          transform: `translateY(${(1 - badgeSpring) * -15}px)`,
          zIndex: 25,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 22px',
            borderRadius: 999,
            background: 'rgba(17, 24, 39, 0.90)',
            border: '1.5px solid rgba(239, 68, 68, 0.5)',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: '#EF4444',
              transform: `scale(${alertPulse})`,
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FCA5A5',
              textTransform: 'uppercase',
              letterSpacing: 1.2,
            }}
          >
            01 • O Problema
          </span>
        </div>
      </div>

      {/* Top Dynamic Card (top: 275 ensures ≥ 30px below badge, bottom at ~400 ensures ≥ 60px above presenter head) */}
      <div
        style={{
          position: 'absolute',
          top: 275,
          left: 60,
          right: 60,
          zIndex: 25,
        }}
      >
        {!isPhase2 ? (
          /* Phase 1: Manhã inteira buscando */
          <div
            style={{
              opacity: cardPhase1Spring,
              transform: `translateY(${(1 - cardPhase1Spring) * 15}px)`,
              padding: '16px 26px',
              borderRadius: 22,
              background: 'rgba(17, 24, 39, 0.92)',
              border: '1.5px solid rgba(245, 158, 11, 0.45)',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              gap: 18,
            }}
          >
            <div
              style={{
                width: 54,
                height: 54,
                borderRadius: 14,
                background: 'rgba(245, 158, 11, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 32,
                flexShrink: 0,
              }}
            >
              ⏳
            </div>
            <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
              <span
                style={{
                  fontSize: 38,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: -0.5,
                  lineHeight: 1.15,
                }}
              >
                Manhã inteira buscando
              </span>
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#FCD34D',
                  lineHeight: 1.2,
                }}
              >
                Informação espalhada na internet
              </span>
            </div>
          </div>
        ) : (
          /* Phase 2: Trabalho parado esperando */
          <div
            style={{
              opacity: cardPhase2Spring,
              transform: `scale(${0.95 + cardPhase2Spring * 0.05}) translateY(${(1 - cardPhase2Spring) * -10}px)`,
              padding: '16px 26px',
              borderRadius: 22,
              background: 'rgba(31, 14, 18, 0.94)',
              border: '2px solid rgba(239, 68, 68, 0.7)',
              boxShadow: '0 12px 35px rgba(239, 68, 68, 0.25)',
              display: 'flex',
              alignItems: 'center',
              gap: 18,
            }}
          >
            <div
              style={{
                width: 54,
                height: 54,
                borderRadius: 14,
                background: 'rgba(239, 68, 68, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 32,
                flexShrink: 0,
              }}
            >
              ⚠️
            </div>
            <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
              <span
                style={{
                  fontSize: 38,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: -0.5,
                  lineHeight: 1.15,
                }}
              >
                Trabalho parado esperando
              </span>
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#FCA5A5',
                  lineHeight: 1.2,
                }}
              >
                Demais tarefas travadas na fila
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Floating Dynamic Overlay Graphics: Work Overload & Stalled Queue (Rosto 100% livre) */}
      {!isPhase2 ? (
        <>
          {/* Phase 1 Graphic 1: Accumulating browser search tabs on left bookshelf area (y: 415, free of face & hair) */}
          {frame >= 32 && (
            <div
              style={{
                position: 'absolute',
                top: 415,
                left: 70,
                opacity: tab1Spring,
                transform: `scale(${0.9 + tab1Spring * 0.1}) translateY(${float1}px)`,
                zIndex: 26,
              }}
            >
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 22px',
                  borderRadius: 16,
                  background: 'rgba(17, 24, 39, 0.94)',
                  border: '1.5px solid rgba(245, 158, 11, 0.7)',
                  boxShadow: '0 6px 20px rgba(0, 0, 0, 0.5)',
                }}
              >
                <span style={{fontSize: 32}}>🌐</span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FFFFFF',
                  }}
                >
                  12 abas abertas
                </span>
              </div>
            </div>
          )}

          {/* Phase 1 Graphic 2: Time spent chip in upper right corner (y: 415, window area, free of face & hair) */}
          {frame >= 64 && (
            <div
              style={{
                position: 'absolute',
                top: 415,
                right: 70,
                opacity: tab2Spring,
                transform: `scale(${0.9 + tab2Spring * 0.1}) translateY(${float2}px)`,
                zIndex: 26,
              }}
            >
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 22px',
                  borderRadius: 16,
                  background: 'rgba(17, 24, 39, 0.94)',
                  border: '1.5px solid rgba(245, 158, 11, 0.7)',
                  boxShadow: '0 6px 20px rgba(0, 0, 0, 0.5)',
                }}
              >
                <span style={{fontSize: 32}}>⏳</span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FCD34D',
                  }}
                >
                  Manhã gasta
                </span>
              </div>
            </div>
          )}
        </>
      ) : (
        <>
          {/* Phase 2 Graphic 1: Queue blocked chip on left bookshelf area (y: 415, free of face & hair) */}
          {frame >= 130 && (
            <div
              style={{
                position: 'absolute',
                top: 415,
                left: 55,
                opacity: tab3Spring,
                transform: `scale(${0.9 + tab3Spring * 0.1}) translateY(${float1}px)`,
                zIndex: 26,
              }}
            >
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 22px',
                  borderRadius: 16,
                  background: 'rgba(31, 14, 18, 0.95)',
                  border: '1.5px solid rgba(239, 68, 68, 0.75)',
                  boxShadow: '0 6px 20px rgba(239, 68, 68, 0.4)',
                }}
              >
                <span style={{fontSize: 32}}>⏸️</span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FCA5A5',
                  }}
                >
                  Fila travada
                </span>
              </div>
            </div>
          )}

          {/* Phase 2 Graphic 2: Work stalled chip in upper right corner (y: 415, window area, free of face & hair) */}
          {frame >= 160 && (
            <div
              style={{
                position: 'absolute',
                top: 415,
                right: 70,
                opacity: tab4Spring,
                transform: `scale(${0.9 + tab4Spring * 0.1}) translateY(${float2}px)`,
                zIndex: 26,
              }}
            >
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 22px',
                  borderRadius: 16,
                  background: 'rgba(31, 14, 18, 0.95)',
                  border: '1.5px solid rgba(239, 68, 68, 0.75)',
                  boxShadow: '0 6px 20px rgba(239, 68, 68, 0.4)',
                }}
              >
                <span style={{fontSize: 32}}>⚠️</span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#EF4444',
                  }}
                >
                  Trabalho parado
                </span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
