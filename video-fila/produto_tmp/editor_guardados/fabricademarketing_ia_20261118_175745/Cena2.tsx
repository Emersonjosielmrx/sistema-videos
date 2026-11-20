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

  // Cinematic pan and zoom on background b-roll
  const bgScale = interpolate(frame, [0, 233], [1.02, 1.14], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 233], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Entrance springs
  const headerSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const subHeaderSpring = spring({
    frame: frame - 25,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Step 1: "ideia inicial" (~14.68s -> local frame 84)
  const step1Spring = spring({
    frame: frame - 84,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Connecting flow line (~15.4s -> frame 105)
  const lineProgress = interpolate(frame, [105, 125], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Step 2: "postagem final" (~16.05s -> local frame 125)
  const step2Spring = spring({
    frame: frame - 125,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Highlight badge: "sem intervenção manual" (~17.3s -> local frame 163)
  const badgeSpring = spring({
    frame: frame - 163,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Continuous micro-movement / pulse for flow indicator
  const pulseScale = 1 + 0.05 * Math.sin(frame * 0.2);

  // Outgoing transition
  const exitOpacity = interpolate(frame, [216, 233], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

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
      {/* Background B-roll Video with continuous pan/scale */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateX(${bgTranslateX}px)`,
          transformOrigin: '40% 50%',
        }}
      >
        <OffthreadVideo
          src={staticFile('video_2.mp4')}
          muted
          style={{
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Dark Translucent Overlay for high readability */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundColor: 'rgba(17, 24, 39, 0.82)',
        }}
      />

      {/* Top Header (y=175..280) */}
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
          zIndex: 10,
        }}
      >
        {headerSpring > 0.01 && (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '6px 20px',
              borderRadius: 20,
              backgroundColor: 'rgba(17, 24, 39, 0.92)',
              border: '1.5px solid #F472B6',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5)',
              transform: `scale(${headerSpring})`,
              marginBottom: 10,
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
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
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              Como Funciona
            </span>
          </div>
        )}

        {subHeaderSpring > 0.01 && (
          <div
            style={{
              fontSize: 44,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 0.5,
              textShadow: '0 4px 16px rgba(0,0,0,0.8)',
              transform: `translateY(${(1 - subHeaderSpring) * 15}px)`,
              opacity: subHeaderSpring,
            }}
          >
            FÁBRICA DE CONTEÚDO
          </div>
        )}
      </div>

      {/* Central Pipeline / Flow Section (y=440..1180) */}
      <div
        style={{
          position: 'absolute',
          top: 450,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 10,
        }}
      >
        {/* Step 1 Card: Da Ideia Inicial */}
        <div
          style={{
            width: '100%',
            padding: '24px 28px',
            borderRadius: 22,
            backgroundColor: 'rgba(17, 24, 39, 0.90)',
            border: '2px solid rgba(244, 114, 182, 0.45)',
            boxShadow: '0 8px 30px rgba(0, 0, 0, 0.6)',
            display: 'flex',
            alignItems: 'center',
            gap: 20,
            transform: `scale(${step1Spring}) translateY(${(1 - step1Spring) * 20}px)`,
            opacity: step1Spring,
          }}
        >
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              backgroundColor: 'rgba(244, 114, 182, 0.18)',
              border: '1.5px solid #F472B6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path
                d="M9 18H15M10 22H14M12 2A7 7 0 005 9C5 12.87 8 14.5 8 16H16C16 14.5 19 12.87 19 9A7 7 0 0012 2Z"
                stroke="#F472B6"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div>
            <div
              style={{
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.15,
              }}
            >
              1. DA IDEIA INICIAL
            </div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 600,
                color: '#CBD5E1',
                marginTop: 4,
              }}
            >
              Automação Full Post iniciada
            </div>
          </div>
        </div>

        {/* Dynamic Connector */}
        <div
          style={{
            height: 90,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            opacity: lineProgress,
          }}
        >
          <div
            style={{
              width: 4,
              height: 90 * lineProgress,
              background: 'linear-gradient(180deg, #F472B6 0%, #FB7185 100%)',
              boxShadow: '0 0 10px #F472B6',
              borderRadius: 2,
            }}
          />
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: 40,
              transform: 'translateY(-50%)',
              padding: '4px 14px',
              borderRadius: 12,
              backgroundColor: 'rgba(17, 24, 39, 0.95)',
              border: '1px solid rgba(244, 114, 182, 0.4)',
              whiteSpace: 'nowrap',
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#F472B6',
                letterSpacing: 1,
              }}
            >
              FLUXO AUTOMÁTICO
            </span>
          </div>
        </div>

        {/* Step 2 Card: Postagem Final */}
        <div
          style={{
            width: '100%',
            padding: '24px 28px',
            borderRadius: 22,
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: '2.5px solid #F472B6',
            boxShadow: '0 12px 36px rgba(244, 114, 182, 0.35)',
            display: 'flex',
            alignItems: 'center',
            gap: 20,
            transform: `scale(${step2Spring * pulseScale}) translateY(${(1 - step2Spring) * 20}px)`,
            opacity: step2Spring,
          }}
        >
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              backgroundColor: '#F472B6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              boxShadow: '0 0 14px #F472B6',
            }}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path
                d="M5 13L9 17L19 7"
                stroke="#111827"
                strokeWidth="3.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div>
            <div
              style={{
                fontSize: 44,
                fontWeight: 900,
                color: '#F472B6',
                lineHeight: 1.15,
              }}
            >
              2. POSTAGEM FINAL
            </div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 600,
                color: '#FFFFFF',
                marginTop: 4,
              }}
            >
              Publicado direto na rede
            </div>
          </div>
        </div>

        {/* Feature Pill: Sem intervenção manual */}
        {badgeSpring > 0.01 && (
          <div
            style={{
              marginTop: 40,
              padding: '14px 32px',
              borderRadius: 20,
              backgroundColor: '#F472B6',
              boxShadow: '0 8px 30px rgba(244, 114, 182, 0.55)',
              transform: `scale(${badgeSpring})`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
              <path
                d="M5 13L9 17L19 7"
                stroke="#111827"
                strokeWidth="3.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span
              style={{
                fontSize: 36,
                fontWeight: 900,
                color: '#111827',
                letterSpacing: 0.5,
                textTransform: 'uppercase',
              }}
            >
              Sem Intervenção Manual
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
