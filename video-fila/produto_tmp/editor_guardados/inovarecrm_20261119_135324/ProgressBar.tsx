import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  totalFrames: number;
  cor?: string;
};

export const ProgressBar: React.FC<Props> = ({
  totalFrames,
  cor = '#38BDF8',
}) => {
  const frame = useCurrentFrame();
  const progress = Math.min(1, Math.max(0, frame / totalFrames));

  return (
    <div
      style={{
        position: 'absolute',
        top: 150,
        left: 60,
        width: 960,
        height: 6,
        borderRadius: 4,
        background: 'rgba(255, 255, 255, 0.12)',
        overflow: 'hidden',
        zIndex: 100,
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          background: `linear-gradient(90deg, #0284C7 0%, ${cor} 100%)`,
          boxShadow: `0 0 12px ${cor}`,
          borderRadius: 4,
          transition: 'width 0.05s linear',
        }}
      />
    </div>
  );
};
