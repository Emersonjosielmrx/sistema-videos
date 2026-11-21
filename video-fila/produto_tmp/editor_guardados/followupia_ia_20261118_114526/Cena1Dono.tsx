import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena1DonoProps {
  fontFamily: string;
}

export const Cena1Dono: React.FC<Cena1DonoProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous zoom on video (1.00 -> 1.055)
  const videoScale = interpolate(frame, [0, 195], [1.0, 1.055], {
    extrapolateRight: 'clamp',
  });

  // Entrance spring for top header
  const headerEntrance = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Second phase transition at frame ~95 (~7.65s in video, when speech shifts to "esquecendo de responder propostas")
  const phaseTransition = spring({
    frame: frame - 95,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const floatY = Math.sin(frame / 10) * 3;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#111827',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Fullscreen Video with camera push */}
      <OffthreadVideo
        src={staticFile('dono_1.mp4')}
        muted
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${videoScale})`,
        }}
      />

      {/* Top vignette to ensure 100% text contrast without affecting face */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 320,
          background:
            'linear-gradient(to bottom, rgba(10, 14, 23, 0.90) 0%, rgba(10, 14, 23, 0.6) 65%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Graphic Header: Strictly at y=165 to y=238, leaving > 80px respiro above the presenter's hair */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          height: 72,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          opacity: headerEntrance,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* Phase 1: "🚨 O PROBLEMA | PERDENDO DINHEIRO TODO MÊS" */}
        <div
          style={{
            position: 'absolute',
            opacity: 1 - phaseTransition,
            transform: `scale(${1 - phaseTransition * 0.08})`,
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: '2px solid rgba(239, 68, 68, 0.75)',
            padding: '10px 28px',
            borderRadius: 36,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span style={{fontSize: 32}}>🚨</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#FCA5A5',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O Problema:
          </span>
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
            }}
          >
            Perdendo dinheiro todo mês
          </span>
        </div>

        {/* Phase 2: "🚨 O PROBLEMA | PROPOSTAS ESQUECIDAS" */}
        <div
          style={{
            position: 'absolute',
            opacity: phaseTransition,
            transform: `scale(${0.92 + phaseTransition * 0.08})`,
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            backgroundColor: 'rgba(17, 24, 39, 0.94)',
            border: '2px solid rgba(78, 205, 196, 0.75)',
            padding: '10px 28px',
            borderRadius: 36,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span style={{fontSize: 32}}>⏳</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#4ECDC4',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O Problema:
          </span>
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
            }}
          >
            Propostas paradas no trabalho
          </span>
        </div>
      </div>
    </div>
  );
};
