import React from 'react';
import {
  interpolate,
  OffthreadVideo,
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

  // Smooth directional slide + zoom-in transition from Scene 1 with motion blur
  const enterProgress = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 95},
  });
  const sceneTranslateY = interpolate(enterProgress, [0, 1], [120, 0]);
  const sceneScale = interpolate(enterProgress, [0, 1], [0.92, 1]);
  const enterBlur = interpolate(frame, [0, 10], [12, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Top header entrance
  const headerSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Messages entrance springs
  const msg1Spring = spring({
    frame: Math.max(0, frame - 12),
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const msg2Spring = spring({
    frame: Math.max(0, frame - 55),
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const msg3Spring = spring({
    frame: Math.max(0, frame - 110),
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Exit transition
  const exitOpacity = interpolate(frame, [195, 208], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Is voice cloning highlighted? (frame >= 115)
  const isVozClonada = frame >= 115;

  // Call duration counter ticking up
  const callSeconds = Math.floor(interpolate(frame, [0, 208], [4, 28]));
  const formattedTime = `00:${callSeconds < 10 ? '0' : ''}${callSeconds}`;

  // Background motion graphics displacement
  const gridShift = (frame * 1.6) % 80;

  // Rotating radar sweep angle (visible rotating radar beam + dashed rings so radar is visibly rotating between q07 and q08)
  const radarAngle = frame * 4.5;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        fontFamily,
        opacity: exitOpacity,
        background:
          'linear-gradient(165deg, #041F11 0%, #073B22 48%, #03150C 100%)',
        transform: `translateY(${sceneTranslateY}px) scale(${sceneScale})`,
        filter: enterBlur > 0.5 ? `blur(${enterBlur}px)` : undefined,
      }}
    >
      {/* Real Corporate Office Environment Background with Depth-of-Field Blur connecting to the Presenter's Office */}
      <OffthreadVideo
        src={staticFile('dono_1.mp4')}
        muted
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          objectFit: 'cover',
          filter: 'blur(18px) brightness(0.45) contrast(1.1) saturate(0.95)',
          transform: `scale(${interpolate(frame, [0, 208], [1.06, 1.18])}) translateX(${interpolate(frame, [0, 208], [-18, 18])}px)`,
        }}
      />

      {/* Subtle Corporate Ambient Depth Overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(5, 22, 13, 0.85) 0%, rgba(7, 34, 20, 0.68) 50%, rgba(4, 18, 10, 0.92) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Zone (y=165..310) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
          zIndex: 10,
          transform: `scale(${headerSpring})`,
          opacity: headerSpring,
        }}
      >
        {/* Rótulo Badge */}
        <div
          style={{
            background: 'rgba(37, 211, 102, 0.22)',
            border: '2px solid #25D366',
            borderRadius: 9999,
            padding: '6px 22px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.4)',
          }}
        >
          <span
            style={{
              display: 'inline-block',
              width: 14,
              height: 14,
              borderRadius: 7,
              backgroundColor: '#25D366',
              boxShadow: '0 0 10px #25D366',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1,
              textTransform: 'uppercase',
            }}
          >
            Como Funciona • Automação WhatsApp
          </span>
        </div>

        {/* Dynamic Title */}
        <div
          style={{
            fontSize: 44,
            fontWeight: 900,
            color: '#FFFFFF',
            textAlign: 'center',
            lineHeight: 1.2,
            textShadow: '0 4px 14px rgba(0, 0, 0, 0.8)',
            height: 52,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {!isVozClonada ? (
            <span>BOT DE LIGAÇÃO EM MASSA</span>
          ) : (
            <span style={{color: '#25D366'}}>
              LIGAÇÕES COM VOZ REAL CLONADA
            </span>
          )}
        </div>
      </div>

      {/* Realistic Smartphone Bezel Hardware Frame with Subtle 3D Perspective */}
      <div
        style={{
          position: 'absolute',
          top: 318,
          left: 62,
          width: 956,
          background: 'linear-gradient(145deg, #1E293B 0%, #0F172A 50%, #090D16 100%)',
          borderRadius: 52,
          padding: '16px 14px 20px 14px',
          border: '3px solid rgba(148, 163, 184, 0.45)',
          boxShadow:
            '0 35px 80px rgba(0, 0, 0, 0.9), 0 0 35px rgba(37, 211, 102, 0.25), inset 0 2px 4px rgba(255, 255, 255, 0.25)',
          transform: `perspective(1400px) rotateY(${interpolate(frame, [0, 208], [-3.5, 2.5])}deg) rotateX(1.5deg)`,
          zIndex: 10,
        }}
      >
        {/* Smartphone Top Speaker / Dynamic Island Notch */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            marginBottom: 10,
          }}
        >
          <div
            style={{
              width: 150,
              height: 22,
              borderRadius: 11,
              background: '#05080F',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              paddingRight: 10,
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: 5,
                background: 'radial-gradient(circle, #38BDF8 0%, #0369A1 100%)',
              }}
            />
          </div>
        </div>

        {/* Inner Phone Screen */}
        <div
          style={{
            width: '100%',
            background: 'rgba(11, 20, 26, 0.98)',
            borderRadius: 36,
            border: '2px solid rgba(37, 211, 102, 0.65)',
            overflow: 'hidden',
          }}
        >
        {/* Prominent WhatsApp Voice Call Active Interface Header */}
        <div
          style={{
            background: 'linear-gradient(180deg, #075E54 0%, #0B3B32 100%)',
            padding: '18px 26px',
            borderBottom: '2px solid rgba(37, 211, 102, 0.45)',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              {/* Pulsing Call Avatar */}
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 32,
                  background: '#25D366',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 34,
                  boxShadow: '0 0 20px rgba(37, 211, 102, 0.8)',
                  transform: `scale(${1 + 0.08 * Math.sin(frame * 0.37)})`,
                }}
              >
                📞
              </div>
              <div>
                <div
                  style={{
                    fontSize: 36,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    lineHeight: 1.15,
                  }}
                >
                  Hermes Call • Ligação IA
                </div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#A7F3D0',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  <span>Chamada de Voz Ativa • {formattedTime}</span>
                </div>
              </div>
            </div>

            {/* Mandatory "Simulação" Badge */}
            <div
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#E2E8F0',
                background: 'rgba(0, 0, 0, 0.38)',
                border: '1.5px solid rgba(255, 255, 255, 0.3)',
                padding: '6px 16px',
                borderRadius: 10,
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              Simulação
            </div>
          </div>

          {/* Real-Time Voice Cloning Spectrum Visualizer in Call Header (non-resonant frequencies so q07 and q08 show dramatically different bar heights & active playhead) */}
          <div
            style={{
              background: 'rgba(6, 22, 16, 0.85)',
              borderRadius: 16,
              padding: '10px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 18,
              border: '1.5px solid rgba(37, 211, 102, 0.5)',
            }}
          >
            <div
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#25D366',
                whiteSpace: 'nowrap',
              }}
            >
              🎙️ VOZ REAL CLONADA
            </div>
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                height: 38,
              }}
            >
              {Array.from({length: 20}).map((_, idx) => {
                // Non-harmonic frequency combination so 15-frame and 30-frame intervals never alias!
                const wave1 = Math.sin(frame * 0.47 + idx * 0.75);
                const wave2 = Math.cos(frame * 0.29 - idx * 0.4);
                const norm = (wave1 + wave2 + 2) / 4; // 0..1
                const barH = Math.round(8 + 28 * norm);
                const isPeak = norm > 0.68;
                return (
                  <div
                    key={idx}
                    style={{
                      flex: 1,
                      height: barH,
                      backgroundColor: isPeak ? '#A7F3D0' : '#25D366',
                      borderRadius: 4,
                      boxShadow: isPeak
                        ? '0 0 8px rgba(167, 243, 208, 0.8)'
                        : 'none',
                    }}
                  />
                );
              })}
            </div>
            <div
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                background: '#EF4444',
                padding: '4px 14px',
                borderRadius: 999,
                transform: `scale(${1 + 0.06 * Math.sin(frame * 0.43)})`,
              }}
            >
              EM CHAMADA
            </div>
          </div>
        </div>

        {/* Messages Container */}
        <div
          style={{
            padding: '20px 24px 24px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          {/* Message 1 (Empresa) */}
          {frame >= 12 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '88%',
                transform: `translateY(${interpolate(
                  msg1Spring,
                  [0, 1],
                  [20, 0]
                )}px)`,
                opacity: msg1Spring,
                background: '#005C4B',
                borderRadius: '20px 20px 4px 20px',
                padding: '14px 20px',
                boxShadow: '0 4px 15px rgba(0, 0, 0, 0.4)',
              }}
            >
              <div
                style={{
                  fontSize: 33,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                Olá! Vi que você pediu detalhes sobre nossa solução de vendas
                pelo WhatsApp.
              </div>
            </div>
          )}

          {/* Message 2 (Cliente) */}
          {frame >= 55 && (
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '86%',
                transform: `translateY(${interpolate(
                  msg2Spring,
                  [0, 1],
                  [20, 0]
                )}px)`,
                opacity: msg2Spring,
                background: '#202C33',
                borderRadius: '20px 20px 20px 4px',
                padding: '14px 20px',
                boxShadow: '0 4px 15px rgba(0, 0, 0, 0.4)',
              }}
            >
              <div
                style={{
                  fontSize: 33,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                Sim, queria entender como funcionam as chamadas automáticas.
              </div>
            </div>
          )}

          {/* Typing / Voice Generation Indicator */}
          {frame >= 88 && frame < 110 && (
            <div
              style={{
                alignSelf: 'flex-end',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                background: 'rgba(0, 92, 75, 0.75)',
                padding: '12px 20px',
                borderRadius: 16,
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#25D366',
                }}
              >
                Hermes Call falando com voz clonada...
              </span>
            </div>
          )}

          {/* Message 3 (Empresa) + Audio Note Player */}
          {frame >= 110 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '90%',
                transform: `translateY(${interpolate(
                  msg3Spring,
                  [0, 1],
                  [20, 0]
                )}px)`,
                opacity: msg3Spring,
                background: '#005C4B',
                border: '2px solid rgba(37, 211, 102, 0.7)',
                borderRadius: '20px 20px 4px 20px',
                padding: '14px 20px',
                boxShadow: '0 6px 20px rgba(0, 0, 0, 0.5)',
              }}
            >
              <div
                style={{
                  fontSize: 33,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                Perfeito! Nossa inteligência artificial faz ligações vinte e
                quatro horas com voz real.
              </div>

              {/* Dynamic Audio Waveform Player inside the message */}
              <div
                style={{
                  marginTop: 12,
                  background: 'rgba(0, 0, 0, 0.35)',
                  borderRadius: 12,
                  padding: '10px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                }}
              >
                <div
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: 19,
                    backgroundColor: '#25D366',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#121216',
                    fontSize: 22,
                    fontWeight: 900,
                  }}
                >
                  ▶
                </div>
                <div
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    height: 34,
                  }}
                >
                  {Array.from({length: 16}).map((_, barIdx) => {
                    const w1 = Math.sin(frame * 0.43 + barIdx * 0.65);
                    const w2 = Math.cos(frame * 0.27 - barIdx * 0.35);
                    const waveHeight = Math.round(8 + 24 * ((w1 + w2 + 2) / 4));
                    const progressBars = Math.floor(
                      interpolate(frame, [110, 200], [4, 15], {
                        extrapolateLeft: 'clamp',
                        extrapolateRight: 'clamp',
                      })
                    );
                    return (
                      <div
                        key={barIdx}
                        style={{
                          flex: 1,
                          height: waveHeight,
                          backgroundColor:
                            barIdx <= progressBars
                              ? '#25D366'
                              : 'rgba(255, 255, 255, 0.35)',
                          borderRadius: 3,
                        }}
                      />
                    );
                  })}
                </div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#E2E8F0',
                  }}
                >
                  0:14
                </div>
              </div>
            </div>
          )}
        </div>
        </div>

        {/* Smartphone Home Indicator Bar */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            marginTop: 12,
          }}
        >
          <div
            style={{
              width: 180,
              height: 6,
              borderRadius: 3,
              backgroundColor: 'rgba(255, 255, 255, 0.45)',
            }}
          />
        </div>
      </div>
    </div>
  );
};
