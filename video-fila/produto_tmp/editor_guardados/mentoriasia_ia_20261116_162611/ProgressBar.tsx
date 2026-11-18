import React from 'react';
import {useCurrentFrame} from 'remotion';

export const ProgressBar: React.FC<{totalFrames: number}> = ({totalFrames}) => {
  const frame = useCurrentFrame();
  const progress = Math.min(100, Math.max(0, (frame / totalFrames) * 100));

  return (
    <div
      style={{
        position: 'absolute',
        top: 155,
        left: 60,
        right: 60,
        height: 6,
        borderRadius: 3,
        backgroundColor: 'rgba(255, 255, 255, 0.18)',
        zIndex: 100,
        overflow: 'hidden',
        pointerEvents: 'none'
      }}
    >
      <div
        style={{
          width: `${progress}%`,
          height: '100%',
          borderRadius: 3,
          background: 'linear-gradient(90deg, #2563EB, #60A5FA)',
          boxShadow: '0 0 10px rgba(96, 165, 250, 0.6)'
        }}
      />
    </div>
  );
};
