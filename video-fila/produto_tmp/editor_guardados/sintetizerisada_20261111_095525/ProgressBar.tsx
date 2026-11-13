import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  destaque: string;
};

export const ProgressBar: React.FC<Props> = ({destaque}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progresso = Math.min(1, Math.max(0, frame / (durationInFrames - 1)));

  return (
    <div
      style={{
        position: 'absolute',
        top: 152,
        left: 60,
        right: 60,
        height: 6,
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        borderRadius: 4,
        overflow: 'hidden',
        zIndex: 100,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          width: `${progresso * 100}%`,
          height: '100%',
          backgroundColor: destaque,
          borderRadius: 4,
          boxShadow: `0 0 12px ${destaque}`,
        }}
      />
    </div>
  );
};
