import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena3Props {
  fontFamily: string;
}

export const Cena3: React.FC<Cena3Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração total: ~245 frames
  const zoom = interpolate(frame, [0, 245], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Badge "O RESULTADO"
  const sprBadge = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card Fase 1 ("Envio automático para milhares")
  const sprCard1 = spring({
    frame: frame - 25,
    fps,
    config: {damping: 15, stiffness: 110},
  });

  // Transição para Fase 2 ("Rotação de números de maneira prática") aos ~frame 136 (4.5s)
  const transFase2 = interpolate(frame, [134, 148], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Ciclo da rotação de chips na Fase 2 (alterna a cada ~20 frames)
  const activeChip = Math.floor((frame / 20) % 3);

  // Shimmer contínuo
  const shimmerPos = (frame * 3.5) % 400;

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
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Gradiente no topo para garantir contraste sem encobrir o apresentador */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 440,
            background:
              'linear-gradient(180deg, rgba(11, 15, 23, 0.9) 0%, rgba(11, 15, 23, 0.45) 65%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* TOP ZONE ESTRITA: y=165 a y=390 (rosto livre a partir de y=420) */}
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
        {/* Badge "O RESULTADO" */}
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
              padding: '8px 24px',
              borderRadius: 24,
              background: '#22C55E',
              boxShadow: '0 4px 18px rgba(34, 197, 94, 0.4)',
            }}
          >
            <span style={{fontSize: 26}}>🚀</span>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: '#111827',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              O RESULTADO
            </span>
          </div>
        )}

        {/* Card Dinâmico Superior */}
        {frame >= 24 && (
          <div
            style={{
              position: 'relative',
              width: '100%',
              maxWidth: 960,
              borderRadius: 24,
              background: 'rgba(17, 24, 39, 0.94)',
              border: '2px solid rgba(34, 197, 94, 0.35)',
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
            {/* Shimmer passando no card */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: -200 + shimmerPos * 3,
                width: 140,
                background:
                  'linear-gradient(90deg, transparent, rgba(34, 197, 94, 0.12), transparent)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            {/* Fase 1: Envio automático para milhares de contatos */}
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
                  }}
                >
                  ENVIO AUTOMÁTICO EM MASSA
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
                      fontWeight: 800,
                      color: '#22C55E',
                      background: 'rgba(34, 197, 94, 0.18)',
                      padding: '4px 16px',
                      borderRadius: 12,
                    }}
                  >
                    ⚡ Disparo Ativo
                  </span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#E2E8F0',
                    }}
                  >
                    👥 Milhares de Contatos
                  </span>
                </div>
              </div>
            )}

            {/* Fase 2: Rotação de números de maneira prática */}
            {transFase2 > 0 && (
              <div
                style={{
                  position: transFase2 < 1 ? 'absolute' : 'relative',
                  opacity: transFase2,
                  transform: `translateY(${(1 - transFase2) * 12}px)`,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 40,
                    fontWeight: 900,
                    color: '#4ADE80',
                    textTransform: 'uppercase',
                    letterSpacing: 1,
                  }}
                >
                  ROTAÇÃO DE NÚMEROS PRÁTICA
                </div>

                {/* Alternância visual de instâncias */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                  }}
                >
                  {[0, 1, 2].map((idx) => {
                    const isCurrent = activeChip === idx;
                    return (
                      <React.Fragment key={idx}>
                        <div
                          style={{
                            padding: '6px 18px',
                            borderRadius: 14,
                            background: isCurrent
                              ? '#22C55E'
                              : 'rgba(255, 255, 255, 0.08)',
                            border: `2px solid ${
                              isCurrent ? '#4ADE80' : 'rgba(255, 255, 255, 0.12)'
                            }`,
                            color: isCurrent ? '#111827' : '#94A3B8',
                            fontFamily,
                            fontSize: 32,
                            fontWeight: 800,
                            boxShadow: isCurrent
                              ? '0 0 16px rgba(34, 197, 94, 0.6)'
                              : 'none',
                          }}
                        >
                          Instância 0{idx + 1}
                        </div>
                        {idx < 2 && (
                          <span
                            style={{
                              color: '#64748B',
                              fontSize: 28,
                              fontWeight: 900,
                            }}
                          >
                            ➔
                          </span>
                        )}
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
