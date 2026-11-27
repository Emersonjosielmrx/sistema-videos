import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Scene2_Conversa: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background camera push-in
  const bgScale = interpolate(frame, [0, 241], [1.08, 1.20], {
    extrapolateRight: 'clamp',
  });
  const bgTranslate = interpolate(frame, [0, 241], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Entrance spring for the phone mockup
  const phoneSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Messages entrance springs (calculated strictly at trigger frames)
  // Message 1 (Cliente) at frame 12 (~0.4s)
  const m1Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Digitando 1: frames 45 to 71
  const isTyping1 = frame >= 45 && frame < 72;

  // Message 2 (Empresa/Bot) at frame 72 (~2.4s)
  const m2Spring = spring({
    frame: frame - 72,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Message 3 (Cliente) at frame 120 (~4.0s) - Instant 100% white text and zero ghost opacity
  const m3Spring = spring({
    frame: frame - 120,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Digitando 2: frames 148 to 171
  const isTyping2 = frame >= 148 && frame < 172;

  // Message 4 (Empresa/Bot) at frame 172 (~5.7s)
  const m4Spring = spring({
    frame: frame - 172,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Catalog absorbed badge (at frame 18, "O sistema absorve as informações...")
  const catalogSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Mockup dynamic scale, perspective oscillation & continuous floating
  const phoneScale = interpolate(frame, [0, 241], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });
  const floatY = Math.sin(frame * 0.08) * 5;
  const glowX = Math.sin(frame * 0.07) * 35;
  const glowY = Math.cos(frame * 0.06) * 25;

  // Perspective oscillation maintaining active 3D motion and depth
  const rotateY =
    interpolate(frame, [0, 60, 130, 200, 241], [12, 8, 12, 9, 11], {
      extrapolateRight: 'clamp',
    }) +
    Math.sin(frame * 0.07) * 1.5;
  const rotateX =
    interpolate(frame, [0, 120, 241], [2.0, 0.8, 1.6], {
      extrapolateRight: 'clamp',
    }) +
    Math.cos(frame * 0.08) * 0.8;

  // Smooth spring-driven scroll: feed rolls upward with natural spring physics when each new message arrives
  const scrollSpring3 = spring({
    frame: frame - 120,
    fps,
    config: {damping: 15, stiffness: 120},
  });
  const scrollSpring4 = spring({
    frame: frame - 172,
    fps,
    config: {damping: 15, stiffness: 120},
  });
  const scrollY =
    (frame >= 120 ? scrollSpring3 * -28 : 0) +
    (frame >= 172 ? scrollSpring4 * -50 : 0);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
      }}
    >
      {/* Background: Ambient physical store video with blur, push-in & dark protective veil */}
      <div
        style={{
          position: 'absolute',
          inset: -20,
          transform: `scale(${bgScale}) translateY(${bgTranslate}px)`,
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(12px) brightness(0.48)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 45%, rgba(15, 23, 42, 0.72) 0%, rgba(10, 13, 20, 0.94) 100%)',
          }}
        />
      </div>

      {/* Floating luminous background glow in active motion behind mockup */}
      <div
        style={{
          position: 'absolute',
          top: 380 + glowY,
          left: 190 + glowX,
          width: 580,
          height: 580,
          borderRadius: '50%',
          background: 'rgba(167, 139, 250, 0.22)',
          filter: 'blur(100px)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Header & Simulation Badge (y=160 to 260) */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 8,
          zIndex: 30,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          {/* Rótulo Badge */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '6px 20px',
              borderRadius: 999,
              backgroundColor: 'rgba(15, 23, 42, 0.94)',
              border: '1.5px solid #A78BFA',
              boxShadow: '0 8px 24px rgba(167, 139, 250, 0.3)',
            }}
          >
            <span style={{fontSize: 22}}>✨</span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#F8FAFC',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              Como Funciona
            </span>
          </div>

          {/* Mandatory Selo Simulação */}
          <div
            style={{
              padding: '6px 18px',
              borderRadius: 999,
              backgroundColor: 'rgba(30, 41, 59, 0.92)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
            }}
          >
            <span
              style={{
                fontSize: 30,
                fontWeight: 600,
                color: '#94A3B8',
              }}
            >
              Simulação
            </span>
          </div>
        </div>

        {/* Dynamic Context Tag: Absorve catálogo (frame >= 18) */}
        {frame >= 18 && (
          <div
            style={{
              opacity: catalogSpring,
              transform: `scale(${0.92 + catalogSpring * 0.08})`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              backgroundColor: 'rgba(15, 23, 42, 0.94)',
              border: '1.5px solid rgba(167, 139, 250, 0.4)',
              borderRadius: 14,
              padding: '6px 22px',
              boxShadow: '0 8px 20px rgba(0, 0, 0, 0.5)',
            }}
          >
            <span style={{fontSize: 24}}>📦</span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 700,
                color: '#DDD6FE',
              }}
            >
              IA absorve todo o catálogo da loja
            </span>
          </div>
        )}
      </div>

      {/* Realistic 3D Smartphone Mockup (left:70, right:70, width=940px, top:335) */}
      <div
        style={{
          position: 'absolute',
          top: 335,
          left: 70,
          right: 70,
          height: 980,
          perspective: 1200,
          zIndex: 20,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            transform: `scale(${phoneScale}) translateY(${(1 - phoneSpring) * 60 + floatY}px) rotateY(${rotateY}deg) rotateX(${rotateX}deg)`,
            backgroundColor: '#0A0E17',
            border: '4px solid #334155',
            borderRadius: 40,
            boxShadow:
              '0 30px 80px rgba(0, 0, 0, 0.9), 0 0 45px rgba(167, 139, 250, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {/* Subtle screen glass diagonal reflection */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              right: 0,
              width: '60%',
              height: '50%',
              background:
                'linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, transparent 60%)',
              pointerEvents: 'none',
              zIndex: 40,
            }}
          />

          {/* Smartphone Speaker slit & Dynamic Island pill */}
          <div
            style={{
              position: 'relative',
              zIndex: 35,
              height: 28,
              backgroundColor: '#1E293B',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                width: 70,
                height: 6,
                backgroundColor: '#0F172A',
                borderRadius: 4,
              }}
            />
          </div>

          {/* Phone Header Bar (Realistic messaging app header with top zIndex) */}
          <div
            style={{
              position: 'relative',
              zIndex: 30,
              height: 94,
              backgroundColor: '#1E293B',
              borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
              display: 'flex',
              alignItems: 'center',
              padding: '0 24px',
              gap: 16,
              flexShrink: 0,
              boxShadow: '0 6px 18px rgba(0, 0, 0, 0.6)',
            }}
          >
            {/* Avatar Bot with glow */}
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                backgroundColor: '#A78BFA',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
                color: '#121216',
                fontWeight: 900,
                boxShadow: '0 0 14px rgba(167, 139, 250, 0.6)',
                position: 'relative',
              }}
            >
              🤖
              {/* Online status green dot */}
              <div
                style={{
                  position: 'absolute',
                  bottom: -2,
                  right: -2,
                  width: 14,
                  height: 14,
                  borderRadius: '50%',
                  backgroundColor: '#10B981',
                  border: '2px solid #1E293B',
                }}
              />
            </div>
            <div style={{display: 'flex', flexDirection: 'column'}}>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  lineHeight: 1.15,
                }}
              >
                Vitrine IA • Loja
              </div>
              <div
                style={{
                  fontSize: 30,
                  fontWeight: 600,
                  color: '#A78BFA',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                Atendimento Inteligente • Online
              </div>
            </div>
          </div>

          {/* Chat Messages Body with spring-based auto-scroll */}
          <div
            style={{
              flex: 1,
              position: 'relative',
              zIndex: 10,
              overflow: 'hidden',
              padding: '24px 22px 24px',
            }}
          >
            {/* Realistic Security / Context System Chip: fills top space gracefully */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                marginBottom: 20,
              }}
            >
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  backgroundColor: 'rgba(30, 41, 59, 0.75)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: 12,
                  padding: '6px 18px',
                }}
              >
                <span style={{fontSize: 20}}>🔒</span>
                <span
                  style={{
                    fontSize: 28,
                    fontWeight: 600,
                    color: '#94A3B8',
                  }}
                >
                  Catálogo conectado • Respostas automáticas
                </span>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 18,
                transform: `translateY(${scrollY}px)`,
              }}
            >
              {/* Message 1 (Cliente) - Frame >= 12, crisp white text */}
              {frame >= 12 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '85%',
                    backgroundColor: '#1E293B',
                    border: '1.5px solid rgba(255, 255, 255, 0.22)',
                    borderRadius: '20px 20px 20px 4px',
                    padding: '16px 22px',
                    transform: `scale(${0.92 + m1Spring * 0.08}) translateX(${(1 - m1Spring) * -25}px)`,
                    boxShadow: '0 8px 20px rgba(0, 0, 0, 0.45)',
                  }}
                >
                  <div
                    style={{
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#FFFFFF',
                      lineHeight: 1.25,
                    }}
                  >
                    Olá! Vocês têm esse modelo em outras cores?
                  </div>
                </div>
              )}

              {/* Digitando indicator 1 - frames 45-71 */}
              {isTyping1 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    backgroundColor: 'rgba(59, 7, 100, 0.95)',
                    border: '1.5px solid rgba(167, 139, 250, 0.5)',
                    borderRadius: '20px 20px 4px 20px',
                    padding: '12px 22px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  <span style={{fontSize: 32, color: '#DDD6FE', fontWeight: 700}}>
                    IA digitando
                  </span>
                  <span
                    style={{
                      display: 'inline-flex',
                      gap: 4,
                    }}
                  >
                    {[0, 1, 2].map((dot) => (
                      <span
                        key={dot}
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          backgroundColor: '#A78BFA',
                          transform: `translateY(${Math.sin((frame + dot * 8) * 0.3) * 4}px)`,
                        }}
                      />
                    ))}
                  </span>
                </div>
              )}

              {/* Message 2 (Empresa/Bot) - Frame >= 72 */}
              {frame >= 72 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '86%',
                    backgroundColor: '#3B0764',
                    border: '1.5px solid #A78BFA',
                    borderRadius: '20px 20px 4px 20px',
                    padding: '16px 22px',
                    transform: `scale(${0.92 + m2Spring * 0.08}) translateX(${(1 - m2Spring) * 25}px)`,
                    boxShadow: '0 8px 24px rgba(167, 139, 250, 0.35)',
                  }}
                >
                  <div
                    style={{
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#FFFFFF',
                      lineHeight: 1.25,
                    }}
                  >
                    Olá! Temos sim. Posso te mostrar as opções disponíveis?
                  </div>
                </div>
              )}

              {/* Message 3 (Cliente) - Frame >= 120, PURE WHITE TEXT #FFFFFF, HIGH CONTRAST */}
              {frame >= 120 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '85%',
                    backgroundColor: '#1E293B',
                    border: '1.5px solid rgba(255, 255, 255, 0.28)',
                    borderRadius: '20px 20px 20px 4px',
                    padding: '16px 22px',
                    transform: `scale(${0.92 + m3Spring * 0.08}) translateX(${(1 - m3Spring) * -25}px)`,
                    boxShadow: '0 8px 22px rgba(0, 0, 0, 0.5)',
                  }}
                >
                  <div
                    style={{
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#FFFFFF',
                      lineHeight: 1.25,
                    }}
                  >
                    Pode! Qual você recomenda para o dia a dia?
                  </div>
                </div>
              )}

              {/* Digitando indicator 2 - frames 148-171 */}
              {isTyping2 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    backgroundColor: 'rgba(59, 7, 100, 0.95)',
                    border: '1.5px solid rgba(167, 139, 250, 0.5)',
                    borderRadius: '20px 20px 4px 20px',
                    padding: '12px 22px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  <span style={{fontSize: 32, color: '#DDD6FE', fontWeight: 700}}>
                    IA recomendando
                  </span>
                  <span
                    style={{
                      display: 'inline-flex',
                      gap: 4,
                    }}
                  >
                    {[0, 1, 2].map((dot) => (
                      <span
                        key={dot}
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          backgroundColor: '#A78BFA',
                          transform: `translateY(${Math.sin((frame + dot * 8) * 0.3) * 4}px)`,
                        }}
                      />
                    ))}
                  </span>
                </div>
              )}

              {/* Message 4 (Empresa/Bot) - Frame >= 172 */}
              {frame >= 172 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '88%',
                    backgroundColor: '#3B0764',
                    border: '1.5px solid #A78BFA',
                    borderRadius: '20px 20px 4px 20px',
                    padding: '16px 22px',
                    transform: `scale(${0.92 + m4Spring * 0.08}) translateX(${(1 - m4Spring) * 25}px)`,
                    boxShadow: '0 8px 24px rgba(167, 139, 250, 0.35)',
                  }}
                >
                  <div
                    style={{
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#FFFFFF',
                      lineHeight: 1.25,
                    }}
                  >
                    Para o dia a dia, esse modelo é uma ótima escolha. Quer que eu separe o seu?
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
