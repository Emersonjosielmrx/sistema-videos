import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

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
        background: 'rgba(255, 255, 255, 0.18)',
        borderRadius: 4,
        overflow: 'hidden',
        zIndex: 99,
        pointerEvents: 'none',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.4)',
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          background: 'linear-gradient(90deg, #059669, #10B981, #34D399)',
          borderRadius: 4,
          boxShadow: '0 0 12px rgba(16, 185, 129, 0.8)',
        }}
      />
    </div>
  );
};
