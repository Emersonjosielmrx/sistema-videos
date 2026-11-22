import React from 'react';
import {useCurrentFrame, useVideoConfig, spring, interpolate, OffthreadVideo, staticFile} from 'remotion';
import {BRIEFING} from './constants';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração da cena: 21.34s a 29.52s (~245 frames)
  // Zoom contínuo suave: 1.00 -> 1.06
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  const cenaOpacity = interpolate(frame, [0, 8, 235, 245], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Rótulo da etapa 3
  const rotuloSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Tag 1: "Explicações todo dia 🚀" entra aos 2.2s da cena (frame 65, fala: "explicações claras")
  const tag1Spring = spring({
    frame: frame - 65,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Tag 2: "Foco nos atendimentos 💼✨" entra aos 5.6s da cena (frame 170, fala: "foco nos atendimentos")
  const tag2Spring = spring({
    frame: frame - 170,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        opacity: cenaOpacity,
        overflow: 'hidden',
        backgroundColor: '#0B0D13',
      }}
    >
      {/* Vídeo do Dono com zoom suave contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 40%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Vinheta superior muito suave para manter rosto limpo e texto legível */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 260,
          background:
            'linear-gradient(to bottom, rgba(11, 13, 19, 0.75) 0%, rgba(11, 13, 19, 0.4) 60%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Faixa Superior (y=165 a 235) — 100% acima do topo da cabeça (y=290), respiro > 50px */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
          zIndex: 50,
        }}
      >
        {/* Rótulo da Etapa */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: 'rgba(15, 23, 42, 0.94)',
            border: `1.5px solid ${BRIEFING.cores.marca}`,
            padding: '8px 22px',
            borderRadius: 24,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
            transform: `scale(${rotuloSpring})`,
            opacity: rotuloSpring,
          }}
        >
          <div
            style={{
              padding: '2px 8px',
              borderRadius: 8,
              backgroundColor: BRIEFING.cores.marca,
              color: '#FFFFFF',
              fontFamily,
              fontSize: 24,
              fontWeight: 900,
            }}
          >
            03
          </div>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}
          >
            O RESULTADO
          </span>
        </div>

        {/* Tags cinéticas dinâmicas de apoio */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 12,
            flexWrap: 'nowrap',
          }}
        >
          {frame >= 60 && (
            <div
              style={{
                background: 'rgba(139, 92, 246, 0.95)',
                border: '1.5px solid #DDD6FE',
                padding: '6px 16px',
                borderRadius: 16,
                boxShadow: '0 6px 18px rgba(139, 92, 246, 0.45)',
                transform: `scale(${tag1Spring}) translateY(${(1 - tag1Spring) * 10}px)`,
                opacity: tag1Spring,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Explicações todo dia 🚀
              </span>
            </div>
          )}

          {frame >= 165 && (
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid #22C55E',
                padding: '6px 16px',
                borderRadius: 16,
                boxShadow: '0 6px 18px rgba(34, 197, 94, 0.35)',
                transform: `scale(${tag2Spring}) translateY(${(1 - tag2Spring) * 10}px)`,
                opacity: tag2Spring,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Foco nos atendimentos 💼✨
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
