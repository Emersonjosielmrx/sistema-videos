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

  // Movimento de câmera suave e contínuo + Transição Dinâmica de Corte
  // Rebaixamento vertical de 45px para garantir respiro total do cabelo do apresentador
  const introPunch = interpolate(frame, [0, 8], [1.14, 1.0], {
    extrapolateRight: 'clamp',
  });
  const videoScale =
    interpolate(frame, [0, 216], [1.02, 1.07], {
      extrapolateRight: 'clamp',
    }) * introPunch;

  const videoY = interpolate(frame, [0, 216], [45, 38], {
    extrapolateRight: 'clamp',
  });

  // Transição de overlap nas bordas
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(frame, [206, 216], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cenaOpacity = fadeIn * fadeOut;

  // Flash ciano suave de transição dinâmica conectando o gancho (Cena 0) à fala do apresentador (Cena 1)
  const flashOpacity = interpolate(frame, [0, 7], [0.45, 0], {
    extrapolateRight: 'clamp',
  });

  // Entrada do badge fixo padronizado com fundo escuro sólido desde o frame inicial
  const pillSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Entrada do alerta de conexões desprotegidas aos ~3.8s (frame 114) na fala "sem proteção adequada"
  const alertCardSpring = spring({
    frame: frame - 114,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Micro-animações contínuas
  const headerFloat = Math.sin(frame / 14) * 2.5;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        opacity: cenaOpacity,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Vídeo do Apresentador com Movimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale}) translateY(${videoY}px)`,
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
        {/* Véu de contraste superior garantindo separação visual */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 320,
            background:
              'linear-gradient(180deg, rgba(10, 15, 28, 0.82) 0%, rgba(10, 15, 28, 0.35) 70%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Flash Dinâmico de Corte (transição entre cena 0 e cena 1) */}
      {frame <= 7 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: '#0EA5E9',
            opacity: flashOpacity,
            pointerEvents: 'none',
            zIndex: 40,
          }}
        />
      )}

      {/* Topo Único (y=162) — Selo Padronizado Subido em 40px com Fundo 100% Opaco */}
      <div
        style={{
          position: 'absolute',
          top: 162,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `translateY(${headerFloat}px)`,
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            background: '#151922',
            border: '2px solid rgba(239, 68, 68, 0.85)',
            padding: '8px 26px',
            borderRadius: 18,
            boxShadow:
              '0 8px 30px rgba(0, 0, 0, 0.9), 0 0 25px rgba(239, 68, 68, 0.35)',
            opacity: Math.max(0, Math.min(1, pillSpring)),
            transform: `translateY(${(1 - Math.min(1, pillSpring)) * -18}px)`,
          }}
        >
          {/* Ícone de Cadeado Aberto */}
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#EF4444"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 9.9-1" />
          </svg>
          <span
            style={{
              fontSize: 34,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1,
              textTransform: 'uppercase',
            }}
          >
            SISTEMA EXPOSTO • SEM PROTEÇÃO
          </span>
        </div>
      </div>

      {/* Alerta animado secundário na fala "sem proteção adequada" subido para y=218 para manter folga total do cabelo */}
      {frame >= 114 && (
        <div
          style={{
            position: 'absolute',
            top: 218,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            zIndex: 20,
            opacity: Math.max(0, Math.min(1, alertCardSpring)),
            transform: `translateY(${(1 - Math.min(1, alertCardSpring)) * -14}px)`,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              background: 'rgba(21, 25, 34, 0.96)',
              border: '1.5px solid rgba(239, 68, 68, 0.8)',
              padding: '6px 22px',
              borderRadius: 14,
              boxShadow: '0 6px 20px rgba(0, 0, 0, 0.8), 0 0 15px rgba(239, 68, 68, 0.25)',
            }}
          >
            <span style={{fontSize: 26}}>⚠️</span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#FCA5A5',
                letterSpacing: 1,
              }}
            >
              RISCO: CONEXÕES DESPROTEGIDAS
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
