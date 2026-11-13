import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

export const ProgressBar: React.FC<{
  corPrimaria?: string;
  corSecundaria?: string;
}> = ({
  corPrimaria = '#E11D48',
  corSecundaria = '#FACC15',
}) => {
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
        backgroundColor: 'rgba(255, 255, 255, 0.18)',
        overflow: 'hidden',
        zIndex: 100,
        boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
      }}
    >
      <div
        style={{
          width: `${progresso * 100}%`,
          height: '100%',
          borderRadius: 3,
          background: `linear-gradient(90deg, ${corPrimaria} 0%, ${corSecundaria} 100%)`,
          boxShadow: `0 0 10px ${corPrimaria}`,
        }}
      />
    </div>
  );
};
