import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig, OffthreadVideo, staticFile} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Push-in zoom on presenter with safe headroom framing
  const videoScale = interpolate(frame, [0, 241], [1.08, 1.13], {
    extrapolateRight: 'clamp',
  });

  // Vertical offset to guarantee generous headroom below top card
  const videoOffsetY = interpolate(frame, [0, 241], [60, 72], {
    extrapolateRight: 'clamp',
  });

  // Badge entrance
  const badgeSpring = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card entrance
  const cardSpring = spring({
    frame: Math.max(0, frame - 22),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Second alert stage entrance (enters at frame 90 when he speaks "não dava conta de responder")
  const stage2Spring = spring({
    frame: Math.max(0, frame - 90),
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Pulse for overload indicator
  const overloadPulse = 0.5 + 0.5 * Math.sin(frame / 6);

  return (
    <div style={{position: 'absolute', width: 1080, height: 1920, overflow: 'hidden'}}>
      {/* Fullscreen Video of the owner/presenter with safe headroom offset */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale}) translateY(${videoOffsetY}px)`,
          transformOrigin: '50% 40%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </div>

      {/* Subtle top gradient shadow ONLY behind top elements (y: 0 to 430) to ensure high readability */}
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

      {/* Top Graphic Card (y: 162 to 410) — Face is completely free below y=460 */}
      <div
        style={{
          position: 'absolute',
          top: 162,
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
            background: 'rgba(239, 68, 68, 0.22)',
            border: '1.5px solid rgba(239, 68, 68, 0.6)',
            boxShadow: '0 4px 16px rgba(239, 68, 68, 0.3)',
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
          }}
        >
          <span style={{fontSize: 26}}>⚠️</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FCA5A5',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            O Problema
          </span>
        </div>

        {/* Main top informative card */}
        <div
          style={{
            width: '100%',
            background: 'rgba(17, 24, 39, 0.90)',
            border: '1.5px solid rgba(244, 114, 182, 0.35)',
            borderRadius: 22,
            padding: '14px 22px',
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
            Responder todo mundo nas postagens
          </div>

          {/* Dynamic status row with high contrast and icon bullet for both */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              width: '100%',
              background: 'rgba(255, 255, 255, 0.06)',
              borderRadius: 14,
              padding: '8px 14px',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
              <div
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  background: '#EF4444',
                  boxShadow: `0 0 10px rgba(239, 68, 68, ${overloadPulse})`,
                }}
              />
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#CBD5E1',
                }}
              >
                Volume alto
              </span>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                background: 'rgba(239, 68, 68, 0.32)',
                border: '1px solid rgba(239, 68, 68, 0.65)',
                padding: '4px 12px',
                borderRadius: 10,
              }}
            >
              <span style={{fontSize: 20}}>⏳</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Sem tempo manual
              </span>
            </div>
          </div>

          {/* Evolving second status line (enters as speech advances to 'responder todo mundo') */}
          {frame >= 90 && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 10,
                width: '100%',
                padding: '6px 14px',
                borderRadius: 12,
                background: 'rgba(239, 68, 68, 0.18)',
                border: '1px solid rgba(239, 68, 68, 0.45)',
                transform: `scale(${stage2Spring})`,
                opacity: stage2Spring,
              }}
            >
              <span style={{fontSize: 22}}>⚠️</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FECACA',
                }}
              >
                Gargalo no atendimento manual
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
