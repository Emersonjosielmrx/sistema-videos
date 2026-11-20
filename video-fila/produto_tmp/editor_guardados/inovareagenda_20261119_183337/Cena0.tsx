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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de push-in no vídeo de fundo da barbearia
  const bgScale = interpolate(frame, [0, 168], [1.1, 1.2], {
    extrapolateRight: 'clamp',
  });

  // Badge topo: gancho da dúvida do profissional (entra no frame 0 com spring)
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const badgeFloat = Math.sin(frame * 0.1) * 3;

  // Cartão da Pergunta Provocativa Rápida (entra aos ~0.2s -> frame 6)
  // "Trabalhar sem parar para o WhatsApp?"
  const questionSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Pulso sutil no destaque focal
  const highlightPulse =
    frame > 25 ? 1 + Math.sin((frame - 25) * 0.15) * 0.025 : 1;

  // Notificação única e elegante do WhatsApp (entra aos ~1.1s -> frame 34)
  const notifSpring = spring({
    frame: frame - 34,
    fps,
    config: {damping: 12, stiffness: 140},
  });
  // Micro-pulso contínuo para evitar quadro estático
  const notifPulse =
    frame >= 34 ? 1 + Math.sin((frame - 34) * 0.14) * 0.025 : 1;
  // Transição de saída suave antes do corte da cena
  const notifExit = interpolate(frame, [140, 152], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const notifExitY = interpolate(frame, [140, 152], [0, -20], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Transição de saída suave nos últimos 10 frames
  const exitOpacity = interpolate(frame, [158, 168], [1, 0], {
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
      {/* Vídeo do apresentador com corte inicial selecionado onde ele já está com olhos abertos e contato visual firme (startFrom=25) */}
      {/* Enquadrado com translateY(220px) para dar amplo respiro visual e deixar o rosto 100% livre */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(220px)`,
          transformOrigin: '50% 40%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          startFrom={25}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(0.72) contrast(1.1)',
          }}
        />
      </div>

      {/* Degradê cinematográfico escuro na parte superior garantindo contraste do topo */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 520,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.94) 0%, rgba(15, 23, 42, 0.75) 75%, rgba(15, 23, 42, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo Seguro (y=168 a 220): Badge do Gancho */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: badgeSpring,
          transform: `translateY(${(1 - badgeSpring) * -20 + badgeFloat}px)`,
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 26px',
            borderRadius: 999,
            background: 'rgba(15, 23, 42, 0.94)',
            border: '2px solid rgba(245, 158, 11, 0.6)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
          }}
        >
          <span style={{fontSize: 32}}>✂️</span>
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
            Barbeiro sem parar o corte
          </span>
        </div>
      </div>

      {/* Pergunta Provocativa e Rápida (y=230 a 355) — Rápida, sem sobrecarregar com 4 linhas */}
      {frame >= 6 && (
        <div
          style={{
            position: 'absolute',
            top: 232,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 8,
            textAlign: 'center',
            opacity: questionSpring,
            transform: `scale(${interpolate(questionSpring, [0, 1], [0.9, 1])}) translateY(${(1 - questionSpring) * 15}px)`,
            zIndex: 20,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 46,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: 1.2,
              textShadow: '0 4px 18px rgba(0,0,0,0.95)',
              lineHeight: 1.15,
            }}
          >
            TRABALHAR SEM PARAR
          </span>
          <div
            style={{
              transform: `scale(${highlightPulse})`,
            }}
          >
            <div
              style={{
                padding: '8px 28px',
                borderRadius: 18,
                backgroundColor: '#F59E0B',
                boxShadow:
                  '0 8px 26px rgba(245, 158, 11, 0.45), 0 4px 12px rgba(0,0,0,0.8)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 48,
                  fontWeight: 900,
                  color: '#121216',
                  textTransform: 'uppercase',
                  letterSpacing: 1.2,
                  lineHeight: 1.1,
                }}
              >
                PRA RESPONDER WHATSAPP?
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Notificação Única e Focada do WhatsApp (y=375 a 455) com movimento contínuo */}
      {frame >= 34 && frame <= 152 && (
        <div
          style={{
            position: 'absolute',
            top: 375,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            zIndex: 20,
            opacity: notifSpring * notifExit,
            transform: `scale(${interpolate(notifSpring, [0, 1], [0.9, 1]) * notifPulse}) translateY(${
              (1 - notifSpring) * 15 + notifExitY
            }px)`,
          }}
        >
          <div
            style={{
              width: 920,
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              padding: '12px 24px',
              borderRadius: 18,
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: '2px solid rgba(239, 68, 68, 0.55)',
              boxShadow:
                '0 10px 28px rgba(0, 0, 0, 0.8), 0 0 16px rgba(239, 68, 68, 0.2)',
            }}
          >
            <div
              style={{
                width: 50,
                height: 50,
                borderRadius: 16,
                backgroundColor: '#22C55E',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
                flexShrink: 0,
                boxShadow: '0 4px 12px rgba(34, 197, 94, 0.4)',
              }}
            >
              💬
            </div>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-start',
                textAlign: 'left',
                flex: 1,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  width: '100%',
                  marginBottom: 2,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#F87171',
                    letterSpacing: 0.5,
                  }}
                >
                  Mensagens acumuladas
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 30,
                    fontWeight: 600,
                    color: '#94A3B8',
                  }}
                >
                  Agora
                </span>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#F1F5F9',
                }}
              >
                Cliente aguardando resposta no WhatsApp
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


