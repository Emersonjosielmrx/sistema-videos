import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES, fontFamily} from './constants';

export const Cena3: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Escala calibrada com push-in e translação para eliminar bordas e proteger o apresentador
  const videoScale = interpolate(frame, [0, 241], [1.22, 1.28], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada e saída
  const fadeIn = interpolate(frame, [0, 10], [0.8, 1], {
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(frame, [228, 241], [1, 0.85], {
    extrapolateRight: 'clamp',
  });

  // Badges no topo
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card 1: CONTEÚDO FREQUENTE (entra no frame 18 ~ 0.6s)
  const card1Spring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Card 2: MAIS TEMPO PARA CLIENTES (entra no frame 122 ~ 4.0s)
  const card2Spring = spring({
    frame: frame - 122,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Flutuação sutil do HUD
  const floatY = Math.sin(frame / 14) * 3;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: CORES.fundoEscuro,
        overflow: 'hidden',
        fontFamily,
        opacity: fadeIn * fadeOut,
      }}
    >
      {/* Vídeo do Avatar IA posicionado para preservar cabeça e tronco */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateY(180px) scale(${videoScale})`,
          transformOrigin: '50% 50%',
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
        {/* Leve gradiente no topo e base para leitura perfeita sem escurecer o apresentador */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(11, 13, 20, 0.78) 0%, rgba(11, 13, 20, 0.12) 22%, rgba(11, 13, 20, 0.0) 45%, rgba(11, 13, 20, 0.2) 75%, rgba(11, 13, 20, 0.85) 100%)',
          }}
        />
      </div>

      {/* ÁREA SUPERIOR (y: 160 a 244) — Cabelo começa em y: 286 -> Respiro de 42 px garantido! */}
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
          zIndex: 20,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* Linha 1: Badges Superiores */}
        <div
          style={{
            opacity: Math.max(0, badgeSpring),
            transform: `translateY(${(1 - badgeSpring) * -14}px)`,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          {/* Badge O RESULTADO */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '6px 18px',
              backgroundColor: 'rgba(15, 23, 42, 0.92)',
              border: '1.5px solid rgba(16, 185, 129, 0.5)',
              borderRadius: 20,
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.6)',
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: '#10B981',
                boxShadow: '0 0 10px #10B981',
              }}
            />
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 1.2,
                textTransform: 'uppercase',
              }}
            >
              O Resultado
            </span>
          </div>

          {/* Selo Holográfico Avatar IA */}
          <div
            style={{
              padding: '6px 16px',
              backgroundColor: 'rgba(109, 40, 217, 0.92)',
              border: '1px solid rgba(167, 139, 250, 0.6)',
              borderRadius: 18,
              boxShadow: '0 4px 16px rgba(109, 40, 217, 0.5)',
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 0.8,
              }}
            >
              ✦ Avatar com IA
            </span>
          </div>
        </div>

        {/* Linha 2: Card Cinético Compacto (não invade a área da cabeça) */}
        {frame < 122 ? (
          // Fase 1: CONTEÚDO FREQUENTE NO PERFIL
          frame >= 18 && (
            <div
              style={{
                opacity: Math.max(0, card1Spring),
                transform: `scale(${Math.max(0.88, card1Spring)})`,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 22px',
                backgroundColor: 'rgba(15, 23, 42, 0.92)',
                border: '1.5px solid rgba(16, 185, 129, 0.5)',
                borderRadius: 20,
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
              }}
            >
              <span
                style={{
                  fontSize: 33,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  letterSpacing: 0.5,
                  textTransform: 'uppercase',
                }}
              >
                Conteúdo frequente no perfil
              </span>
            </div>
          )
        ) : (
          // Fase 2: MAIS TEMPO PARA CLIENTES
          <div
            style={{
              opacity: Math.max(0, card2Spring),
              transform: `scale(${Math.max(0.88, card2Spring)})`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 22px',
              backgroundColor: 'rgba(15, 23, 42, 0.92)',
              border: '1.5px solid rgba(139, 92, 246, 0.5)',
              borderRadius: 20,
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
            }}
          >
            <span
              style={{
                fontSize: 33,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 0.5,
                textTransform: 'uppercase',
              }}
            >
              Mais tempo para os clientes
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
