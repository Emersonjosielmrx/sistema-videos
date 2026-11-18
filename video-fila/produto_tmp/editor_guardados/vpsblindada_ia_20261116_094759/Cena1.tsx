import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Cena1: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Corte dinâmico (punch-in zoom seco) exatamente no frame 162 (início de 'Faltavam dados para decidir')
  // Antes do frame 162: escala base sutil (1.02 a 1.05).
  // A partir do frame 162: salto dinâmico para 1.18x centrado no rosto do apresentador.
  const isPunchIn = frame >= 162;
  const baseScale = interpolate(frame, [0, 241], [1.02, 1.06], {
    extrapolateRight: 'clamp',
  });
  const videoScale = isPunchIn ? 1.18 : baseScale;

  // Tag do topo "O PROBLEMA"
  const tagSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Card 1: "Servidor no escuro" (entra frame 8, sai frame 160)
  const card1In = spring({
    frame: frame - 8,
    fps,
    config: {damping: 13, stiffness: 120},
  });
  const card1Out = interpolate(frame, [156, 162], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Card 2: "Faltavam dados para decidir" (entra frame 162 no exato momento da fala e do punch-in)
  const card2In = spring({
    frame: frame - 162,
    fps,
    config: {damping: 11, stiffness: 150},
  });

  // Pulso sutil no card para garantir movimento contínuo
  const cardPulse = Math.sin(frame * 0.15) * 0.02 + 1.0;

  // Transição de saída aos frames 230 a 241
  const exitOpacity = interpolate(frame, [230, 241], [1, 0.4], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        opacity: exitOpacity,
      }}
    >
      {/* Vídeo do dono em tela cheia com corte dinâmico punch-in centrado no rosto aos frames 162+ */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale}) translateY(${isPunchIn ? 55 : 45}px)`,
          transformOrigin: '50% 30%',
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

      {/* Vinheta superior e inferior para legibilidade absoluta preservando o rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(to bottom, rgba(15, 23, 42, 0.90) 0%, rgba(15, 23, 42, 0.65) 60%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 440,
          background:
            'linear-gradient(to top, rgba(15, 23, 42, 0.92) 0%, rgba(15, 23, 42, 0.60) 60%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Faixa superior (y=155 a 440) — ROSTO TOTALMENTE LIVRE */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 60,
          right: 60,
          height: 450,
          pointerEvents: 'none',
        }}
      >
        {/* Rótulo da cena: "O PROBLEMA" (y=155) */}
        {tagSpring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 155,
              left: 0,
              right: 0,
              display: 'flex',
              justifyContent: 'center',
              transform: `scale(${Math.max(0, tagSpring)})`,
              opacity: Math.min(1, tagSpring),
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 22px',
                borderRadius: 999,
                background: 'rgba(15, 23, 42, 0.92)',
                border: '1.5px solid rgba(239, 68, 68, 0.5)',
                boxShadow: '0 4px 18px rgba(0, 0, 0, 0.5)',
              }}
            >
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: '#EF4444',
                }}
              />
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#F87171',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                }}
              >
                O Problema
              </span>
            </div>
          </div>
        )}

        {/* Card 1: Servidor no escuro (Frame 8 a 160) */}
        {frame < 162 && card1In > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 210,
              left: 0,
              right: 0,
              transform: `scale(${Math.max(0, card1In) * cardPulse}) translateY(${interpolate(
                card1In,
                [0, 1],
                [20, 0]
              )}px)`,
              opacity: Math.min(1, card1In) * card1Out,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.92)',
                border: '1.5px solid rgba(239, 68, 68, 0.45)',
                borderRadius: 20,
                padding: '16px 24px',
                boxShadow: '0 16px 36px rgba(0, 0, 0, 0.65)',
                backdropFilter: 'blur(14px)',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  fontSize: 44,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: '-0.5px',
                  lineHeight: 1.15,
                }}
              >
                Servidor no Escuro
              </div>
              <div
                style={{
                  marginTop: 6,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#FCA5A5',
                  lineHeight: 1.25,
                }}
              >
                ⚠️ Sem dados para saber se estava tudo certo
              </div>
            </div>
          </div>
        )}

        {/* Card 2: Faltavam dados para decidir (Frame 162 a 241) */}
        {frame >= 160 && card2In > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 210,
              left: 0,
              right: 0,
              transform: `scale(${Math.max(0, card2In) * cardPulse}) translateY(${interpolate(
                card2In,
                [0, 1],
                [20, 0]
              )}px)`,
              opacity: Math.min(1, card2In),
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.92)',
                border: '1.5px solid rgba(14, 165, 233, 0.55)',
                borderRadius: 20,
                padding: '16px 24px',
                boxShadow:
                  '0 16px 36px rgba(0, 0, 0, 0.65), 0 0 25px rgba(14, 165, 233, 0.2)',
                backdropFilter: 'blur(14px)',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  fontSize: 44,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: '-0.5px',
                  lineHeight: 1.15,
                }}
              >
                Faltavam Dados Para Decidir
              </div>
              <div
                style={{
                  marginTop: 6,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#38BDF8',
                  lineHeight: 1.25,
                }}
              >
                📉 Sem relatórios de saúde da infraestrutura
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
