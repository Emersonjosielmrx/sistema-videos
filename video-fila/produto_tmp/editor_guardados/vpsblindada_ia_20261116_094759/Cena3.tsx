import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Cena3: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Enquadramento diferenciado da Cena 1: plano mais fechado (close-up cinematográfico com escala 1.28x a 1.34x)
  // que quebra a repetição visual e traz mais proximidade e autoridade ao apresentador
  const videoScale = interpolate(frame, [0, 246], [1.28, 1.34], {
    extrapolateRight: 'clamp',
  });

  // Tag do topo "O RESULTADO" (y=155)
  const tagSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Grafismo de Relatório Técnico (HUD semi-transparente) enquanto diz "Hoje eu leio o relatório..." (frames 10 a 175)
  const reportSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 12, stiffness: 130},
  });
  const reportOut = interpolate(frame, [170, 178], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Card de conclusão: "Decido com segurança" (entra frame 178 no momento exato da fala "Decido com segurança")
  const card2In = spring({
    frame: frame - 178,
    fps,
    config: {damping: 11, stiffness: 150},
  });

  // Pulso sutil no card para garantir movimento contínuo
  const cardPulse = Math.sin(frame * 0.16) * 0.02 + 1.0;
  const heartbeat = Math.sin(frame * 0.22) * 0.15 + 1.0;

  // Transição de saída aos frames 235 a 246
  const exitOpacity = interpolate(frame, [235, 246], [1, 0.4], {
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
      {/* Vídeo do dono em plano fechado (close-up 1.30x) diferenciado da cena 1, com respiro confortável no headroom */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale}) translateY(75px)`,
          transformOrigin: '52% 28%',
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

      {/* Vinhetas para garantir contraste e legibilidade com rosto preservado */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(to bottom, rgba(15, 23, 42, 0.92) 0%, rgba(15, 23, 42, 0.65) 60%, transparent 100%)',
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
        {/* Rótulo da cena: "O RESULTADO" (y=155) */}
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
                padding: '8px 24px',
                borderRadius: 999,
                background: 'rgba(15, 23, 42, 0.92)',
                border: '1.5px solid rgba(16, 185, 129, 0.65)',
                boxShadow: '0 4px 20px rgba(16, 185, 129, 0.3)',
              }}
            >
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: '#10B981',
                  boxShadow: '0 0 10px #10B981',
                  transform: `scale(${heartbeat})`,
                }}
              />
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#34D399',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                }}
              >
                O Resultado
              </span>
            </div>
          </div>
        )}

        {/* Grafismo de Relatório Técnico (HUD) enquanto diz "Hoje eu leio o relatório..." (Frames 10 a 175) */}
        {frame < 178 && reportSpring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 210,
              left: 0,
              right: 0,
              transform: `scale(${Math.max(0, reportSpring) * cardPulse}) translateY(${interpolate(
                reportSpring,
                [0, 1],
                [20, 0]
              )}px)`,
              opacity: Math.min(1, reportSpring) * reportOut,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.92)',
                border: '1.5px solid rgba(16, 185, 129, 0.6)',
                borderRadius: 20,
                padding: '16px 24px',
                boxShadow:
                  '0 16px 36px rgba(0, 0, 0, 0.65), 0 0 24px rgba(16, 185, 129, 0.2)',
                backdropFilter: 'blur(14px)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 10,
                      background: 'rgba(16, 185, 129, 0.25)',
                      border: '1px solid #10B981',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path d="M9 12L11 14L15 10" stroke="#34D399" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                      <rect x="3" y="3" width="18" height="18" rx="3" stroke="#34D399" strokeWidth="2" />
                    </svg>
                  </div>
                  <span
                    style={{
                      fontSize: 40,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      textTransform: 'uppercase',
                      letterSpacing: '-0.3px',
                    }}
                  >
                    Relatório da VPS
                  </span>
                </div>
                <div
                  style={{
                    padding: '4px 16px',
                    borderRadius: 999,
                    background: 'rgba(16, 185, 129, 0.22)',
                    border: '1.5px solid #10B981',
                    color: '#34D399',
                    fontSize: 32,
                    fontWeight: 800,
                  }}
                >
                  ● Situação Real
                </div>
              </div>
              <div
                style={{
                  marginTop: 8,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#6EE7B7',
                  lineHeight: 1.25,
                }}
              >
                ✓ Visibilidade total e métricas claras da infraestrutura
              </div>
            </div>
          </div>
        )}

        {/* Card 2: Decido com segurança (Frame 178 a 246) */}
        {frame >= 175 && card2In > 0.01 && (
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
                background: 'rgba(15, 23, 42, 0.94)',
                border: '1.5px solid rgba(14, 165, 233, 0.65)',
                borderRadius: 20,
                padding: '16px 24px',
                boxShadow:
                  '0 16px 36px rgba(0, 0, 0, 0.65), 0 0 25px rgba(14, 165, 233, 0.25)',
                backdropFilter: 'blur(14px)',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  fontSize: 44,
                  fontWeight: 900,
                  color: '#38BDF8',
                  textTransform: 'uppercase',
                  letterSpacing: '-0.5px',
                  lineHeight: 1.15,
                }}
              >
                Decido Com Segurança
              </div>
              <div
                style={{
                  marginTop: 6,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#E2E8F0',
                  lineHeight: 1.25,
                }}
              >
                ✓ Servidor monitorado e backup automático
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
