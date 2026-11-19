import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena2ConversaProps {
  fontFamily: string;
}

export const Cena2Conversa: React.FC<Cena2ConversaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous background movement
  const bgScale = interpolate(frame, [0, 220], [1.02, 1.14], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 220], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Phone entrance spring
  const phoneEntrance = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // 3D perspective tilt & float
  const tiltY = interpolate(frame, [0, 220], [-3, 3], {
    extrapolateRight: 'clamp',
  });
  const floatY = Math.sin(frame / 12) * 5;

  // Header entrance
  const headerEntrance = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Message 1 Entrance (~10.9s -> frame 12)
  const msg1Entrance = spring({
    frame: frame - 12,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Typing indicator (~12.8s -> frame 68 to 98)
  const showTyping = frame >= 68 && frame < 99;

  // Message 2 Entrance (~13.8s -> frame 99)
  const msg2Entrance = spring({
    frame: frame - 99,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Message 3 Entrance (~15.2s -> frame 141)
  const msg3Entrance = spring({
    frame: frame - 141,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Success pill entrance (~16.1s -> frame 168)
  const successEntrance = spring({
    frame: frame - 168,
    fps,
    config: {damping: 11, stiffness: 150},
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#111827',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Background with motion */}
      <img
        src={staticFile('img_2.jpg')}
        alt=""
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${bgScale}) translateX(${bgTranslateX}px)`,
        }}
      />

      {/* Dark overlay & blur backdrop */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 45%, rgba(17, 24, 39, 0.78) 0%, rgba(10, 14, 23, 0.95) 85%)',
        }}
      />

      {/* Top Header: Como Funciona */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 8,
          opacity: headerEntrance,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 28px',
            borderRadius: 24,
            backgroundColor: 'rgba(78, 205, 196, 0.18)',
            border: '2px solid rgba(78, 205, 196, 0.65)',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5)',
          }}
        >
          <span style={{fontSize: 32}}>⚡</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#4ECDC4',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>
      </div>

      {/* Phone Mockup in 3D (Snug height: 950px, no empty dark void) */}
      <div
        style={{
          position: 'absolute',
          top: 250,
          left: 90,
          right: 90,
          perspective: 1200,
          opacity: phoneEntrance,
          transform: `scale(${0.94 + phoneEntrance * 0.06}) rotateY(${tiltY}deg) translateY(${floatY}px)`,
          transformStyle: 'preserve-3d',
        }}
      >
        <div
          style={{
            width: '100%',
            height: 950,
            borderRadius: 44,
            backgroundColor: '#0F172A',
            border: '4px solid rgba(78, 205, 196, 0.45)',
            boxShadow:
              '0 24px 60px rgba(0, 0, 0, 0.8), 0 0 30px rgba(78, 205, 196, 0.2)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Mockup Top Header (WhatsApp Style) */}
          <div
            style={{
              height: 105,
              backgroundColor: '#1E293B',
              borderBottom: '2px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 28px',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              {/* Bot Avatar */}
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: '50%',
                  backgroundColor: '#4ECDC4',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(78, 205, 196, 0.4)',
                }}
              >
                <span style={{fontSize: 34}}>🤖</span>
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontSize: 36,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    lineHeight: 1.15,
                  }}
                >
                  Follow-up IA
                </span>
                <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
                  <div
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      backgroundColor: '#22C55E',
                    }}
                  />
                  <span
                    style={{
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#22C55E',
                    }}
                  >
                    Online agora
                  </span>
                </div>
              </div>
            </div>

            {/* Mandatory Simulation Badge */}
            <div
              style={{
                padding: '6px 18px',
                borderRadius: 14,
                backgroundColor: 'rgba(255, 255, 255, 0.12)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#CBD5E1',
                  letterSpacing: 1,
                  textTransform: 'uppercase',
                }}
              >
                Simulação
              </span>
            </div>
          </div>

          {/* Conversation Screen */}
          <div
            style={{
              flex: 1,
              backgroundColor: '#0B132B',
              padding: '20px 24px',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              position: 'relative',
            }}
          >
            {/* Top Previous Proposal Attachment Context */}
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '88%',
                backgroundColor: 'rgba(15, 118, 110, 0.35)',
                border: '1px solid rgba(78, 205, 196, 0.3)',
                borderRadius: '20px 20px 4px 20px',
                padding: '12px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
              }}
            >
              <span style={{fontSize: 34}}>📄</span>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span style={{fontSize: 32, fontWeight: 700, color: '#FFFFFF'}}>
                  Proposta_Comercial.pdf
                </span>
                <span style={{fontSize: 32, color: '#99F6E4'}}>
                  Enviada há 3 dias • 10:00
                </span>
              </div>
            </div>

            {/* Date separator */}
            <div
              style={{
                alignSelf: 'center',
                padding: '4px 18px',
                borderRadius: 12,
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
              }}
            >
              <span style={{fontSize: 32, color: '#94A3B8', fontWeight: 600}}>
                HOJE • RESPOSTA AUTOMÁTICA
              </span>
            </div>

            {/* Bubble 1: Empresa */}
            {msg1Entrance > 0 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '88%',
                  backgroundColor: '#0F766E',
                  borderRadius: '24px 24px 4px 24px',
                  padding: '16px 22px',
                  opacity: msg1Entrance,
                  transform: `scale(${0.9 + msg1Entrance * 0.1}) translateY(${(1 - msg1Entrance) * 15}px)`,
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.45)',
                }}
              >
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Olá! Conseguiu avaliar a proposta que te enviei?
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    alignItems: 'center',
                    gap: 6,
                    marginTop: 6,
                  }}
                >
                  <span style={{fontSize: 32, color: '#99F6E4', fontWeight: 600}}>
                    10:14
                  </span>
                  <span style={{fontSize: 32, color: '#38BDF8'}}>✓✓</span>
                </div>
              </div>
            )}

            {/* Typing Indicator */}
            {showTyping && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  backgroundColor: '#1E293B',
                  borderRadius: '20px 20px 20px 4px',
                  padding: '12px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    color: '#94A3B8',
                    fontStyle: 'italic',
                    fontWeight: 600,
                  }}
                >
                  Cliente digitando
                </span>
                <span style={{fontSize: 32}}>💬</span>
              </div>
            )}

            {/* Bubble 2: Cliente */}
            {msg2Entrance > 0 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '88%',
                  backgroundColor: '#1E293B',
                  borderRadius: '24px 24px 24px 4px',
                  padding: '16px 22px',
                  opacity: msg2Entrance,
                  transform: `scale(${0.9 + msg2Entrance * 0.1}) translateY(${(1 - msg2Entrance) * 15}px)`,
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.45)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#F8FAFC',
                    lineHeight: 1.3,
                  }}
                >
                  Oi! Na correria acabei esquecendo. Vamos fechar sim!
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    marginTop: 6,
                  }}
                >
                  <span style={{fontSize: 32, color: '#94A3B8', fontWeight: 600}}>
                    10:15
                  </span>
                </div>
              </div>
            )}

            {/* Bubble 3: Empresa */}
            {msg3Entrance > 0 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '88%',
                  backgroundColor: '#0F766E',
                  borderRadius: '24px 24px 4px 24px',
                  padding: '16px 22px',
                  opacity: msg3Entrance,
                  transform: `scale(${0.9 + msg3Entrance * 0.1}) translateY(${(1 - msg3Entrance) * 15}px)`,
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.45)',
                }}
              >
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Perfeito! Já vou preparar tudo para você.
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    alignItems: 'center',
                    gap: 6,
                    marginTop: 6,
                  }}
                >
                  <span style={{fontSize: 32, color: '#99F6E4', fontWeight: 600}}>
                    10:15
                  </span>
                  <span style={{fontSize: 32, color: '#38BDF8'}}>✓✓</span>
                </div>
              </div>
            )}

            {/* Floating Conversion Banner */}
            {successEntrance > 0 && (
              <div
                style={{
                  marginTop: 'auto',
                  opacity: successEntrance,
                  transform: `scale(${0.92 + successEntrance * 0.08})`,
                  backgroundColor: 'rgba(34, 197, 94, 0.95)',
                  borderRadius: 18,
                  padding: '14px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 12,
                  boxShadow: '0 12px 32px rgba(34, 197, 94, 0.45)',
                }}
              >
                <span style={{fontSize: 36}}>✅</span>
                <span
                  style={{
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#052E16',
                    letterSpacing: 1,
                    textTransform: 'uppercase',
                  }}
                >
                  Lead Recuperado Sozinho
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
