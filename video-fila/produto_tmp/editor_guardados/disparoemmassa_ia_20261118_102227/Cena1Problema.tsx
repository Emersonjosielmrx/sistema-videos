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

export const Cena1Problema: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Smooth entrance (frames 0 to 10) and exit (frames 230 to 241)
  const sceneOpacity = interpolate(
    frame,
    [0, 10, 230, 241],
    [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Gentle push-in camera zoom on the video (scale 1.04 to 1.09)
  const videoScale = interpolate(frame, [0, 241], [1.04, 1.09], {
    extrapolateRight: 'clamp',
  });

  // Top pill entrance
  const pillSpring = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.6},
  });

  // Headline 1: "ESQUECIA DO CONTATO" (active during first half, frames 0 to 136)
  const headline1Spring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Headline 2: "CLIENTES NÃO VOLTAVAM" (speech shifts at 8.44s -> relative frame 137)
  const isSecondPart = frame >= 137;
  const headline2Spring = spring({
    frame: frame - 137,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Micro pulse on amber indicator
  const amberPulse = 1 + Math.sin(frame / 7) * 0.08;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        opacity: sceneOpacity,
      }}
    >
      {/* Background Video of Presenter - Shifted down 160px so head starts safely below y=360 */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `translateY(160px) scale(${videoScale})`,
          transformOrigin: 'center 40%',
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
      </div>

      {/* Top Protective Gradient: ensures 100% contrast for top badges without touching presenter */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 360,
          background:
            'linear-gradient(to bottom, rgba(17, 24, 39, 0.9) 0%, rgba(17, 24, 39, 0.6) 65%, transparent 100%)',
          pointerEvents: 'none',
          zIndex: 10,
        }}
      />

      {/* Top Header Section (y=190 to y=300 strictly in safe zone, respiro >= 40px from progress bar and presenter) */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 20,
        }}
      >
        {/* Pill Badge */}
        <div
          style={{
            opacity: pillSpring,
            transform: `translateY(${(1 - pillSpring) * -15}px)`,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 999,
            backgroundColor: 'rgba(17, 24, 39, 0.9)',
            border: '1.5px solid rgba(245, 158, 11, 0.45)',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.6)',
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: '#F59E0B',
              boxShadow: '0 0 10px #F59E0B',
              transform: `scale(${amberPulse})`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FDE68A',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            O Problema Real
          </span>
        </div>

        {/* Dynamic Headline synced with speech */}
        <div style={{height: 56, display: 'flex', alignItems: 'center'}}>
          {!isSecondPart ? (
            <div
              style={{
                opacity: Math.max(0, headline1Spring),
                transform: `translateY(${(1 - headline1Spring) * 15}px)`,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 44,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: '-0.02em',
                  textShadow: '0 3px 14px rgba(0,0,0,0.95)',
                }}
              >
                Esquecia de manter contato
              </span>
            </div>
          ) : (
            <div
              style={{
                opacity: Math.max(0, headline2Spring),
                transform: `translateY(${(1 - headline2Spring) * 15}px)`,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 44,
                  fontWeight: 900,
                  color: '#FDE68A',
                  textTransform: 'uppercase',
                  letterSpacing: '-0.02em',
                  textShadow: '0 3px 14px rgba(0,0,0,0.95)',
                }}
              >
                Clientes não compravam de novo
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
