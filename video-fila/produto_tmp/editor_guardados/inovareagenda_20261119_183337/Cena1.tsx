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

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Plano dinâmico com jump cut de corte aos 9.5s (frame 126):
  // Plano médio 1.02x no início e punch-in zoom 1.14x focado na expressão do conflito
  const videoScale =
    frame < 126
      ? interpolate(frame, [0, 126], [1.02, 1.05], {extrapolateRight: 'clamp'})
      : interpolate(frame, [126, 246], [1.14, 1.18], {extrapolateRight: 'clamp'});

  // Badge topo: entra aos 0.1s (frame 3)
  const badgeSpring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Bloco 1 (5.97s -> local frame 20): "PARAVA O CORTE NO MEIO"
  const block1Spring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Micro-animação na fala "para responder mensagem" (frame 70) para evitar quadro estático
  const subtitlePulse =
    frame >= 70 ? 1 + Math.sin((frame - 70) * 0.15) * 0.025 : 1;

  // Transição rápida de saída do Bloco 1 aos 126-129 frames (mantém 100% legível até a fala mudar)
  const block1ExitOpacity = interpolate(frame, [126, 129], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const block1ExitY = interpolate(frame, [126, 129], [0, -18], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const isBlock1Visible = frame >= 20 && frame <= 129;

  // Bloco 2A (9.51s -> local frame 125): "Cliente na cadeira esperando o corte continuar"
  // Entrada suave com spring e overshoot rápido
  const cardASpring = spring({
    frame: frame - 125,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Bloco 2B (11.23s -> local frame 178): "Outro cliente no WhatsApp sem resposta"
  const cardBSpring = spring({
    frame: frame - 178,
    fps,
    config: {damping: 14, stiffness: 135},
  });

  // Micro pulso no badge
  const badgeFloat = Math.sin(frame * 0.1) * 3;

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
      {/* Vídeo do apresentador com punch-in dinâmico e rebaixado para dar respiro visual adequado acima da cabeça e no peito */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale}) translateY(60px)`,
          transformOrigin: '50% 45%',
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

      {/* Degradê superior escuro no teto para garantir contraste absoluto dos textos */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 490,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.94) 0%, rgba(15, 23, 42, 0.72) 70%, rgba(15, 23, 42, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo Seguro (y=165 a 220): Badge de Contexto */}
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
            border: '2px solid rgba(239, 68, 68, 0.6)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
          }}
        >
          <span style={{fontSize: 32}}>⚠️</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#F87171',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O Problema • Interrupções
          </span>
        </div>
      </div>

      {/* Faixa superior (y=242 a 360): Amplo respiro visual acima da cabeça rebaixada */}
      {/* Fase 1: Parava o corte no meio (com transição suave de saída em 6 frames) */}
      {isBlock1Visible && (
        <div
          style={{
            position: 'absolute',
            top: 242,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: block1Spring * block1ExitOpacity,
            transform: `scale(${interpolate(block1Spring, [0, 1], [0.92, 1])}) translateY(${
              (1 - block1Spring) * 15 + block1ExitY
            }px)`,
            zIndex: 10,
          }}
        >
          <div
            style={{
              width: 920,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              gap: 8,
              padding: '16px 28px',
              borderRadius: 22,
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: '2px solid rgba(245, 158, 11, 0.65)',
              boxShadow:
                '0 12px 32px rgba(0, 0, 0, 0.85), 0 0 20px rgba(245, 158, 11, 0.25)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 42,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              ✂️ PARAVA O CORTE NO MEIO
            </span>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 700,
                color: frame >= 70 ? '#FBBF24' : '#FDE68A',
                letterSpacing: 0.5,
                transform: `scale(${subtitlePulse})`,
                transition: 'color 0.2s ease',
              }}
            >
              Para responder mensagens no WhatsApp
            </span>
          </div>
        </div>
      )}

      {/* Fase 2: Conflito duplo (Cliente na cadeira vs Outro esperando) - entrada suave aos frames 125+ */}
      {frame >= 125 && (
        <div
          style={{
            position: 'absolute',
            top: 238,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            alignItems: 'center',
            zIndex: 10,
          }}
        >
          {/* Card A: Cliente na cadeira esperando o corte continuar (com 'o' e sem palavra órfã) */}
          <div
            style={{
              width: 940,
              opacity: cardASpring,
              transform: `scale(${interpolate(cardASpring, [0, 1], [0.9, 1])}) translateY(${(1 - cardASpring) * 15}px)`,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                padding: '14px 22px',
                borderRadius: 20,
                backgroundColor: 'rgba(15, 23, 42, 0.96)',
                border: '2px solid rgba(245, 158, 11, 0.5)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
                whiteSpace: 'nowrap',
              }}
            >
              <span style={{fontSize: 34, flexShrink: 0}}>⏳</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FDE68A',
                  letterSpacing: 0.2,
                }}
              >
                Cliente na cadeira esperando o corte continuar
              </span>
            </div>
          </div>

          {/* Card B: Outro cliente esperando resposta */}
          {frame >= 178 && (
            <div
              style={{
                width: 940,
                opacity: cardBSpring,
                transform: `scale(${interpolate(cardBSpring, [0, 1], [0.9, 1])}) translateY(${(1 - cardBSpring) * 15}px)`,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  padding: '14px 22px',
                  borderRadius: 20,
                  backgroundColor: 'rgba(15, 23, 42, 0.96)',
                  border: '2px solid rgba(239, 68, 68, 0.6)',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
                  whiteSpace: 'nowrap',
                }}
              >
                <span style={{fontSize: 34, flexShrink: 0}}>📱</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    letterSpacing: 0.2,
                  }}
                >
                  Outro cliente no WhatsApp sem resposta
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

