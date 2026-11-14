import React from 'react';
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Dynamic ambient scale and movement for tech background
  const bgScale = interpolate(frame, [0, 263], [1.02, 1.15], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Top tag entrance (frame 4)
  const tagSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Headline entrance (frame 10)
  const titleSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Dashboard Header entrance (frame 16)
  const headerSpring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Call Row 1 entrance ("dispara chamadas automáticas" ~frame 32)
  const row1Spring = spring({
    frame: frame - 32,
    fps,
    config: {damping: 12, stiffness: 115},
  });

  // Call Row 2 entrance ("de WhatsApp" ~frame 72)
  const row2Spring = spring({
    frame: frame - 72,
    fps,
    config: {damping: 12, stiffness: 115},
  });

  // Call Row 3 entrance ("em grande escala" ~frame 112)
  const row3Spring = spring({
    frame: frame - 112,
    fps,
    config: {damping: 12, stiffness: 115},
  });

  // Bottom Banner entrance ("atendimento inteligente vinte e quatro horas" ~frame 152)
  const bannerSpring = spring({
    frame: frame - 152,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Continuous subtle motion for waves & badges
  const pulseScale = 1 + Math.sin(frame / 5) * 0.05;
  const floatY = Math.sin(frame / 12) * 5;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#061D0F',
        fontFamily,
      }}
    >
      {/* Dynamic Hermes Call Automated Tech System Background (Solves Problems 2, 3, 14, 17) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        {/* Deep ambient radial glow */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(ellipse at 50% 35%, rgba(12, 74, 38, 0.95) 0%, rgba(6, 32, 16, 0.98) 65%, #031409 100%)',
          }}
        />

        {/* High-tech perspective grid simulating live dialer server connection */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: 0.24,
            backgroundImage:
              'linear-gradient(rgba(37, 211, 102, 0.28) 1px, transparent 1px), linear-gradient(90deg, rgba(37, 211, 102, 0.28) 1px, transparent 1px)',
            backgroundSize: '75px 75px',
            transform: 'perspective(550px) rotateX(22deg) translateY(-50px)',
            transformOrigin: 'top center',
          }}
        />

        {/* Network connection pulses drifting across the screen */}
        {[0, 1, 2, 3, 4, 5].map((k) => {
          const y = ((frame * 3 + k * 320) % 1920);
          const x = 140 + ((k * 180) % 800);
          return (
            <div
              key={k}
              style={{
                position: 'absolute',
                left: x,
                bottom: y,
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: '#25D366',
                boxShadow: '0 0 14px #25D366',
                opacity: 0.4 + 0.3 * Math.sin(frame / 6 + k),
              }}
            />
          );
        })}
      </div>

      {/* Top Tag (y=180) */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: tagSpring,
          transform: `scale(${tagSpring})`,
          zIndex: 10,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 30,
            background: 'rgba(8, 46, 22, 0.95)',
            border: '2px solid rgba(37, 211, 102, 0.65)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#25D366',
              boxShadow: '0 0 10px #25D366',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#25D366',
              letterSpacing: 2,
            }}
          >
            A SOLUÇÃO • HERMES CALL
          </span>
        </div>
      </div>

      {/* Headline (y=265 to 355) */}
      <div
        style={{
          position: 'absolute',
          top: 265,
          left: 60,
          right: 60,
          textAlign: 'center',
          opacity: titleSpring,
          transform: `translateY(${(1 - titleSpring) * 30}px)`,
          zIndex: 10,
        }}
      >
        <span
          style={{
            fontSize: 54,
            fontWeight: 900,
            color: '#FFFFFF',
            letterSpacing: 1,
            textShadow: '0 4px 18px rgba(0,0,0,0.85)',
          }}
        >
          LIGAÇÕES WHATSAPP COM IA
        </span>
      </div>

      {/* Real-time System Dispatcher Dashboard (y=375 to 1350) - Solves Problem 17: Tela do sistema disparando ligações na prática */}
      <div
        style={{
          position: 'absolute',
          top: 375,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
          transform: `translateY(${floatY}px)`,
          zIndex: 10,
        }}
      >
        {/* Dashboard Status Header Bar */}
        <div
          style={{
            opacity: headerSpring,
            transform: `translateY(${(1 - headerSpring) * 20}px)`,
            padding: '16px 26px',
            borderRadius: 22,
            backgroundColor: 'rgba(7, 94, 84, 0.75)',
            backdropFilter: 'blur(16px)',
            border: '2px solid rgba(37, 211, 102, 0.55)',
            boxShadow: '0 12px 34px rgba(0, 0, 0, 0.55)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 16,
                height: 16,
                borderRadius: '50%',
                backgroundColor: '#25D366',
                transform: `scale(${pulseScale})`,
                boxShadow: '0 0 14px #25D366',
              }}
            />
            <span style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
              Discador Automático Ativo
            </span>
          </div>
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#25D366',
              backgroundColor: 'rgba(37, 211, 102, 0.18)',
              padding: '6px 16px',
              borderRadius: 12,
              letterSpacing: 1,
            }}
          >
            DISPAROS IA
          </span>
        </div>

        {/* Live Call Feed: Item 1 - Chamadas Automáticas com Voz Real */}
        {frame >= 25 && (
          <div
            style={{
              opacity: row1Spring,
              transform: `translateX(${(1 - row1Spring) * -40}px)`,
              borderRadius: 22,
              padding: '22px 24px',
              backgroundColor: 'rgba(8, 42, 22, 0.94)',
              backdropFilter: 'blur(16px)',
              border: '2px solid rgba(37, 211, 102, 0.45)',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 14,
                  backgroundColor: 'rgba(37, 211, 102, 0.2)',
                  border: '1.5px solid #25D366',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <svg
                  width="28"
                  height="28"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#25D366"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                </svg>
              </div>
              <div>
                <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                  Chamada Automática Ativa
                </div>
                <div style={{fontSize: 32, fontWeight: 700, color: '#25D366', marginTop: 2}}>
                  Voz Real com IA
                </div>
              </div>
            </div>

            {/* Live oscillating audio waveform */}
            <div style={{display: 'flex', gap: 5, alignItems: 'center', height: 36}}>
              {[18, 32, 22, 38, 26, 18, 34].map((h, i) => {
                const animH = Math.max(10, Math.round(h * (0.4 + 0.6 * Math.abs(Math.sin(frame * 0.35 + i * 0.9)))));
                return (
                  <div
                    key={i}
                    style={{
                      width: 6,
                      height: animH,
                      borderRadius: 3,
                      backgroundColor: '#25D366',
                    }}
                  />
                );
              })}
            </div>
          </div>
        )}

        {/* Live Call Feed: Item 2 - Disparo Simultâneo com Voz Clonada */}
        {frame >= 65 && (
          <div
            style={{
              opacity: row2Spring,
              transform: `translateX(${(1 - row2Spring) * 40}px)`,
              borderRadius: 22,
              padding: '22px 24px',
              backgroundColor: 'rgba(8, 42, 22, 0.94)',
              backdropFilter: 'blur(16px)',
              border: '2px solid rgba(37, 211, 102, 0.45)',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 14,
                  backgroundColor: 'rgba(37, 211, 102, 0.2)',
                  border: '1.5px solid #25D366',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <svg
                  width="28"
                  height="28"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#25D366"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
              </div>
              <div>
                <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                  Disparos no WhatsApp
                </div>
                <div style={{fontSize: 32, fontWeight: 700, color: '#25D366', marginTop: 2}}>
                  Voz Clonada com IA
                </div>
              </div>
            </div>

            <div
              style={{
                padding: '8px 18px',
                borderRadius: 12,
                backgroundColor: 'rgba(37, 211, 102, 0.22)',
                border: '1.5px solid #25D366',
                color: '#25D366',
                fontSize: 32,
                fontWeight: 800,
              }}
            >
              Conectado
            </div>
          </div>
        )}

        {/* Live Call Feed: Item 3 - Escala Total */}
        {frame >= 105 && (
          <div
            style={{
              opacity: row3Spring,
              transform: `translateY(${(1 - row3Spring) * 30}px)`,
              borderRadius: 22,
              padding: '22px 24px',
              backgroundColor: 'rgba(8, 42, 22, 0.94)',
              backdropFilter: 'blur(16px)',
              border: '2px solid rgba(37, 211, 102, 0.55)',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 14,
                  backgroundColor: 'rgba(37, 211, 102, 0.2)',
                  border: '1.5px solid #25D366',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <svg
                  width="28"
                  height="28"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#25D366"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <path d="M8 12h8" />
                  <path d="M12 8v8" />
                </svg>
              </div>
              <div>
                <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                  Disparos em Grande Escala
                </div>
                <div style={{fontSize: 32, fontWeight: 700, color: '#25D366', marginTop: 2}}>
                  Quantas você precisar
                </div>
              </div>
            </div>

            <div
              style={{
                padding: '8px 18px',
                borderRadius: 12,
                backgroundColor: 'rgba(37, 211, 102, 0.25)',
                border: '1.5px solid #25D366',
                color: '#25D366',
                fontSize: 32,
                fontWeight: 900,
              }}
            >
              Alta Escala
            </div>
          </div>
        )}

        {/* Bottom Feature Ribbon: Atendimento Inteligente 24h (enters f152) */}
        {frame >= 145 && (
          <div
            style={{
              opacity: bannerSpring,
              transform: `translateY(${(1 - bannerSpring) * 35}px)`,
              borderRadius: 22,
              padding: '24px 28px',
              backgroundColor: 'rgba(8, 46, 24, 0.96)',
              backdropFilter: 'blur(16px)',
              border: '2px solid rgba(37, 211, 102, 0.65)',
              boxShadow: '0 14px 40px rgba(0, 0, 0, 0.65)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: 16,
                  backgroundColor: 'rgba(37, 211, 102, 0.25)',
                  border: '1.5px solid #25D366',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <svg
                  width="30"
                  height="30"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#25D366"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
              </div>
              <div>
                <div style={{fontSize: 36, fontWeight: 900, color: '#FFFFFF'}}>
                  Atendimento Inteligente
                </div>
                <div style={{fontSize: 32, fontWeight: 700, color: '#25D366', marginTop: 2}}>
                  Hermes Call 24 horas
                </div>
              </div>
            </div>

            <div
              style={{
                padding: '10px 22px',
                borderRadius: 14,
                backgroundColor: '#25D366',
                color: '#121216',
                fontSize: 34,
                fontWeight: 900,
                boxShadow: '0 0 18px rgba(37, 211, 102, 0.5)',
              }}
            >
              24 HORAS
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
