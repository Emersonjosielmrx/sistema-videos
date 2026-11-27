import React from 'react';
import {interpolate, OffthreadVideo, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração total: 241 frames (~8.03s)
  // Virada da fala aos 10.4s (frame 156): "Era tempo que não voltava para o negócio."
  // Punch-in digital de 1.02x para 1.15x com corte no frame 156
  const isBloco2 = frame >= 156;
  const videoScale = isBloco2
    ? interpolate(frame, [156, 162], [1.14, 1.16], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
    : interpolate(frame, [0, 156], [1.00, 1.03], {extrapolateRight: 'clamp'});

  // Compensação vertical: rebaixa o vídeo para garantir respiro (headroom) amplo entre o cabelo e o card superior
  const videoTranslateY = isBloco2 ? 115 : 65;

  // Badge "01 • O PROBLEMA" entra no frame 6 (~0.2s)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Card superior entra no frame 10 (~0.33s)
  const cardSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Transição animada do card superior na virada da fala (frame 156) com slide vertical e blur fade
  const bloco1ExitY = interpolate(frame, [150, 156], [0, -18], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const bloco1Opacity = interpolate(frame, [150, 156], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  const bloco2EnterY = interpolate(frame, [156, 164], [18, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const bloco2Opacity = interpolate(frame, [156, 162], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#000000',
      }}
    >
      {/* Vídeo do Dono com punch-in dinâmico e compensação vertical de headroom */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: '50% 35%',
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

      {/* Gradiente escuro protetor EXCLUSIVAMENTE no topo (y=0 a y=360) — ROSTO 100% LIVRE */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 360,
          background: 'linear-gradient(to bottom, rgba(11, 15, 25, 0.90) 0%, rgba(15, 23, 42, 0.55) 75%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Badge Superior: Rótulo "01 • O PROBLEMA" (y=165) */}
      {frame >= 6 && (
        <div
          style={{
            position: 'absolute',
            top: 165,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            transform: `scale(${badgeSpring})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 22px',
              borderRadius: 999,
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1.5px solid #7C3AED',
              boxShadow: '0 6px 20px rgba(0, 0, 0, 0.65)',
            }}
          >
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#EF4444',
                boxShadow: '0 0 8px #EF4444',
                transform: `scale(${1 + Math.sin(frame * 0.25) * 0.2})`,
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
              01 • O PROBLEMA
            </span>
          </div>
        </div>
      )}

      {/* Card Superior Compacto e Informativo (y=230 a y=340) — Deixa headroom livre até o topo do cabelo */}
      {frame >= 10 && (
        <div
          style={{
            position: 'absolute',
            top: 228,
            left: 60,
            right: 60,
            transform: `scale(${cardSpring})`,
            transformOrigin: 'top center',
          }}
        >
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1.5px solid rgba(255, 255, 255, 0.16)',
              borderRadius: 22,
              padding: '12px 24px',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.75)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              minHeight: 88,
              justifyContent: 'center',
            }}
          >
            {!isBloco2 ? (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 6,
                  transform: `translateY(${bloco1ExitY}px)`,
                  opacity: bloco1Opacity,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 38,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    letterSpacing: '0.02em',
                    textTransform: 'uppercase',
                    lineHeight: 1.15,
                  }}
                >
                  HORAS EM TAREFAS REPETITIVAS
                </span>
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    background: 'rgba(239, 68, 68, 0.18)',
                    border: '1px solid rgba(239, 68, 68, 0.45)',
                    padding: '4px 14px',
                    borderRadius: 999,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 30,
                      fontWeight: 700,
                      color: '#FCA5A5',
                    }}
                  >
                    Rotina operacional travando o time
                  </span>
                </div>
              </div>
            ) : (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 6,
                  transform: `translateY(${bloco2EnterY}px)`,
                  opacity: bloco2Opacity,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 38,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    letterSpacing: '0.02em',
                    textTransform: 'uppercase',
                    lineHeight: 1.15,
                  }}
                >
                  TEMPO QUE NÃO VOLTAVA PARA O NEGÓCIO
                </span>
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    background: 'rgba(245, 158, 11, 0.18)',
                    border: '1px solid rgba(245, 158, 11, 0.45)',
                    padding: '4px 14px',
                    borderRadius: 999,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 30,
                      fontWeight: 700,
                      color: '#FDE68A',
                    }}
                  >
                    Horas desperdiçadas sem gerar valor
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
