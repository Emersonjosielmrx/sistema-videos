import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background zoom contínuo
  const bgScale = interpolate(frame, [0, 249], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Saída suave no final
  const exitOpacity = interpolate(frame, [236, 249], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Topo badge e título
  const badgeSpring = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const titleSpring = spring({
    frame: Math.max(0, frame - 15),
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Card 1: "cada solicitação vira chamado e fica registrada" (frame 35 / ~22.1s)
  const card1Spring = spring({
    frame: Math.max(0, frame - 35),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Card 2: "Eu acompanho o suporte" (frame 120 / ~25.0s)
  const card2Spring = spring({
    frame: Math.max(0, frame - 120),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Card 3: "com mais clareza e organização" (frame 165 / ~26.5s)
  const card3Spring = spring({
    frame: Math.max(0, frame - 165),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Flutuação contínua viva
  const floatY = Math.sin(frame / 12) * 4;

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
      {/* Background com zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_3.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Overlay com contraste escuro e glow sutil */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(2, 132, 199, 0.22) 0%, rgba(15, 23, 42, 0.90) 60%, rgba(11, 15, 25, 0.96) 100%)',
          }}
        />
      </div>

      {/* TOPO INFORMATIVO (y = 165 a 380) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 20,
        }}
      >
        {/* Badge "O RESULTADO" */}
        <div
          style={{
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 999,
            background: 'rgba(16, 185, 129, 0.18)',
            border: '1.5px solid rgba(52, 211, 153, 0.5)',
            boxShadow: '0 4px 20px rgba(16, 185, 129, 0.25)',
            marginBottom: 14,
          }}
        >
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: '#34D399',
              boxShadow: '0 0 10px #34D399',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: '#A7F3D0',
            }}
          >
            O RESULTADO
          </span>
        </div>

        {/* Título Principal */}
        <div
          style={{
            transform: `translateY(${(1 - titleSpring) * 20}px) scale(${titleSpring})`,
            opacity: titleSpring,
            textAlign: 'center',
            maxWidth: 960,
          }}
        >
          <h2
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              lineHeight: 1.18,
              color: '#FFFFFF',
              margin: 0,
              textWrap: 'balance',
            }}
          >
            CLAREZA E ORGANIZAÇÃO NO{' '}
            <span
              style={{
                color: '#38BDF8',
                background: 'rgba(2, 132, 199, 0.25)',
                padding: '2px 14px',
                borderRadius: 10,
                border: '1px solid rgba(56, 189, 248, 0.4)',
              }}
            >
              SUPORTE
            </span>
          </h2>
        </div>
      </div>

      {/* CENTRO FOCAL (y = 420 a 1280): 3 CHIPS/CARDS DINÂMICOS ESCALONADOS */}
      <div
        style={{
          position: 'absolute',
          top: 420,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 24,
          transform: `translateY(${floatY}px)`,
          zIndex: 10,
        }}
      >
        {/* Card 1: Solicitação vira chamado (frame >= 35) */}
        {frame >= 35 && (
          <div
            style={{
              transform: `translateY(${(1 - card1Spring) * 45}px) scale(${card1Spring})`,
              opacity: card1Spring,
              background: 'rgba(15, 23, 42, 0.90)',
              backdropFilter: 'blur(16px)',
              border: '1.5px solid rgba(56, 189, 248, 0.35)',
              borderRadius: 24,
              padding: '24px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 22,
              boxShadow: '0 16px 36px rgba(0, 0, 0, 0.65)',
            }}
          >
            <div
              style={{
                width: 68,
                height: 68,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 34,
                flexShrink: 0,
                boxShadow: '0 0 16px rgba(2, 132, 199, 0.5)',
              }}
            >
              ✓
            </div>
            <div style={{flex: 1}}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 6,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Solicitação vira chamado
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#34D399',
                    background: 'rgba(16, 185, 129, 0.16)',
                    padding: '4px 12px',
                    borderRadius: 8,
                  }}
                >
                  Registrado
                </span>
              </div>
              <p
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 500,
                  color: '#94A3B8',
                  margin: 0,
                }}
              >
                Atendimento formalizado sem mensagens esquecidas
              </p>
            </div>
          </div>
        )}

        {/* Card 2: Acompanhamento em tempo real (frame >= 120) */}
        {frame >= 120 && (
          <div
            style={{
              transform: `translateY(${(1 - card2Spring) * 45}px) scale(${card2Spring})`,
              opacity: card2Spring,
              background: 'rgba(15, 23, 42, 0.90)',
              backdropFilter: 'blur(16px)',
              border: '1.5px solid rgba(56, 189, 248, 0.35)',
              borderRadius: 24,
              padding: '24px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 22,
              boxShadow: '0 16px 36px rgba(0, 0, 0, 0.65)',
            }}
          >
            <div
              style={{
                width: 68,
                height: 68,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #0284C7 0%, #0284C7 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 34,
                flexShrink: 0,
                boxShadow: '0 0 16px rgba(56, 189, 248, 0.5)',
              }}
            >
              📊
            </div>
            <div style={{flex: 1}}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 6,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Acompanhamento total
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#38BDF8',
                    background: 'rgba(2, 132, 199, 0.18)',
                    padding: '4px 12px',
                    borderRadius: 8,
                  }}
                >
                  Visão Clara
                </span>
              </div>
              <p
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 500,
                  color: '#94A3B8',
                  margin: 0,
                }}
              >
                Painel com o status e andamento de cada solicitação
              </p>
            </div>
          </div>
        )}

        {/* Card 3: Histórico e Organização (frame >= 165) */}
        {frame >= 165 && (
          <div
            style={{
              transform: `translateY(${(1 - card3Spring) * 45}px) scale(${card3Spring})`,
              opacity: card3Spring,
              background: 'rgba(15, 23, 42, 0.90)',
              backdropFilter: 'blur(16px)',
              border: '1.5px solid rgba(52, 211, 153, 0.45)',
              borderRadius: 24,
              padding: '24px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 22,
              boxShadow: '0 16px 36px rgba(0, 0, 0, 0.65)',
            }}
          >
            <div
              style={{
                width: 68,
                height: 68,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 34,
                flexShrink: 0,
                boxShadow: '0 0 16px rgba(16, 185, 129, 0.5)',
              }}
            >
              📁
            </div>
            <div style={{flex: 1}}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 6,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Histórico completo
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#6EE7B7',
                    background: 'rgba(16, 185, 129, 0.16)',
                    padding: '4px 12px',
                    borderRadius: 8,
                  }}
                >
                  Centralizado
                </span>
              </div>
              <p
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 500,
                  color: '#94A3B8',
                  margin: 0,
                }}
              >
                Tickets e histórico de cada cliente em um só lugar
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
