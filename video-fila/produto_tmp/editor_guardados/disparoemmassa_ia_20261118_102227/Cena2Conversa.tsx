import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2Conversa: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Scene fade in / out
  const sceneOpacity = interpolate(
    frame,
    [0, 10, 258, 269],
    [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Background camera movement
  const bgScale = interpolate(frame, [0, 269], [1.06, 1.18], {
    extrapolateRight: 'clamp',
  });
  const bgPan = interpolate(frame, [0, 269], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Top header entrance
  const headerSpring = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.6},
  });

  // Phone 3D perspective rotation and floating
  const phoneSpring = spring({
    frame,
    fps,
    config: {damping: 15, mass: 0.8},
  });
  const rotY = interpolate(frame, [0, 269], [-8, 4], {
    extrapolateRight: 'clamp',
  });
  const floatY = Math.sin(frame / 16) * 6;

  // Typing indicator before message 1 (active from frame 4 to 24)
  const isTyping1 = frame >= 4 && frame < 24;

  // Message 1 Entrance (Empresa) - frame 24 (~12.34s)
  const msg1Spring = spring({
    frame: frame - 24,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 190},
  });

  // Message 2 Entrance (Cliente) - frame 78 (~14.14s)
  const msg2Spring = spring({
    frame: frame - 78,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 190},
  });

  // Message 3 Entrance (Empresa + Cartão de Aniversário) - frame 125 (~15.7s)
  const msg3Spring = spring({
    frame: frame - 125,
    fps,
    config: {damping: 13, mass: 0.6, stiffness: 180},
  });

  // Floating confirmation badge (enters at frame 180 = ~17.54s)
  const badgeSpring = spring({
    frame: frame - 180,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 200},
  });

  // Typing dots animation
  const dot1 = Math.sin((frame * 8) / 10) * 4;
  const dot2 = Math.sin(((frame * 8 + 6) / 10)) * 4;
  const dot3 = Math.sin(((frame * 8 + 12) / 10)) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        opacity: sceneOpacity,
      }}
    >
      {/* Background Image with continuous movement */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale}) translateY(${bgPan}px)`,
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(17, 24, 39, 0.6) 0%, rgba(17, 24, 39, 0.94) 100%)',
          }}
        />
      </div>

      {/* Subtle floating WhatsApp-inspired circular rings */}
      <div
        style={{
          position: 'absolute',
          top: '35%',
          left: '50%',
          width: 900,
          height: 900,
          transform: `translate(-50%, -50%) scale(${1 + Math.sin(frame / 20) * 0.05})`,
          borderRadius: '50%',
          border: '1.5px solid rgba(34, 197, 94, 0.12)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Header Section (y=190, respiro 40px da barra em y=150) */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
          opacity: headerSpring,
          transform: `translateY(${(1 - headerSpring) * -20}px)`,
          zIndex: 30,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 999,
            backgroundColor: 'rgba(17, 24, 39, 0.88)',
            border: '1.5px solid rgba(34, 197, 94, 0.45)',
            boxShadow: '0 8px 30px rgba(0, 0, 0, 0.6)',
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: '#22C55E',
              boxShadow: '0 0 10px #22C55E',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#86EFAC',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>

        <span
          style={{
            fontFamily,
            fontSize: 42,
            fontWeight: 900,
            color: '#FFFFFF',
            textTransform: 'uppercase',
            letterSpacing: '-0.02em',
            textShadow: '0 4px 16px rgba(0,0,0,0.95)',
          }}
        >
          Disparo Inteligente no WhatsApp
        </span>
      </div>

      {/* Center Phone Mockup (3D perspective, y=315 to y=1265, respiro amplo) */}
      <div
        style={{
          position: 'absolute',
          top: 315,
          left: 100,
          width: 880,
          height: 950,
          opacity: phoneSpring,
          transform: `perspective(1300px) rotateY(${rotY}deg) rotateX(2deg) translateY(${floatY}px) scale(${0.94 + phoneSpring * 0.06})`,
          zIndex: 20,
        }}
      >
        {/* Phone Body Frame */}
        <div
          style={{
            width: '100%',
            height: '100%',
            backgroundColor: '#0F172A',
            borderRadius: 44,
            border: '4px solid #334155',
            boxShadow:
              '0 30px 80px rgba(0, 0, 0, 0.85), inset 0 0 0 2px rgba(255, 255, 255, 0.1)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            position: 'relative',
          }}
        >
          {/* Top Notch / Speaker bar */}
          <div
            style={{
              height: 28,
              backgroundColor: '#090D16',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            <div
              style={{
                width: 90,
                height: 5,
                borderRadius: 4,
                backgroundColor: '#1E293B',
              }}
            />
          </div>

          {/* WhatsApp Header */}
          <div
            style={{
              height: 100,
              backgroundColor: '#1F2C34',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 24px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span style={{fontSize: 32, color: '#94A3B8'}}>←</span>
              {/* Avatar */}
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: '50%',
                  backgroundColor: '#059669',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '2px solid #34D399',
                }}
              >
                <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
                  M
                </span>
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#F1F5F9',
                  }}
                >
                  Marcelo Santos
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 500,
                    color: '#22C55E',
                  }}
                >
                  online
                </span>
              </div>
            </div>

            {/* Simulação badge (Required by rule 22 & 65, font >= 32px) */}
            <div
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                padding: '4px 14px',
                borderRadius: 12,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#94A3B8',
                }}
              >
                Simulação
              </span>
            </div>
          </div>

          {/* Chat Messages Canvas */}
          <div
            style={{
              flex: 1,
              backgroundColor: '#0B141A',
              padding: '20px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            {/* Messages container - all 3 messages comfortably visible */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 18,
              }}
            >
              {/* Typing indicator bubble */}
              {isTyping1 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    backgroundColor: '#1F2C34',
                    padding: '16px 26px',
                    borderRadius: 22,
                    borderBottomLeftRadius: 6,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <div
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      backgroundColor: '#22C55E',
                      transform: `translateY(${dot1}px)`,
                    }}
                  />
                  <div
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      backgroundColor: '#22C55E',
                      transform: `translateY(${dot2}px)`,
                    }}
                  />
                  <div
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      backgroundColor: '#22C55E',
                      transform: `translateY(${dot3}px)`,
                    }}
                  />
                </div>
              )}

              {/* Message 1 (Empresa) */}
              {frame >= 24 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '86%',
                    backgroundColor: '#005C4B',
                    padding: '20px 24px',
                    borderRadius: 24,
                    borderBottomLeftRadius: 6,
                    boxShadow: '0 4px 15px rgba(0, 0, 0, 0.4)',
                    opacity: Math.max(0, msg1Spring),
                    transform: `translateY(${(1 - msg1Spring) * 20}px) scale(${0.95 + msg1Spring * 0.05})`,
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#E9EDEF',
                      lineHeight: 1.35,
                    }}
                  >
                    Olá, Marcelo! Passando para checar se deu tudo certo com o seu pedido.
                  </p>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-end',
                      gap: 6,
                      marginTop: 8,
                    }}
                  >
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        color: 'rgba(233, 237, 239, 0.7)',
                      }}
                    >
                      09:41
                    </span>
                    <span style={{fontSize: 32, color: '#53BDEB'}}>✓✓</span>
                  </div>
                </div>
              )}

              {/* Message 2 (Cliente) */}
              {frame >= 78 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '82%',
                    backgroundColor: '#202C33',
                    padding: '20px 24px',
                    borderRadius: 24,
                    borderBottomRightRadius: 6,
                    boxShadow: '0 4px 15px rgba(0, 0, 0, 0.4)',
                    opacity: Math.max(0, msg2Spring),
                    transform: `translateY(${(1 - msg2Spring) * 20}px) scale(${0.95 + msg2Spring * 0.05})`,
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#E9EDEF',
                      lineHeight: 1.35,
                    }}
                  >
                    Chegou perfeito, estou usando bastante!
                  </p>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-end',
                      marginTop: 8,
                    }}
                  >
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        color: 'rgba(233, 237, 239, 0.7)',
                      }}
                    >
                      09:43
                    </span>
                  </div>
                </div>
              )}

              {/* Message 3 (Empresa com Cartão de Aniversário Automático) */}
              {frame >= 125 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '92%',
                    backgroundColor: '#005C4B',
                    padding: '22px 24px',
                    borderRadius: 24,
                    borderBottomLeftRadius: 6,
                    boxShadow: '0 6px 20px rgba(0, 0, 0, 0.5)',
                    opacity: Math.max(0, msg3Spring),
                    transform: `translateY(${(1 - msg3Spring) * 25}px) scale(${0.94 + msg3Spring * 0.06})`,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 16,
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontFamily,
                      fontSize: 33,
                      fontWeight: 600,
                      color: '#E9EDEF',
                      lineHeight: 1.35,
                    }}
                  >
                    Que ótimo! Feliz aniversário adiantado, enviamos um cartão especial para comemorar.
                  </p>

                  {/* Cartão de Aniversário Visual Card */}
                  <div
                    style={{
                      backgroundColor: 'rgba(6, 78, 59, 0.85)',
                      border: '2px solid #F59E0B',
                      borderRadius: 18,
                      padding: '18px 20px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 16,
                      boxShadow: '0 4px 18px rgba(245, 158, 11, 0.25)',
                    }}
                  >
                    <div
                      style={{
                        width: 56,
                        height: 56,
                        borderRadius: 14,
                        backgroundColor: '#F59E0B',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 32,
                      }}
                    >
                      🎁
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
                      <span
                        style={{
                          fontFamily,
                          fontSize: 32,
                          fontWeight: 800,
                          color: '#FDE68A',
                          textTransform: 'uppercase',
                        }}
                      >
                        Cartão de Aniversário
                      </span>
                      <span
                        style={{
                          fontFamily,
                          fontSize: 32,
                          fontWeight: 600,
                          color: '#E2E8F0',
                        }}
                      >
                        Envio Automático Ativo
                      </span>
                    </div>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-end',
                      gap: 6,
                    }}
                  >
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        color: 'rgba(233, 237, 239, 0.7)',
                      }}
                    >
                      09:44
                    </span>
                    <span style={{fontSize: 32, color: '#53BDEB'}}>✓✓</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Floating badge entering at frame 180 (WhatsApp de cada cliente) */}
        {frame >= 180 && (
          <div
            style={{
              position: 'absolute',
              bottom: 40,
              right: -30,
              opacity: Math.max(0, badgeSpring),
              transform: `translateY(${(1 - badgeSpring) * 20}px) scale(${0.9 + badgeSpring * 0.1})`,
              backgroundColor: '#22C55E',
              padding: '16px 28px',
              borderRadius: 20,
              boxShadow: '0 12px 35px rgba(34, 197, 94, 0.55)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <span style={{fontSize: 34}}>⚡</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: '#111827',
                textTransform: 'uppercase',
                letterSpacing: '0.02em',
              }}
            >
              Envio Automático
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
