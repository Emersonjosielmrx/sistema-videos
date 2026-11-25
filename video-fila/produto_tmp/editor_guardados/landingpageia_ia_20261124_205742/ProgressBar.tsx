import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  cor?: string;
};

export const ProgressBar: React.FC<Props> = ({cor = '#F59E0B'}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  const progress = Math.min(1, Math.max(0, frame / (durationInFrames - 1)));

  return (
    <div
      style={{
        position: 'absolute',
        top: 150,
        left: 60,
        right: 60,
        height: 6,
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        borderRadius: 3,
        overflow: 'hidden',
        zIndex: 100,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          backgroundColor: cor,
          boxShadow: `0 0 10px ${cor}`,
          borderRadius: 3,
        }}
      />
    </div>
  );
};
