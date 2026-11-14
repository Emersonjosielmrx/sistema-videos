import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig, OffthreadVideo, staticFile} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Framing variation from Cena 1: punchier angle with slight side offset and safe headroom offset Y
  const videoScale = interpolate(frame, [0, 241], [1.12, 1.18], {
    extrapolateRight: 'clamp',
  });

  const videoOffsetY = interpolate(frame, [0, 241], [72, 85], {
    extrapolateRight: 'clamp',
  });

  const videoOffsetX = interpolate(frame, [0, 241], [-28, -14], {
    extrapolateRight: 'clamp',
  });

  // Badge entrance
  const badgeSpring = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card entrance
  const cardSpring = spring({
    frame: Math.max(0, frame - 16),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Progressive badge entrances spaced throughout the scene
  // Badge 1 entrance (at frame 20, ~18.4s, "não perco o contato comercial")
  const badge1Spring = spring({
    frame: Math.max(0, frame - 20),
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Badge 2 entrance (at frame 90, ~20.8s, "de quem demonstra interesse")
  const badge2Spring = spring({
    frame: Math.max(0, frame - 90),
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Badge 3 entrance (at frame 165, ~23.3s, "nas minhas publicações")
  const badge3Spring = spring({
    frame: Math.max(0, frame - 165),
    fps,
    config: {damping: 12, stiffness: 130},
  });

  return (
    <div style={{position: 'absolute', width: 1080, height: 1920, overflow: 'hidden'}}>
      {/* Fullscreen Video of the owner/presenter with alternate framing and safe headroom */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale}) translate(${videoOffsetX}px, ${videoOffsetY}px)`,
          transformOrigin: '50% 40%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </div>

      {/* Subtle top gradient shadow behind top elements only */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 440,
          background:
            'linear-gradient(to bottom, rgba(17, 24, 39, 0.75) 0%, rgba(17, 24, 39, 0.35) 60%, rgba(17, 24, 39, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Graphic Card (y: 158 to 395) — Face is completely free and protected below y=460 */}
      <div
        style={{
          position: 'absolute',
          top: 158,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
        }}
      >
        {/* Rotulo Badge */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 20px',
            borderRadius: 24,
            background: 'rgba(16, 185, 129, 0.22)',
            border: '1.5px solid rgba(16, 185, 129, 0.6)',
            boxShadow: '0 4px 16px rgba(16, 185, 129, 0.3)',
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
          }}
        >
          <span style={{fontSize: 26}}>✅</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#6EE7B7',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            O Resultado
          </span>
        </div>

        {/* Main top informative card */}
        <div
          style={{
            width: '100%',
            background: 'rgba(17, 24, 39, 0.90)',
            border: '1.5px solid rgba(16, 185, 129, 0.4)',
            borderRadius: 22,
            padding: '14px 20px',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.75)',
            transform: `translateY(${(1 - cardSpring) * -20}px)`,
            opacity: cardSpring,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 40,
              fontWeight: 900,
              color: '#FFFFFF',
              textAlign: 'center',
              lineHeight: 1.15,
            }}
          >
            Contato comercial aproveitado
          </div>

          {/* Sequential badges - compact single row without wrapping */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 10,
              width: '100%',
              flexWrap: 'nowrap',
            }}
          >
            {frame >= 20 && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 12px',
                  borderRadius: 12,
                  background: 'rgba(16, 185, 129, 0.25)',
                  border: '1px solid rgba(16, 185, 129, 0.55)',
                  transform: `scale(${badge1Spring})`,
                  opacity: badge1Spring,
                  whiteSpace: 'nowrap',
                }}
              >
                <span style={{fontSize: 20}}>✓</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#A7F3D0',
                  }}
                >
                  Contatos Salvos
                </span>
              </div>
            )}

            {frame >= 90 && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 12px',
                  borderRadius: 12,
                  background: 'rgba(244, 114, 182, 0.25)',
                  border: '1px solid rgba(244, 114, 182, 0.55)',
                  transform: `scale(${badge2Spring})`,
                  opacity: badge2Spring,
                  whiteSpace: 'nowrap',
                }}
              >
                <span style={{fontSize: 20}}>⚡</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FBCFE8',
                  }}
                >
                  Interesse Real
                </span>
              </div>
            )}

            {frame >= 165 && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 12px',
                  borderRadius: 12,
                  background: 'rgba(59, 130, 246, 0.25)',
                  border: '1px solid rgba(59, 130, 246, 0.55)',
                  transform: `scale(${badge3Spring})`,
                  opacity: badge3Spring,
                  whiteSpace: 'nowrap',
                }}
              >
                <span style={{fontSize: 20}}>💬</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#BFDBFE',
                  }}
                >
                  Postagens Atendidas
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
