import React from 'react';
import {useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {BRIEFING} from './constants';

type Props = {
  fontFamily: string;
};

export const TopBar: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  const progresso = interpolate(frame, [0, durationInFrames], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: 150,
        left: 60,
        right: 60,
        height: 6,
        zIndex: 100,
        pointerEvents: 'none',
      }}
    >
      {/* Trilho de fundo */}
      <div
        style={{
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          borderRadius: 3,
          overflow: 'hidden',
          boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
        }}
      >
        {/* Barra ativa */}
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            background: `linear-gradient(90deg, ${BRIEFING.cores.marca}, ${BRIEFING.cores.destaque_brilho})`,
            borderRadius: 3,
            boxShadow: `0 0 10px ${BRIEFING.cores.destaque}`,
          }}
        />
      </div>
    </div>
  );
};
