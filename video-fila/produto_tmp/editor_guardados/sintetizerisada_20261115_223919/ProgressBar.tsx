import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

export const ProgressBar: React.FC<{cor?: string}> = ({cor = '#FFA94D'}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  const progresso = Math.min(1, Math.max(0, frame / durationInFrames));

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
        boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
      }}
    >
      <div
        style={{
          width: `${progresso * 100}%`,
          height: '100%',
          borderRadius: 3,
          background: `linear-gradient(90deg, ${cor}, #FFD43B)`,
          boxShadow: `0 0 12px ${cor}`,
        }}
      />
    </div>
  );
};
