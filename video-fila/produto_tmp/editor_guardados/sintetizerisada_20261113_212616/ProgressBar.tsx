import React from 'react';
import {useCurrentFrame} from 'remotion';
import {CORES, TOTAL_FRAMES} from './constants';

export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const progresso = Math.min(1, Math.max(0, frame / TOTAL_FRAMES));

  return (
    <div
      style={{
        position: 'absolute',
        top: 152,
        left: 60,
        width: 960,
        height: 6,
        borderRadius: 3,
        backgroundColor: 'rgba(255, 255, 255, 0.18)',
        overflow: 'hidden',
        zIndex: 100,
      }}
    >
      <div
        style={{
          width: `${progresso * 100}%`,
          height: '100%',
          backgroundColor: CORES.marca,
          borderRadius: 3,
          boxShadow: `0 0 12px ${CORES.marca}`,
        }}
      />
    </div>
  );
};
