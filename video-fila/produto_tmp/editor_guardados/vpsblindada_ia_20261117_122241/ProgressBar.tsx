import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

export const ProgressBar: React.FC<{color?: string}> = ({color = '#0EA5E9'}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progress = Math.min(1, Math.max(0, frame / durationInFrames));

  return (
    <div
      style={{
        position: 'absolute',
        top: 154,
        left: 60,
        right: 60,
        height: 6,
        borderRadius: 3,
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        overflow: 'hidden',
        zIndex: 100,
        boxShadow: '0 2px 8px rgba(0,0,0,0.5)',
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          backgroundColor: color,
          borderRadius: 3,
          boxShadow: `0 0 12px ${color}`,
        }}
      />
    </div>
  );
};
