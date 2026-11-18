import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

type ProgressBarProps = {
  totalFrames: number;
  corMarca?: string;
  corApoio?: string;
};

export const ProgressBar: React.FC<ProgressBarProps> = ({
  totalFrames,
  corMarca = '#E11D48',
  corApoio = '#FACC15',
}) => {
  const frame = useCurrentFrame();
  const progress = Math.min(1, Math.max(0, frame / totalFrames));

  return (
    <div
      style={{
        position: 'absolute',
        top: 152,
        left: 60,
        right: 60,
        height: 6,
        borderRadius: 3,
        background: 'rgba(255, 255, 255, 0.16)',
        overflow: 'hidden',
        zIndex: 100,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          borderRadius: 3,
          background: `linear-gradient(90deg, ${corMarca} 0%, ${corApoio} 100%)`,
          boxShadow: `0 0 10px ${corMarca}`,
          transition: 'width 0.03s linear',
        }}
      />
    </div>
  );
};
