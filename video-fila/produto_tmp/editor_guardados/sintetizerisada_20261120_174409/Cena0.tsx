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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous Ken Burns push-in from 1.0 to 1.08 across the entire hook scene (157 frames)
  const bgScale = interpolate(frame, [0, 157], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 157], [0, -15], {
    extrapolateRight: 'clamp',
  });

  // Entrance springs
  const titleSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  const highlightSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Notification card enters during the first second (starts at frame 6) with downward slide & elastic spring overshoot
  const cardSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Continuous micro-movement and slow zoom on the card to prevent any static feel
  const cardFloat = Math.sin(frame / 10) * 5;
  const cardZoom = interpolate(frame, [0, 157], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Haptic vibration upon arrival (frames 10 to 22)
  const hapticVibration =
    frame >= 10 && frame <= 22
      ? Math.sin((frame - 10) * 2.2) * 4 * (1 - (frame - 10) / 13)
      : 0;

  const alertPulse = 1 + Math.sin(frame / 6) * 0.02;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0F172A',
        overflow: 'hidden',
      }}
    >
      {/* Background Image: 100% full bleed vertical (1080x1920), object-fit: cover, no letterbox/pillarbox */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
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

      {/* Gentle dark overlay ensuring high text readability and immersive feel */}
      <AbsoluteFill
        style={{
          background: 'rgba(15, 23, 42, 0.40)',
          pointerEvents: 'none',
        }}
      />

      {/* Soft top gradient ensuring clear headline readability */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 380,
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.88) 0%, rgba(15,23,42,0.50) 70%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Unified Kinetic Headline Area (y: 190 - 430) */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 10,
        }}
      >
        {/* Title line 1: CLIENTE CANCELA */}
        <div
          style={{
            transform: `translateY(${interpolate(titleSpring, [0, 1], [30, 0])}px) scale(${titleSpring})`,
            opacity: titleSpring,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 56,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-0.5px',
              textTransform: 'uppercase',
              textShadow: '0 4px 18px rgba(0,0,0,0.85)',
            }}
          >
            Cliente cancela
          </span>
        </div>

        {/* Title line 2: DE MADRUGADA - Solid pill containing full text */}
        <div
          style={{
            marginTop: 12,
            transform: `translateY(${interpolate(highlightSpring, [0, 1], [25, 0])}px) scale(${highlightSpring})`,
            opacity: highlightSpring,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#FFA94D',
              borderRadius: 18,
              padding: '8px 36px',
              minWidth: 440,
              boxSizing: 'border-box',
              boxShadow: '0 10px 30px rgba(255, 169, 77, 0.45)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 58,
                fontWeight: 900,
                color: '#1F2937',
                letterSpacing: '-0.5px',
                textTransform: 'uppercase',
                whiteSpace: 'nowrap',
              }}
            >
              de madrugada
            </span>
          </div>
        </div>
      </div>

      {/* Enlarged Smartphone Lockscreen Notification Card (y: 460 - 920) */}
      <div
        style={{
          position: 'absolute',
          top: 460,
          left: 50,
          right: 50,
          transform: `translateY(${interpolate(cardSpring, [0, 1], [-220, 0]) + cardFloat}px) translateX(${hapticVibration}px) scale(${cardSpring * cardZoom})`,
          opacity: cardSpring,
          zIndex: 15,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(31, 41, 55, 0.96)',
            borderRadius: 32,
            border: '2px solid rgba(255, 255, 255, 0.22)',
            padding: '28px 32px',
            boxShadow:
              '0 28px 60px rgba(0, 0, 0, 0.8), 0 0 30px rgba(255, 169, 77, 0.25)',
            backdropFilter: 'blur(16px)',
          }}
        >
          {/* Card Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 18,
              borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
              paddingBottom: 14,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: 16,
                  backgroundColor: '#25D366',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  color: '#FFFFFF',
                  fontWeight: 900,
                  boxShadow: '0 4px 14px rgba(37, 211, 102, 0.45)',
                }}
              >
                💬
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 40,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Mensagem recebida
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 700,
                    color: '#E2E8F0',
                    marginTop: 2,
                  }}
                >
                  Cliente • Horário 09:00
                </div>
              </div>
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#FFA94D',
                backgroundColor: 'rgba(255, 169, 77, 0.25)',
                padding: '8px 20px',
                borderRadius: 14,
                border: '2px solid #FFA94D',
              }}
            >
              02:47
            </div>
          </div>

          {/* Card Message Body */}
          <div
            style={{
              fontFamily,
              fontSize: 44,
              fontWeight: 800,
              color: '#FFFFFF',
              lineHeight: 1.35,
              marginBottom: 20,
            }}
          >
            “Não vou conseguir ir amanhã cedo.”
          </div>

          {/* High-Contrast Status Alert Banner */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              backgroundColor: '#B91C1C',
              border: '2px solid #FCA5A5',
              borderRadius: 18,
              padding: '16px 24px',
              boxShadow: '0 6px 24px rgba(220, 38, 38, 0.5)',
              transform: `scale(${alertPulse})`,
            }}
          >
            <span style={{fontSize: 38}}>⚠️</span>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                fontFamily,
                fontSize: 36,
                fontWeight: 900,
                color: '#FEF08A',
                letterSpacing: '-0.3px',
                lineHeight: 1.25,
              }}
            >
              <div>Horário vago sem</div>
              <div>ninguém para atender</div>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
