import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom leve e contínuo no vídeo do apresentador (1.00 -> 1.05)
  const videoScale = interpolate(frame, [0, 226], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Fade de saída nos últimos frames da cena (frames 212 a 226)
  const exitOpacity = interpolate(frame, [212, 226], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Badge "O PROBLEMA" entra aos ~0.25s (frame 8)
  const badgeSpring = spring({
    frame: Math.max(0, frame - 8),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Título principal entra aos ~0.7s (frame 22) na fala "Eu perdia pedidos de suporte"
  const titleSpring = spring({
    frame: Math.max(0, frame - 22),
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Sub-badge entra aos ~3.8s (frame 115) na fala "e ninguém abria chamado"
  const subBadgeSpring = spring({
    frame: Math.max(0, frame - 115),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  const pulseAlert = 1 + Math.sin(frame / 6) * 0.04;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        opacity: exitOpacity,
      }}
    >
      {/* Vídeo do apresentador (OffthreadVideo em tela cheia com zoom sutil) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: 'center 40%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />

        {/* Gradiente sutil no topo para garantir legibilidade dos textos sem escurecer o rosto */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(180deg, rgba(15, 23, 42, 0.92) 0%, rgba(15, 23, 42, 0.70) 50%, rgba(15, 23, 42, 0) 100%)',
          }}
        />
      </div>

      {/* TOPO INFORMATIVO EXCLUSIVO (y = 165 a 420) — ROSTO 100% LIVRE ABAIXO */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 20,
        }}
      >
        {/* Badge do Rótulo "O PROBLEMA" */}
        <div
          style={{
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 999,
            background: 'rgba(15, 23, 42, 0.88)',
            backdropFilter: 'blur(12px)',
            border: '1.5px solid rgba(239, 68, 68, 0.5)',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.6)',
            marginBottom: 14,
          }}
        >
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
              transform: `scale(${pulseAlert})`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: '#FCA5A5',
            }}
          >
            O PROBLEMA
          </span>
        </div>

        {/* Título Forte no Alto */}
        <div
          style={{
            transform: `translateY(${(1 - titleSpring) * 25}px) scale(${titleSpring})`,
            opacity: titleSpring,
            textAlign: 'center',
            maxWidth: 960,
            background: 'rgba(15, 23, 42, 0.82)',
            backdropFilter: 'blur(16px)',
            padding: '16px 28px',
            borderRadius: 20,
            border: '1.5px solid rgba(255, 255, 255, 0.14)',
            boxShadow: '0 12px 30px rgba(0,0,0,0.7)',
          }}
        >
          <h2
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              lineHeight: 1.18,
              color: '#FFFFFF',
              margin: 0,
              textWrap: 'balance',
            }}
          >
            PEDIDOS DE SUPORTE PERDIDOS{' '}
            <span
              style={{
                color: '#F87171',
                textDecoration: 'underline',
                textDecorationColor: '#EF4444',
              }}
            >
              NA CONVERSA
            </span>
          </h2>
        </div>

        {/* Sub-chip dinâmico sincronizado aos ~3.8s */}
        {frame >= 115 && (
          <div
            style={{
              marginTop: 14,
              transform: `scale(${subBadgeSpring})`,
              opacity: subBadgeSpring,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '6px 20px',
              borderRadius: 999,
              background: 'rgba(239, 68, 68, 0.20)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#FECACA',
              }}
            >
              ⚠️ SEM CHAMADO • SUPORTE ESQUECIDO
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
