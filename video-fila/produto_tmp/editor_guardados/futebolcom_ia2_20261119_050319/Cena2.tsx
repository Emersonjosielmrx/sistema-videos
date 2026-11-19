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

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Push-in contínuo no vídeo do dono (1.02 a 1.07)
  const videoScale = interpolate(frame, [0, 236], [1.02, 1.07], {
    extrapolateRight: 'clamp',
  });

  // Entrada do badge da etapa
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 100},
  });

  // Fases do bloco textual sincronizadas à fala do dono:
  // Fase 1: 0 a 86 frames ("Com o cardápio digital")
  // Fase 2: 86 a 160 frames ("o cliente olha as fotos")
  // Fase 3: 160 a 236 frames ("e tira dúvida com a IA sem esperar")
  const phase1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 120},
  });

  const phase2Spring = spring({
    frame: frame - 86,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 120},
  });

  const phase3Spring = spring({
    frame: frame - 160,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 120},
  });

  // Microanimação de flutuação no card ativo
  const cardFloat = Math.sin(frame * 0.12) * 3;

  // Desmonte suave nos últimos 15 frames
  const fadeOut = interpolate(frame, [220, 236], [1, 0.85], {
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
        src={staticFile('dono_2.mp4')}
        muted
        style={{
          width: 1080,
          height: 1920,
          objectFit: 'cover',
          transform: `scale(${videoScale})`,
        }}
      />

      {/* Gradiente sutil no topo para proteger contraste do card */}
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
            background: '#FACC15',
            padding: '6px 20px',
            borderRadius: 16,
            boxShadow: '0 4px 14px rgba(250, 204, 21, 0.4)',
            marginBottom: 8,
          }}
        >
          <span
            style={{
              color: '#31060F',
              fontSize: 32,
              fontWeight: 900,
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            ETAPA 2/3 • COMO FUNCIONA
          </span>
        </div>

        {/* Card cinético dinâmico compacto */}
        <div
          style={{
            width: 920,
            background: 'rgba(30, 5, 10, 0.94)',
            borderRadius: 20,
            padding: '12px 20px',
            border: '1.5px solid rgba(250, 204, 21, 0.5)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
            transform: `translateY(${cardFloat}px)`,
          }}
        >
          {frame < 86 && (
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
                CARDÁPIO DIGITAL NO CELULAR
              </div>
              <div
                style={{
                  color: '#FACC15',
                  fontSize: 32,
                  fontWeight: 600,
                }}
              >
                📱 Cardápio interativo e prático
              </div>
            </div>
          )}

          {frame >= 86 && frame < 160 && (
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
                  color: '#FFFFFF',
                  fontSize: 40,
                  fontWeight: 900,
                  lineHeight: 1.15,
                  textShadow: '0 2px 10px rgba(0,0,0,0.8)',
                }}
              >
                FOTOS REAIS DOS PRATOS
              </div>
              <div
                style={{
                  color: '#FEF08A',
                  fontSize: 32,
                  fontWeight: 600,
                }}
              >
                📸 O cliente visualiza e escolhe fácil
              </div>
            </div>
          )}

          {frame >= 160 && (
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
                  color: '#FACC15',
                  fontSize: 42,
                  fontWeight: 900,
                  lineHeight: 1.15,
                  background: 'rgba(225, 29, 72, 0.95)',
                  padding: '2px 16px',
                  borderRadius: 12,
                  boxShadow: '0 4px 14px rgba(225, 29, 72, 0.6)',
                }}
              >
                DÚVIDAS COM A IA NA HORA
              </div>
              <div
                style={{
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 700,
                }}
              >
                🤖 Atendimento automático sem esperar
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
