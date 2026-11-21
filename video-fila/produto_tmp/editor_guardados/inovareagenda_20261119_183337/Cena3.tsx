import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Enquadramento dinâmico com corte/punch-in fechado (1.10x na virada do bloco e aproximando para 1.18x no comparativo de preço)
  const baseScale = interpolate(frame, [0, 187], [1.10, 1.14], {
    extrapolateRight: 'clamp',
  });
  // Punch-in adicional suave no momento do comparativo financeiro (frame >= 188)
  const financePunch = interpolate(frame, [188, 205], [0, 0.05], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const videoScale = baseScale + financePunch;

  // Badge topo: O Resultado
  const badgeSpring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Fase 1: "Atendimento sem interrupção" aos 21.5s (local frame 18)
  const phase1Spring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 13, stiffness: 130},
  });
  // Transição de saída suave da Fase 1 em 6 frames (74 a 80)
  const phase1ExitOpacity = interpolate(frame, [74, 80], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const phase1ExitY = interpolate(frame, [74, 80], [0, -18], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const isPhase1Visible = frame >= 18 && frame <= 80;

  // Fase 2: "Funciona 24 horas" aos 23.6s (local frame 80)
  const phase2Spring = spring({
    frame: frame - 80,
    fps,
    config: {damping: 13, stiffness: 130},
  });
  // Transição de saída suave da Fase 2 em 6 frames (182 a 188)
  const phase2ExitOpacity = interpolate(frame, [182, 188], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const phase2ExitY = interpolate(frame, [182, 188], [0, -18], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const isPhase2Visible = frame >= 80 && frame <= 188;

  // Pulso contínuo do status 24h
  const dotPulse =
    frame >= 80 ? 1 + Math.sin((frame - 80) * 0.2) * 0.25 : 1;

  // Fase 3: Comparativo de Custo com entrada sequencial (frame 188 e frame 196)
  const isPhase3 = frame >= 188;
  const phase3LeftSpring = spring({
    frame: frame - 188,
    fps,
    config: {damping: 13, stiffness: 140},
  });
  const phase3RightSpring = spring({
    frame: frame - 196,
    fps,
    config: {damping: 12, stiffness: 150},
  });
  // Micro-pulso no card da Agenda IA para evidenciar o contraste de preço
  const iaCardPulse =
    frame >= 196 ? 1 + Math.sin((frame - 196) * 0.16) * 0.025 : 1;

  // Transição de saída suave nos últimos 8 frames
  const exitOpacity = interpolate(frame, [238, 246], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        opacity: exitOpacity,
      }}
    >
      {/* Vídeo do dono com variedade de plano e rebaixado em 60px para dar respiro visual adequado acima da cabeça */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale}) translateY(60px)`,
          transformOrigin: '50% 42%',
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

      {/* Degradê superior escuro protetor de legibilidade */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 490,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.94) 0%, rgba(15, 23, 42, 0.7) 70%, rgba(15, 23, 42, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo Seguro (y=165 a 215): Badge Contextual */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: badgeSpring,
          transform: `translateY(${(1 - badgeSpring) * -20}px)`,
          zIndex: 10,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 999,
            backgroundColor: 'rgba(15, 23, 42, 0.94)',
            border: '2px solid rgba(245, 158, 11, 0.6)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
          }}
        >
          <span style={{fontSize: 32}}>⭐</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#F59E0B',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O Resultado • Eficiência Total
          </span>
        </div>
      </div>

      {/* Bloco Focal Único (y=235 a 360) — Alterna de acordo com o momento da fala com transição suave em 6 frames */}

      {/* Fase 1: Atendimento sem interrupção (local frames 18 a 80) */}
      {isPhase1Visible && (
        <div
          style={{
            position: 'absolute',
            top: 235,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: phase1Spring * phase1ExitOpacity,
            transform: `scale(${interpolate(phase1Spring, [0, 1], [0.9, 1])}) translateY(${
              (1 - phase1Spring) * 15 + phase1ExitY
            }px)`,
            zIndex: 10,
          }}
        >
          <div
            style={{
              padding: '14px 34px',
              borderRadius: 20,
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: '2px solid rgba(245, 158, 11, 0.55)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 42,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 0.5,
                textTransform: 'uppercase',
              }}
            >
              ✂️ ATENDIMENTO SEM INTERRUPÇÃO
            </span>
          </div>
        </div>
      )}

      {/* Fase 2: Funciona 24 Horas (local frames 80 a 188 com entrada suave e saída suave) */}
      {isPhase2Visible && (
        <div
          style={{
            position: 'absolute',
            top: 235,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: phase2Spring * phase2ExitOpacity,
            transform: `scale(${interpolate(phase2Spring, [0, 1], [0.9, 1])}) translateY(${
              (1 - phase2Spring) * 15 + phase2ExitY
            }px)`,
            zIndex: 10,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              padding: '14px 32px',
              borderRadius: 20,
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: '2px solid #22C55E',
              boxShadow: '0 8px 26px rgba(34, 197, 94, 0.35)',
            }}
          >
            <div
              style={{
                width: 20,
                height: 20,
                borderRadius: '50%',
                backgroundColor: '#22C55E',
                boxShadow: '0 0 14px #22C55E',
                transform: `scale(${dotPulse})`,
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 900,
                color: '#F1F5F9',
                letterSpacing: 0.5,
              }}
            >
              AGENDA FUNCIONA 24 HORAS
            </span>
          </div>
        </div>
      )}

      {/* Fase 3: Comparativo de Custo Padronizado e com Entrada Sequencial (local frames 188 a 245) */}
      {isPhase3 && (
        <div
          style={{
            position: 'absolute',
            top: 228,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            gap: 16,
            zIndex: 10,
          }}
        >
          {/* Card Esquerda: Recepção Humana (desliza da esquerda no frame 188) */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              padding: '14px 16px',
              borderRadius: 20,
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: '1.5px solid rgba(226, 232, 240, 0.45)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
              opacity: phase3LeftSpring,
              transform: `translateX(${(1 - phase3LeftSpring) * -25}px)`,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#F1F5F9',
                marginBottom: 8,
                letterSpacing: 0.3,
                textAlign: 'center',
              }}
            >
              Recepção Humana
            </span>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '6px 14px',
                borderRadius: 14,
                backgroundColor: 'rgba(239, 68, 68, 0.16)',
                border: '1px solid rgba(239, 68, 68, 0.45)',
                whiteSpace: 'nowrap',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 22,
                  fontWeight: 700,
                  color: '#FCA5A5',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                  lineHeight: 1.1,
                  marginBottom: 2,
                }}
              >
                Custo mensal
              </span>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: 4,
                  whiteSpace: 'nowrap',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    whiteSpace: 'nowrap',
                  }}
                >
                  R$ 2.500
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 26,
                    fontWeight: 600,
                    color: '#FCA5A5',
                    whiteSpace: 'nowrap',
                  }}
                >
                  /mês
                </span>
              </div>
            </div>
          </div>

          {/* Card Direita: Agenda IA 24h (entra no frame 196 com pop 1.05x e brilho de ancoragem) */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              padding: '14px 16px',
              borderRadius: 20,
              background:
                'linear-gradient(135deg, rgba(245, 158, 11, 0.24) 0%, rgba(217, 119, 6, 0.36) 100%)',
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: '2px solid #F59E0B',
              boxShadow:
                '0 10px 30px rgba(245, 158, 11, 0.4), 0 0 20px rgba(245, 158, 11, 0.25)',
              opacity: phase3RightSpring,
              transform: `scale(${interpolate(phase3RightSpring, [0, 1], [0.85, 1]) * iaCardPulse})`,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FDE68A',
                marginBottom: 8,
                letterSpacing: 0.3,
                textAlign: 'center',
              }}
            >
              Agenda IA 24h
            </span>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '6px 14px',
                borderRadius: 14,
                backgroundColor: 'rgba(245, 158, 11, 0.28)',
                border: '1px solid rgba(245, 158, 11, 0.65)',
                whiteSpace: 'nowrap',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 22,
                  fontWeight: 700,
                  color: '#FDE68A',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                  lineHeight: 1.1,
                  marginBottom: 2,
                }}
              >
                A partir de
              </span>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: 4,
                  whiteSpace: 'nowrap',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 900,
                    color: '#FBBF24',
                    whiteSpace: 'nowrap',
                  }}
                >
                  R$ 199
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 26,
                    fontWeight: 700,
                    color: '#FDE68A',
                    whiteSpace: 'nowrap',
                  }}
                >
                  /mês
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

