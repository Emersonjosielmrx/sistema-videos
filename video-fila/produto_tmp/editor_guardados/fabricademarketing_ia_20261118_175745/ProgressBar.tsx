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
        top: 154,
        left: 60,
        width: 960,
        height: 6,
        borderRadius: 3,
        backgroundColor: 'rgba(255, 255, 255, 0.18)',
        overflow: 'hidden',
        zIndex: 95,
      }}
    >
      <div
        style={{
          width: `${progress}%`,
          height: '100%',
          borderRadius: 3,
          background: 'linear-gradient(90deg, #F472B6 0%, #FB7185 100%)',
          boxShadow: '0 0 10px rgba(244, 114, 182, 0.8)',
        }}
      />
    </div>
  );
};
