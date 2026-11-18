import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {BRIEFING} from './data';

export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, BRIEFING.totalFrames - 1], [0, 1], {
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
        borderRadius: 3,
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        backdropFilter: 'blur(4px)',
        zIndex: 100,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          borderRadius: 3,
          background: 'linear-gradient(90deg, #0284C7 0%, #0EA5E9 70%, #38BDF8 100%)',
          boxShadow: '0 0 10px rgba(14, 165, 233, 0.8)',
        }}
      />
    </div>
  );
};
