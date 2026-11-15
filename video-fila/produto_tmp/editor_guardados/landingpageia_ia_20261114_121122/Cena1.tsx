import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
} from 'remotion';

interface Cena1Props {
  fontFamily: string;
  destaque: string;
}

export const Cena1: React.FC<Cena1Props> = ({fontFamily, destaque}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom contínuo e suave na filmagem do apresentador
  const videoScale = interpolate(frame, [0, 229], [1.0, 1.045], {
    extrapolateRight: 'clamp',
  });

  // Badge "O PROBLEMA" entra no frame 5 (0.16s)
  const badgeSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Card fase 1: entra no frame 18 (0.6s)
  const cardPhase1Spring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Transição para fase 2 no frame 125 (4.16s na cena, ~9.5s no vídeo: "não transformava os visitantes em clientes")
  const phase2 = frame >= 125;
  const cardPhase2Spring = spring({
    frame: frame - 125,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Flutuação sutil do card no topo
  const floatY = Math.sin(frame * 0.1) * 2;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* Vídeo do Dono em tela cheia com zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 60%',
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

      {/* Degradê sutil exclusivo no topo (y=0 a 320) para máxima legibilidade sem tocar o rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 310,
          background:
            'linear-gradient(to bottom, rgba(10, 14, 23, 0.88) 0%, rgba(10, 14, 23, 0.45) 70%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Faixa superior informativa ultra compacta (y=160 a 280) - ROSTO 100% LIVRE COM RESPIRO > 60PX */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 8,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* Badge: O PROBLEMA */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '6px 20px',
            borderRadius: 20,
            backgroundColor: 'rgba(17, 24, 39, 0.94)',
            border: `2px solid ${destaque}`,
            boxShadow: '0 4px 16px rgba(0,0,0,0.6)',
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O Problema
          </span>
        </div>

        {/* Card Dinâmico no topo - compacto para não aproximar do cabelo */}
        {!phase2 ? (
          <div
            style={{
              padding: '10px 24px',
              borderRadius: 16,
              backgroundColor: 'rgba(17, 24, 39, 0.94)',
              border: '2px solid rgba(255, 255, 255, 0.15)',
              boxShadow: '0 8px 24px rgba(0,0,0,0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transform: `scale(${cardPhase1Spring}) translateY(${(1 - cardPhase1Spring) * 15}px)`,
              opacity: cardPhase1Spring,
            }}
          >
            <span
              style={{
                fontSize: 36,
                fontWeight: 800,
                color: '#FFFFFF',
                textAlign: 'center',
                textWrap: 'balance',
              }}
            >
              Site institucional tradicional
            </span>
          </div>
        ) : (
          <div
            style={{
              padding: '10px 24px',
              borderRadius: 16,
              backgroundColor: 'rgba(24, 18, 12, 0.95)',
              border: `2px solid ${destaque}`,
              boxShadow: `0 8px 28px rgba(0,0,0,0.8), 0 0 16px rgba(245, 158, 11, 0.25)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transform: `scale(${cardPhase2Spring}) translateY(${(1 - cardPhase2Spring) * 15}px)`,
              opacity: cardPhase2Spring,
            }}
          >
            <span
              style={{
                fontSize: 36,
                fontWeight: 900,
                color: '#FFFFFF',
                textAlign: 'center',
                textWrap: 'balance',
              }}
            >
              Não transformava{' '}
              <span style={{color: destaque}}>visitantes em clientes</span>
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
