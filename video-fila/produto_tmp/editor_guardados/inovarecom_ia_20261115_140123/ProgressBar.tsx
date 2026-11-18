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
        borderRadius: 3,
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
        overflow: 'hidden',
        zIndex: 95,
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.5)',
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          borderRadius: 3,
          background: 'linear-gradient(90deg, #075E54 0%, #25D366 100%)',
          boxShadow: '0 0 10px rgba(37, 211, 102, 0.8)',
        }}
      />
    </div>
  );
};
