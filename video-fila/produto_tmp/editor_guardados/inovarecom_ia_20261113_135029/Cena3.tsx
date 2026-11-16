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

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Push-in punch zoom (5% to 8%) synchronized with "quantos contatos precisamos" (~frame 43 / 20.34s)
  // Solves Problem 10: ritmo arrastado & punch-in focal
  const punchSpring = spring({
    frame: frame - 43,
    fps,
    config: {damping: 14, stiffness: 180},
  });

  // Base video scale: 1.20 so translating down by 170px leaves generous headroom without top black border
  const baseScale = 1.18 + interpolate(frame, [0, 241], [0, 0.04], {
    extrapolateRight: 'clamp',
  });
  const videoScale = baseScale + punchSpring * 0.06;

  // Video repositioned down (+165px) to provide ample headroom above speaker's hair (Solves Problem 6)
  const videoPanY = 165 + punchSpring * 8;

  // Top tag entrance (frame 4)
  const tagSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Top card entrance (frame 10)
  const cardSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Motion graphic badge entrance synchronized with "quantos contatos precisamos" (frame 43)
  const stickerSpring = spring({
    frame: frame - 43,
    fps,
    config: {damping: 13, stiffness: 150},
  });

  // Dynamic banner reaction to focal point
  const bannerScale = 1.0 + punchSpring * 0.03;
  const cardFloat = Math.sin(frame / 12) * 3;
  const pulseIcon = 1 + Math.sin(frame / 5) * 0.08;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#061D0F',
        fontFamily,
      }}
    >
      {/* Reframed Owner Video with Generous Headroom and Dynamic Punch-In (Solves Problems 6 & 10) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale}) translateY(${videoPanY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Subtle top vignette strictly behind top graphics */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 420,
            background:
              'linear-gradient(180deg, rgba(6, 29, 15, 0.94) 0%, rgba(6, 29, 15, 0.45) 60%, rgba(6, 29, 15, 0) 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Top Tag Pill (y=165) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: tagSpring,
          transform: `scale(${tagSpring})`,
          zIndex: 10,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 22px',
            borderRadius: 30,
            background: 'rgba(8, 46, 22, 0.95)',
            border: '2px solid rgba(37, 211, 102, 0.65)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.55)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#25D366',
              boxShadow: '0 0 10px #25D366',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#25D366',
              letterSpacing: 2,
            }}
          >
            O RESULTADO REAL
          </span>
        </div>
      </div>

      {/* Raised & Compact Top Informative Banner (y=215 to 305) */}
      <div
        style={{
          position: 'absolute',
          top: 215,
          left: 60,
          right: 60,
          opacity: cardSpring,
          transform: `translateY(${(1 - cardSpring) * 20 + cardFloat}px) scale(${bannerScale})`,
          zIndex: 10,
        }}
      >
        <div
          style={{
            borderRadius: 20,
            padding: '12px 24px',
            backgroundColor: 'rgba(8, 38, 18, 0.94)',
            backdropFilter: 'blur(16px)',
            border: '2px solid rgba(37, 211, 102, 0.6)',
            boxShadow: '0 12px 34px rgba(0, 0, 0, 0.6)',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            gap: 6,
          }}
        >
          <div
            style={{
              fontSize: 38,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1,
              textShadow: '0 3px 12px rgba(0,0,0,0.85)',
            }}
          >
            ESCALA TOTAL NO WHATSAPP
          </div>
          <div
            style={{
              fontSize: 32,
              fontWeight: 700,
              color: '#25D366',
              letterSpacing: 0.5,
            }}
          >
            Sem sobrecarregar a equipe comercial
          </div>
        </div>
      </div>

      {/* Dynamic Animated Motion Graphic Badge (y=315 to 365, leaving clear headroom above hair) */}
      {/* Solves Problem 10: motion graphics pop at "quantos contatos precisamos" while keeping face 100% free */}
      {frame >= 42 && (
        <div
          style={{
            position: 'absolute',
            top: 315,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: stickerSpring,
            transform: `scale(${stickerSpring}) translateY(${cardFloat}px)`,
            zIndex: 10,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '6px 20px',
              borderRadius: 24,
              backgroundColor: 'rgba(6, 32, 16, 0.95)',
              border: '2px solid rgba(37, 211, 102, 0.75)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6), 0 0 16px rgba(37, 211, 102, 0.35)',
            }}
          >
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 9,
                backgroundColor: '#25D366',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transform: `scale(${pulseIcon})`,
              }}
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#121216"
                strokeWidth="2.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
              </svg>
            </div>
            <span style={{fontSize: 32, fontWeight: 900, color: '#FFFFFF'}}>
              Escala Ativa no WhatsApp
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
