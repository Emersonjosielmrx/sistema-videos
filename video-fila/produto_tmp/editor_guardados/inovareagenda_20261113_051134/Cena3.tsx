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

  // Video smooth push-in (1.00 -> 1.05)
  const videoScale = interpolate(frame, [0, 241], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Top header entrance spring
  const headerSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  // Action tags timing
  // "agenda" spoken ~frame 102
  const agendaActive = frame >= 102;
  // "confirma" spoken ~frame 130
  const confirmaActive = frame >= 130;
  // "reagenda" spoken ~frame 146
  const reagendaActive = frame >= 146;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Background Video: Dono da empresa */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${videoScale})`,
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
      </div>

      {/* Subtle top & bottom vignette to frame the presenter without touching his face */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 250,
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.85) 0%, rgba(15,23,42,0.50) 60%, rgba(15,23,42,0) 100%)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(0deg, rgba(15,23,42,0.88) 0%, rgba(15,23,42,0.40) 65%, rgba(15,23,42,0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Bar strictly in safe zone (y=160 to 235), keeping face 100% free */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          opacity: Math.min(1, Math.max(0, headerSpring)),
          transform: `scale(${0.92 + 0.08 * Math.min(1, Math.max(0, headerSpring))})`,
        }}
      >
        {/* Pill 1: O RESULTADO */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 20px',
            borderRadius: 24,
            background: 'rgba(31, 41, 55, 0.90)',
            border: '2px solid rgba(245, 158, 11, 0.7)',
            boxShadow: '0 6px 20px rgba(0,0,0,0.6)',
          }}
        >
          <span style={{fontSize: 32}}>⭐</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#F59E0B',
              letterSpacing: '1.5px',
              textTransform: 'uppercase',
            }}
          >
            O Resultado no Salão
          </span>
        </div>

        {/* 3 Action Status Tags side-by-side */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          {/* Tag 1: AGENDA */}
          <div
            style={{
              padding: '6px 18px',
              borderRadius: 14,
              background: agendaActive ? '#F59E0B' : 'rgba(31, 41, 55, 0.85)',
              color: agendaActive ? '#121216' : '#9CA3AF',
              border: `2px solid ${agendaActive ? '#F59E0B' : 'rgba(156,163,175,0.4)'}`,
              fontSize: 32,
              fontWeight: 900,
              letterSpacing: '1px',
              boxShadow: agendaActive
                ? '0 4px 16px rgba(245, 158, 11, 0.5)'
                : 'none',
              transform: agendaActive ? 'scale(1.05)' : 'scale(1.0)',
              transition: 'transform 0.2s ease',
            }}
          >
            ✓ AGENDA
          </div>

          {/* Tag 2: CONFIRMA */}
          <div
            style={{
              padding: '6px 18px',
              borderRadius: 14,
              background: confirmaActive ? '#F59E0B' : 'rgba(31, 41, 55, 0.85)',
              color: confirmaActive ? '#121216' : '#9CA3AF',
              border: `2px solid ${confirmaActive ? '#F59E0B' : 'rgba(156,163,175,0.4)'}`,
              fontSize: 32,
              fontWeight: 900,
              letterSpacing: '1px',
              boxShadow: confirmaActive
                ? '0 4px 16px rgba(245, 158, 11, 0.5)'
                : 'none',
              transform: confirmaActive ? 'scale(1.05)' : 'scale(1.0)',
              transition: 'transform 0.2s ease',
            }}
          >
            ✓ CONFIRMA
          </div>

          {/* Tag 3: REAGENDA */}
          <div
            style={{
              padding: '6px 18px',
              borderRadius: 14,
              background: reagendaActive ? '#F59E0B' : 'rgba(31, 41, 55, 0.85)',
              color: reagendaActive ? '#121216' : '#9CA3AF',
              border: `2px solid ${reagendaActive ? '#F59E0B' : 'rgba(156,163,175,0.4)'}`,
              fontSize: 32,
              fontWeight: 900,
              letterSpacing: '1px',
              boxShadow: reagendaActive
                ? '0 4px 16px rgba(245, 158, 11, 0.5)'
                : 'none',
              transform: reagendaActive ? 'scale(1.05)' : 'scale(1.0)',
              transition: 'transform 0.2s ease',
            }}
          >
            ✓ REAGENDA
          </div>
        </div>
      </div>
    </div>
  );
};
