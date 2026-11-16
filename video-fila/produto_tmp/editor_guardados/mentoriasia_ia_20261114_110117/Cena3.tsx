import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {COLORS, fontFamily} from './theme';

export const Cena3: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera: push-in suave (1.00 -> 1.06)
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Mudança da mensagem aos 23.6s (frame local ~108 da cena)
  const segundaFase = frame >= 108;
  const animSegundaFase = spring({
    frame: frame - 108,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do badge no topo
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        background: COLORS.apoio,
      }}
    >
      {/* Vídeo do Dono em Tela Cheia */}
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
            width: 1080,
            height: 1920,
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Vinheta superior muito leve APENAS atrás do topo (y < 420), preservando o rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 440,
          background:
            'linear-gradient(180deg, rgba(11, 15, 25, 0.85) 0%, rgba(11, 15, 25, 0.4) 75%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Zone: Elementos de Contexto (y=175 a 410) — Rosto livre abaixo de y=450 */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
          zIndex: 20,
          transform: `scale(${Math.min(1, Math.max(0, badgeSpring))})`,
        }}
      >
        {/* Rótulo Oficial da Cena: O Resultado */}
        <div
          style={{
            padding: '8px 24px',
            borderRadius: 24,
            background: 'rgba(15, 23, 42, 0.9)',
            border: `2px solid ${COLORS.verdeSucesso}`,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            boxShadow: '0 4px 16px rgba(16, 185, 129, 0.3)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: COLORS.verdeSucesso,
              boxShadow: `0 0 10px ${COLORS.verdeSucesso}`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            O Resultado
          </span>
        </div>

        {/* Card Dinâmico no Topo */}
        {!segundaFase ? (
          <div
            style={{
              padding: '14px 30px',
              borderRadius: 20,
              background:
                'linear-gradient(135deg, rgba(30, 58, 138, 0.95), rgba(37, 99, 235, 0.95))',
              border: '2px solid rgba(147, 197, 253, 0.8)',
              backdropFilter: 'blur(8px)',
              boxShadow: '0 10px 30px rgba(37, 99, 235, 0.5)',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: '0.02em',
              }}
            >
              Criação de Automações com IA
            </span>
          </div>
        ) : (
          <div
            style={{
              transform: `scale(${Math.min(1, Math.max(0, animSegundaFase))})`,
              padding: '14px 30px',
              borderRadius: 20,
              background:
                'linear-gradient(135deg, rgba(6, 78, 59, 0.95), rgba(16, 185, 129, 0.95))',
              border: '2px solid rgba(110, 231, 183, 0.8)',
              backdropFilter: 'blur(8px)',
              boxShadow: '0 10px 30px rgba(16, 185, 129, 0.5)',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: '0.02em',
              }}
            >
              Soluções Próprias na Rotina
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
