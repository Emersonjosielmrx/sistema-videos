import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES} from './constants';

interface Cena2Props {
  fontFamily: string;
}

export const Cena2: React.FC<Cena2Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Presenter video:
  // Escala elevada (1.48x) para garantir que com translateX(240px) para a direita,
  // a margem esquerda continue com sobra de quase 20px de vídeo, ELIMINANDO completamente qualquer fresta preta.
  // Desloca o apresentador confortavelmente para a direita (0 a 240px), deixando >150px de vão livre para o smartphone.
  const shiftX = interpolate(frame, [35, 60], [0, 240], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const videoScale = interpolate(frame, [0, 191], [1.48, 1.52], {
    extrapolateRight: 'clamp',
  });

  // Top Rótulo Badge entrance
  const badgeSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Step 1 activation: frame 25 ("A landing page pronta")
  const step1Active = frame >= 25;
  const step1Spring = spring({
    frame: frame - 25,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Step 2 activation: frame 75 ("com vídeo demo")
  const step2Active = frame >= 75;
  const step2Spring = spring({
    frame: frame - 75,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Step 3 activation: frame 134 ("retém a atenção")
  const step3Active = frame >= 134;
  const step3Spring = spring({
    frame: frame - 134,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Smartphone Mockup entrance: entra suavemente a partir do frame 45 (13.6s)
  const mockupSpring = spring({
    frame: frame - 45,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Micro-floating effect for header container
  const floatY = Math.sin(frame * 0.08) * 3;

  // Mockup floating micro-motion (contínuo)
  const mockupFloatY = Math.sin(frame * 0.12) * 6;

  // Interactive page scroll inside mockup
  const pageScrollY = interpolate(frame, [60, 190], [0, 50], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Continuous active sound/demo video equalizer bars
  const wave1 = 18 + Math.sin(frame * 0.35) * 14;
  const wave2 = 24 + Math.sin(frame * 0.4 + 1.2) * 16;
  const wave3 = 20 + Math.sin(frame * 0.32 + 2.4) * 12;
  const wave4 = 28 + Math.sin(frame * 0.38 + 3.6) * 15;
  const wave5 = 16 + Math.sin(frame * 0.3 + 4.8) * 10;

  // Video scrubber timeline progress (0% to 100% loop)
  const videoProgress = ((frame * 1.5) % 100);

  // Play button glow pulse
  const playPulse = 1 + Math.sin(frame * 0.22) * 0.08;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0B0D13',
        fontFamily,
      }}
    >
      {/* Fullscreen Presenter Video: scale 1.42x com translateX de 190px mantém o canvas 100% preenchido sem faixa preta */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateX(${shiftX}px) translateY(40px) scale(${videoScale})`,
          transformOrigin: 'center 40%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_2.mp4')}
          muted
          style={{
            width: 1080,
            height: 1920,
            objectFit: 'cover',
          }}
        />
        {/* Subtle top darkening exclusively under the top bar for maximum contrast */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 320,
            background:
              'linear-gradient(180deg, rgba(11, 13, 19, 0.85) 0%, rgba(11, 13, 19, 0.35) 75%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Realistic Smartphone Mockup Demonstrating Real Agency Landing Page with Active Video Demo */}
      {/* Posicionado em left: 40px com largura ultra-compacta de 295px (termina em x=335px).
          Com o apresentador deslocado para a direita em 240px (orelha/óculos em x=510px),
          existe um vão livre seguro de >170px, garantindo que NUNCA invada o rosto do apresentador. */}
      {frame >= 40 && (
        <div
          style={{
            position: 'absolute',
            top: 360,
            left: 40,
            width: 295,
            height: 600,
            borderRadius: 36,
            background: '#0B0D13',
            border: `2.5px solid rgba(255, 255, 255, 0.3)`,
            boxShadow: `0 25px 60px rgba(0, 0, 0, 0.95), 0 0 35px ${CORES.marcaGlow}`,
            transform: `perspective(1000px) rotateY(12deg) scale(${Math.max(
              0,
              mockupSpring
            )}) translateY(${mockupFloatY}px)`,
            opacity: Math.min(1, Math.max(0, mockupSpring)),
            overflow: 'hidden',
            zIndex: 42,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Dynamic Island / Top Notch */}
          <div
            style={{
              position: 'relative',
              height: 32,
              background: '#090A0F',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0 16px',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
              zIndex: 10,
            }}
          >
            {/* Clock */}
            <span
              style={{
                position: 'absolute',
                left: 18,
                fontSize: 16,
                fontWeight: 700,
                color: '#94A3B8',
              }}
            >
              09:41
            </span>
            {/* Notch pill */}
            <div
              style={{
                width: 72,
                height: 14,
                borderRadius: 7,
                backgroundColor: '#000000',
                border: '1px solid rgba(255,255,255,0.1)',
              }}
            />
            {/* Battery & 5G */}
            <span
              style={{
                position: 'absolute',
                right: 18,
                fontSize: 16,
                color: '#94A3B8',
                fontWeight: 700,
              }}
            >
              5G 🔋
            </span>
          </div>

          {/* Landing Page Content Window (simula scroll real de tela) */}
          <div
            style={{
              flex: 1,
              background: 'linear-gradient(180deg, #120D1A 0%, #0B0D13 100%)',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              position: 'relative',
            }}
          >
            {/* Scrollable Container */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 14,
                padding: '16px 14px',
                transform: `translateY(-${pageScrollY}px)`,
              }}
            >
              {/* Agency Brand Bar inside Landing Page */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingBottom: 8,
                  borderBottom: '1px solid rgba(255,255,255,0.1)',
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
                  <div
                    style={{
                      width: 14,
                      height: 14,
                      borderRadius: 4,
                      background: CORES.marca,
                    }}
                  />
                  <span
                    style={{
                      fontSize: 18,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      letterSpacing: 0.5,
                    }}
                  >
                    INOVARE SITES
                  </span>
                </div>
                <div
                  style={{
                    background: 'rgba(236,72,153,0.2)',
                    borderRadius: 6,
                    padding: '2px 8px',
                    border: `1px solid ${CORES.marca}`,
                  }}
                >
                  <span
                    style={{
                      fontSize: 14,
                      fontWeight: 800,
                      color: '#F472B6',
                    }}
                  >
                    DEMO
                  </span>
                </div>
              </div>

              {/* Landing Page Hero Text */}
              <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                <span
                  style={{
                    fontSize: 22,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                    lineHeight: 1.15,
                    letterSpacing: -0.2,
                  }}
                >
                  PÁGINA PRONTA QUE VENDE
                </span>
                <span
                  style={{
                    fontSize: 16,
                    fontWeight: 700,
                    color: '#F472B6',
                    textTransform: 'uppercase',
                  }}
                >
                  VÍDEO DEMO DO SEU PRODUTO
                </span>
              </div>

              {/* REALISTIC ACTIVE VIDEO DEMO PLAYER */}
              <div
                style={{
                  borderRadius: 18,
                  background: 'linear-gradient(145deg, #1F102B 0%, #0D0B18 100%)',
                  border: '2px solid rgba(236, 72, 153, 0.7)',
                  padding: '14px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 10,
                  boxShadow: '0 8px 24px rgba(0,0,0,0.8)',
                  position: 'relative',
                }}
              >
                {/* Video Demo Player Screen */}
                <div
                  style={{
                    height: 140,
                    borderRadius: 12,
                    background: 'linear-gradient(135deg, #2A1538 0%, #151028 100%)',
                    border: '1px solid rgba(255,255,255,0.12)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                >
                  {/* Subtle video shine */}
                  <div
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: '50%',
                      background:
                        'linear-gradient(180deg, rgba(255,255,255,0.08) 0%, transparent 100%)',
                    }}
                  />

                  {/* Pulsing Play Button */}
                  <div
                    style={{
                      width: 52,
                      height: 52,
                      borderRadius: '50%',
                      background: `linear-gradient(135deg, ${CORES.marca}, ${CORES.marcaDark})`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: `0 0 20px ${CORES.marcaGlow}`,
                      transform: `scale(${playPulse})`,
                      zIndex: 2,
                    }}
                  >
                    <span style={{fontSize: 22, color: '#FFFFFF', marginLeft: 3}}>▶</span>
                  </div>

                  {/* "PRODUTO EM AÇÃO" live banner */}
                  <div
                    style={{
                      position: 'absolute',
                      bottom: 8,
                      left: 10,
                      right: 10,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div
                      style={{
                        background: 'rgba(0,0,0,0.7)',
                        borderRadius: 6,
                        padding: '2px 6px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                      }}
                    >
                      <div
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          background: '#EF4444',
                        }}
                      />
                      <span
                        style={{
                          fontSize: 12,
                          fontWeight: 800,
                          color: '#FFFFFF',
                        }}
                      >
                        PRODUTO EM AÇÃO
                      </span>
                    </div>

                    {/* Animated equalizer waves */}
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'flex-end',
                        gap: 3,
                        height: 20,
                      }}
                    >
                      <div
                        style={{
                          width: 4,
                          height: wave1 * 0.6,
                          background: CORES.marca,
                          borderRadius: 2,
                        }}
                      />
                      <div
                        style={{
                          width: 4,
                          height: wave2 * 0.6,
                          background: '#F472B6',
                          borderRadius: 2,
                        }}
                      />
                      <div
                        style={{
                          width: 4,
                          height: wave3 * 0.6,
                          background: CORES.marca,
                          borderRadius: 2,
                        }}
                      />
                      <div
                        style={{
                          width: 4,
                          height: wave4 * 0.6,
                          background: '#F472B6',
                          borderRadius: 2,
                        }}
                      />
                      <div
                        style={{
                          width: 4,
                          height: wave5 * 0.6,
                          background: CORES.marca,
                          borderRadius: 2,
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Scrubber Timeline Bar (demonstrates active video playing) */}
                <div
                  style={{
                    width: '100%',
                    height: 5,
                    borderRadius: 3,
                    background: 'rgba(255,255,255,0.15)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${videoProgress}%`,
                      height: '100%',
                      background: CORES.marca,
                    }}
                  />
                </div>
              </div>

              {/* Landing Page Action Button */}
              <div
                style={{
                  background: `linear-gradient(90deg, ${CORES.marca}, #DB2777)`,
                  borderRadius: 14,
                  padding: '10px 12px',
                  textAlign: 'center',
                  boxShadow: `0 4px 14px ${CORES.marcaGlow}`,
                }}
              >
                <span
                  style={{
                    fontSize: 18,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                    letterSpacing: 0.5,
                  }}
                >
                  RETÉM A ATENÇÃO
                </span>
              </div>

              {/* Social Proof badge */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 6,
                  padding: '4px',
                }}
              >
                <span style={{fontSize: 16, color: '#FBBF24'}}>★★★★★</span>
                <span
                  style={{
                    fontSize: 15,
                    fontWeight: 800,
                    color: '#E2E8F0',
                  }}
                >
                  COMUNICAÇÃO QUE CONVERTE
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Rótulo Badge (y = 162, height = 38) */}
      <div
        style={{
          position: 'absolute',
          top: 162,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${Math.max(0, badgeSpring)})`,
          opacity: Math.max(0, badgeSpring),
          zIndex: 40,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 20px',
            borderRadius: 999,
            background: 'rgba(11, 13, 19, 0.95)',
            border: `1.5px solid ${CORES.bordaCard}`,
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.7)',
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: CORES.marca,
              boxShadow: `0 0 8px ${CORES.marca}`,
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: 2,
              color: '#F1F5F9',
              textTransform: 'uppercase',
            }}
          >
            02 • COMO FUNCIONA
          </span>
        </div>
      </div>

      {/* 3 Step Chips (y = 212 to 276, height = 64px) -> Head at y=360+ gives >80px respiro */}
      <div
        style={{
          position: 'absolute',
          top: 212,
          left: 60,
          right: 60,
          height: 64,
          display: 'flex',
          gap: 14,
          justifyContent: 'space-between',
          transform: `translateY(${floatY}px)`,
          zIndex: 40,
        }}
      >
        {/* Step 1 Chip: 1 • PÁGINA */}
        <div
          style={{
            flex: 1,
            height: '100%',
            borderRadius: 18,
            background: step1Active ? CORES.marca : 'rgba(11, 13, 19, 0.95)',
            border: step1Active
              ? '2px solid #FFFFFF'
              : '1.5px solid rgba(255, 255, 255, 0.16)',
            boxShadow: step1Active
              ? `0 6px 20px ${CORES.marcaGlow}`
              : '0 6px 16px rgba(0, 0, 0, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            padding: '0 8px',
            whiteSpace: 'nowrap',
            transform: step1Active
              ? `scale(${1 + Math.max(0, step1Spring) * 0.04})`
              : 'scale(1)',
            transition: 'background 0.25s, border 0.25s, box-shadow 0.25s',
          }}
        >
          <span style={{fontSize: 32, color: '#FFFFFF'}}>
            {step1Active ? '✓' : '1.'}
          </span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              whiteSpace: 'nowrap',
              textShadow: step1Active ? '0 2px 6px rgba(0,0,0,0.5)' : 'none',
            }}
          >
            PÁGINA
          </span>
        </div>

        {/* Step 2 Chip: 2 • VÍDEO */}
        <div
          style={{
            flex: 1,
            height: '100%',
            borderRadius: 18,
            background: step2Active ? CORES.marca : 'rgba(11, 13, 19, 0.95)',
            border: step2Active
              ? '2px solid #FFFFFF'
              : '1.5px solid rgba(255, 255, 255, 0.16)',
            boxShadow: step2Active
              ? `0 6px 20px ${CORES.marcaGlow}`
              : '0 6px 16px rgba(0, 0, 0, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            padding: '0 8px',
            whiteSpace: 'nowrap',
            transform: step2Active
              ? `scale(${1 + Math.max(0, step2Spring) * 0.04})`
              : 'scale(1)',
            transition: 'background 0.25s, border 0.25s, box-shadow 0.25s',
          }}
        >
          <span style={{fontSize: 32, color: '#FFFFFF'}}>
            {step2Active ? '✓' : '2.'}
          </span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              whiteSpace: 'nowrap',
              textShadow: step2Active ? '0 2px 6px rgba(0,0,0,0.5)' : 'none',
            }}
          >
            VÍDEO
          </span>
        </div>

        {/* Step 3 Chip: 3 • ATENÇÃO */}
        <div
          style={{
            flex: 1,
            height: '100%',
            borderRadius: 18,
            background: step3Active ? CORES.marca : 'rgba(11, 13, 19, 0.95)',
            border: step3Active
              ? '2px solid #FFFFFF'
              : '1.5px solid rgba(255, 255, 255, 0.16)',
            boxShadow: step3Active
              ? `0 6px 20px ${CORES.marcaGlow}`
              : '0 6px 16px rgba(0, 0, 0, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            padding: '0 8px',
            whiteSpace: 'nowrap',
            transform: step3Active
              ? `scale(${1 + Math.max(0, step3Spring) * 0.04})`
              : 'scale(1)',
            transition: 'background 0.25s, border 0.25s, box-shadow 0.25s',
          }}
        >
          <span style={{fontSize: 32, color: '#FFFFFF'}}>
            {step3Active ? '✓' : '3.'}
          </span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              whiteSpace: 'nowrap',
              textShadow: step3Active ? '0 2px 6px rgba(0,0,0,0.5)' : 'none',
            }}
          >
            ATENÇÃO
          </span>
        </div>
      </div>
    </div>
  );
};
