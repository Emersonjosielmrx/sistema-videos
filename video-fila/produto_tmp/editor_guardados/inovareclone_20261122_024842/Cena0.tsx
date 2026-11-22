import React from 'react';
import {useCurrentFrame, useVideoConfig, spring, interpolate, Img, staticFile} from 'remotion';
import {BRIEFING} from './constants';

type Props = {
  fontFamily: string;
};

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração da cena: 0.0s a 4.55s (136 frames)
  // Zoom contínuo do fundo para garantir ≥ 4% de movimento contínuo
  const bgScale = interpolate(frame, [0, 136], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });

  const bgTranslateY = interpolate(frame, [0, 136], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Fade out suave na transição para a Cena 1 (a partir de 4.2s = frame 126)
  const cenaOpacity = interpolate(frame, [125, 136], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Gancho inicial aos 0.15s (frame 4)
  const topBadgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Linha 1: "FALTA TEMPO?" entra aos 0.30s (frame 9)
  const line1Spring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Linha 2: "PARA EXPLICAR" entra aos 1.15s (frame 34)
  const line2Spring = spring({
    frame: frame - 34,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Linha 3: "SEUS SERVIÇOS" entra aos 1.80s (frame 54)
  const line3Spring = spring({
    frame: frame - 54,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Linha 4: "EM VÍDEO? 🎬" entra aos 2.60s (frame 78)
  const line4Spring = spring({
    frame: frame - 78,
    fps,
    config: {damping: 11, stiffness: 150},
  });

  // Pulso do elemento focal (relógio / radar da dor da falta de tempo)
  const radarPulse = (Math.sin(frame / 6) + 1) / 2;
  const clockRotation = frame * 2.5;

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
      {/* Imagem de Fundo com zoom e pan contínuos */}
      <div
        style={{
          position: 'absolute',
          inset: -40,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Camada de Contraste e Escurecimento Tecnológico */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 40%, rgba(15, 23, 42, 0.72) 0%, rgba(11, 13, 19, 0.94) 80%)',
        }}
      />

      {/* Grid sutil futurista */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.12,
          backgroundImage:
            'linear-gradient(to right, rgba(139, 92, 246, 0.3) 1px, transparent 1px), linear-gradient(to bottom, rgba(139, 92, 246, 0.3) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
          transform: `translateY(${frame % 60}px)`,
        }}
      />

      {/* Top Badge (y=175 a 230) - Gancho da Tela */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          transform: `scale(${topBadgeSpring})`,
          opacity: topBadgeSpring,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 30,
            background: 'rgba(15, 23, 42, 0.92)',
            border: `1.5px solid ${BRIEFING.cores.marca}`,
            boxShadow: '0 8px 24px rgba(139, 92, 246, 0.35)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
              transform: `scale(${1 + radarPulse * 0.3})`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            {BRIEFING.gancho_tela}
          </span>
        </div>
      </div>

      {/* Bloco Central Cinético (y=360 a 1150) */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
        }}
      >
        {/* Ícone de Relógio Dinâmico (Dor da falta de tempo) */}
        <div
          style={{
            width: 110,
            height: 110,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(31, 41, 55, 0.8))',
            border: `2px solid ${BRIEFING.cores.destaque_brilho}`,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            marginBottom: 36,
            boxShadow: `0 0 ${20 + radarPulse * 15}px rgba(139, 92, 246, 0.5)`,
            transform: `scale(${1 + radarPulse * 0.05})`,
          }}
        >
          <svg
            width="64"
            height="64"
            viewBox="0 0 24 24"
            fill="none"
            stroke={BRIEFING.cores.destaque_claro}
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12" />
            <line
              x1="12"
              y1="12"
              x2="17"
              y2="12"
              transform={`rotate(${clockRotation} 12 12)`}
              stroke="#FFFFFF"
              strokeWidth="2.5"
            />
          </svg>
        </div>

        {/* Linha 1: FALTA TEMPO? */}
        {frame >= 8 && (
          <div
            style={{
              transform: `scale(${line1Spring}) translateY(${(1 - line1Spring) * 30}px)`,
              opacity: line1Spring,
              marginBottom: 20,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              flexWrap: 'wrap',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 74,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '-0.02em',
                textShadow: '0 4px 16px rgba(0,0,0,0.8)',
              }}
            >
              FALTA
            </span>
            <div
              style={{
                background: `linear-gradient(135deg, ${BRIEFING.cores.marca}, #7C3AED)`,
                padding: '6px 26px',
                borderRadius: 18,
                boxShadow: '0 10px 30px rgba(139, 92, 246, 0.6)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 76,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  letterSpacing: '-0.02em',
                }}
              >
                TEMPO?
              </span>
            </div>
          </div>
        )}

        {/* Linha 2: PARA EXPLICAR */}
        {frame >= 33 && (
          <div
            style={{
              transform: `scale(${line2Spring}) translateY(${(1 - line2Spring) * 25}px)`,
              opacity: line2Spring,
              marginBottom: 16,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 54,
                fontWeight: 800,
                color: '#E2E8F0',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                textShadow: '0 3px 12px rgba(0,0,0,0.8)',
              }}
            >
              PARA EXPLICAR
            </span>
          </div>
        )}

        {/* Linha 3: SEUS SERVIÇOS */}
        {frame >= 53 && (
          <div
            style={{
              transform: `scale(${line3Spring}) translateY(${(1 - line3Spring) * 25}px)`,
              opacity: line3Spring,
              marginBottom: 32,
              position: 'relative',
              display: 'inline-block',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 66,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '-0.01em',
                textTransform: 'uppercase',
                textShadow: '0 4px 18px rgba(0,0,0,0.9)',
              }}
            >
              SEUS SERVIÇOS
            </span>
            {/* Barra luminosa de destaque abaixo */}
            <div
              style={{
                height: 6,
                width: '100%',
                background: `linear-gradient(90deg, transparent, ${BRIEFING.cores.destaque}, transparent)`,
                borderRadius: 3,
                marginTop: 8,
                boxShadow: `0 0 12px ${BRIEFING.cores.destaque}`,
              }}
            />
          </div>
        )}

        {/* Linha 4: EM VÍDEO? */}
        {frame >= 77 && (
          <div
            style={{
              transform: `scale(${line4Spring}) translateY(${(1 - line4Spring) * 20}px)`,
              opacity: line4Spring,
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 16,
                background: 'rgba(15, 23, 42, 0.95)',
                border: `2px solid ${BRIEFING.cores.destaque}`,
                padding: '14px 36px',
                borderRadius: 24,
                boxShadow: '0 12px 36px rgba(139, 92, 246, 0.45)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 56,
                  fontWeight: 900,
                  color: BRIEFING.cores.destaque_claro,
                  letterSpacing: '0.02em',
                  textTransform: 'uppercase',
                }}
              >
                EM VÍDEO? 🎬
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
