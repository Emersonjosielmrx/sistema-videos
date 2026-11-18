import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena1Props {
  fontFamily: string;
}

export const Cena1: React.FC<Cena1Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração total da cena 1: ~245 frames
  const zoom = interpolate(frame, [0, 245], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Badge "O PROBLEMA"
  const sprBadge = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card Fase 1: "Centenas de contatos parados na agenda" (~frame 35)
  const sprCard1 = spring({
    frame: frame - 32,
    fps,
    config: {damping: 15, stiffness: 110},
  });

  // Transição para Fase 2: "Como reaquecer conversas?" (~frame 155, quando a fala diz "sem saber como reaquecer")
  const transFase2 = interpolate(frame, [150, 165], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Shimmer contínuo no card superior
  const shimmerPos = (frame * 3) % 400;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        background: '#0B0F17',
      }}
    >
      {/* Vídeo do Dono em tela cheia com leve zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${zoom})`,
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
        {/* Gradiente sutil no topo para garantir legibilidade dos cards sem cobrir o rosto */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 440,
            background:
              'linear-gradient(180deg, rgba(11, 15, 23, 0.88) 0%, rgba(11, 15, 23, 0.4) 65%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* TOP ZONE ESTRITA: y=165 a y=390 (rosto do apresentador começa em y ~420) */}
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
          zIndex: 30,
        }}
      >
        {/* Badge do Rótulo "O PROBLEMA" */}
        {frame >= 5 && (
          <div
            style={{
              opacity: sprBadge,
              transform: `scale(${0.85 + sprBadge * 0.15}) translateY(${
                (1 - sprBadge) * 15
              }px)`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 22px',
              borderRadius: 24,
              background: 'rgba(239, 68, 68, 0.22)',
              border: '2px solid rgba(239, 68, 68, 0.55)',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.6)',
            }}
          >
            <span style={{fontSize: 28}}>⚠️</span>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FECACA',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              O PROBLEMA
            </span>
          </div>
        )}

        {/* Card Dinâmico no Topo */}
        {frame >= 30 && (
          <div
            style={{
              position: 'relative',
              width: '100%',
              maxWidth: 960,
              borderRadius: 24,
              background: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid rgba(255, 255, 255, 0.15)',
              padding: '18px 28px',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.7)',
              overflow: 'hidden',
              minHeight: 130,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              textAlign: 'center',
            }}
          >
            {/* Shimmer de luz passando no card */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: -200 + shimmerPos * 3,
                width: 120,
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.08), transparent)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            {/* Conteúdo Fase 1: Centenas de contatos parados na agenda */}
            {transFase2 < 1 && (
              <div
                style={{
                  opacity: (1 - transFase2) * sprCard1,
                  transform: `translateY(-${transFase2 * 12}px)`,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 42,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                    letterSpacing: 1,
                    textShadow: '0 2px 8px rgba(0,0,0,0.8)',
                  }}
                >
                  CENTENAS DE CONTATOS PARADOS
                </div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 16,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#F87171',
                      background: 'rgba(239, 68, 68, 0.2)',
                      padding: '4px 14px',
                      borderRadius: 12,
                    }}
                  >
                    📇 Agenda Inativa
                  </span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#94A3B8',
                    }}
                  >
                    ⏸️ Sem Contato
                  </span>
                </div>
              </div>
            )}

            {/* Conteúdo Fase 2: Como reaquecer essas conversas? */}
            {transFase2 > 0 && (
              <div
                style={{
                  position: transFase2 < 1 ? 'absolute' : 'relative',
                  opacity: transFase2,
                  transform: `translateY(${(1 - transFase2) * 12}px)`,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 40,
                    fontWeight: 900,
                    color: '#FEF08A',
                    textTransform: 'uppercase',
                    letterSpacing: 1,
                  }}
                >
                  COMO REAQUECER ESSAS CONVERSAS?
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#CBD5E1',
                    background: 'rgba(255, 255, 255, 0.1)',
                    padding: '4px 16px',
                    borderRadius: 12,
                  }}
                >
                  💬 Mensagens Pausadas na Agenda
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
