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

  // Agency-style Punch-in Jump Cut on emphasis:
  // Before frame 76: Medium shot (1.02 -> 1.06)
  // At frame 76 ('centenas de mensagens acumuladas'): Digital Punch-in Cut to 1.16x -> 1.22x!
  const isPunchIn = frame >= 76;
  const videoScale = isPunchIn
    ? interpolate(frame, [76, 222], [1.16, 1.22], {extrapolateRight: 'clamp'})
    : interpolate(frame, [0, 75], [1.02, 1.06], {extrapolateRight: 'clamp'});

  // Entry spring for badge and title
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, mass: 0.6},
  });

  const titleSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 13, mass: 0.6},
  });

  // Floating microanimation badges entering on emphasis
  const bubble1Spring = spring({
    frame: frame - 76, // on 'centenas de mensagens'
    fps,
    config: {damping: 12, mass: 0.5},
  });

  const bubble2Spring = spring({
    frame: frame - 110, // on 'acumuladas'
    fps,
    config: {damping: 12, mass: 0.5},
  });

  // Continuous subtle floating motion
  const floatY = Math.sin(frame * 0.08) * 4;
  const floatBubble1 = Math.sin(frame * 0.12) * 5;
  const floatBubble2 = Math.cos(frame * 0.10) * 5;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* Presenter Video Fullscreen with Punch-in Jump Cut at frame 76 */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 42%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Soft vignette/gradient on top ONLY to ensure contrast without dimming face */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(180deg, rgba(17, 24, 39, 0.88) 0%, rgba(17, 24, 39, 0.4) 70%, rgba(17, 24, 39, 0) 100%)',
          }}
        />
      </div>

      {/* Floating Microanimation Badges (lateral, face 100% free) */}
      {frame >= 76 && (
        <div
          style={{
            position: 'absolute',
            top: 420 + floatBubble1,
            left: 45,
            transform: `scale(${interpolate(bubble1Spring, [0, 1], [0.6, 1])})`,
            padding: '10px 20px',
            borderRadius: 999,
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: '2px solid #EF4444',
            boxShadow: '0 0 25px rgba(239, 68, 68, 0.5)',
            backdropFilter: 'blur(10px)',
            color: '#FCA5A5',
            fontSize: 28,
            fontWeight: 800,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            zIndex: 15,
          }}
        >
          <span>💬</span>
          <span>Centenas de mensagens</span>
        </div>
      )}

      {frame >= 110 && (
        <div
          style={{
            position: 'absolute',
            top: 420 + floatBubble2,
            right: 40,
            transform: `scale(${interpolate(bubble2Spring, [0, 1], [0.6, 1])})`,
            padding: '10px 20px',
            borderRadius: 999,
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: '2px solid #EF4444',
            boxShadow: '0 0 25px rgba(239, 68, 68, 0.5)',
            backdropFilter: 'blur(10px)',
            color: '#FCA5A5',
            fontSize: 28,
            fontWeight: 800,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            zIndex: 15,
          }}
        >
          <span>⚠️</span>
          <span>Grupos acumulados</span>
        </div>
      )}

      {/* Upper Information Area (strictly between y=165 and y=380 — ROSTO 100% LIVRE) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          transform: `translateY(${floatY}px)`,
          zIndex: 10,
        }}
      >
        {/* Rótulo: O PROBLEMA */}
        <div
          style={{
            opacity: badgeSpring,
            transform: `translateY(${interpolate(badgeSpring, [0, 1], [-15, 0])}px)`,
            padding: '8px 22px',
            borderRadius: 999,
            backgroundColor: 'rgba(239, 68, 68, 0.22)',
            border: '1.5px solid rgba(239, 68, 68, 0.7)',
            backdropFilter: 'blur(10px)',
            color: '#F87171',
            fontSize: 32,
            fontWeight: 800,
            letterSpacing: 1.5,
            textTransform: 'uppercase',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: 999,
              backgroundColor: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span>O Problema</span>
        </div>

        {/* Title Card: CENTENAS DE MENSAGENS ACUMULADAS */}
        <div
          style={{
            opacity: titleSpring,
            transform: `scale(${interpolate(titleSpring, [0, 1], [0.9, 1])})`,
            padding: '16px 30px',
            borderRadius: 20,
            backgroundColor: 'rgba(17, 24, 39, 0.90)',
            border: isPunchIn
              ? '2px solid rgba(239, 68, 68, 0.75)'
              : '1px solid rgba(255, 255, 255, 0.15)',
            boxShadow: isPunchIn
              ? '0 12px 35px rgba(239, 68, 68, 0.35)'
              : '0 12px 30px rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(14px)',
            maxWidth: 920,
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontSize: 44,
              fontWeight: 900,
              color: '#FFFFFF',
              textWrap: 'balance',
              lineHeight: 1.2,
              letterSpacing: -0.5,
            }}
          >
            {isPunchIn ? (
              <span
                style={{
                  color: '#F87171',
                  textShadow: '0 0 25px rgba(239, 68, 68, 0.8)',
                }}
              >
                Centenas de mensagens
              </span>
            ) : (
              <span>Centenas de mensagens</span>
            )}{' '}
            acumuladas nos grupos
          </div>
        </div>
      </div>
    </div>
  );
};
