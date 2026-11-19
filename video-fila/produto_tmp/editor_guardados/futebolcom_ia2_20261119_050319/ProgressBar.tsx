import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  totalFrames: number;
  corPrimaria?: string;
  corApoio?: string;
};

export const ProgressBar: React.FC<Props> = ({
  totalFrames,
  corPrimaria = '#E11D48',
  corApoio = '#FACC15',
}) => {
  const frame = useCurrentFrame();
  const progresso = Math.min(1, Math.max(0, frame / totalFrames));

  return (
    <div
      style={{
        position: 'absolute',
        top: 150,
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
          width: `${progresso * 100}%`,
          height: '100%',
          background: `linear-gradient(90deg, ${corPrimaria} 0%, ${corApoio} 100%)`,
          borderRadius: 3,
          boxShadow: `0 0 10px ${corPrimaria}`,
        }}
      />
    </div>
  );
};
