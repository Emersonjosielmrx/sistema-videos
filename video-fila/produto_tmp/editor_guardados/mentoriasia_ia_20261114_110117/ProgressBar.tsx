import React from 'react';
import {useCurrentFrame} from 'remotion';
import {COLORS} from './theme';

interface Props {
  totalFrames: number;
}

export const ProgressBar: React.FC<Props> = ({totalFrames}) => {
  const frame = useCurrentFrame();
  const progress = Math.min(1, Math.max(0, frame / totalFrames));

  return (
    <div
      style={{
        position: 'absolute',
        top: 155,
        left: 60,
        right: 60,
        height: 6,
        borderRadius: 3,
        background: 'rgba(255, 255, 255, 0.15)',
        backdropFilter: 'blur(4px)',
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
          background: `linear-gradient(90deg, ${COLORS.marca}, ${COLORS.marcaClara})`,
          boxShadow: `0 0 12px ${COLORS.marcaClara}`,
          transition: 'width 0.1s linear',
        }}
      />
    </div>
  );
};
