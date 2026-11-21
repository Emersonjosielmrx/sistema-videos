import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES} from './constants';

interface Cena3Props {
  fontFamily: string;
}

export const Cena3: React.FC<Cena3Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Phases:
  // Phase 1: 0 to 86 ("Essa comunicação clara") - frame 0 a 86
  // Phase 2: 87 to 144 ("apresenta a solução de verdade") - frame 87 a 144
  // Phase 3: 145 to 220 ("para transformar visita em cliente.") - frame 145+
  const currentPhase = frame < 87 ? 1 : frame < 145 ? 2 : 3;

  // Punch-in cut for Phase 2: "solução de verdade" (frame 87)
  const punchPhase2 = spring({
    frame: frame - 87,
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // Punch-in cut for Phase 3: "para transformar visita em cliente" (frame 145)
  const punchPhase3 = spring({
    frame: frame - 145,
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // Dynamic Multi-Scale Punch-in Zoom (elimina a monotonia de 5s estático em q10, q11, q12)
  const baseScale = 1.15;
  const scaleBonusPhase2 = Math.max(0, punchPhase2) * 0.13; // vai para 1.28
  const scaleBonusPhase3 = Math.max(0, punchPhase3) * 0.11; // vai para 1.39
  const continuousDrift = interpolate(frame, [0, 220], [0, 0.04], {
    extrapolateRight: 'clamp',
  });

  const videoScale = baseScale + scaleBonusPhase2 + scaleBonusPhase3 + continuousDrift;

  // Top Bar entrance
  const barSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Spring for Phase 2 floating badge
  const badge2Spring = spring({
    frame: frame - 87,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Spring for Phase 3 Conversion Showcase Card
  const conversionSpring = spring({
    frame: frame - 145,
    fps,
    config: {damping: 13, stiffness: 150},
  });

  // Arrow pulse for conversion transformation
  const arrowPulse = 1 + Math.sin(frame * 0.25) * 0.12;

  // Micro-floating effect for top bar
  const barFloatY = Math.sin(frame * 0.08) * 3;

  // Conversion card micro-float
  const conversionFloatY = Math.sin(frame * 0.14) * 6;

  // Suave escurecimento de transição no final (frame 180+) antes da piscada do apresentador
  const endCoverOpacity = interpolate(frame, [180, 205], [0, 0.85], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0B0D13',
        fontFamily,
      }}
    >
      {/* Fullscreen Presenter Video com Punch-ins Dinâmicos de Câmera */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateY(40px) scale(${videoScale})`,
          transformOrigin: 'center 38%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: 1080,
            height: 1920,
            objectFit: 'cover',
          }}
        />
        {/* Subtle top darkening exclusively under the top bar for maximum contrast */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 320,
            background:
              'linear-gradient(180deg, rgba(11, 13, 19, 0.85) 0%, rgba(11, 13, 19, 0.35) 75%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Floating Animated Conversion Showcase Card (y = 980 to 1160)
          Ilustra graficamente a conversão "VISITA EM CLIENTE" em sincronia com a fala aos 22.99s.
          Posicionado abaixo do queixo do apresentador (y=980) e acima da legenda karaokê (y=1320),
          sem nunca cobrir o rosto! */}
      {frame >= 143 && (
        <div
          style={{
            position: 'absolute',
            top: 980,
            left: 70,
            right: 70,
            display: 'flex',
            justifyContent: 'center',
            transform: `scale(${Math.max(
              0,
              conversionSpring
            )}) translateY(${conversionFloatY}px)`,
            opacity: Math.min(1, Math.max(0, conversionSpring)),
            zIndex: 45,
          }}
        >
          <div
            style={{
              background: 'rgba(11, 13, 19, 0.95)',
              border: `2px solid ${CORES.marca}`,
              borderRadius: 26,
              padding: '18px 24px',
              boxShadow: `0 16px 40px rgba(0, 0, 0, 0.9), 0 0 30px ${CORES.marcaGlow}`,
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
              alignItems: 'center',
              width: '100%',
            }}
          >
            {/* Header Tag */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span style={{fontSize: 28}}>⚡</span>
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#F472B6',
                  textTransform: 'uppercase',
                  letterSpacing: 1.5,
                }}
              >
                TRANSFORMAÇÃO REAL
              </span>
            </div>

            {/* Conversion Flow: VISITANTE -> CLIENTE */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 16,
                width: '100%',
              }}
            >
              {/* Visitante Box */}
              <div
                style={{
                  flex: 1,
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1.5px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: 16,
                  padding: '12px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 10,
                }}
              >
                <span style={{fontSize: 32}}>👤</span>
                <span
                  style={{
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#E2E8F0',
                    textTransform: 'uppercase',
                  }}
                >
                  VISITA
                </span>
              </div>

              {/* Pulsing Arrow */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transform: `scale(${arrowPulse})`,
                }}
              >
                <span
                  style={{
                    fontSize: 44,
                    color: CORES.marca,
                    textShadow: `0 0 16px ${CORES.marca}`,
                  }}
                >
                  ➔
                </span>
              </div>

              {/* Cliente Convertido Box */}
              <div
                style={{
                  flex: 1.2,
                  background: `linear-gradient(135deg, ${CORES.marca}, #DB2777)`,
                  borderRadius: 16,
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 10,
                  boxShadow: `0 4px 20px ${CORES.marcaGlow}`,
                  border: '1.5px solid rgba(255, 255, 255, 0.4)',
                }}
              >
                <span style={{fontSize: 32}}>⭐</span>
                <span
                  style={{
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                    letterSpacing: 0.5,
                  }}
                >
                  CLIENTE
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Floating Solução Real Pill (Phase 2, frame 87+) */}
      {frame >= 87 && frame < 145 && (
        <div
          style={{
            position: 'absolute',
            top: 280,
            right: 60,
            transform: `scale(${Math.max(0, badge2Spring)}) translateY(${barFloatY}px)`,
            opacity: Math.min(1, Math.max(0, badge2Spring)),
            zIndex: 42,
          }}
        >
          <div
            style={{
              background: 'rgba(11, 13, 19, 0.95)',
              border: `1.5px solid ${CORES.marca}`,
              borderRadius: 16,
              padding: '8px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              boxShadow: `0 8px 24px rgba(0, 0, 0, 0.8), 0 0 16px ${CORES.marcaGlow}`,
            }}
          >
            <span style={{fontSize: 28}}>🛡️</span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
              }}
            >
              SOLUÇÃO DE VERDADE
            </span>
          </div>
        </div>
      )}

      {/* Unified Sleek Top Bar (y = 172, height = 76px, ends at y = 248) -> Head at y=360+ gives >110px respiro */}
      <div
        style={{
          position: 'absolute',
          top: 172,
          left: 60,
          right: 60,
          height: 76,
          borderRadius: 22,
          background: 'rgba(11, 13, 19, 0.95)',
          border: '2px solid rgba(255, 255, 255, 0.18)',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.85)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          transform: `scale(${Math.max(0, barSpring)}) translateY(${barFloatY}px)`,
          opacity: Math.max(0, barSpring),
          zIndex: 40,
        }}
      >
        {/* Left Badge: 03 • O RESULTADO */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 16px',
            borderRadius: 14,
            background: 'rgba(236, 72, 153, 0.25)',
            border: `1.5px solid ${CORES.marca}`,
            flexShrink: 0,
            whiteSpace: 'nowrap',
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: CORES.marca,
              boxShadow: `0 0 8px ${CORES.marca}`,
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#F472B6',
              textTransform: 'uppercase',
              letterSpacing: 1,
              whiteSpace: 'nowrap',
            }}
          >
            03 • O RESULTADO
          </span>
        </div>

        {/* Right Content: Dynamic State */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            flexShrink: 0,
            whiteSpace: 'nowrap',
          }}
        >
          {currentPhase === 1 && (
            <div style={{display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0}}>
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                }}
              >
                COMUNICAÇÃO CLARA
              </span>
            </div>
          )}

          {currentPhase === 2 && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                flexShrink: 0,
                background: 'rgba(236, 72, 153, 0.25)',
                border: `1.5px solid ${CORES.marca}`,
                padding: '6px 16px',
                borderRadius: 12,
              }}
            >
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                }}
              >
                SOLUÇÃO REAL
              </span>
            </div>
          )}

          {currentPhase === 3 && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                flexShrink: 0,
                background: 'rgba(236, 72, 153, 0.3)',
                border: `1.5px solid ${CORES.marca}`,
                padding: '6px 18px',
                borderRadius: 12,
              }}
            >
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  whiteSpace: 'nowrap',
                }}
              >
                CONVERSÃO
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Elegant Transition Cover at frame 180+ to prevent the presenter's blink/eyes closed from ever being seen */}
      {frame >= 180 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 45%, rgba(15, 9, 19, 0.7) 0%, rgba(11, 13, 19, 0.95) 100%)',
            opacity: endCoverOpacity,
            pointerEvents: 'none',
            zIndex: 35,
          }}
        />
      )}
    </div>
  );
};
