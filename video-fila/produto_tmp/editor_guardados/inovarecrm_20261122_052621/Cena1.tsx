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

  // Movimento de câmera sutil no vídeo do dono
  const scale = interpolate(frame, [0, 241], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Entrada do badge de etapa
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada da dor 1: Sistemas Prontos (0s a 4.0s - frame 0 a 120)
  const card1Spring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Transição para Dor 2 aos 4.0s (frame 120): Nenhum se encaixava no processo
  const card2Spring = spring({
    frame: Math.max(0, frame - 120),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Animação de pulso do ponto de status
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
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Gradiente de Proteção Exclusivo no Topo (Não escurece o rosto que está abaixo de y=500) */}
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

      {/* Elementos Gráficos no Alto (y=160 a y=440) - Totalmente fora do rosto do dono */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          padding: '0 60px',
        }}
      >
        {/* Badge "01 • O PROBLEMA" (y=175) */}
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
            border: '2px solid #EF4444',
            borderRadius: 30,
            padding: '10px 24px',
            boxShadow: '0 8px 24px rgba(239, 68, 68, 0.35)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              transform: `scale(${pulse})`,
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FCA5A5',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            01 • O PROBLEMA
          </span>
        </div>

        {/* Card Dinâmico no Alto (y=255 a y=430) */}
        {frame < 120 ? (
          /* Bloco 1: Sistemas Prontos */
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
                border: '2px solid rgba(255, 255, 255, 0.15)',
                borderRadius: 20,
                padding: '18px 28px',
                boxShadow: '0 12px 30px rgba(0, 0, 0, 0.7)',
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
                  Sistemas Prontos
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
                  Modelos engessados do mercado
                </span>
              </div>
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1.5px solid #EF4444',
                  borderRadius: 12,
                  padding: '8px 16px',
                  color: '#EF4444',
                  fontSize: 32,
                  fontWeight: 800,
                }}
              >
                GENÉRICO
              </div>
            </div>
          </div>
        ) : (
          /* Bloco 2: Nenhum se encaixava no processo */
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
                border: '2.5px solid #F59E0B',
                borderRadius: 20,
                padding: '18px 28px',
                boxShadow: '0 12px 30px rgba(245, 158, 11, 0.35)',
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
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                    display: 'block',
                    lineHeight: 1.15,
                  }}
                >
                  Não Encaixa no Processo
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FCD34D',
                    display: 'block',
                    marginTop: 4,
                  }}
                >
                  Limita o fluxo da sua empresa
                </span>
              </div>
              <div
                style={{
                  background: 'rgba(245, 158, 11, 0.25)',
                  border: '1.5px solid #F59E0B',
                  borderRadius: 12,
                  padding: '8px 16px',
                  color: '#FCD34D',
                  fontSize: 32,
                  fontWeight: 800,
                }}
              >
                TRAVADO
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
