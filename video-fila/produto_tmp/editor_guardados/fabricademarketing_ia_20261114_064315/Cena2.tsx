import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig, Img, staticFile} from 'remotion';

type Props<T = unknown> = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background zoom and subtle pan
  const bgScale = interpolate(frame, [0, 188], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Dynamic ambient background glow pulse
  const ambientGlow = 0.28 + 0.12 * Math.sin(frame / 10);

  // Top badge entrance
  const badgeSpring = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Phone entrance
  const phoneSpring = spring({
    frame: Math.max(0, frame - 7),
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Messages entrances
  // Msg 1 (cliente): at frame 10 (~12.16s)
  const msg1Spring = spring({
    frame: Math.max(0, frame - 10),
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Typing indicator visible between frame 36 and frame 62
  const showTyping = frame >= 36 && frame < 64;

  // Msg 2 (empresa / bot oficial): at frame 64 (~13.96s)
  const msg2Spring = spring({
    frame: Math.max(0, frame - 64),
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Msg 3 (cliente): at frame 98 (~15.10s)
  const msg3Spring = spring({
    frame: Math.max(0, frame - 98),
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Msg 4 (empresa / bot oficial): at frame 128 (~16.10s)
  const msg4Spring = spring({
    frame: Math.max(0, frame - 128),
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Continuous subtle 3D tilt and smooth zoom
  const rotY = interpolate(frame, [0, 188], [-5, -1.5]);
  const phoneScale = interpolate(frame, [0, 188], [1.0, 1.03]);

  return (
    <div style={{position: 'absolute', width: 1080, height: 1920, overflow: 'hidden'}}>
      {/* Background with continuous slow zoom */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at center, rgba(17, 24, 39, 0.45) 0%, rgba(17, 24, 39, 0.90) 100%)',
          }}
        />
      </div>

      {/* Dynamic ambient glowing orbs in background to eliminate bottom void */}
      <div
        style={{
          position: 'absolute',
          width: 700,
          height: 700,
          borderRadius: '50%',
          background: `radial-gradient(circle, rgba(244, 114, 182, ${ambientGlow}) 0%, transparent 70%)`,
          filter: 'blur(60px)',
          top: 450,
          left: 190,
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 450,
          height: 450,
          borderRadius: '50%',
          background: 'rgba(59, 130, 246, 0.16)',
          filter: 'blur(80px)',
          bottom: 250 + Math.sin(frame / 14) * 30,
          right: 120 + Math.cos(frame / 18) * 30,
          pointerEvents: 'none',
        }}
      />

      {/* Top Zone: Category Badges (y: 154 - 200) */}
      <div
        style={{
          position: 'absolute',
          top: 156,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 14,
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring,
          zIndex: 10,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 20px',
            borderRadius: 22,
            background: 'rgba(244, 114, 182, 0.22)',
            border: '1.5px solid rgba(244, 114, 182, 0.55)',
            boxShadow: '0 4px 18px rgba(244, 114, 182, 0.3)',
          }}
        >
          <span style={{fontSize: 24}}>⚡</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#F472B6',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>

        <div
          style={{
            padding: '6px 18px',
            borderRadius: 22,
            background: 'rgba(17, 24, 39, 0.88)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
            }}
          >
            Agente nos Comentários
          </span>
        </div>
      </div>

      {/* Complete Smartphone Mockup with Social Feed Thread (y: 216 - 1432) */}
      <div
        style={{
          position: 'absolute',
          top: 216,
          left: 90,
          width: 900,
          height: 1216,
          borderRadius: 48,
          background: '#0B1120',
          border: '4px solid rgba(244, 114, 182, 0.45)',
          boxShadow: '0 30px 80px rgba(0, 0, 0, 0.95), 0 0 35px rgba(244, 114, 182, 0.3)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          transform: `perspective(1200px) rotateY(${rotY}deg) rotateX(2deg) scale(${phoneScale * phoneSpring})`,
          transformOrigin: 'center center',
          opacity: phoneSpring,
        }}
      >
        {/* Smartphone Speaker / Notch Bar */}
        <div
          style={{
            height: 28,
            background: '#0F172A',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              width: 120,
              height: 6,
              borderRadius: 3,
              background: '#334155',
            }}
          />
        </div>

        {/* Social Feed Header: Comments Thread Context */}
        <div
          style={{
            height: 116,
            background: '#1E293B',
            borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 26px',
          }}
        >
          {/* Company info with Verified Bot Badge */}
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 58,
                height: 58,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #F472B6 0%, #DB2777 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily,
                fontSize: 26,
                fontWeight: 900,
                color: '#FFFFFF',
                boxShadow: '0 4px 12px rgba(244, 114, 182, 0.45)',
              }}
            >
              FM
            </div>
            <div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
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
                  Fábrica de Marketing IA
                </span>
                <span style={{fontSize: 24, color: '#38BDF8'}}>✓</span>
              </div>
              <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: '#10B981',
                  }}
                />
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#34D399',
                  }}
                >
                  Agente Oficial de Respostas
                </span>
              </div>
            </div>
          </div>

          {/* Mandatory "Simulação" Tag */}
          <div
            style={{
              padding: '6px 16px',
              borderRadius: 12,
              background: 'rgba(255, 255, 255, 0.12)',
              border: '1px solid rgba(255, 255, 255, 0.25)',
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#F1F5F9',
            }}
          >
            Simulação
          </div>
        </div>

        {/* Post Context Sub-header */}
        <div
          style={{
            background: 'rgba(244, 114, 182, 0.12)',
            borderBottom: '1px solid rgba(244, 114, 182, 0.25)',
            padding: '8px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              color: '#FBCFE8',
            }}
          >
            💬 Respostas automáticas na postagem
          </span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#34D399',
            }}
          >
            Ativo ⚡
          </span>
        </div>

        {/* Comments Thread Body */}
        <div
          style={{
            flex: 1,
            padding: '20px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            overflow: 'hidden',
            justifyContent: 'flex-start',
          }}
        >
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
            }}
          >
            {/* Msg 1: Seguidor Comment */}
            {frame >= 10 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '85%',
                  background: '#1E293B',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: '24px 24px 24px 6px',
                  padding: '16px 22px',
                  transform: `scale(${msg1Spring})`,
                  opacity: msg1Spring,
                  boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 4,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#94A3B8',
                    }}
                  >
                    @seguidor.comercial
                  </span>
                  <span style={{fontSize: 22, color: '#64748B'}}>• há 5 min</span>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Como funciona o serviço de vocês?
                </div>
              </div>
            )}

            {/* Typing Indicator */}
            {showTyping && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  background: 'rgba(244, 114, 182, 0.22)',
                  border: '1.5px solid rgba(244, 114, 182, 0.5)',
                  borderRadius: '24px 24px 6px 24px',
                  padding: '12px 22px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#F472B6',
                  }}
                >
                  Agente IA digitando
                </span>
                <span style={{fontSize: 26}}>⚡</span>
              </div>
            )}

            {/* Msg 2: Empresa Bot Reply */}
            {frame >= 64 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '88%',
                  background: 'linear-gradient(135deg, #EC4899 0%, #BE185D 100%)',
                  borderRadius: '24px 24px 6px 24px',
                  padding: '16px 22px',
                  transform: `scale(${msg2Spring})`,
                  opacity: msg2Spring,
                  boxShadow: '0 8px 22px rgba(236, 72, 153, 0.45)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 4,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 900,
                      color: '#FDF2F8',
                    }}
                  >
                    Fábrica de Marketing IA
                  </span>
                  <span
                    style={{
                      fontSize: 22,
                      padding: '2px 8px',
                      borderRadius: 8,
                      background: 'rgba(255, 255, 255, 0.25)',
                      color: '#FFFFFF',
                      fontWeight: 800,
                    }}
                  >
                    BOT
                  </span>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Olá! Atendemos da ideia à postagem com blog e podcast.
                </div>
              </div>
            )}

            {/* Msg 3: Seguidor Reply */}
            {frame >= 98 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '85%',
                  background: '#1E293B',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: '24px 24px 24px 6px',
                  padding: '16px 22px',
                  transform: `scale(${msg3Spring})`,
                  opacity: msg3Spring,
                  boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 4,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#94A3B8',
                    }}
                  >
                    @seguidor.comercial
                  </span>
                  <span style={{fontSize: 22, color: '#64748B'}}>• há 2 min</span>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Gostei, quero entender melhor!
                </div>
              </div>
            )}

            {/* Msg 4: Empresa Bot Closing */}
            {frame >= 128 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '88%',
                  background: 'linear-gradient(135deg, #EC4899 0%, #BE185D 100%)',
                  borderRadius: '24px 24px 6px 24px',
                  padding: '16px 22px',
                  transform: `scale(${msg4Spring})`,
                  opacity: msg4Spring,
                  boxShadow: '0 8px 22px rgba(236, 72, 153, 0.45)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 4,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 900,
                      color: '#FDF2F8',
                    }}
                  >
                    Fábrica de Marketing IA
                  </span>
                  <span
                    style={{
                      fontSize: 22,
                      padding: '2px 8px',
                      borderRadius: 8,
                      background: 'rgba(255, 255, 255, 0.25)',
                      color: '#FFFFFF',
                      fontWeight: 800,
                    }}
                  >
                    BOT
                  </span>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Perfeito! Enviamos os detalhes para você agora mesmo.
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Smartphone Realistic Bottom Comment Input Bar */}
        <div
          style={{
            height: 94,
            background: '#1E293B',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '10px 24px 8px',
          }}
        >
          <div
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'rgba(255, 255, 255, 0.08)',
              borderRadius: 22,
              padding: '8px 18px',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                color: '#94A3B8',
              }}
            >
              💬 Resposta pública automática...
            </span>
            <span style={{fontSize: 24, color: '#F472B6'}}>➤</span>
          </div>

          {/* Smartphone Home Indicator bar */}
          <div
            style={{
              width: 140,
              height: 5,
              borderRadius: 3,
              background: 'rgba(255, 255, 255, 0.35)',
            }}
          />
        </div>
      </div>
    </div>
  );
};
