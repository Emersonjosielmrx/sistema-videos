import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

interface ProgressBarProps {
  color: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({color}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progress = Math.min(1, Math.max(0, frame / durationInFrames));

  return (
    <div
      style={{
        position: 'absolute',
        top: 152,
        left: 60,
        width: 960,
        height: 6,
        backgroundColor: 'rgba(255, 255, 255, 0.18)',
        borderRadius: 3,
        overflow: 'hidden',
        zIndex: 100,
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          backgroundColor: color,
          boxShadow: `0 0 10px ${color}`,
          borderRadius: 3,
        }}
      />
    </div>
  );
};
