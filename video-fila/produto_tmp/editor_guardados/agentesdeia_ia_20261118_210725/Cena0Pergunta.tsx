import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena0Pergunta: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Speech transition: at frame 60 (~2.0s), 'enquanto cuido do meu negócio' begins.
  // Punch-in camera zoom provides instant agency energy and avoids slow opening
  const isPunchZoom = frame >= 60;
  const bgScale = !isPunchZoom
    ? interpolate(frame, [0, 59], [1.05, 1.09], {extrapolateRight: 'clamp'})
    : interpolate(frame, [60, 151], [1.18, 1.24], {extrapolateRight: 'clamp'});

  // Scene exit fade
  const sceneOpacity = interpolate(frame, [138, 151], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Question card bouncy scale & slide entrance
  const questionCardSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const cardScale = interpolate(questionCardSpring, [0, 1], [0.85, 1.0]);
  const cardSlideY = interpolate(questionCardSpring, [0, 1], [25, 0]);

  // Subtitle smooth entrance spring
  const subtitleSpring = spring({
    frame: Math.max(0, frame - 6),
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Continuous subtle shimmer sweep across the highlight pill
  const shimmerPillProgress = (frame % 45) / 45;
  const shimmerPillX = interpolate(shimmerPillProgress, [0, 1], [-160, 480]);

  // Subtle breathing pulse for the green highlight pill to keep eyes engaged
  const pillPulse = 1.0 + Math.sin(frame * 0.18) * 0.025;

  // Subtle floating micro-motion
  const floatY = Math.sin(frame / 12) * 3;

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
      {/* Background: Presenter naturally lit from second 0, displaced down so upper third has ample headroom */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale}) translateY(145px)`,
          transformOrigin: '50% 35%',
        }}
      >
        <Img
          src={staticFile('sample_dono_1.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />

        {/* Localized top gradient solely for text contrast behind card, leaving presenter face bright & natural */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(180deg, rgba(17, 24, 39, 0.85) 0%, rgba(17, 24, 39, 0.35) 70%, rgba(17, 24, 39, 0) 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Top Category Badge (y = 185) */}
      <div
        style={{
          position: 'absolute',
          top: 185,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: interpolate(frame, [0, 8], [0, 1]),
          zIndex: 25,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 22px',
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
              boxShadow: '0 0 10px #10B981',
            }}
          />
          <span
            style={{
              fontSize: 30,
              fontWeight: 800,
              color: '#A7F3D0',
              textTransform: 'uppercase',
              letterSpacing: 1.5,
            }}
          >
            Dúvida do Cliente
          </span>
        </div>
      </div>

      {/* Compacted Impact Question Card firmly anchored in upper third (top: 245, bottom: ~440, headroom: ~100px above hair) */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `translateY(${floatY + cardSlideY}px) scale(${cardScale})`,
          zIndex: 30,
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: 920,
            padding: '24px 30px',
            borderRadius: 26,
            background: 'rgba(17, 24, 39, 0.90)',
            border: '2px solid rgba(16, 185, 129, 0.55)',
            boxShadow:
              '0 18px 45px rgba(0, 0, 0, 0.55), 0 0 25px rgba(16, 185, 129, 0.2)',
            backdropFilter: 'blur(16px)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 14,
          }}
        >
          {/* Line 1 */}
          <span
            style={{
              fontSize: 38,
              fontWeight: 800,
              color: '#F9FAFB',
              textTransform: 'uppercase',
              letterSpacing: -0.5,
              lineHeight: 1.15,
            }}
          >
            Dá para receber a
          </span>

          {/* Line 2 with High-Impact Highlight Pill with Shimmer and Continuous Pulse */}
          <div
            style={{
              position: 'relative',
              display: 'inline-block',
              background: 'linear-gradient(135deg, #10B981, #059669)',
              padding: '10px 32px',
              borderRadius: 20,
              boxShadow:
                '0 10px 30px rgba(16, 185, 129, 0.5), 0 0 25px rgba(16, 185, 129, 0.3)',
              transform: `scale(${pillPulse})`,
              overflow: 'hidden',
            }}
          >
            {/* Shimmer sweep light reflection */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 120,
                transform: `translateX(${shimmerPillX}px) skewX(-25deg)`,
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.35), transparent)',
                pointerEvents: 'none',
              }}
            />
            <span
              style={{
                position: 'relative',
                fontSize: 48,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: -0.5,
                lineHeight: 1.1,
                textShadow: '0 2px 10px rgba(0,0,0,0.3)',
              }}
            >
              Pesquisa pronta?
            </span>
          </div>

          {/* Line 3 Context */}
          <div
            style={{
              opacity: subtitleSpring,
              transform: `translateY(${(1 - subtitleSpring) * 8}px)`,
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 700,
                color: '#A7F3D0',
                lineHeight: 1.25,
              }}
            >
              enquanto cuido do meu negócio?
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
