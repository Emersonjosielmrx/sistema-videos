import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

interface Props {
  cor?: string;
}

export const ProgressBar: React.FC<Props> = ({cor = '#FFA94D'}) => {
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
        top: 160,
        left: 60,
        right: 60,
        height: 6,
        borderRadius: 3,
        backgroundColor: 'rgba(255, 255, 255, 0.16)',
        overflow: 'hidden',
        zIndex: 100,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          width: `${progress}%`,
          height: '100%',
          backgroundColor: cor,
          borderRadius: 3,
          boxShadow: `0 0 12px ${cor}`,
        }}
      />
    </div>
  );
};
