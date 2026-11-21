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

  // Push-in contínuo no vídeo do dono (1.00 a 1.05)
  const videoScale = interpolate(frame, [0, 229], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Entrada do badge da etapa
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 100},
  });

  // Fases do bloco textual sincronizadas à fala do dono:
  // Fase 1: 0 a 135 frames ("Hoje o pedido sai do cardápio direto para o WhatsApp")
  // Fase 2: 135 a 229 frames ("e eu deixo de perder venda pela demora")
  const phase1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 120},
  });

  const phase2Spring = spring({
    frame: frame - 135,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 120},
  });

  // Microanimação de flutuação no card ativo
  const cardFloat = Math.sin(frame * 0.12) * 3;

  // Desmonte suave nos últimos 15 frames
  const fadeOut = interpolate(frame, [214, 229], [1, 0.85], {
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
      {/* Vídeo do dono em tela cheia com leve zoom contínuo e respiro seguro */}
      <OffthreadVideo
        src={staticFile('dono_3.mp4')}
        muted
        style={{
          width: 1080,
          height: 1920,
          objectFit: 'cover',
          transform: `scale(${videoScale}) translateY(25px)`,
        }}
      />

      {/* Gradiente sutil no topo para proteger contraste do card */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 400,
          background:
            'linear-gradient(180deg, rgba(15, 2, 5, 0.85) 0%, rgba(15, 2, 5, 0.5) 60%, rgba(15, 2, 5, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* TOPO INFORMATIVO (y = 158 a 305) — Rosto do apresentador 100% livre com >80px de respiro */}
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
            background: '#10B981',
            padding: '6px 20px',
            borderRadius: 16,
            boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)',
            marginBottom: 8,
          }}
        >
          <span
            style={{
              color: '#064E3B',
              fontSize: 32,
              fontWeight: 900,
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            ETAPA 3/3 • O RESULTADO
          </span>
        </div>

        {/* Card cinético dinâmico compacto */}
        <div
          style={{
            width: 920,
            background: 'rgba(30, 5, 10, 0.94)',
            borderRadius: 20,
            padding: '12px 20px',
            border: '1.5px solid rgba(16, 185, 129, 0.5)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
            transform: `translateY(${cardFloat}px)`,
          }}
        >
          {frame < 135 && (
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
                PEDIDO DIRETO NO WHATSAPP
              </div>
              <div
                style={{
                  color: '#A7F3D0',
                  fontSize: 32,
                  fontWeight: 600,
                }}
              >
                ⚡ Sem demora e sem complicação
              </div>
            </div>
          )}

          {frame >= 135 && (
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
                  color: '#10B981',
                  fontSize: 42,
                  fontWeight: 900,
                  lineHeight: 1.15,
                  background: 'rgba(6, 78, 59, 0.95)',
                  padding: '2px 16px',
                  borderRadius: 12,
                  border: '1px solid #10B981',
                  boxShadow: '0 4px 14px rgba(16, 185, 129, 0.5)',
                }}
              >
                ZERO VENDAS PERDIDAS!
              </div>
              <div
                style={{
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 700,
                }}
              >
                ✓ Faturamento protegido todo dia
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
