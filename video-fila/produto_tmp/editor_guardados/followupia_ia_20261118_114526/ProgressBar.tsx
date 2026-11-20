import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

interface ProgressBarProps {
  color?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({color = '#4ECDC4'}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  const progress = Math.min(1, Math.max(0, frame / Math.max(1, durationInFrames - 1)));

  return (
    <div
      style={{
        position: 'absolute',
        top: 150,
        left: 60,
        right: 60,
        height: 6,
        borderRadius: 3,
        backgroundColor: 'rgba(255, 255, 255, 0.16)',
        overflow: 'hidden',
        zIndex: 100,
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.4)',
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          backgroundColor: color,
          borderRadius: 3,
          boxShadow: `0 0 12px ${color}`,
          transition: 'width 0.05s linear',
        }}
      />
    </div>
  );
};
