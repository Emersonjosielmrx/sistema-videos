import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';

type Props = {
  totalFrames: number;
};

export const ProgressBar: React.FC<Props> = ({totalFrames}) => {
  const frame = useCurrentFrame();
  const progresso = interpolate(frame, [0, totalFrames], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: 152,
        left: 60,
        right: 60,
        height: 6,
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        borderRadius: 4,
        overflow: 'hidden',
        zIndex: 100,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          width: `${progresso}%`,
          height: '100%',
          background: 'linear-gradient(90deg, #1F93FF, #60A5FA)',
          boxShadow: '0 0 10px rgba(31, 147, 255, 0.8)',
          borderRadius: 4,
        }}
      />
    </div>
  );
};
