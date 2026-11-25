import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {BRIEFING} from './constants';

export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  const progress = Math.min(1, Math.max(0, frame / durationInFrames));

  return (
    <div
      style={{
        position: 'absolute',
        top: 152,
        left: 60,
        width: 960,
        height: 6,
        borderRadius: 4,
        background: 'rgba(255, 255, 255, 0.15)',
        overflow: 'hidden',
        zIndex: 100,
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.5)',
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: '100%',
          background: `linear-gradient(90deg, ${BRIEFING.cores.marca} 0%, ${BRIEFING.cores.apoio} 100%)`,
          borderRadius: 4,
          boxShadow: `0 0 10px ${BRIEFING.cores.marca}`,
        }}
      />
    </div>
  );
};
