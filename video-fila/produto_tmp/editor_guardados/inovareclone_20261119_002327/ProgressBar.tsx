import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {CORES} from './constants';

export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progress = Math.min(1, Math.max(0, frame / durationInFrames));

  return (
    <div
      style={{
        position: 'absolute',
        top: 152,
        left: 60,
        right: 60,
        height: 6,
        borderRadius: 3,
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
        overflow: 'hidden',
        zIndex: 100,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          borderRadius: 3,
          background: `linear-gradient(90deg, ${CORES.marcaEscura}, ${CORES.marca}, ${CORES.marcaClara})`,
          boxShadow: `0 0 12px ${CORES.marca}`,
        }}
      />
    </div>
  );
};
