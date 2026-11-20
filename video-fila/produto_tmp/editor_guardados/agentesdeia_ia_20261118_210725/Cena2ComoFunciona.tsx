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

export const Cena2ComoFunciona: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const sceneDuration = 227;

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

  // Top badge entrance with spring slide
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Phase transition: frames 96 to 106 (words "ao Agente Pessoal IA" start at frame 112)
  // Transition is a smooth motion-design zoom through rather than an abrupt cut
  const transitionProgress = interpolate(frame, [96, 108], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const isSimulation = frame >= 106;

  // Presenter video zoom-through motion during transition
  const presenterVideoScale = interpolate(
    frame,
    [0, 96, 108],
    [1.12, 1.16, 1.32],
    {extrapolateRight: 'clamp'}
  );
  const presenterOpacity = 1 - transitionProgress;

  // Card Phase 1 entrance spring (top card "EXPLICO O QUE PRECISO")
  const cardPhase1Spring = spring({
    frame: Math.max(0, frame - 8),
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Emerald beacon pulse
  const emeraldPulse = 1 + Math.sin(frame / 6) * 0.15;

  // Audio wave heights animation for card 1
  const wave1 = 14 + Math.sin(frame * 0.4) * 10;
  const wave2 = 22 + Math.cos(frame * 0.35) * 12;
  const wave3 = 18 + Math.sin(frame * 0.5) * 10;

  // Smartphone Mockup Overlay springs (starts entering at frame 96 during zoom-through)
  const phoneSpring = spring({
    frame: Math.max(0, frame - 96),
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Presenter Picture-in-Picture window spring in lower third (keeps human connection alive, avoids empty void!)
  const pipSpring = spring({
    frame: Math.max(0, frame - 96),
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // User message is IMMEDIATELY ready when the phone appears (NO empty container!)
  const userMsgSpring = spring({
    frame: Math.max(0, frame - 98),
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Typing indicator active between frame 108 and 142
  const showTyping = frame >= 108 && frame < 144;
  const dot1 = 1 + Math.sin(frame * 0.5) * 0.25;
  const dot2 = 1 + Math.sin((frame + 3) * 0.5) * 0.25;
  const dot3 = 1 + Math.sin((frame + 6) * 0.5) * 0.25;

  // Agent message arrives at frame 142 ("e ele pesquisa por mim")
  const agentMsgSpring = spring({
    frame: Math.max(0, frame - 142),
    fps,
    config: {damping: 12, stiffness: 150},
  });

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
      {/* Background 1: Presenter Video with lowered framing (translateY 110px) giving 60px+ headroom */}
      {presenterOpacity > 0 && (
        <div
          style={{
            position: 'absolute',
            width: 1080,
            height: 1920,
            transform: `scale(${presenterVideoScale}) translateY(110px)`,
            transformOrigin: '50% 35%',
            opacity: presenterOpacity,
          }}
        >
          <OffthreadVideo
            src={staticFile('dono_2.mp4')}
            muted
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
          {/* Subtle Top Gradient for readability */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: 480,
              background:
                'linear-gradient(180deg, rgba(17, 24, 39, 0.88) 0%, rgba(17, 24, 39, 0.35) 70%, rgba(17, 24, 39, 0) 100%)',
              pointerEvents: 'none',
            }}
          />
        </div>
      )}

      {/* Background 2: Dedicated Tech Demonstration Background with animated depth particles */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          background: '#111827',
          opacity: transitionProgress,
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 35%, rgba(16, 185, 129, 0.25) 0%, rgba(17, 24, 39, 0.98) 75%)',
          }}
        />
        {/* Subtle decorative tech grid */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(rgba(16, 185, 129, 0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(16, 185, 129, 0.06) 1px, transparent 1px)',
            backgroundSize: '80px 80px',
            pointerEvents: 'none',
          }}
        />
        {/* Floating animated depth glow particles */}
        {[
          {x: 80, y: 320, size: 140, color: 'rgba(16, 185, 129, 0.18)'},
          {x: 880, y: 520, size: 180, color: 'rgba(16, 185, 129, 0.14)'},
          {x: 120, y: 950, size: 160, color: 'rgba(59, 130, 246, 0.16)'},
          {x: 860, y: 1300, size: 200, color: 'rgba(16, 185, 129, 0.18)'},
          {x: 520, y: 680, size: 220, color: 'rgba(16, 185, 129, 0.10)'},
        ].map((p, idx) => {
          const driftY = Math.sin((frame + idx * 25) * 0.06) * 18;
          const driftX = Math.cos((frame + idx * 20) * 0.05) * 14;
          return (
            <div
              key={idx}
              style={{
                position: 'absolute',
                left: p.x,
                top: p.y,
                width: p.size,
                height: p.size,
                borderRadius: '50%',
                background: `radial-gradient(circle, ${p.color} 0%, transparent 70%)`,
                transform: `translate(${driftX}px, ${driftY}px)`,
                pointerEvents: 'none',
              }}
            />
          );
        })}
      </div>

      {/* Top Badge: 02 • COMO FUNCIONA (top: 168 ensures ample breathing room and no overlap) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: badgeSpring,
          transform: `translateY(${(1 - badgeSpring) * -15}px)`,
          zIndex: 50,
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
            border: '1.5px solid rgba(16, 185, 129, 0.6)',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: '#10B981',
              transform: `scale(${emeraldPulse})`,
              boxShadow: '0 0 10px #10B981',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#A7F3D0',
              textTransform: 'uppercase',
              letterSpacing: 1.2,
            }}
          >
            02 • Como Funciona
          </span>
        </div>
      </div>

      {/* Phase 1 Top Dynamic Card: Explico o que preciso (top: 255, height: 105px, bottom: 360px -> 65px above hair) */}
      {!isSimulation && (
        <div
          style={{
            position: 'absolute',
            top: 255,
            left: 60,
            right: 60,
            opacity: cardPhase1Spring * presenterOpacity,
            transform: `translateY(${(1 - cardPhase1Spring) * 15}px)`,
            zIndex: 25,
          }}
        >
          <div
            style={{
              padding: '16px 26px',
              borderRadius: 22,
              background: 'rgba(17, 24, 39, 0.92)',
              border: '1.5px solid rgba(59, 130, 246, 0.5)',
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
                background: 'rgba(59, 130, 246, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 32,
                flexShrink: 0,
              }}
            >
              🎙️
            </div>
            <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: 4}}>
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
                Explico o que preciso
              </span>
              <span
                style={{
                  fontSize: 28,
                  fontWeight: 600,
                  color: '#93C5FD',
                  lineHeight: 1.2,
                }}
              >
                Instrução direta ao agente
              </span>
            </div>
            {/* Animated Audio Waveform */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                height: 40,
                paddingRight: 6,
              }}
            >
              <div
                style={{
                  width: 5,
                  height: wave1,
                  background: '#60A5FA',
                  borderRadius: 3,
                }}
              />
              <div
                style={{
                  width: 5,
                  height: wave2,
                  background: '#3B82F6',
                  borderRadius: 3,
                }}
              />
              <div
                style={{
                  width: 5,
                  height: wave3,
                  background: '#93C5FD',
                  borderRadius: 3,
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Product Demonstration: WhatsApp Simulation Mockup (Phase 2) */}
      {/* Centered smartphone interface with large, readable typography (letra >= 32px) */}
      {frame >= 96 && (
        <div
          style={{
            position: 'absolute',
            top: 245,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: phoneSpring,
            transform: `scale(${phoneSpring}) translateY(${(1 - phoneSpring) * 25}px)`,
            zIndex: 40,
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: 940,
              borderRadius: 32,
              background: 'rgba(15, 23, 42, 0.96)',
              border: '2px solid rgba(16, 185, 129, 0.65)',
              boxShadow:
                '0 20px 50px rgba(0, 0, 0, 0.8), 0 0 35px rgba(16, 185, 129, 0.25)',
              overflow: 'hidden',
              backdropFilter: 'blur(20px)',
            }}
          >
            {/* Mockup Chat Header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px 24px',
                background: 'rgba(17, 24, 39, 0.95)',
                borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #10B981, #059669)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 28,
                    boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)',
                  }}
                >
                  🤖
                </div>
                <div>
                  <div
                    style={{
                      fontSize: 38,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      letterSpacing: -0.5,
                    }}
                  >
                    Agente Pessoal IA
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#34D399',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      marginTop: 2,
                    }}
                  >
                    <span
                      style={{
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        background: '#10B981',
                        display: 'inline-block',
                        boxShadow: '0 0 8px #10B981',
                      }}
                    />
                    <span>online • assistente</span>
                  </div>
                </div>
              </div>

              {/* Selo Simulação Obrigatório */}
              <div
                style={{
                  padding: '8px 18px',
                  borderRadius: 999,
                  background: 'rgba(16, 185, 129, 0.18)',
                  border: '1.5px solid rgba(16, 185, 129, 0.55)',
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#A7F3D0',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                Simulação
              </div>
            </div>

            {/* Mockup Chat Messages */}
            <div
              style={{
                padding: '20px 24px',
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
              }}
            >
              {/* Message 1: User / Empreendedor (Visible immediately on simulation entry - NEVER EMPTY!) */}
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '90%',
                  padding: '16px 22px',
                  borderRadius: '24px 24px 6px 24px',
                  background: '#065F46',
                  border: '1.5px solid rgba(52, 211, 153, 0.35)',
                  boxShadow: '0 6px 20px rgba(0, 0, 0, 0.35)',
                  opacity: userMsgSpring,
                  transform: `scale(${0.92 + userMsgSpring * 0.08}) translateY(${(1 - userMsgSpring) * 15}px)`,
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
                  Preciso de uma pesquisa completa sobre o setor.
                </div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#A7F3D0',
                    textAlign: 'right',
                    marginTop: 6,
                  }}
                >
                  09:42 ✓✓
                </div>
              </div>

              {/* Animated Typing Indicator during "ao Agente Pessoal IA" (frames 108 to 142) */}
              {showTyping && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    padding: '12px 20px',
                    borderRadius: '20px 20px 20px 6px',
                    background: 'rgba(30, 41, 59, 0.9)',
                    border: '1px solid rgba(16, 185, 129, 0.4)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                  }}
                >
                  <span style={{fontSize: 32, color: '#6EE7B7', fontWeight: 700}}>
                    Agente Pessoal digitando
                  </span>
                  <div style={{display: 'flex', gap: 6, alignItems: 'center'}}>
                    <div
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: '#34D399',
                        transform: `scale(${dot1})`,
                      }}
                    />
                    <div
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: '#34D399',
                        transform: `scale(${dot2})`,
                      }}
                    />
                    <div
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: '#34D399',
                        transform: `scale(${dot3})`,
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Message 2: Agente Pessoal IA (arrives at frame 142 on "e ele pesquisa por mim") */}
              {frame >= 142 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '92%',
                    padding: '18px 24px',
                    borderRadius: '24px 24px 24px 6px',
                    background: '#1E293B',
                    border: '2px solid rgba(16, 185, 129, 0.7)',
                    boxShadow:
                      '0 10px 30px rgba(0, 0, 0, 0.45), 0 0 20px rgba(16, 185, 129, 0.2)',
                    opacity: agentMsgSpring,
                    transform: `scale(${0.92 + agentMsgSpring * 0.08}) translateY(${(1 - agentMsgSpring) * 15}px)`,
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      fontSize: 36,
                      fontWeight: 900,
                      color: '#34D399',
                      marginBottom: 8,
                    }}
                  >
                    <span>✨</span>
                    <span>Pesquisa Concluída</span>
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#F8FAFC',
                      lineHeight: 1.35,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 6,
                    }}
                  >
                    <div>✓ Fontes verificadas na internet</div>
                    <div>✓ Relatório estruturado pronto para você</div>
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#94A3B8',
                      marginTop: 8,
                    }}
                  >
                    09:43
                  </div>
                </div>
              )}
            </div>

            {/* Simulated Chat Input Bar */}
            <div
              style={{
                padding: '12px 20px',
                background: 'rgba(17, 24, 39, 0.95)',
                borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div
                style={{
                  fontSize: 32,
                  color: '#64748B',
                  fontWeight: 500,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <span>💬</span>
                <span>Mensagem...</span>
              </div>
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: '50%',
                  background: 'rgba(16, 185, 129, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#34D399',
                  fontSize: 32,
                }}
              >
                ➤
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Picture-in-Picture: Presenter reacts & speaks live in lower third (mantém ritmo humano, zero vazio vertical!) */}
      {frame >= 96 && (
        <div
          style={{
            position: 'absolute',
            top: 870,
            left: 60,
            right: 60,
            height: 500,
            borderRadius: 32,
            overflow: 'hidden',
            background: 'rgba(15, 23, 42, 0.95)',
            border: '2px solid rgba(16, 185, 129, 0.7)',
            boxShadow:
              '0 20px 50px rgba(0, 0, 0, 0.8), 0 0 35px rgba(16, 185, 129, 0.25)',
            opacity: pipSpring,
            transform: `scale(${pipSpring}) translateY(${(1 - pipSpring) * 25}px)`,
            zIndex: 35,
          }}
        >
          <OffthreadVideo
            src={staticFile('dono_2.mp4')}
            muted
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              objectPosition: '50% 44%',
            }}
          />

          {/* Subtle gradient overlay for framing */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background:
                'linear-gradient(180deg, rgba(17, 24, 39, 0.45) 0%, transparent 40%, rgba(17, 24, 39, 0.5) 100%)',
              pointerEvents: 'none',
            }}
          />

          {/* Live Presenter Pill inside PiP */}
          <div
            style={{
              position: 'absolute',
              top: 18,
              left: 20,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 20px',
              borderRadius: 999,
              background: 'rgba(17, 24, 39, 0.88)',
              border: '1.5px solid rgba(16, 185, 129, 0.65)',
              backdropFilter: 'blur(10px)',
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: '#10B981',
                boxShadow: '0 0 10px #10B981',
                transform: `scale(${emeraldPulse})`,
              }}
            />
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#A7F3D0',
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              Apresentador
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
