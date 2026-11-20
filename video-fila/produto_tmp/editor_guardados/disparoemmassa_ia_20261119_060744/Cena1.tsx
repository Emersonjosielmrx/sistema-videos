import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom lento contínuo no vídeo do dono (1.00 -> 1.06)
  const videoScale = interpolate(frame, [0, 222], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Entrada do selo "O PROBLEMA"
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card 1: "DISPARO NA BASE INTEIRA" (surge aos ~0.7s / frame 20)
  const card1Spring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Transição do Card 1 para Card 2 aos ~4.5s (frame 135)
  const card1Exit = interpolate(frame, [130, 140], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Card 2: "RISCO NO NÚMERO PRINCIPAL" (surge aos ~4.7s / frame 140)
  const card2Spring = spring({
    frame: frame - 140,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Micro flutuação contínua nos cards do topo
  const floatY = Math.sin(frame * 0.1) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
      }}
    >
      {/* Vídeo do Dono em Tela Cheia com Zoom Contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 45%',
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
      </div>

      {/* Camada sutil de vinheta no topo para leitura cristalina dos cards sem escurecer o apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(180deg, rgba(10, 14, 23, 0.85) 0%, rgba(10, 14, 23, 0.4) 65%, rgba(10, 14, 23, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* TOPO INFORMATIVO (y = 165 a 390) — TOTALMENTE ACIMA DA CABEÇA DO DONO */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
          transform: `translateY(${floatY}px)`,
          zIndex: 30,
        }}
      >
        {/* Selo de Etapa / Rótulo: 01 • O PROBLEMA */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 26px',
            borderRadius: 999,
            background: 'rgba(17, 24, 39, 0.92)',
            border: '1.5px solid rgba(239, 68, 68, 0.6)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
            transform: `translateY(${(1 - badgeSpring) * -20}px) scale(${badgeSpring})`,
            opacity: badgeSpring,
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            01 • O Problema
          </span>
        </div>

        {/* Card 1: Disparo para a base inteira (frames 20 a 135) */}
        {frame >= 20 && frame < 140 && (
          <div
            style={{
              width: '100%',
              maxWidth: 920,
              padding: '20px 32px',
              borderRadius: 24,
              background: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid rgba(255, 255, 255, 0.15)',
              backdropFilter: 'blur(16px)',
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              transform: `scale(${card1Spring})`,
              opacity: card1Spring * card1Exit,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span style={{fontSize: 40}}>📤</span>
              <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 40,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    lineHeight: 1.15,
                  }}
                >
                  Disparo na Base Inteira
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#94A3B8',
                  }}
                >
                  Muitos envios simultâneos
                </span>
              </div>
            </div>
            <div
              style={{
                padding: '6px 16px',
                borderRadius: 12,
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid #EF4444',
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#FCA5A5',
              }}
            >
              Alto Risco
            </div>
          </div>
        )}

        {/* Card 2: Risco de Bloqueio no Número Principal (a partir do frame 140) */}
        {frame >= 140 && (
          <div
            style={{
              width: '100%',
              maxWidth: 920,
              padding: '20px 32px',
              borderRadius: 24,
              background: 'rgba(17, 24, 39, 0.95)',
              border: '2px solid rgba(239, 68, 68, 0.8)',
              backdropFilter: 'blur(16px)',
              boxShadow: '0 16px 40px rgba(239, 68, 68, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              transform: `scale(${card2Spring})`,
              opacity: card2Spring,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span style={{fontSize: 42}}>⚠️</span>
              <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 40,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    lineHeight: 1.15,
                  }}
                >
                  Número Principal Comprometido
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#FCA5A5',
                  }}
                >
                  Risco de perda do atendimento
                </span>
              </div>
            </div>
            <div
              style={{
                padding: '8px 18px',
                borderRadius: 12,
                background: '#EF4444',
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                boxShadow: '0 0 16px rgba(239, 68, 68, 0.6)',
              }}
            >
              Perigo
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
