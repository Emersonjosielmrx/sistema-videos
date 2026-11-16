import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  destaque?: string;
};

export const ProgressBar: React.FC<Props> = ({destaque = '#25D366'}) => {
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
        top: 152,
        left: 60,
        right: 60,
        height: 6,
        borderRadius: 3,
        backgroundColor: 'rgba(255, 255, 255, 0.18)',
        overflow: 'hidden',
        zIndex: 100,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          width: `${progress}%`,
          height: '100%',
          borderRadius: 3,
          background: `linear-gradient(90deg, #075E54 0%, ${destaque} 100%)`,
          boxShadow: `0 0 12px ${destaque}`,
        }}
      />
    </div>
  );
};
