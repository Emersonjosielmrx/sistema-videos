import React from 'react';
import {useCurrentFrame, useVideoConfig, spring, interpolate, OffthreadVideo, staticFile} from 'remotion';
import {BRIEFING} from './constants';

type Props = {
  fontFamily: string;
};

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração da cena: 4.2s a 12.38s (~245 frames)
  // Zoom contínuo no vídeo do dono: 1.00 -> 1.06
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Fade in rápido no início da cena (frame 0 a 8) e fade out suave no fim (frame 235 a 245)
  const cenaOpacity = interpolate(frame, [0, 8, 235, 245], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Entrada do rótulo "O PROBLEMA" aos 0.2s da cena (frame 6)
  const rotuloSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Tag 1: "Agenda Cheia ⏳" entra aos 1.8s da cena (frame 54, fala: "o dia atendendo")
  const tag1Spring = spring({
    frame: frame - 54,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Tag 2: "Sem tempo p/ gravar 📹❌" entra aos 4.3s da cena (frame 129, fala: "nunca sobrava tempo")
  const tag2Spring = spring({
    frame: frame - 129,
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
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Vinheta superior muito leve para dar legibilidade ao topo sem escurecer o rosto */}
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
            01
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
            O PROBLEMA
          </span>
        </div>

        {/* Tags cinéticas dinâmicas de apoio que surgem com a fala */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 12,
            flexWrap: 'nowrap',
          }}
        >
          {frame >= 50 && (
            <div
              style={{
                background: 'rgba(31, 41, 55, 0.95)',
                border: '1.5px solid rgba(255, 255, 255, 0.2)',
                padding: '6px 16px',
                borderRadius: 16,
                boxShadow: '0 6px 18px rgba(0,0,0,0.6)',
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
                  fontWeight: 700,
                  color: '#F3F4F6',
                }}
              >
                Agenda Lotada ⏳
              </span>
            </div>
          )}

          {frame >= 125 && (
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.95)',
                border: '1.5px solid #FCA5A5',
                padding: '6px 16px',
                borderRadius: 16,
                boxShadow: '0 6px 18px rgba(239, 68, 68, 0.4)',
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
                Sem tempo p/ gravar 📹❌
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
