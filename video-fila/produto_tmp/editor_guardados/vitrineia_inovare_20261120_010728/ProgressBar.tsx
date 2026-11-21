import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  cor?: string;
  altura?: number;
  top?: number;
};

export const ProgressBar: React.FC<Props> = ({
  cor = '#A78BFA',
  altura = 6,
  top = 150,
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  const progresso = interpolate(frame, [0, durationInFrames - 1], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top,
        left: 60,
        right: 60,
        height: altura,
        backgroundColor: 'rgba(255, 255, 255, 0.16)',
        borderRadius: altura / 2,
        overflow: 'hidden',
        zIndex: 99,
        pointerEvents: 'none',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.4)',
      }}
    >
      <div
        style={{
          width: `${progresso}%`,
          height: '100%',
          backgroundColor: cor,
          borderRadius: altura / 2,
          boxShadow: `0 0 12px ${cor}`,
        }}
      />
    </div>
  );
};
