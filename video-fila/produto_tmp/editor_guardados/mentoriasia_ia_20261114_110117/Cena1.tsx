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

export const Cena1: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera: push-in leve (1.00 -> 1.06)
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Transição do tema aos 7.6s (frame local ~96 da cena)
  const virada = frame >= 96;
  const animVirada = spring({
    frame: frame - 96,
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
      {/* Vídeo do Dono em Tela Cheia com Push-in sutil */}
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
            width: 1080,
            height: 1920,
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Vinheta superior muito leve APENAS atrás da barra de status (y < 420), preservando o rosto */}
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
        {/* Rótulo Oficial da Cena: A Situação */}
        <div
          style={{
            padding: '8px 24px',
            borderRadius: 24,
            background: 'rgba(15, 23, 42, 0.85)',
            border: `2px solid ${virada ? COLORS.marcaClara : COLORS.destaque}`,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: virada ? COLORS.verdeSucesso : COLORS.amareloAlerta,
              boxShadow: `0 0 8px ${
                virada ? COLORS.verdeSucesso : COLORS.amareloAlerta
              }`,
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
            A Situação
          </span>
        </div>

        {/* Card Dinâmico no Topo: Muda aos 7.6s quando a voz anuncia a solução */}
        {!virada ? (
          <div
            style={{
              padding: '14px 28px',
              borderRadius: 20,
              background: 'rgba(239, 68, 68, 0.22)',
              border: '2px solid rgba(239, 68, 68, 0.6)',
              backdropFilter: 'blur(8px)',
              boxShadow: '0 8px 25px rgba(0,0,0,0.6)',
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
                color: '#FECACA',
                textTransform: 'uppercase',
                letterSpacing: '0.02em',
              }}
            >
              Fluxos Lentos na Empresa
            </span>
          </div>
        ) : (
          <div
            style={{
              transform: `scale(${Math.min(1, Math.max(0, animVirada))})`,
              padding: '14px 30px',
              borderRadius: 20,
              background: 'linear-gradient(135deg, rgba(30, 58, 138, 0.95), rgba(37, 99, 235, 0.95))',
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
              Consultoria de Otimização & IA
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
