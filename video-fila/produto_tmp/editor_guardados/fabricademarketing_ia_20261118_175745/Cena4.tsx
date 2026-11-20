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

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background camera motion
  const bgScale = interpolate(frame, [0, 119], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Entrance animations
  const brandSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const productSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const btnSpring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Continuous breathing pulse for CTA button (rule: scale 1.00 to 1.08 until final frame)
  const buttonPulse = 1.04 + 0.04 * Math.sin(frame * 0.18);

  // Moving shimmer light over CTA button
  const shimmerPos = interpolate(frame % 40, [0, 40], [-250, 650]);

  // Ambient floating gradient orbs
  const orb1Y = Math.sin(frame * 0.08) * 30;
  const orb2Y = Math.cos(frame * 0.07) * 25;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Blurred background photo with push-in */}
      <div
        style={{
          position: 'absolute',
          inset: -40,
          transform: `scale(${bgScale})`,
          filter: 'blur(35px)',
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Dark branded overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundColor: 'rgba(17, 24, 39, 0.88)',
        }}
      />

      {/* Dynamic Ambient Glowing Orbs */}
      <div
        style={{
          position: 'absolute',
          top: 350 + orb1Y,
          left: -100,
          width: 500,
          height: 500,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(244,114,182,0.22) 0%, rgba(244,114,182,0) 70%)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 850 + orb2Y,
          right: -100,
          width: 550,
          height: 550,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(244,114,182,0.18) 0%, rgba(244,114,182,0) 70%)',
          pointerEvents: 'none',
        }}
      />

      {/* Main Content Container inside safe zone */}
      <div
        style={{
          position: 'absolute',
          top: 240,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 10,
        }}
      >
        {/* Brand Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '10px 24px',
            borderRadius: 30,
            backgroundColor: 'rgba(255, 255, 255, 0.07)',
            border: '1.5px solid rgba(244, 114, 182, 0.5)',
            transform: `scale(${brandSpring})`,
            marginBottom: 35,
          }}
        >
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: 10,
              backgroundColor: '#F472B6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path
                d="M13 2L3 14H12L11 22L21 10H12L13 2Z"
                fill="#111827"
                stroke="#111827"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <span
            style={{
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1,
            }}
          >
            Fábrica de Marketing IA
          </span>
        </div>

        {/* Product Name & Tagline */}
        <div
          style={{
            transform: `scale(${productSpring}) translateY(${(1 - productSpring) * 20}px)`,
            opacity: productSpring,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              fontSize: 58,
              fontWeight: 900,
              color: '#F472B6',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
              textShadow: '0 0 35px rgba(244, 114, 182, 0.5)',
              lineHeight: 1.1,
            }}
          >
            FÁBRICA DE CONTEÚDO
          </div>

          <div
            style={{
              marginTop: 18,
              fontSize: 38,
              fontWeight: 600,
              color: '#E2E8F0',
              lineHeight: 1.35,
              maxWidth: 820,
              textShadow: '0 4px 16px rgba(0,0,0,0.8)',
            }}
          >
            Da ideia à postagem automática
          </div>

          {/* Pillars from briefing facts */}
          <div
            style={{
              marginTop: 26,
              display: 'flex',
              gap: 12,
              flexWrap: 'wrap',
              justifyContent: 'center',
            }}
          >
            {['Blog SEO', 'Podcast', 'Full Post'].map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '8px 18px',
                  borderRadius: 14,
                  backgroundColor: 'rgba(17, 24, 39, 0.85)',
                  border: '1.5px solid rgba(244, 114, 182, 0.4)',
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#F472B6',
                  }}
                >
                  ✓ {item}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Call to Action Button (Continuous Pulse) */}
        <div
          style={{
            marginTop: 80,
            transform: `scale(${btnSpring * buttonPulse})`,
            position: 'relative',
          }}
        >
          <div
            style={{
              width: 580,
              padding: '26px 36px',
              borderRadius: 26,
              background: 'linear-gradient(90deg, #F472B6 0%, #FB7185 100%)',
              boxShadow: '0 12px 45px rgba(244, 114, 182, 0.65)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Shimmer sweep effect */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shimmerPos,
                width: 120,
                background:
                  'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.45) 50%, rgba(255,255,255,0) 100%)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontSize: 46,
                fontWeight: 900,
                color: '#111827',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              CHAME NO DIRECT
            </span>

            <svg width="34" height="34" viewBox="0 0 24 24" fill="none">
              <path
                d="M5 12H19M19 12L12 5M19 12L12 19"
                stroke="#111827"
                strokeWidth="3.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
        </div>

        {/* Handle Profile - Always visible from frame 0 */}
        <div
          style={{
            marginTop: 70,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 30px',
            borderRadius: 30,
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
            border: '1.5px solid rgba(255, 255, 255, 0.22)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)',
          }}
        >
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <rect
              x="2"
              y="2"
              width="20"
              height="20"
              rx="5"
              stroke="#F472B6"
              strokeWidth="2.2"
            />
            <path
              d="M16 11.37A4 4 0 1112.63 8 4 4 0 0116 11.37Z"
              stroke="#F472B6"
              strokeWidth="2.2"
            />
            <circle cx="17.5" cy="6.5" r="1.5" fill="#F472B6" />
          </svg>
          <span
            style={{
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1,
            }}
          >
            @fabricademarketing.ia
          </span>
        </div>
      </div>
    </div>
  );
};
