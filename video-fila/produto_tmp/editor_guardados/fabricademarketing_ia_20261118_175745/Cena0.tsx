import React from 'react';
import {
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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background camera motion (push-in + pan)
  const bgScale = interpolate(frame, [0, 148], [1.02, 1.15], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 148], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Entrance animations for typography
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const title1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const title2Spring = spring({
    frame: frame - 28,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  const title3Spring = spring({
    frame: frame - 53,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Alert card animation at 3.0s (frame 90)
  const cardSpring = spring({
    frame: frame - 90,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Scene exit fade
  const exitOpacity = interpolate(frame, [135, 148], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Continuous micro-pulse for warning element
  const warningPulse = 1 + 0.1 * Math.sin(frame * 0.25);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        opacity: exitOpacity,
        fontFamily,
      }}
    >
      {/* Background Image with continuous motion */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateX(${bgTranslateX}px)`,
          transformOrigin: '70% 35%',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Cinematic Vignette protecting text and highlighting the subject */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(135deg, rgba(17,24,39,0.92) 0%, rgba(17,24,39,0.76) 38%, rgba(17,24,39,0.20) 72%, rgba(17,24,39,0.65) 100%)',
        }}
      />

      {/* Top Left Text Container - carefully sized to avoid presenter's face */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 70,
          maxWidth: 620,
          zIndex: 10,
        }}
      >
        {/* Category Badge */}
        {badgeSpring > 0.01 && (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 18px',
              borderRadius: 30,
              backgroundColor: 'rgba(17, 24, 39, 0.90)',
              border: '1.5px solid rgba(244, 114, 182, 0.7)',
              boxShadow: '0 4px 15px rgba(0, 0, 0, 0.4)',
              transform: `scale(${badgeSpring})`,
              transformOrigin: 'left center',
              marginBottom: 16,
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: '#F472B6',
                boxShadow: '0 0 8px #F472B6',
              }}
            />
            <span
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: '#F472B6',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              Rotina Manual
            </span>
          </div>
        )}

        {/* Question Title Line 1 */}
        {title1Spring > 0.01 && (
          <div
            style={{
              fontSize: 54,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.15,
              textShadow: '0 4px 16px rgba(0,0,0,0.8)',
              transform: `translateY(${(1 - title1Spring) * 20}px)`,
              opacity: title1Spring,
            }}
          >
            CANSADO DE
          </div>
        )}

        {/* Question Title Line 2 - Key phrase highlighted */}
        {title2Spring > 0.01 && (
          <div
            style={{
              marginTop: 10,
              transform: `scale(${title2Spring}) translateY(${(1 - title2Spring) * 15}px)`,
              transformOrigin: 'left center',
            }}
          >
            <span
              style={{
                display: 'inline-block',
                fontSize: 58,
                fontWeight: 900,
                color: '#111827',
                backgroundColor: '#F472B6',
                padding: '6px 20px',
                borderRadius: 14,
                boxShadow: '0 8px 24px rgba(244, 114, 182, 0.45)',
                letterSpacing: -0.5,
              }}
            >
              PARAR TUDO?
            </span>
          </div>
        )}

        {/* Question Title Line 3 */}
        {title3Spring > 0.01 && (
          <div
            style={{
              marginTop: 18,
              fontSize: 44,
              fontWeight: 800,
              color: '#F1F5F9',
              lineHeight: 1.2,
              textShadow: '0 4px 16px rgba(0,0,0,0.9)',
              transform: `translateY(${(1 - title3Spring) * 15}px)`,
              opacity: title3Spring,
            }}
          >
            PRA SUBIR ARTE E LEGENDA?
          </div>
        )}
      </div>

      {/* Floating Pain Alert Card on the left (clear of the man on the right) */}
      {cardSpring > 0.01 && (
        <div
          style={{
            position: 'absolute',
            top: 720,
            left: 70,
            width: 480,
            padding: '20px 24px',
            borderRadius: 22,
            backgroundColor: 'rgba(17, 24, 39, 0.88)',
            border: '1.5px solid rgba(239, 68, 68, 0.45)',
            boxShadow: '0 12px 32px rgba(0, 0, 0, 0.6)',
            transform: `scale(${cardSpring}) translateY(${(1 - cardSpring) * 30}px)`,
            zIndex: 10,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                backgroundColor: 'rgba(239, 68, 68, 0.18)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transform: `scale(${warningPulse})`,
              }}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 9V13M12 17H12.01M10.29 3.86L1.82 18A2 2 0 003.55 21H20.45A2 2 0 0022.18 18L13.71 3.86A2 2 0 0010.29 3.86Z"
                  stroke="#EF4444"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                }}
              >
                Upload Manual
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#F87171',
                  marginTop: 4,
                }}
              >
                Interrompendo seu dia
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
