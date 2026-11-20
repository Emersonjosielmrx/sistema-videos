import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

type ProgressBarProps = {
  cor?: string;
  altura?: number;
  y?: number;
};

export const ProgressBar: React.FC<ProgressBarProps> = ({
  cor = '#4ECDC4',
  altura = 8,
  y = 152,
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progresso = Math.min(1, Math.max(0, frame / (durationInFrames - 1)));

  return (
    <div
      style={{
        position: 'absolute',
        top: y,
        left: 60,
        right: 60,
        height: altura,
        borderRadius: altura / 2,
        backgroundColor: 'rgba(255, 255, 255, 0.18)',
        backdropFilter: 'blur(4px)',
        overflow: 'hidden',
        zIndex: 100,
      }}
    >
      <div
        style={{
          width: `${progresso * 100}%`,
          height: '100%',
          backgroundColor: cor,
          borderRadius: altura / 2,
          boxShadow: `0 0 12px ${cor}`,
        }}
      />
    </div>
  );
};
