import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  const progress = interpolate(frame, [0, durationInFrames], [0, 100], {
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
        borderRadius: 4,
        background: 'rgba(255, 255, 255, 0.12)',
        overflow: 'hidden',
        zIndex: 100,
      }}
    >
      <div
        style={{
          width: `${progress}%`,
          height: '100%',
          background: 'linear-gradient(90deg, #16A34A 0%, #22C55E 50%, #4ADE80 100%)',
          boxShadow: '0 0 12px rgba(34, 197, 94, 0.8)',
          borderRadius: 4,
        }}
      />
    </div>
  );
};
