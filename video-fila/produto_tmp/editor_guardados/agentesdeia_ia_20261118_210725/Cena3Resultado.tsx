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

export const Cena3Resultado: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const sceneDuration = 245;

  // Switch at "e uso a manhã para cuidar..." ~ 23.3s (relative to 19.74s: ~3.5s = frame 106)
  const isPhase2 = frame >= 106;

  // Video camera scale: corte seco em enquadramento mais fechado (close-up dramático a 1.32x) na fase 2 para dar ênfase à vitória
  const videoScale = !isPhase2
    ? interpolate(frame, [0, 105], [1.10, 1.15], {extrapolateRight: 'clamp'})
    : interpolate(frame, [106, sceneDuration], [1.32, 1.38], {extrapolateRight: 'clamp'});

  const videoY = !isPhase2 ? 70 : 135;

  // Rocket icon micro-motion bounce & tilt during Phase 2
  const rocketBounce = isPhase2 ? Math.sin((frame - 106) * 0.32) * 6 : 0;
  const rocketRotate = isPhase2 ? Math.sin((frame - 106) * 0.32) * 8 : 0;

  // Continuous shimmer sweep across the card to ensure ongoing visual evolution
  const shimmerProgress = isPhase2 ? ((frame - 106) % 45) / 45 : 0;
  const shimmerX = interpolate(shimmerProgress, [0, 1], [-200, 950]);

  // Continuous growth bar fill progression (frames 110 to 220)
  const growthFill = interpolate(frame, [110, 220], [15, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

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

  // Top badge entrance
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const cardPhase1Spring = spring({
    frame: Math.max(0, frame - 8),
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const cardPhase2Spring = spring({
    frame: Math.max(0, frame - 106),
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Growth pulse animation
  const growthPulse = 1 + Math.sin(frame / 7) * 0.04;

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
      {/* Dono 3 Video: startFrom={6} eliminates the blink/half-closed right eye, showing firm gaze immediately */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${videoScale}) translateY(${videoY}px)`,
          transformOrigin: '50% 35%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          startFrom={6}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Subtle Top Gradient for readability without darkening face */}
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

      {/* Top Badge: 03 • O RESULTADO (top: 192) */}
      <div
        style={{
          position: 'absolute',
          top: 192,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: badgeSpring,
          transform: `translateY(${(1 - badgeSpring) * -15}px)`,
          zIndex: 25,
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
            border: '1.5px solid rgba(16, 185, 129, 0.7)',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: '#10B981',
              boxShadow: '0 0 10px #10B981',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#6EE7B7',
              textTransform: 'uppercase',
              letterSpacing: 1.2,
            }}
          >
            03 • O Resultado
          </span>
        </div>
      </div>

      {/* Top Dynamic Card (top: 275 ensures ≥ 100px headroom above presenter head) */}
      <div
        style={{
          position: 'absolute',
          top: 275,
          left: 60,
          right: 60,
          zIndex: 25,
        }}
      >
        {!isPhase2 ? (
          /* Phase 1: Tarefa Concluída */
          <div
            style={{
              opacity: cardPhase1Spring,
              transform: `translateY(${(1 - cardPhase1Spring) * 15}px)`,
              padding: '16px 26px',
              borderRadius: 22,
              background: 'rgba(6, 78, 59, 0.94)',
              border: '2px solid rgba(52, 211, 153, 0.7)',
              boxShadow: '0 12px 35px rgba(16, 185, 129, 0.3)',
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
                background: 'rgba(52, 211, 153, 0.25)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 32,
                color: '#34D399',
                fontWeight: 900,
                flexShrink: 0,
              }}
            >
              ✓
            </div>
            <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
              <span
                style={{
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: -0.5,
                  lineHeight: 1.15,
                }}
              >
                Tarefa concluída
              </span>
              <span
                style={{
                  fontSize: 28,
                  fontWeight: 600,
                  color: '#A7F3D0',
                  lineHeight: 1.2,
                }}
              >
                Pesquisa pronta sem perder tempo
              </span>
            </div>
          </div>
        ) : (
          /* Phase 2: Foco no crescimento com microanimações e evolução contínua */
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              opacity: cardPhase2Spring,
              transform: `scale(${growthPulse}) translateY(${(1 - cardPhase2Spring) * -10}px)`,
              padding: '16px 26px',
              borderRadius: 22,
              background: 'rgba(17, 24, 39, 0.94)',
              border: '2px solid rgba(16, 185, 129, 0.8)',
              boxShadow: '0 12px 35px rgba(16, 185, 129, 0.35)',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
            {/* Shimmer light sweep */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 140,
                transform: `translateX(${shimmerX}px) skewX(-25deg)`,
                background:
                  'linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.25), transparent)',
                pointerEvents: 'none',
              }}
            />

            <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: 14,
                  background: 'rgba(16, 185, 129, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  flexShrink: 0,
                  transform: `translateY(${rocketBounce}px) rotate(${rocketRotate}deg)`,
                }}
              >
                🚀
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 4, flex: 1}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                  <span
                    style={{
                      fontSize: 38,
                      fontWeight: 900,
                      color: '#34D399',
                      textTransform: 'uppercase',
                      letterSpacing: -0.5,
                      lineHeight: 1.15,
                    }}
                  >
                    Foco no crescimento
                  </span>
                  <span style={{fontSize: 28, color: '#10B981', fontWeight: 900}}>✓</span>
                </div>
                <span
                  style={{
                    fontSize: 28,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                  }}
                >
                  Cuidando do que faz a empresa crescer
                </span>
              </div>
            </div>

            {/* Micro-animation: Animated Growth progress bar showing ongoing evolution */}
            <div
              style={{
                width: '100%',
                height: 6,
                borderRadius: 999,
                background: 'rgba(255, 255, 255, 0.1)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${growthFill}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, #10B981, #34D399)',
                  boxShadow: '0 0 8px #10B981',
                }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
