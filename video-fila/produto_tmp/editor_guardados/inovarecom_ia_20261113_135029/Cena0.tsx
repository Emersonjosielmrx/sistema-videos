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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background ambient dynamic scale & pan
  const bgScale = interpolate(frame, [0, 141], [1.0, 1.15], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Smooth slide-up transition at scene exit (frames 120 to 141) to seamlessly connect to Scene 1
  const exitSlideY = interpolate(frame, [122, 141], [0, -120], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitOpacity = interpolate(frame, [128, 141], [1, 0.4], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Badge entrance (frame 0)
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Line 1: "SUA EQUIPE" (frame 1)
  const line1Spring = spring({
    frame: frame - 1,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Line 2: "NÃO DÁ CONTA" (frame 6 - fast, bright contrast)
  const line2Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Line 3: "DE LIGAR?" (frame 12)
  const line3Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 11, stiffness: 150},
  });

  // Incoming WhatsApp Call Mockup entrance (frame 18) - Immediate visual hook showing real-time WhatsApp calls
  const callMockSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 13, stiffness: 125},
  });

  // Queue Overload Card entrance (frame 44 / ~1.45s)
  const cardSpring = spring({
    frame: frame - 44,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Continuous subtle motion
  const pulseDot = (Math.sin(frame / 5) + 1) / 2;
  const lotacaoPulse = 1 + Math.sin(frame / 4) * 0.08;
  const phoneVibrate = Math.sin(frame * 0.8) * 6;
  const rippleScale = 1 + ((frame % 24) / 24) * 0.8;
  const rippleOpacity = 1 - (frame % 24) / 24;

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
      {/* Dynamic Background: Ambient emerald tech space with perspective grid & subtle glowing rings */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        {/* Radial ambient glow */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(ellipse at 50% 25%, rgba(10, 68, 35, 0.9) 0%, rgba(6, 32, 16, 0.96) 65%, #031409 100%)',
          }}
        />

        {/* Perspective grid simulating commercial operations interface */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: 0.18,
            backgroundImage:
              'linear-gradient(rgba(37, 211, 102, 0.25) 1px, transparent 1px), linear-gradient(90deg, rgba(37, 211, 102, 0.25) 1px, transparent 1px)',
            backgroundSize: '80px 80px',
            transform: 'perspective(600px) rotateX(20deg) translateY(-40px)',
            transformOrigin: 'top center',
          }}
        />

        {/* Subtle decorative particles floating */}
        {[0, 1, 2, 3].map((k) => {
          const y = ((frame * 2 + k * 450) % 1920);
          const x = 180 + ((k * 220) % 720);
          return (
            <div
              key={k}
              style={{
                position: 'absolute',
                left: x,
                top: y,
                width: 6,
                height: 6,
                borderRadius: '50%',
                backgroundColor: '#25D366',
                opacity: 0.35,
                boxShadow: '0 0 10px #25D366',
              }}
            />
          );
        })}
      </div>

      {/* Top Tag / Pill (y=180) */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: badgeSpring,
          transform: `scale(${badgeSpring})`,
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
            border: '2px solid rgba(37, 211, 102, 0.55)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              opacity: 0.6 + pulseDot * 0.4,
              boxShadow: '0 0 12px #EF4444',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#25D366',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            GARGALO COMERCIAL
          </span>
        </div>
      </div>

      {/* Kinetic Headline (y=265 to 640) - full question revealed in first second */}
      <div
        style={{
          position: 'absolute',
          top: 265,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          textAlign: 'center',
          zIndex: 10,
        }}
      >
        {/* Line 1 */}
        <div
          style={{
            opacity: line1Spring,
            transform: `translateY(${(1 - line1Spring) * 20}px) scale(${0.9 + line1Spring * 0.1})`,
          }}
        >
          <span
            style={{
              fontSize: 66,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1,
              textShadow: '0 4px 18px rgba(0,0,0,0.9)',
            }}
          >
            SUA EQUIPE
          </span>
        </div>

        {/* Line 2: High-contrast bright text (#FFFFFF with vibrant red glow) */}
        {frame >= 6 && (
          <div
            style={{
              opacity: line2Spring,
              transform: `translateY(${(1 - line2Spring) * 20}px) scale(${0.9 + line2Spring * 0.1})`,
            }}
          >
            <span
              style={{
                fontSize: 72,
                fontWeight: 900,
                color: '#FFA2A2',
                letterSpacing: 1,
                textShadow: '0 4px 22px rgba(0,0,0,0.95), 0 0 16px rgba(239, 68, 68, 0.6)',
              }}
            >
              NÃO DÁ CONTA
            </span>
          </div>
        )}

        {/* Line 3: DE LIGAR? with green brand pill */}
        {frame >= 12 && (
          <div
            style={{
              opacity: line3Spring,
              transform: `translateY(${(1 - line3Spring) * 20}px) scale(${0.9 + line3Spring * 0.1})`,
              marginTop: 4,
            }}
          >
            <div
              style={{
                display: 'inline-block',
                padding: '6px 28px',
                borderRadius: 18,
                backgroundColor: '#25D366',
                boxShadow: '0 8px 30px rgba(37, 211, 102, 0.5)',
              }}
            >
              <span
                style={{
                  fontSize: 74,
                  fontWeight: 900,
                  color: '#121216',
                  letterSpacing: 1,
                }}
              >
                DE LIGAR?
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Main Action Area: Real-time WhatsApp Incoming Call & Queue Overload Cards (y=670 to 1350) */}
      <div
        style={{
          position: 'absolute',
          top: 670,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 20,
          transform: `translateY(${exitSlideY}px)`,
          opacity: exitOpacity,
          zIndex: 10,
        }}
      >
        {/* Real-time WhatsApp Incoming Call Mockup (enters frame 18) - solves Problem 16 */}
        <div
          style={{
            opacity: callMockSpring,
            transform: `translateY(${(1 - callMockSpring) * 35}px)`,
            borderRadius: 24,
            padding: '24px 28px',
            backgroundColor: 'rgba(8, 42, 20, 0.94)',
            backdropFilter: 'blur(16px)',
            border: '2px solid rgba(37, 211, 102, 0.5)',
            boxShadow: '0 16px 40px rgba(0, 0, 0, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
            {/* Vibrating Phone Icon with Ripple effect */}
            <div style={{position: 'relative', width: 62, height: 62}}>
              {/* Expanding Ripple */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  borderRadius: '50%',
                  backgroundColor: 'rgba(37, 211, 102, 0.35)',
                  transform: `scale(${rippleScale})`,
                  opacity: rippleOpacity,
                }}
              />
              <div
                style={{
                  position: 'relative',
                  width: 62,
                  height: 62,
                  borderRadius: 20,
                  backgroundColor: '#25D366',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transform: `rotate(${phoneVibrate}deg)`,
                  boxShadow: '0 0 16px rgba(37, 211, 102, 0.6)',
                }}
              >
                <svg
                  width="32"
                  height="32"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#121216"
                  strokeWidth="2.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                </svg>
              </div>
            </div>

            <div>
              <div style={{fontSize: 32, fontWeight: 800, color: '#25D366', letterSpacing: 1}}>
                CHAMADA WHATSAPP
              </div>
              <div style={{fontSize: 36, fontWeight: 900, color: '#FFFFFF', marginTop: 2}}>
                Novo Contato Tocando
              </div>
            </div>
          </div>

          <div
            style={{
              padding: '8px 18px',
              borderRadius: 14,
              backgroundColor: 'rgba(37, 211, 102, 0.2)',
              border: '1.5px solid #25D366',
              color: '#25D366',
              fontSize: 32,
              fontWeight: 800,
            }}
          >
            Ao Vivo
          </div>
        </div>

        {/* Problem Simulation Card "Fila de Ligações" (enters frame 44) - Solves Problems 8 and 9 */}
        <div
          style={{
            opacity: cardSpring,
            transform: `translateY(${(1 - cardSpring) * 35}px)`,
            borderRadius: 26,
            padding: '32px 32px',
            backgroundColor: 'rgba(8, 36, 18, 0.95)',
            backdropFilter: 'blur(16px)',
            border: '2px solid rgba(239, 68, 68, 0.45)',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.65)',
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
          }}
        >
          {/* Card Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: 16,
                  backgroundColor: 'rgba(239, 68, 68, 0.2)',
                  border: '1.5px solid #EF4444',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <svg
                  width="32"
                  height="32"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#EF4444"
                  strokeWidth="2.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                </svg>
              </div>
              <div>
                <div style={{fontSize: 38, fontWeight: 900, color: '#FFFFFF'}}>
                  Fila de Ligações
                </div>
                <div style={{fontSize: 34, fontWeight: 700, color: '#FFFFFF', marginTop: 2}}>
                  Chamadas Manuais no WhatsApp
                </div>
              </div>
            </div>

            {/* Pulsing Alert LOTAÇÃO (Problem 9 solved) */}
            <div
              style={{
                padding: '8px 18px',
                borderRadius: 14,
                backgroundColor: 'rgba(239, 68, 68, 0.25)',
                border: '2px solid #EF4444',
                color: '#FFA2A2',
                fontSize: 32,
                fontWeight: 900,
                transform: `scale(${lotacaoPulse})`,
                boxShadow: '0 0 14px rgba(239, 68, 68, 0.5)',
              }}
            >
              LOTAÇÃO
            </div>
          </div>

          {/* Continuous Live Waveform & Fila Sobrecarregada (Problem 8 & 9 solved) */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '18px 24px',
              borderRadius: 18,
              backgroundColor: 'rgba(0, 0, 0, 0.55)',
              border: '1.5px solid rgba(255, 255, 255, 0.12)',
            }}
          >
            {/* Live animated waveform looping continuously */}
            <div style={{display: 'flex', gap: 6, alignItems: 'center', height: 48}}>
              {[24, 40, 20, 52, 30, 56, 26, 46, 52, 28, 48, 34].map((h, i) => {
                const waveFactor = Math.abs(Math.sin(frame * 0.42 + i * 0.85));
                const animH = Math.max(14, Math.round(h * (0.35 + 0.75 * waveFactor)));
                return (
                  <div
                    key={i}
                    style={{
                      width: 8,
                      height: animH,
                      borderRadius: 4,
                      backgroundColor: i % 2 === 0 ? '#EF4444' : '#FFA2A2',
                      boxShadow: '0 0 8px rgba(239, 68, 68, 0.5)',
                    }}
                  />
                );
              })}
            </div>

            {/* High-contrast solid badge for 'Fila Sobrecarregada' */}
            <div
              style={{
                padding: '8px 18px',
                borderRadius: 12,
                backgroundColor: '#DC2626',
                border: '1px solid #EF4444',
                boxShadow: '0 0 12px rgba(239, 68, 68, 0.4)',
              }}
            >
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  letterSpacing: 0.5,
                }}
              >
                Fila Sobrecarregada
              </span>
            </div>
          </div>

          {/* High-contrast alert footer (fontSize: 34, bold, bright #FFFFFF) */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingTop: 4,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <svg
                width="28"
                height="28"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#EF4444"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span style={{fontSize: 34, color: '#FFFFFF', fontWeight: 700}}>
                Tempo esgotando para atender contatos
              </span>
            </div>
            <span
              style={{
                fontSize: 24,
                color: '#CBD5E1',
                padding: '2px 8px',
                borderRadius: 6,
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                letterSpacing: 0.5,
              }}
            >
              Simulação
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
