import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig, Img, staticFile} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background zoom - continuous and smooth
  const bgScale = interpolate(frame, [0, 135], [1.0, 1.07], {
    extrapolateRight: 'clamp',
  });

  // Subtle floating effect
  const floatY = Math.sin(frame / 12) * 5;

  // Title entrance
  const titleSpring = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Comment card 1 entrance: IMMEDIATE AT 0.3s (frame 9) for fast visual retention hook!
  const card1Spring = spring({
    frame: Math.max(0, frame - 9),
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Comment card 2 entrance (at ~1.15s -> frame 35, "comentam")
  const card2Spring = spring({
    frame: Math.max(0, frame - 35),
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Alert Badge entrance (at ~2.15s -> frame 65, "sem resposta")
  const alertSpring = spring({
    frame: Math.max(0, frame - 65),
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Alert dynamic glow pulse
  const alertGlowPulse = 0.35 + 0.25 * Math.sin(frame / 4.5);

  // Gancho pill entrance (at ~3.0s -> frame 90)
  const ganchoSpring = spring({
    frame: Math.max(0, frame - 90),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Continuous content slow zoom (1.0 to 1.04) to maintain active camera movement throughout
  const contentScale = interpolate(frame, [0, 135], [1.0, 1.04], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        transform: `scale(${contentScale})`,
        transformOrigin: 'center 45%',
      }}
    >
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
          src={staticFile('img_0.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
        {/* Dark brand vignette */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at center, rgba(17, 24, 39, 0.35) 0%, rgba(17, 24, 39, 0.88) 100%)',
          }}
        />
      </div>

      {/* Ambient dynamic glowing orbs */}
      <div
        style={{
          position: 'absolute',
          width: 550,
          height: 550,
          borderRadius: '50%',
          background: 'rgba(244, 114, 182, 0.20)',
          filter: 'blur(95px)',
          top: 320 + Math.sin(frame / 15) * 35,
          left: 260 + Math.cos(frame / 18) * 45,
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 400,
          height: 400,
          borderRadius: '50%',
          background: 'rgba(59, 130, 246, 0.15)',
          filter: 'blur(80px)',
          top: 680 + Math.cos(frame / 16) * 30,
          right: 80 + Math.sin(frame / 14) * 35,
          pointerEvents: 'none',
        }}
      />

      {/* Top Section (y: 170 - 460) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `translateY(${(1 - titleSpring) * -30}px)`,
          opacity: titleSpring,
        }}
      >
        {/* Top category badge */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 24px',
            borderRadius: 30,
            background: 'rgba(244, 114, 182, 0.18)',
            border: '1px solid rgba(244, 114, 182, 0.45)',
            marginBottom: 16,
          }}
        >
          <span style={{fontSize: 28}}>💬</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#F472B6',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            Atenção aos comentários
          </span>
        </div>

        {/* Main Title Question (speech of this scene) */}
        <div
          style={{
            fontFamily,
            fontSize: 50,
            fontWeight: 900,
            color: '#FFFFFF',
            textAlign: 'center',
            lineHeight: 1.2,
            textWrap: 'balance',
            textShadow: '0 4px 18px rgba(0,0,0,0.9)',
          }}
        >
          Seus seguidores comentam e ficam{' '}
          <span
            style={{
              color: '#F472B6',
              background: 'rgba(244, 114, 182, 0.22)',
              padding: '2px 14px',
              borderRadius: 12,
              borderBottom: '4px solid #F472B6',
              whiteSpace: 'nowrap',
            }}
          >
            sem resposta?
          </span>
        </div>

        {/* Gancho pill (appears after dor) */}
        {frame >= 90 && (
          <div
            style={{
              marginTop: 18,
              padding: '8px 26px',
              borderRadius: 24,
              background: 'rgba(17, 24, 39, 0.9)',
              border: '1.5px solid rgba(244, 114, 182, 0.6)',
              transform: `scale(${ganchoSpring})`,
              opacity: ganchoSpring,
              boxShadow: '0 4px 20px rgba(244, 114, 182, 0.25)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
              }}
            >
              ⚡ Comentários viram clientes?
            </span>
          </div>
        )}
      </div>

      {/* Middle Section: Follower Comments Stack (y: 550 - 1260) */}
      <div
        style={{
          position: 'absolute',
          top: 550,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 24,
        }}
      >
        {/* Comment Card 1 - Enters at 0.3s (frame 9) */}
        {frame >= 8 && (
          <div
            style={{
              background: 'rgba(17, 24, 39, 0.88)',
              border: '1.5px solid rgba(255, 255, 255, 0.14)',
              borderRadius: 24,
              padding: '22px 28px',
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.7)',
              transform: `scale(${0.94 + 0.06 * card1Spring}) translateY(${(1 - card1Spring) * 35 + floatY}px)`,
              opacity: card1Spring,
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily,
                    fontSize: 26,
                    fontWeight: 900,
                    color: '#FFFFFF',
                  }}
                >
                  M
                </div>
                <div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    @marcos.silva
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      color: '#94A3B8',
                    }}
                  >
                    há 2 horas
                  </div>
                </div>
              </div>

              {/* Status Tag */}
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid rgba(239, 68, 68, 0.5)',
                  padding: '6px 16px',
                  borderRadius: 14,
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#F87171',
                }}
              >
                Sem resposta
              </div>
            </div>

            <div
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 600,
                color: '#E2E8F0',
                lineHeight: 1.3,
              }}
            >
              &quot;Como funciona a postagem automática? Qual o valor?&quot;
            </div>
          </div>
        )}

        {/* Comment Card 2 - Enters at 1.15s (frame 35) */}
        {frame >= 34 && (
          <div
            style={{
              background: 'rgba(17, 24, 39, 0.88)',
              border: '1.5px solid rgba(255, 255, 255, 0.14)',
              borderRadius: 24,
              padding: '22px 28px',
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.7)',
              transform: `scale(${0.94 + 0.06 * card2Spring}) translateY(${(1 - card2Spring) * 35 + floatY * -1}px)`,
              opacity: card2Spring,
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #3B82F6 0%, #10B981 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily,
                    fontSize: 26,
                    fontWeight: 900,
                    color: '#FFFFFF',
                  }}
                >
                  C
                </div>
                <div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    @carla.consultoria
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      color: '#94A3B8',
                    }}
                  >
                    há 4 horas
                  </div>
                </div>
              </div>

              {/* Status Tag */}
              <div
                style={{
                  background: 'rgba(245, 158, 11, 0.2)',
                  border: '1px solid rgba(245, 158, 11, 0.5)',
                  padding: '6px 16px',
                  borderRadius: 14,
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FBBF24',
                }}
              >
                Pendente ⏳
              </div>
            </div>

            <div
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 600,
                color: '#E2E8F0',
                lineHeight: 1.3,
              }}
            >
              &quot;Quero saber mais sobre blog com SEO e podcast!&quot;
            </div>
          </div>
        )}

        {/* Alert Callout on Dor - Enters at 2.15s (frame 65) */}
        {frame >= 64 && (
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.22) 0%, rgba(244, 114, 182, 0.22) 100%)',
              border: '2px solid rgba(244, 114, 182, 0.65)',
              borderRadius: 22,
              padding: '18px 24px',
              transform: `scale(${0.92 + 0.08 * alertSpring}) translateY(${(1 - alertSpring) * 20}px)`,
              opacity: alertSpring,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              boxShadow: `0 8px 28px rgba(239, 68, 68, ${alertGlowPulse})`,
            }}
          >
            <span style={{fontSize: 34}}>⚠️</span>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
              }}
            >
              Comentário não respondido = cliente perdido!
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
