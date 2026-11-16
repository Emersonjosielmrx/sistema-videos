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

  // Background zoom and pan
  const bgScale = interpolate(frame, [0, 271], [1.0, 1.12], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 271], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Whip-pan entrance from the right (first 12 frames) with motion blur streak to connect from Cena 1
  const whipEnterProgress = spring({
    frame,
    fps,
    config: {damping: 15, stiffness: 170},
  });
  const whipEnterX = interpolate(whipEnterProgress, [0, 1], [960, 0]);
  const motionBlurStreak = interpolate(frame, [0, 10], [0.65, 0], {
    extrapolateRight: 'clamp',
  });

  // Fade out transition at the end (last 12 frames)
  const sceneOpacity = interpolate(frame, [258, 271], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Top header spring
  const topBadgeProgress = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Phone entry spring
  const phoneProgress = spring({
    frame: frame - 1,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Continuous 3D camera push-in and organic tilt on the smartphone mockup
  // Starts closer & larger (1.10 -> 1.12) in q07/q08 to maximize legibility and eliminate idle empty area,
  // then smoothly adjusts to 1.02 at frame 160 to frame all 4 messages cleanly in q09
  const cameraPushScale = interpolate(
    frame,
    [0, 80, 150, 175, 271],
    [1.10, 1.13, 1.10, 1.02, 1.04],
    {extrapolateRight: 'clamp'}
  );
  const tiltY = interpolate(frame, [0, 135, 271], [-4.0, 2.5, -2.0], {
    extrapolateRight: 'clamp',
  });
  const floatPhoneY = Math.sin(frame * 0.09) * 5;

  // Timings for messages:
  // Msg 1 (Cliente + Fixed Item Attachment): enters immediately at frame 5
  const msg1Progress = spring({
    frame: frame - 5,
    fps,
    config: {damping: 13, stiffness: 145},
  });

  // Dynamic AI Typing Indicator 1: active early (frame 20 to 92) so q07 has live AI activity!
  const showTyping1 = frame >= 20 && frame < 92;
  const typingDotPulse = (frame * 0.35) % 3;

  // Msg 2 (Empresa / IA): frame 92
  const msg2Progress = spring({
    frame: frame - 92,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Msg 3 (Cliente): frame 162
  const msg3Progress = spring({
    frame: frame - 162,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Micro typing indicator 2 before Msg 4 (frame 190 to 208)
  const showTyping2 = frame >= 190 && frame < 208;

  // Msg 4 (Empresa / IA): frame 208
  const msg4Progress = spring({
    frame: frame - 208,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // ZERO CLIPPING! All 4 bubbles fit comfortably inside the 860px chat body with 0 scroll!
  // Instead of scrolling and cutting Message 1 under the header, all bubbles remain 100% whole.

  return (
    <AbsoluteFill
      style={{
        opacity: sceneOpacity,
        transform: `translateX(${whipEnterX}px)`,
        backgroundColor: '#31060F',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Motion Blur Streak during Whip-Pan Entrance */}
      {motionBlurStreak > 0.02 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(90deg, rgba(225, 29, 72, 0.45) 0%, rgba(250, 204, 21, 0.25) 50%, transparent 100%)',
            opacity: motionBlurStreak,
            zIndex: 50,
            pointerEvents: 'none',
          }}
        />
      )}
      {/* Background with continuous slow zoom */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
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
              'radial-gradient(circle at 50% 35%, rgba(225, 29, 72, 0.26) 0%, rgba(49, 6, 15, 0.9) 75%, rgba(15, 2, 5, 0.98) 100%)',
          }}
        />
      </div>

      {/* Top Badge: "COMO FUNCIONA" (y=164) */}
      <div
        style={{
          position: 'absolute',
          top: 164,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: topBadgeProgress,
          transform: `translateY(${(1 - topBadgeProgress) * -14}px)`,
          zIndex: 30,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 22px',
            borderRadius: 20,
            background: 'rgba(34, 197, 94, 0.32)',
            border: '2px solid #22C55E',
            boxShadow: '0 4px 16px rgba(34, 197, 94, 0.35)',
            backdropFilter: 'blur(6px)',
          }}
        >
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>
      </div>

      {/* Top Title: "ATENDIMENTO COM IA NO WHATSAPP" (y=210) */}
      <div
        style={{
          position: 'absolute',
          top: 210,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: topBadgeProgress,
          zIndex: 30,
        }}
      >
        <span
          style={{
            fontSize: 35,
            fontWeight: 900,
            color: '#FFFFFF',
            textTransform: 'uppercase',
            letterSpacing: '0.02em',
            textShadow: '0 4px 18px rgba(0,0,0,0.85)',
            textAlign: 'center',
          }}
        >
          Atendimento com IA no WhatsApp
        </span>
      </div>

      {/* Realistic Smartphone Mockup Container (y=288 to y=1408) */}
      <div
        style={{
          position: 'absolute',
          top: 288,
          left: 64,
          width: 952,
          height: 1120,
          perspective: 1200,
          zIndex: 20,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            borderRadius: 48,
            background: 'linear-gradient(180deg, #111B21 0%, #0B141A 100%)',
            border: '10px solid #334155',
            boxShadow:
              '0 30px 80px rgba(0, 0, 0, 0.9), 0 0 45px rgba(34, 197, 94, 0.25), inset 0 0 0 2px rgba(255,255,255,0.15)',
            transform: `rotateY(${tiltY}deg) translateY(${floatPhoneY}px) scale(${phoneProgress * cameraPushScale})`,
            transformOrigin: '50% 15%',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* WhatsApp Header */}
          <div
            style={{
              background: '#1F2C34',
              padding: '14px 22px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              zIndex: 10,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #E11D48 0%, #FACC15 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 26,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
                }}
              >
                🤖
              </div>
              <div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#E9EDEF',
                    lineHeight: 1.1,
                  }}
                >
                  Cardápio Digital • IA
                </div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#4ADE80',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span
                    style={{
                      width: 9,
                      height: 9,
                      borderRadius: '50%',
                      background: '#4ADE80',
                    }}
                  />
                  Online no WhatsApp
                </div>
              </div>
            </div>

            {/* Selo Simulação */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.12)',
                border: '1px solid rgba(255, 255, 255, 0.22)',
                padding: '5px 14px',
                borderRadius: 14,
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#CBD5E1',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                Simulação
              </span>
            </div>
          </div>

          {/* Chat Messages Body — All messages + Item tag stay 100% visible, NEVER clipped! */}
          <div
            style={{
              flex: 1,
              padding: frame < 162 ? '22px 22px' : '12px 18px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: frame < 162 ? 'center' : 'space-between',
              gap: frame < 162 ? 28 : 10,
              background:
                'radial-gradient(circle at 50% 45%, rgba(0, 92, 75, 0.24) 0%, rgba(11, 20, 26, 0.98) 82%)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: frame < 162 ? 18 : 10,
              }}
            >
              {/* Message 1 (Cliente) — WITH PERMANENT FIXED ITEM ATTACHMENT across q07, q08 and q09! */}
              {frame >= 4 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '94%',
                    opacity: msg1Progress,
                    transform: `scale(${0.92 + msg1Progress * 0.08}) translateX(${(1 - msg1Progress) * -16}px)`,
                    background: '#202C33',
                    border: '1.5px solid rgba(255, 255, 255, 0.16)',
                    borderRadius: '20px 20px 20px 4px',
                    padding: frame < 162 ? '14px 18px' : '10px 16px',
                    boxShadow: '0 6px 16px rgba(0, 0, 0, 0.45)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: frame < 162 ? 10 : 6,
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: 12,
                    }}
                  >
                    <span
                      style={{
                        fontSize: 33,
                        fontWeight: 800,
                        color: '#FACC15',
                        lineHeight: 1.05,
                      }}
                    >
                      Cliente
                    </span>
                  </div>

                  {/* Fixed Item Tag inside Message 1 — NEVER disappears in q08 or q09! */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      background: 'rgba(225, 29, 72, 0.28)',
                      border: '2px solid rgba(250, 204, 21, 0.75)',
                      borderRadius: 14,
                      padding: frame < 162 ? '8px 14px' : '5px 12px',
                    }}
                  >
                    <Img
                      src={staticFile('prato_executivo.jpg')}
                      style={{
                        width: frame < 162 ? 54 : 42,
                        height: frame < 162 ? 54 : 42,
                        borderRadius: 10,
                        objectFit: 'cover',
                        border: '1.5px solid #FACC15',
                      }}
                    />
                    <span
                      style={{
                        fontSize: 33,
                        fontWeight: 800,
                        color: '#FACC15',
                        lineHeight: 1.1,
                      }}
                    >
                      Item: Prato Executivo Especial
                    </span>
                  </div>

                  <div
                    style={{
                      fontSize: frame < 162 ? 35 : 32,
                      fontWeight: 700,
                      color: '#FFFFFF',
                      lineHeight: 1.22,
                    }}
                  >
                    Boa noite! Estou olhando as fotos aqui no cardápio digital. Esse prato executivo vem com salada separada?
                  </div>
                </div>
              )}

              {/* Dynamic Typing Indicator + AI Menu Consultation Card in q07 (frames 20 to 92) */}
              {showTyping1 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-end',
                    gap: 10,
                    marginTop: 4,
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 14,
                      background: '#005C4B',
                      border: '2.5px solid #25D366',
                      padding: '16px 24px',
                      borderRadius: '20px 20px 4px 20px',
                      boxShadow: '0 8px 24px rgba(0, 92, 75, 0.65)',
                    }}
                  >
                    <span
                      style={{
                        fontSize: 34,
                        fontWeight: 900,
                        color: '#FFFFFF',
                      }}
                    >
                      🤖 IA consultando cardápio e digitando
                    </span>
                    <div style={{display: 'flex', gap: 7}}>
                      {[0, 1, 2].map((dot) => (
                        <span
                          key={dot}
                          style={{
                            width: 12,
                            height: 12,
                            borderRadius: '50%',
                            background: '#25D366',
                            opacity:
                              Math.floor(typingDotPulse) === dot ? 1.0 : 0.35,
                            transform: `scale(${Math.floor(typingDotPulse) === dot ? 1.35 : 1.0})`,
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Message 2 (Empresa / IA) */}
              {frame >= 92 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '94%',
                    opacity: msg2Progress,
                    transform: `scale(${0.92 + msg2Progress * 0.08}) translateX(${(1 - msg2Progress) * 16}px)`,
                    background: '#005C4B',
                    border: '2px solid #25D366',
                    borderRadius: '20px 20px 4px 20px',
                    padding: frame < 162 ? '14px 18px' : '10px 16px',
                    boxShadow: '0 6px 18px rgba(0, 92, 75, 0.55)',
                  }}
                >
                  <div
                    style={{
                      fontSize: 33,
                      fontWeight: 900,
                      color: '#BEF264',
                      lineHeight: 1.08,
                      marginBottom: 4,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                    }}
                  >
                    <span>IA • Explica na Hora</span>
                    <span style={{fontSize: 28}}>⚡</span>
                  </div>
                  <div
                    style={{
                      fontSize: frame < 162 ? 35 : 32,
                      fontWeight: 700,
                      color: '#FFFFFF',
                      lineHeight: 1.22,
                    }}
                  >
                    Boa noite! Vem sim, a salada vai em uma embalagem separada do prato quente.
                  </div>
                </div>
              )}

              {/* Message 3 (Cliente) */}
              {frame >= 162 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '90%',
                    opacity: msg3Progress,
                    transform: `scale(${0.92 + msg3Progress * 0.08}) translateX(${(1 - msg3Progress) * -16}px)`,
                    background: '#202C33',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '18px 18px 18px 4px',
                    padding: '9px 16px',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.35)',
                  }}
                >
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#FACC15',
                      lineHeight: 1.08,
                      marginBottom: 2,
                    }}
                  >
                    Cliente
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#E9EDEF',
                      lineHeight: 1.18,
                    }}
                  >
                    Perfeito, era essa a minha dúvida. Vou enviar o pedido por aqui mesmo.
                  </div>
                </div>
              )}

              {/* Typing Indicator 2 before Msg 4 */}
              {showTyping2 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    background: '#005C4B',
                    border: '1.5px solid #4ADE80',
                    padding: '8px 16px',
                    borderRadius: '18px 18px 4px 18px',
                  }}
                >
                  <span style={{fontSize: 32, fontWeight: 800, color: '#BEF264'}}>
                    IA digitando...
                  </span>
                </div>
              )}

              {/* Message 4 (Empresa / IA) — High contrast bright lime '#BEF264' on 'IA • Atendimento' */}
              {frame >= 208 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '90%',
                    opacity: msg4Progress,
                    transform: `scale(${0.92 + msg4Progress * 0.08}) translateX(${(1 - msg4Progress) * 16}px)`,
                    background: '#005C4B',
                    border: '1.5px solid rgba(74, 222, 128, 0.5)',
                    borderRadius: '18px 18px 4px 18px',
                    padding: '9px 16px',
                    boxShadow: '0 4px 16px rgba(0, 92, 75, 0.5)',
                  }}
                >
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 900,
                      color: '#BEF264',
                      lineHeight: 1.08,
                      marginBottom: 2,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                    }}
                  >
                    <span>IA • Atendimento</span>
                    <span style={{fontSize: 26}}>✓</span>
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#FFFFFF',
                      lineHeight: 1.18,
                    }}
                  >
                    Combinado! Assim que escolher, pode mandar o pedido direto por aqui.
                  </div>
                </div>
              )}
            </div>

            {/* Active Digital Menu Context Panel at bottom of chat in early frames (q07 & q08) — High Contrast & Prominent! */}
            {frame < 162 && (
              <div
                style={{
                  background: '#0A1914',
                  border: '2.5px solid #25D366',
                  borderRadius: 22,
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  boxShadow: '0 10px 28px rgba(0,0,0,0.75)',
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
                  <Img
                    src={staticFile('prato_executivo.jpg')}
                    style={{
                      width: 88,
                      height: 88,
                      borderRadius: 16,
                      objectFit: 'cover',
                      border: '2.5px solid #FACC15',
                    }}
                  />
                  <div style={{display: 'flex', flexDirection: 'column', gap: 8}}>
                    <div
                      style={{
                        fontSize: 34,
                        fontWeight: 900,
                        color: '#FFFFFF',
                        lineHeight: 1.1,
                      }}
                    >
                      Cardápio Digital com Fotos
                    </div>
                    <div
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 8,
                        background: 'rgba(37, 211, 102, 0.2)',
                        border: '2px solid #25D366',
                        padding: '6px 18px',
                        borderRadius: 12,
                        alignSelf: 'flex-start',
                      }}
                    >
                      <span
                        style={{
                          fontSize: 34,
                          fontWeight: 900,
                          color: '#25D366',
                          lineHeight: 1.1,
                        }}
                      >
                        ✓ IA tira dúvidas na hora
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Native Mobile WhatsApp Input Bar */}
          <div
            style={{
              background: '#1F2C34',
              padding: '8px 18px',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              borderTop: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            <div
              style={{
                flex: 1,
                background: '#2A3942',
                borderRadius: 22,
                padding: '6px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <span style={{fontSize: 26}}>😊</span>
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#CBD5E1',
                }}
              >
                Pedido via Cardápio Digital
              </span>
            </div>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: '50%',
                background: '#00A884',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 24,
              }}
            >
              🎤
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
