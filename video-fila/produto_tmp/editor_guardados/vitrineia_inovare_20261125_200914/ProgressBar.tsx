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
        top: 150,
        left: 60,
        right: 60,
        height: 6,
        backgroundColor: 'rgba(255, 255, 255, 0.18)',
        borderRadius: 3,
        overflow: 'hidden',
        zIndex: 100,
      }}
    >
      <div
        style={{
          height: '100%',
          width: `${progress * 100}%`,
          backgroundColor: '#A78BFA',
          boxShadow: '0 0 12px rgba(167, 139, 250, 0.8)',
          borderRadius: 3,
        }}
      />
    </div>
  );
};
