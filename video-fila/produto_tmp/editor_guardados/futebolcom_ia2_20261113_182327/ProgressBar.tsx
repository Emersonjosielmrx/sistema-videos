import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  const progress = interpolate(frame, [0, durationInFrames - 1], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: 155,
        left: 60,
        right: 60,
        height: 6,
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        borderRadius: 4,
        overflow: 'hidden',
        zIndex: 100,
      }}
    >
      <div
        style={{
          width: `${progress}%`,
          height: '100%',
          background: 'linear-gradient(90deg, #E11D48 0%, #FACC15 100%)',
          borderRadius: 4,
          boxShadow: '0 0 10px rgba(250, 204, 21, 0.7)',
        }}
      />
    </div>
  );
};
