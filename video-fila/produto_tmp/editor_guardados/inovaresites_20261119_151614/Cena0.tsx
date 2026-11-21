import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';
import {CORES} from './constants';

interface Cena0Props {
  fontFamily: string;
}

export const Cena0: React.FC<Cena0Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background continuous zoom
  const bgScale = interpolate(frame, [0, 115], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });

  // Accelerated whip zoom transition to Cena 1 (frames 115 to 144)
  const whipZoom = interpolate(frame, [115, 144], [1, 1.45], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Scene fade out before cut
  const sceneOpacity = interpolate(frame, [130, 144], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Top Badge entrance (pop at frame 1)
  const badgeSpring = spring({
    frame: frame - 1,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Main Card entrance (immediate pop at frame 2 for instant hook in 0-1.8s)
  const cardSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 13, stiffness: 150},
  });

  // Rejection chart line animation (fast draw: frame 4 to 35)
  const chartProgress = interpolate(frame, [4, 35], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Floating abandon cursor position (moves fast away)
  const cursorProgress = interpolate(frame, [15, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Stamp badge entrance ("SEM ENTENDER?") at frame 42 (1.4s) - delivers climax before 1.8s
  const stampSpring = spring({
    frame: frame - 42,
    fps,
    config: {damping: 10, stiffness: 180},
  });

  // Pulse animation for pink alert and stamp
  const pulseScale = 1 + Math.sin(frame * 0.18) * 0.04;
  const alertGlow = 0.5 + Math.sin(frame * 0.2) * 0.3;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: 1080,
        height: 1920,
        opacity: sceneOpacity,
        overflow: 'hidden',
        backgroundColor: '#0F0913',
        fontFamily,
        transform: `scale(${whipZoom})`,
        transformOrigin: 'center 45%',
      }}
    >
      {/* Background with continuous push-in zoom */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(0.60) contrast(1.2)',
          }}
        />
        {/* Dark radial vignette for legibility */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 45%, rgba(15, 9, 19, 0.4) 0%, rgba(15, 9, 19, 0.92) 100%)',
          }}
        />
      </div>

      {/* Floating pink & red ambient glow */}
      <div
        style={{
          position: 'absolute',
          top: 380,
          left: 120,
          width: 500,
          height: 500,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(236,72,153,0.25) 0%, transparent 70%)',
          filter: 'blur(55px)',
          transform: `translateY(${Math.sin(frame * 0.08) * 20}px)`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 600,
          right: 100,
          width: 450,
          height: 450,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(239,68,68,0.2) 0%, transparent 70%)',
          filter: 'blur(50px)',
          transform: `translateY(${Math.sin(frame * 0.07 + 2) * 18}px)`,
        }}
      />

      {/* Top Header Badge (y = 175) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${Math.max(0, badgeSpring)})`,
          opacity: Math.max(0, badgeSpring),
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 28px',
            borderRadius: 999,
            background: 'rgba(11, 13, 19, 0.94)',
            border: `1.5px solid ${CORES.bordaCard}`,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.65)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              boxShadow: '0 0 12px #EF4444',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              letterSpacing: 2,
              color: CORES.textoBranco,
              textTransform: 'uppercase',
            }}
          >
            ALERTA DE CONVERSÃO
          </span>
        </div>
      </div>

      {/* High-Impact Dynamic Focal Card: Taxa de Rejeição & Abandono (y = 380 to 980) */}
      {/* Removido o texto central redundante que duplicava a legenda karaokê */}
      <div
        style={{
          position: 'absolute',
          top: 400,
          left: 60,
          right: 60,
          transform: `scale(${Math.max(0, cardSpring)}) translateY(${Math.sin(frame * 0.08) * 8}px)`,
          opacity: Math.min(1, Math.max(0, cardSpring)),
        }}
      >
        <div
          style={{
            background: 'rgba(15, 12, 22, 0.95)',
            border: '2.5px solid rgba(239, 68, 68, 0.75)',
            borderRadius: 36,
            padding: '36px 36px',
            boxShadow: `0 25px 60px rgba(0, 0, 0, 0.95), 0 0 40px rgba(239, 68, 68, ${alertGlow})`,
            display: 'flex',
            flexDirection: 'column',
            gap: 24,
          }}
        >
          {/* Simulated Browser Bar */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingBottom: 18,
              borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <div style={{width: 14, height: 14, borderRadius: '50%', background: '#EF4444'}} />
              <div style={{width: 14, height: 14, borderRadius: '50%', background: '#F59E0B'}} />
              <div style={{width: 14, height: 14, borderRadius: '50%', background: '#10B981'}} />
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#94A3B8',
                  marginLeft: 14,
                }}
              >
                sualandingpage.com.br
              </span>
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                background: 'rgba(239, 68, 68, 0.25)',
                border: '1.5px solid #EF4444',
                borderRadius: 14,
                padding: '6px 18px',
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#FCA5A5',
                  textTransform: 'uppercase',
                }}
              >
                ABANDONO
              </span>
            </div>
          </div>

          {/* Metric Row: TAXA DE REJEIÇÃO */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 48}}>📉</span>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    letterSpacing: 0.5,
                  }}
                >
                  TAXA DE REJEIÇÃO
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#94A3B8',
                  }}
                >
                  Visitante sai da página
                </span>
              </div>
            </div>

            <div
              style={{
                background: 'rgba(239, 68, 68, 0.3)',
                border: '2px solid #EF4444',
                borderRadius: 16,
                padding: '10px 24px',
                boxShadow: '0 0 20px rgba(239, 68, 68, 0.4)',
                transform: `scale(${pulseScale})`,
              }}
            >
              <span
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                CRÍTICA
              </span>
            </div>
          </div>

          {/* Plunging Chart Line with animated dropoff curve and cursor */}
          <div style={{width: '100%', height: 120, position: 'relative'}}>
            <svg width="100%" height="120" viewBox="0 0 880 120" preserveAspectRatio="none">
              <defs>
                <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="rgba(239, 68, 68, 0.4)" />
                  <stop offset="100%" stopColor="rgba(239, 68, 68, 0.0)" />
                </linearGradient>
              </defs>
              <line
                x1="0"
                y1="20"
                x2="880"
                y2="20"
                stroke="rgba(255,255,255,0.12)"
                strokeWidth="2"
                strokeDasharray="6 6"
              />
              <line
                x1="0"
                y1="100"
                x2="880"
                y2="100"
                stroke="rgba(255,255,255,0.12)"
                strokeWidth="2"
                strokeDasharray="6 6"
              />
              {/* Plunging Path */}
              <path
                d="M 20 25 C 240 25, 420 80, 860 105"
                fill="none"
                stroke="#EF4444"
                strokeWidth="8"
                strokeDasharray="900"
                strokeDashoffset={900 * (1 - chartProgress)}
                strokeLinecap="round"
              />
            </svg>

            {/* Simulated cursor abandon icon moving away */}
            <div
              style={{
                position: 'absolute',
                top: 75 - cursorProgress * 45,
                right: 20 + (1 - cursorProgress) * 60,
                transform: `scale(${1 + Math.sin(frame * 0.25) * 0.15})`,
                fontSize: 44,
                filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.9))',
              }}
            >
              ↖️
            </div>
          </div>

          {/* Bottom Alert Message */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(239, 68, 68, 0.16)',
              border: '1.5px solid rgba(239, 68, 68, 0.35)',
              borderRadius: 18,
              padding: '14px 20px',
            }}
          >
            <span
              style={{
                fontSize: 34,
                color: '#FECACA',
                fontWeight: 800,
                textAlign: 'center',
                letterSpacing: 0.3,
              }}
            >
              ⚠️ Cliente não entendeu a proposta comercial
            </span>
          </div>
        </div>
      </div>

      {/* Climax Hook Punch: SEM ENTENDER? badge popping at frame 42 (1.4s) */}
      {frame >= 40 && (
        <div
          style={{
            position: 'absolute',
            top: 1040,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            transform: `scale(${Math.max(0, stampSpring)}) translateY(${
              (1 - Math.max(0, stampSpring)) * 30
            }px)`,
            opacity: Math.min(1, Math.max(0, stampSpring)),
          }}
        >
          <div
            style={{
              background: `linear-gradient(135deg, ${CORES.marca}, #DB2777)`,
              padding: '16px 44px',
              borderRadius: 30,
              boxShadow: `0 12px 40px ${CORES.marcaGlow}, 0 0 30px ${CORES.marca}`,
              transform: `scale(${pulseScale})`,
              border: '2.5px solid rgba(255, 255, 255, 0.6)',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span style={{fontSize: 44}}>❓</span>
            <span
              style={{
                fontSize: 56,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1,
                textTransform: 'uppercase',
                textShadow: '0 4px 18px rgba(0,0,0,0.6)',
              }}
            >
              SEM ENTENDER?
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
