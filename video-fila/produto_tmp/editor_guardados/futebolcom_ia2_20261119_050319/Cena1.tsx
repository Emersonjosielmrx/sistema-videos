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

  // Push-in contínuo no vídeo do dono (1.00 a 1.05)
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Entrada do badge da etapa
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 100},
  });

  // Fases do bloco textual sincronizadas à fala do dono:
  // Fase 1: 0 a 110 frames ("Quando eu demorava a responder o cardápio")
  // Fase 2: 110 a 180 frames ("o cliente cansava de esperar")
  // Fase 3: 180 a 245 frames ("e pedia no concorrente")
  const phase1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 120},
  });

  const phase2Spring = spring({
    frame: frame - 110,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 120},
  });

  const phase3Spring = spring({
    frame: frame - 180,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 120},
  });

  // Microanimação de flutuação no card ativo
  const cardFloat = Math.sin(frame * 0.1) * 3;

  // Desmonte suave nos últimos 15 frames
  const fadeOut = interpolate(frame, [230, 245], [1, 0.85], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Vídeo do dono em tela cheia com leve zoom contínuo */}
      <OffthreadVideo
        src={staticFile('dono_1.mp4')}
        muted
        style={{
          width: 1080,
          height: 1920,
          objectFit: 'cover',
          transform: `scale(${videoScale})`,
        }}
      />

      {/* Gradiente suave apenas no topo para proteger contraste do card (z-index sob os textos, sem escurecer o rosto) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(180deg, rgba(15, 2, 5, 0.85) 0%, rgba(15, 2, 5, 0.5) 70%, rgba(15, 2, 5, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* TOPO INFORMATIVO (y = 158 a 305) — Rosto do apresentador 100% livre */}
      <div
        style={{
          position: 'absolute',
          top: 158,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 20,
          opacity: fadeOut,
        }}
      >
        {/* Tag ordinal da etapa */}
        <div
          style={{
            transform: `scale(${Math.max(0, badgeSpring)})`,
            opacity: Math.min(1, badgeSpring),
            background: 'rgba(49, 6, 15, 0.95)',
            padding: '6px 20px',
            borderRadius: 16,
            border: '1.5px solid #E11D48',
            boxShadow: '0 4px 14px rgba(225, 29, 72, 0.4)',
            marginBottom: 8,
          }}
        >
          <span
            style={{
              color: '#FFFFFF',
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            ETAPA 1/3 • O PROBLEMA
          </span>
        </div>

        {/* Card cinético dinâmico compacto */}
        <div
          style={{
            width: 920,
            background: 'rgba(30, 5, 10, 0.94)',
            borderRadius: 20,
            padding: '12px 20px',
            border: '1.5px solid rgba(225, 29, 72, 0.5)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
            transform: `translateY(${cardFloat}px)`,
          }}
        >
          {frame < 110 && (
            <div
              style={{
                transform: `scale(${Math.max(0, phase1Spring)})`,
                opacity: Math.min(1, phase1Spring),
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <div
                style={{
                  color: '#FFFFFF',
                  fontSize: 40,
                  fontWeight: 900,
                  lineHeight: 1.15,
                  textShadow: '0 2px 10px rgba(0,0,0,0.8)',
                }}
              >
                DEMORA NO ATENDIMENTO
              </div>
              <div
                style={{
                  color: '#FECDD3',
                  fontSize: 32,
                  fontWeight: 600,
                }}
              >
                ⏱️ Cardápio demorado no WhatsApp
              </div>
            </div>
          )}

          {frame >= 110 && frame < 180 && (
            <div
              style={{
                transform: `scale(${Math.max(0, phase2Spring)})`,
                opacity: Math.min(1, phase2Spring),
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <div
                style={{
                  color: '#FACC15',
                  fontSize: 40,
                  fontWeight: 900,
                  lineHeight: 1.15,
                  textShadow: '0 2px 10px rgba(0,0,0,0.8)',
                }}
              >
                CLIENTE CANSAVA DE ESPERAR
              </div>
              <div
                style={{
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 600,
                }}
              >
                ⏳ Fila de espera gerando desistência
              </div>
            </div>
          )}

          {frame >= 180 && (
            <div
              style={{
                transform: `scale(${Math.max(0, phase3Spring)})`,
                opacity: Math.min(1, phase3Spring),
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <div
                style={{
                  color: '#FFFFFF',
                  fontSize: 42,
                  fontWeight: 900,
                  lineHeight: 1.15,
                  background: '#E11D48',
                  padding: '2px 16px',
                  borderRadius: 12,
                  boxShadow: '0 4px 14px rgba(225, 29, 72, 0.6)',
                }}
              >
                PEDIA NO CONCORRENTE!
              </div>
              <div
                style={{
                  color: '#FECDD3',
                  fontSize: 32,
                  fontWeight: 700,
                }}
              >
                ⚠️ Venda perdida pela demora na resposta
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
