import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  destaque?: string;
};

export const ProgressBar: React.FC<Props> = ({destaque = '#0EA5E9'}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progresso = Math.min(1, Math.max(0, frame / (durationInFrames - 1)));

  return (
    <div
      style={{
        position: 'absolute',
        top: 150,
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
          width: `${progresso * 100}%`,
          height: '100%',
          borderRadius: 3,
          background: `linear-gradient(90deg, ${destaque}, #38BDF8)`,
          boxShadow: `0 0 12px ${destaque}`,
        }}
      />
    </div>
  );
};
