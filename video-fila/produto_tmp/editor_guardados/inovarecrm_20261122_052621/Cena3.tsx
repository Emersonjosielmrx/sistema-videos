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

  // Movimento de câmera no vídeo do dono
  const scale = interpolate(frame, [0, 245], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Entrada do badge de etapa (frame 0)
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Resultado 1: Histórico Completo (frame 0 a 95)
  const card1Spring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Entrada do Resultado 2: Suporte Integrado (frame 95 a 155)
  const card2Spring = spring({
    frame: Math.max(0, frame - 95),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Entrada do Resultado 3: No formato que meu time precisa (frame 155 a 245)
  const card3Spring = spring({
    frame: Math.max(0, frame - 155),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Pulso de status
  const pulse = Math.sin((frame / 20) * Math.PI * 2) * 0.05 + 1.0;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#0F172A',
        fontFamily,
      }}
    >
      {/* Vídeo do Dono em Tela Cheia com Zoom Suave */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 1080,
          height: 1920,
          transform: `scale(${scale})`,
          transformOrigin: 'center 40%',
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

      {/* Gradiente de Proteção no Topo (Não encosta no rosto em y >= 550) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.94) 0%, rgba(15, 23, 42, 0.82) 55%, rgba(15, 23, 42, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Elementos Gráficos no Alto (y=160 a y=440) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          padding: '0 60px',
        }}
      >
        {/* Badge "03 • O RESULTADO" (y=175) */}
        <div
          style={{
            position: 'absolute',
            top: 175,
            left: 60,
            transform: `scale(${badgeSpring})`,
            transformOrigin: 'left center',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: '#0F172A',
            border: '2px solid #10B981',
            borderRadius: 30,
            padding: '10px 24px',
            boxShadow: '0 8px 24px rgba(16, 185, 129, 0.35)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#10B981',
              transform: `scale(${pulse})`,
              boxShadow: '0 0 10px #10B981',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#6EE7B7',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            03 • O RESULTADO
          </span>
        </div>

        {/* Card Dinâmico no Alto (y=255 a y=430) */}
        {frame < 95 ? (
          /* Bloco 1: Histórico Completo */
          <div
            style={{
              position: 'absolute',
              top: 255,
              left: 60,
              right: 60,
              transform: `translateY(${interpolate(card1Spring, [0, 1], [30, 0])}px)`,
              opacity: card1Spring,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2px solid #0284C7',
                borderRadius: 20,
                padding: '18px 28px',
                boxShadow: '0 12px 30px rgba(2, 132, 199, 0.35)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <span
                  style={{
                    fontSize: 44,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                    display: 'block',
                    lineHeight: 1.15,
                  }}
                >
                  Histórico Completo
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#94A3B8',
                    display: 'block',
                    marginTop: 4,
                  }}
                >
                  Cada cliente em um só lugar
                </span>
              </div>
              <div
                style={{
                  background: 'rgba(2, 132, 199, 0.25)',
                  border: '1.5px solid #0284C7',
                  borderRadius: 12,
                  padding: '8px 16px',
                  color: '#38BDF8',
                  fontSize: 32,
                  fontWeight: 800,
                }}
              >
                CENTRAL
              </div>
            </div>
          </div>
        ) : frame < 155 ? (
          /* Bloco 2: Suporte Integrado */
          <div
            style={{
              position: 'absolute',
              top: 255,
              left: 60,
              right: 60,
              transform: `translateY(${interpolate(card2Spring, [0, 1], [30, 0])}px)`,
              opacity: card2Spring,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2px solid #10B981',
                borderRadius: 20,
                padding: '18px 28px',
                boxShadow: '0 12px 30px rgba(16, 185, 129, 0.35)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <span
                  style={{
                    fontSize: 44,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                    display: 'block',
                    lineHeight: 1.15,
                  }}
                >
                  Suporte & Tickets
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#6EE7B7',
                    display: 'block',
                    marginTop: 4,
                  }}
                >
                  Atendimento unificado
                </span>
              </div>
              <div
                style={{
                  background: 'rgba(16, 185, 129, 0.25)',
                  border: '1.5px solid #10B981',
                  borderRadius: 12,
                  padding: '8px 16px',
                  color: '#6EE7B7',
                  fontSize: 32,
                  fontWeight: 800,
                }}
              >
                UNIFICADO
              </div>
            </div>
          </div>
        ) : (
          /* Bloco 3: Formato do seu time */
          <div
            style={{
              position: 'absolute',
              top: 255,
              left: 60,
              right: 60,
              transform: `translateY(${interpolate(card3Spring, [0, 1], [30, 0])}px)`,
              opacity: card3Spring,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2.5px solid #0284C7',
                borderRadius: 20,
                padding: '18px 28px',
                boxShadow: '0 12px 30px rgba(2, 132, 199, 0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <span
                  style={{
                    fontSize: 42,
                    fontWeight: 900,
                    color: '#38BDF8',
                    textTransform: 'uppercase',
                    display: 'block',
                    lineHeight: 1.15,
                  }}
                >
                  Sob Medida Pro Time
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    display: 'block',
                    marginTop: 4,
                  }}
                >
                  Processos rápidos e eficientes
                </span>
              </div>
              <div
                style={{
                  background: 'rgba(2, 132, 199, 0.3)',
                  border: '1.5px solid #38BDF8',
                  borderRadius: 12,
                  padding: '8px 16px',
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 800,
                }}
              >
                100%
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
