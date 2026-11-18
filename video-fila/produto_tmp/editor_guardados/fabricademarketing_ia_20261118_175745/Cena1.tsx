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

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Subtle continuous push-in on presenter
  const videoScale = interpolate(frame, [0, 230], [1.00, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Entrance animations for top graphics (strictly above presenter's head)
  const badgeSpring = spring({
    frame: frame - 22,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const headlineSpring = spring({
    frame: frame - 64,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const subPillSpring = spring({
    frame: frame - 135,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Exit transition for graphics
  const exitOpacity = interpolate(frame, [214, 230], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitSlide = interpolate(frame, [214, 230], [0, -30], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Presenter Video with gentle scale */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 45%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Top Header Shading - strictly confined to y=0..420 to protect face naturally */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 420,
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.85) 0%, rgba(17,24,39,0.55) 60%, rgba(17,24,39,0.0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Graphic Information Container (strictly y=165..400) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          opacity: exitOpacity,
          transform: `translateY(${exitSlide}px)`,
          zIndex: 10,
        }}
      >
        {/* Rótulo Badge */}
        {badgeSpring > 0.01 && (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '6px 18px',
              borderRadius: 20,
              backgroundColor: 'rgba(17, 24, 39, 0.92)',
              border: '1.5px solid #F472B6',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5)',
              transform: `scale(${badgeSpring})`,
              marginBottom: 10,
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: '#F472B6',
                boxShadow: '0 0 6px #F472B6',
              }}
            />
            <span
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: '#F472B6',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              O Problema
            </span>
          </div>
        )}

        {/* Headline */}
        {headlineSpring > 0.01 && (
          <div
            style={{
              fontSize: 46,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.15,
              textShadow: '0 4px 16px rgba(0, 0, 0, 0.95)',
              textWrap: 'balance',
              transform: `translateY(${(1 - headlineSpring) * 15}px)`,
              opacity: headlineSpring,
            }}
          >
            INTERROMPER ATENDIMENTO
          </div>
        )}

        {/* Sub-Pill */}
        {subPillSpring > 0.01 && (
          <div
            style={{
              marginTop: 10,
              padding: '6px 20px',
              borderRadius: 14,
              backgroundColor: 'rgba(17, 24, 39, 0.88)',
              border: '1.5px solid rgba(244, 114, 182, 0.6)',
              transform: `scale(${subPillSpring})`,
            }}
          >
            <span
              style={{
                fontSize: 34,
                fontWeight: 700,
                color: '#F472B6',
                letterSpacing: 0.5,
              }}
            >
              Agendamento manual de posts
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
