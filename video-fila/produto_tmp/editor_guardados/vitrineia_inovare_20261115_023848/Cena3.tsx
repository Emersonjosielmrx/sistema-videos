import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Cena3: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tRel = frame / fps;
  const tAbs = 20.16 + tRel; // 20.16s to 28.34s

  // Closer punch-in camera scale (1.13 -> 1.19) + emphasis zoom on 'orienta quem está em dúvida' to contrast with Cena 1's wider framing while keeping head >180px below top card
  const orientaZoom = spring({
    frame: Math.max(0, frame - Math.round((22.91 - 20.16) * fps)),
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const baseScale = interpolate(tRel, [0, 8.18], [1.11, 1.16], {
    extrapolateRight: 'clamp',
  });
  const videoScale = baseScale + orientaZoom * 0.04;
  const videoX = interpolate(tRel, [0, 8.18], [-22, 18], {
    extrapolateRight: 'clamp',
  });

  const enterIn = spring({frame, fps, config: {damping: 14, stiffness: 150}});
  const exitOut = interpolate(tAbs, [27.99, 28.32], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Exact spoken timestamps in Cena 3:
  // "orienta quem está em dúvida," (22.911s..24.931s)
  // "apresenta outros produtos da loja" (25.291s..27.331s)
  // "e fecha a venda." (27.331s..28.331s)
  const orientaAtivo = tAbs >= 22.91;
  const apresentaAtivo = tAbs >= 25.29;
  const fechaAtivo = tAbs >= 27.33;

  const floatY = Math.sin(tRel * 3.1) * 5;
  const pulse = 1 + Math.sin(tRel * 5.5) * 0.025;

  // Dynamic single-banner status text that evolves cleanly with spoken words without fragmented top boxes
  let statusTexto = 'Bot com o conhecimento da loja';
  if (fechaAtivo) {
    statusTexto = '✓ Orienta, mostra opções e fecha a venda';
  } else if (apresentaAtivo) {
    statusTexto = '✓ Apresenta outros produtos da loja';
  } else if (orientaAtivo) {
    statusTexto = '✓ Orienta o cliente na dúvida';
  }

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', opacity: exitOut}}>
      {/* Fullscreen owner video — clear face, no face dimming */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transformOrigin: '50% 22%',
            transform: `scale(${videoScale}) translateX(${videoX}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Top-only gradient for HUD readability */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 380,
          background:
            'linear-gradient(180deg, rgba(17,24,39,0.82) 0%, rgba(17,24,39,0.38) 65%, rgba(17,24,39,0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* SINGLE CLEAN TOP HEADER BANNER (y=158..315) — lets presenter breathe without competing fragmented boxes */}
      <div
        style={{
          position: 'absolute',
          top: 158,
          left: 60,
          right: 60,
          transform: `translateY(${interpolate(enterIn, [0, 1], [-28, 0]) + floatY}px)`,
          opacity: enterIn,
          backgroundColor: 'rgba(17, 24, 39, 0.92)',
          border: '2.5px solid #A78BFA',
          borderRadius: 24,
          padding: '16px 26px',
          boxShadow: '0 14px 32px rgba(0,0,0,0.5)',
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              backgroundColor: '#A78BFA',
              color: '#121216',
              padding: '4px 18px',
              borderRadius: 999,
              textTransform: 'uppercase',
            }}
          >
            O resultado
          </span>
          <span
            style={{
              fontFamily,
              fontSize: 33,
              fontWeight: 800,
              color: '#A78BFA',
            }}
          >
            Vitrine IA
          </span>
        </div>

        <div
          style={{
            fontFamily,
            fontSize: 38,
            fontWeight: 900,
            color: '#FFFFFF',
            lineHeight: 1.15,
            transform: `scale(${orientaAtivo ? pulse : 1})`,
            transformOrigin: 'left center',
          }}
        >
          {statusTexto}
        </div>
      </div>
    </AbsoluteFill>
  );
};
