import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

export const ProgressBar: React.FC<{cor?: string}> = ({cor = '#4ECDC4'}) => {
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
        backgroundColor: 'rgba(255, 255, 255, 0.16)',
        overflow: 'hidden',
        zIndex: 100,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          width: `${progresso * 100}%`,
          height: '100%',
          borderRadius: 3,
          background: `linear-gradient(90deg, ${cor}, #2DD4BF)`,
          boxShadow: `0 0 10px ${cor}88`,
        }}
      />
    </div>
  );
};
