import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Dynamic motion transition entering from Cena 1 (frames 0 to 14)
  const entranceScale = interpolate(frame, [0, 14], [1.12, 1.0], {
    extrapolateRight: 'clamp',
  });
  const entranceSlideX = interpolate(frame, [0, 14], [70, 0], {
    extrapolateRight: 'clamp',
  });
  const entranceOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Background slow continuous zoom (1.02 -> 1.12)
  const bgScale = interpolate(frame, [0, 317], [1.02, 1.12], {
    extrapolateRight: 'clamp',
  });

  // 3D Phone Perspective & Continuous Subtle Motion
  const phoneRotateY = interpolate(frame, [0, 317], [-10, -4], {
    extrapolateRight: 'clamp',
  });
  const phoneFloat = Math.sin(frame / 14) * 4;

  // Header entrance
  const headerSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Phone spring entrance
  const phoneEntranceSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Message Entrance Timings:
  // Msg 1 (Cliente): frame 5
  // Frame 24-44: "IA digitando..."
  // Msg 2 (IA): frame 45
  // Msg 3 (Cliente): frame 95
  // Msg 4 (IA): frame 125 ("reagenda sozinha")
  // Frame 165+: Auto-scroll + fade older messages to focus on key highlights
  // Banner 1: frame 170 ("Vaga das 09h oferecida à lista de espera")
  // Banner 2: frame 195 ("Vaga preenchida pela lista de espera!")
  // Banner 3: frame 220 ("Sem conflito e sem duplo agendamento")

  const msg1Spring = spring({frame: frame - 5, fps, config: {damping: 12, stiffness: 120}});
  const showTyping = frame >= 24 && frame < 45;
  const msg2Spring = spring({frame: frame - 45, fps, config: {damping: 12, stiffness: 120}});
  const msg3Spring = spring({frame: frame - 95, fps, config: {damping: 12, stiffness: 120}});
  const msg4Spring = spring({frame: frame - 125, fps, config: {damping: 12, stiffness: 120}});
  const offerSpring = spring({frame: frame - 170, fps, config: {damping: 12, stiffness: 120}});
  const filledSpring = spring({frame: frame - 195, fps, config: {damping: 12, stiffness: 120}});
  const guaranteeSpring = spring({frame: frame - 220, fps, config: {damping: 12, stiffness: 120}});

  // Container height dynamically hugs the conversation as messages appear:
  // Frame 0-23: 270px (Msg 1 alone - NO giant black empty space in q07/q08!)
  // Frame 24-44: 330px (Msg 1 + typing)
  // Frame 45-94: 390px (Msg 1 + Msg 2)
  // Frame 95-124: 510px (Msg 1 + Msg 2 + Msg 3)
  // Frame 125+: 640px (Msg 1-4, then smooth auto-scroll)
  const phoneHeight = interpolate(
    frame,
    [0, 23, 24, 44, 45, 94, 95, 124, 125],
    [270, 270, 330, 330, 390, 390, 510, 510, 645],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Smooth auto-scroll when transitioning to the solution resolution (frames 160 to 195)
  const chatScrollY = interpolate(frame, [160, 195], [0, -170], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Older messages fade out slightly to focus attention on the resolution
  const oldMsgOpacity = interpolate(frame, [160, 185], [1, 0.25], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Continuous push-in scale on the phone mockup
  const phoneScale = interpolate(frame, [0, 317], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        transform: `scale(${entranceScale}) translateX(${entranceSlideX}px)`,
        opacity: entranceOpacity,
      }}
    >
      {/* Warm blurred clinic reception background */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          filter: 'blur(5px)',
          opacity: 0.75,
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </div>

      {/* Protective overlay preserving ambiance while guaranteeing contrast */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.85) 0%, rgba(15,23,42,0.65) 40%, rgba(15,23,42,0.85) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Header Section (y: 165 - 235) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          transform: `scale(${headerSpring})`,
          opacity: headerSpring,
          zIndex: 30,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            backgroundColor: '#1F2937',
            border: '2px solid #FFA94D',
            padding: '10px 24px',
            borderRadius: 999,
            boxShadow: '0 8px 24px rgba(255, 169, 77, 0.25)',
          }}
        >
          <span style={{fontSize: 32}}>⚡</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFA94D',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>

        {/* Mandatory Simulation Badge with font >= 32px */}
        <div
          style={{
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            border: '2px solid rgba(255, 255, 255, 0.3)',
            padding: '8px 20px',
            borderRadius: 12,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#F3F4F6',
              textTransform: 'uppercase',
              letterSpacing: '1px',
            }}
          >
            Simulação
          </span>
        </div>
      </div>

      {/* 3D Smartphone Container (y: 250 to ~920) */}
      <div
        style={{
          position: 'absolute',
          top: 250,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'center',
          perspective: 1200,
          zIndex: 25,
        }}
      >
        <div
          style={{
            width: 880,
            height: phoneHeight,
            transform: `rotateY(${phoneRotateY}deg) translateY(${phoneFloat}px) scale(${phoneEntranceSpring * phoneScale})`,
            transformStyle: 'preserve-3d',
            borderRadius: 36,
            backgroundColor: '#111827',
            border: '3px solid #374151',
            boxShadow:
              '0 28px 60px rgba(0, 0, 0, 0.85), inset 0 0 0 2px rgba(255,255,255,0.1)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            transition: 'height 0.25s ease-out',
          }}
        >
          {/* Phone Header (WhatsApp Theme) */}
          <div
            style={{
              backgroundColor: '#1F2937',
              borderBottom: '2px solid rgba(255, 255, 255, 0.1)',
              padding: '16px 24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              zIndex: 10,
              position: 'relative',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              {/* Avatar */}
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: '50%',
                  backgroundColor: '#FFA94D',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  boxShadow: '0 4px 12px rgba(255, 169, 77, 0.4)',
                }}
              >
                🤖
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Agenda IA
                </div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginTop: 2,
                  }}
                >
                  <span
                    style={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: '#22C55E',
                      boxShadow: '0 0 8px #22C55E',
                    }}
                  />
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#9CA3AF',
                    }}
                  >
                    Online 24h
                  </span>
                </div>
              </div>
            </div>

            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFA94D',
                backgroundColor: 'rgba(255, 169, 77, 0.15)',
                padding: '8px 18px',
                borderRadius: 14,
              }}
            >
              WhatsApp
            </div>
          </div>

          {/* Messages Feed with Dynamic Hugging & Auto-scroll */}
          <div
            style={{
              flex: 1,
              padding: '16px 22px',
              backgroundColor: '#0B0F17',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
                transform: `translateY(${chatScrollY}px)`,
              }}
            >
              {/* Message 1 (Cliente) */}
              {frame >= 5 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '82%',
                    backgroundColor: '#1E293B',
                    border: '1.5px solid rgba(255, 255, 255, 0.12)',
                    borderRadius: '22px 22px 22px 6px',
                    padding: '12px 20px',
                    transform: `scale(${msg1Spring})`,
                    opacity: msg1Spring * oldMsgOpacity,
                    boxShadow: '0 4px 14px rgba(0,0,0,0.35)',
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#F8FAFC',
                      lineHeight: 1.3,
                    }}
                  >
                    Não vou conseguir ir amanhã cedo.
                  </div>
                </div>
              )}

              {/* Typing Indicator */}
              {showTyping && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    backgroundColor: 'rgba(255, 169, 77, 0.2)',
                    border: '1.5px solid #FFA94D',
                    borderRadius: '22px 22px 6px 22px',
                    padding: '10px 18px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#FFA94D',
                    }}
                  >
                    IA digitando
                  </span>
                  <span style={{display: 'inline-flex', gap: 5}}>
                    {[0, 1, 2].map((dot) => (
                      <span
                        key={dot}
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          backgroundColor: '#FFA94D',
                          opacity: Math.sin(frame / 4 + dot * 1.2) * 0.5 + 0.5,
                        }}
                      />
                    ))}
                  </span>
                </div>
              )}

              {/* Message 2 (Empresa / IA) */}
              {frame >= 45 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '84%',
                    backgroundColor: '#064E3B',
                    border: '1.5px solid #10B981',
                    borderRadius: '22px 22px 6px 22px',
                    padding: '12px 20px',
                    transform: `scale(${msg2Spring})`,
                    opacity: msg2Spring * oldMsgOpacity,
                    boxShadow: '0 6px 18px rgba(16, 185, 129, 0.25)',
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#ECFDF5',
                      lineHeight: 1.3,
                    }}
                  >
                    Tudo bem! Posso reagendar para quinta às 10h ou sexta às 15h.
                  </div>
                </div>
              )}

              {/* Message 3 (Cliente) */}
              {frame >= 95 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '82%',
                    backgroundColor: '#1E293B',
                    border: '1.5px solid rgba(255, 255, 255, 0.12)',
                    borderRadius: '22px 22px 22px 6px',
                    padding: '12px 20px',
                    transform: `scale(${msg3Spring})`,
                    opacity: msg3Spring,
                    boxShadow: '0 4px 14px rgba(0,0,0,0.35)',
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#F8FAFC',
                      lineHeight: 1.3,
                    }}
                  >
                    Quinta às 10h, por favor.
                  </div>
                </div>
              )}

              {/* Message 4 (Empresa / IA - Reagenda sozinha) */}
              {frame >= 125 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '84%',
                    backgroundColor: '#064E3B',
                    border: '1.5px solid #10B981',
                    borderRadius: '22px 22px 6px 22px',
                    padding: '12px 20px',
                    transform: `scale(${msg4Spring})`,
                    opacity: msg4Spring,
                    boxShadow: '0 6px 18px rgba(16, 185, 129, 0.25)',
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#ECFDF5',
                      lineHeight: 1.3,
                    }}
                  >
                    Pronto, reagendado! Horário confirmado para você.
                  </div>
                </div>
              )}

              {/* Moment-Key Highlight 1: Horário livre oferecido à lista de espera */}
              {frame >= 170 && (
                <div
                  style={{
                    alignSelf: 'center',
                    maxWidth: '92%',
                    backgroundColor: 'rgba(255, 169, 77, 0.15)',
                    border: '2px solid #FFA94D',
                    borderRadius: 16,
                    padding: '10px 18px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    transform: `scale(${offerSpring})`,
                    opacity: offerSpring,
                    boxShadow: '0 4px 16px rgba(255, 169, 77, 0.25)',
                  }}
                >
                  <span style={{fontSize: 28}}>⚡</span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#FFA94D',
                      textTransform: 'uppercase',
                    }}
                  >
                    Vaga das 09h oferecida à lista de espera
                  </span>
                </div>
              )}

              {/* Moment-Key Highlight 2: Vaga Preenchida com Confirmação em Tempo Real */}
              {frame >= 195 && (
                <div
                  style={{
                    alignSelf: 'center',
                    maxWidth: '92%',
                    backgroundColor: 'rgba(34, 197, 94, 0.18)',
                    border: '2px solid #22C55E',
                    borderRadius: 16,
                    padding: '12px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    transform: `scale(${filledSpring})`,
                    opacity: filledSpring,
                    boxShadow: '0 6px 20px rgba(34, 197, 94, 0.3)',
                  }}
                >
                  <span style={{fontSize: 30}}>✓</span>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#86EFAC',
                      textTransform: 'uppercase',
                    }}
                  >
                    Vaga preenchida pela lista de espera!
                  </div>
                </div>
              )}

              {/* Guarantee: Sem Conflito e Sem Duplo Agendamento (frame >= 220) */}
              {frame >= 220 && (
                <div
                  style={{
                    alignSelf: 'center',
                    backgroundColor: '#1E293B',
                    border: '1.5px solid #38BDF8',
                    borderRadius: 999,
                    padding: '8px 22px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 10,
                    transform: `scale(${guaranteeSpring})`,
                    opacity: guaranteeSpring,
                  }}
                >
                  <span style={{fontSize: 24}}>🛡️</span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 30,
                      fontWeight: 800,
                      color: '#BAE6FD',
                      textTransform: 'uppercase',
                    }}
                  >
                    Sem conflito • Sem duplo agendamento
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
