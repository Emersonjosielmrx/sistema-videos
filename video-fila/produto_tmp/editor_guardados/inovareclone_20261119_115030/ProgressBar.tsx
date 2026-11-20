import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {CORES} from './constants';

export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progresso = Math.min(1, Math.max(0, frame / durationInFrames));

  return (
    <div
      style={{
        position: 'absolute',
        top: 154,
        left: 60,
        right: 60,
        height: 6,
        backgroundColor: 'rgba(255, 255, 255, 0.18)',
        borderRadius: 3,
        overflow: 'hidden',
        zIndex: 100,
        backdropFilter: 'blur(4px)',
      }}
    >
      <div
        style={{
          width: `${progresso * 100}%`,
          height: '100%',
          backgroundColor: CORES.marca,
          borderRadius: 3,
          boxShadow: `0 0 10px ${CORES.marca}`,
        }}
      />
    </div>
  );
};
