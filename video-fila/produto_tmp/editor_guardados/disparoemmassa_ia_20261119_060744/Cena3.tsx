import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom lento contínuo no vídeo do dono (1.00 -> 1.06)
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Entrada do selo "O RESULTADO"
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card 1: "MILHARES DE CLIENTES AVISADOS" (frame 20)
  const card1Spring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const card1Exit = interpolate(frame, [130, 140], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Card 2: "ATENDIMENTO 100% TRANQUILO" (frame 140)
  const card2Spring = spring({
    frame: frame - 140,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Micro animação contínua nos cards do topo
  const floatY = Math.sin(frame * 0.1) * 4;
  const pulseScale = 1 + Math.sin(frame * 0.15) * 0.015;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
      }}
    >
      {/* Vídeo do Dono em Tela Cheia com Zoom Contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 45%',
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

      {/* Camada de vinheta no topo para contraste sem afetar o rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(180deg, rgba(10, 14, 23, 0.85) 0%, rgba(10, 14, 23, 0.4) 65%, rgba(10, 14, 23, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* TOPO INFORMATIVO (y = 165 a 390) — TOTALMENTE ACIMA DA CABEÇA DO DONO */}
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
          transform: `translateY(${floatY}px)`,
          zIndex: 30,
        }}
      >
        {/* Selo: 03 • O RESULTADO */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 28px',
            borderRadius: 999,
            background: '#22C55E',
            boxShadow: '0 8px 24px rgba(34, 197, 94, 0.5)',
            transform: `translateY(${(1 - badgeSpring) * -20}px) scale(${badgeSpring})`,
            opacity: badgeSpring,
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: '#121216',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 900,
              color: '#121216',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            03 • O Resultado
          </span>
        </div>

        {/* Card 1: Milhares de clientes avisados (frame 20 a 135) */}
        {frame >= 20 && frame < 140 && (
          <div
            style={{
              width: '100%',
              maxWidth: 920,
              padding: '20px 32px',
              borderRadius: 24,
              background: 'rgba(17, 24, 39, 0.94)',
              border: '2px solid rgba(34, 197, 94, 0.5)',
              backdropFilter: 'blur(16px)',
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              transform: `scale(${card1Spring})`,
              opacity: card1Spring * card1Exit,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span style={{fontSize: 42}}>🚀</span>
              <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 40,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    lineHeight: 1.15,
                  }}
                >
                  Milhares de Clientes Avisados
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#86EFAC',
                  }}
                >
                  Envios em massa automáticos
                </span>
              </div>
            </div>
            <div
              style={{
                padding: '8px 16px',
                borderRadius: 12,
                background: 'rgba(34, 197, 94, 0.2)',
                border: '1px solid #22C55E',
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#4ADE80',
              }}
            >
              Sucesso
            </div>
          </div>
        )}

        {/* Card 2: Atendimento Principal Tranquilo (a partir do frame 140) */}
        {frame >= 140 && (
          <div
            style={{
              width: '100%',
              maxWidth: 920,
              padding: '20px 32px',
              borderRadius: 24,
              background: 'rgba(17, 24, 39, 0.95)',
              border: '2px solid rgba(34, 197, 94, 0.8)',
              backdropFilter: 'blur(16px)',
              boxShadow: '0 16px 40px rgba(34, 197, 94, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              transform: `scale(${card2Spring * pulseScale})`,
              opacity: card2Spring,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span style={{fontSize: 42}}>🛡️</span>
              <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 40,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    lineHeight: 1.15,
                  }}
                >
                  Atendimento Principal Tranquilo
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#86EFAC',
                  }}
                >
                  Totalmente separado das campanhas
                </span>
              </div>
            </div>
            <div
              style={{
                padding: '8px 16px',
                borderRadius: 12,
                background: '#22C55E',
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: '#121216',
                boxShadow: '0 0 16px rgba(34, 197, 94, 0.6)',
              }}
            >
              100% Seguro
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
