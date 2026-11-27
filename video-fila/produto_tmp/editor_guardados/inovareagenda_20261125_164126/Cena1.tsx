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

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Câmera dinâmica contínua: pan horizontal, leve pan vertical e zoom suave constante
  const scale = interpolate(frame, [0, 215], [1.12, 1.26], {
    extrapolateRight: 'clamp',
  });
  const panX = interpolate(frame, [0, 215], [-40, 40], {
    extrapolateRight: 'clamp',
  });
  const panY = interpolate(frame, [0, 215], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada suave (frames 0 a 10) e saída (frames 200 a 215)
  const opacity = interpolate(frame, [0, 10, 200, 215], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Estágio do card dinâmico baseado na fala:
  // Estágio 1 (frame 15+): "Eu perdia cliente que escrevia à noite"
  // Estágio 2 (frame 85+): "Ele queria horário para o dia seguinte"
  // Estágio 3 (frame 142+): "e ninguém respondia"
  const spring1 = spring({
    frame: frame - 15,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 120},
  });

  const spring2 = spring({
    frame: frame - 85,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 120},
  });

  const spring3 = spring({
    frame: frame - 142,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 120},
  });

  // Micro-interação contínua no card
  const hoverY = Math.sin(frame * 0.1) * 6;

  // Transições suaves com slide e fade entre os tópicos (evita corte seco tipo PowerPoint)
  const opac1 = interpolate(frame, [15, 23, 76, 85], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const slide1 = interpolate(frame, [76, 85], [0, -25], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const opac2 = interpolate(frame, [85, 94, 134, 142], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const slide2 = interpolate(frame, [85, 94, 134, 142], [25, 0, 0, -25], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const opac3 = interpolate(frame, [142, 152], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const slide3 = interpolate(frame, [142, 152], [25, 0], {
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
        backgroundColor: '#0F172A',
        opacity,
      }}
    >
      {/* Background Image com corte nítido em relação à Cena 0: mesa com laptop fechado à noite */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${scale}) translateX(${panX}px) translateY(${panY}px)`,
          transformOrigin: 'center center',
          filter: 'brightness(0.68) contrast(1.15) saturate(0.90)',
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Box protetor com gradiente moderado para preservar a cena */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.85) 0%, rgba(15,23,42,0.40) 45%, rgba(15,23,42,0.88) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo dentro da Safe Zone */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Rótulo superior */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 999,
            backgroundColor: 'rgba(31, 41, 55, 0.94)',
            border: '1.5px solid rgba(239, 68, 68, 0.6)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#FCA5A5',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            ⚠️ O PROBLEMA
          </span>
        </div>

        {/* Título de Dor */}
        <div
          style={{
            marginTop: 30,
            padding: '16px 36px',
            borderRadius: 20,
            backgroundColor: 'rgba(15, 23, 42, 0.96)',
            border: '2px solid rgba(255, 255, 255, 0.15)',
            boxShadow: '0 16px 40px rgba(0,0,0,0.7)',
          }}
        >
          <h2
            style={{
              margin: 0,
              fontFamily,
              fontSize: 58,
              fontWeight: 900,
              color: '#FFFFFF',
              textAlign: 'center',
              lineHeight: 1.15,
              letterSpacing: 1,
            }}
          >
            DEMORA NO ATENDIMENTO
          </h2>
        </div>

        {/* Card Dinâmico Único Evolutivo (Respeita regra de no máximo 2 blocos simultâneos) */}
        {frame >= 15 && (
          <div
            style={{
              marginTop: 40,
              width: 860,
              maxWidth: '100%',
              transform: `translateY(${hoverY}px)`,
              padding: '32px 36px',
              borderRadius: 24,
              backgroundColor:
                frame >= 142
                  ? 'rgba(153, 27, 27, 0.95)'
                  : 'rgba(30, 41, 59, 0.96)',
              border:
                frame >= 142
                  ? '2px solid #EF4444'
                  : '2px solid rgba(245, 158, 11, 0.6)',
              boxShadow: '0 20px 50px rgba(0,0,0,0.75)',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              transition: 'background-color 0.3s ease, border 0.3s ease',
            }}
          >
            {frame < 85 && (
              <div
                style={{
                  transform: `scale(${spring1}) translateX(${slide1}px)`,
                  opacity: opac1,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                  <span style={{fontSize: 38}}>🌙</span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 38,
                      fontWeight: 800,
                      color: '#F59E0B',
                    }}
                  >
                    Cliente Escrevia à Noite
                  </span>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 600,
                    color: '#F1F5F9',
                    lineHeight: 1.3,
                  }}
                >
                  Mensagens chegando tarde sem ninguém da equipe disponível.
                </div>
              </div>
            )}

            {frame >= 85 && frame < 142 && (
              <div
                style={{
                  transform: `scale(${spring2}) translateX(${slide2}px)`,
                  opacity: opac2,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                  <span style={{fontSize: 38}}>⏰</span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 38,
                      fontWeight: 800,
                      color: '#38BDF8',
                    }}
                  >
                    Horário Para o Dia Seguinte
                  </span>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 600,
                    color: '#F1F5F9',
                    lineHeight: 1.3,
                  }}
                >
                  O cliente tinha urgência para ser atendido logo pela manhã.
                </div>
              </div>
            )}

            {frame >= 142 && (
              <div
                style={{
                  transform: `scale(${spring3}) translateX(${slide3}px)`,
                  opacity: opac3,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                  <span style={{fontSize: 38}}>❌</span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 38,
                      fontWeight: 900,
                      color: '#FFFFFF',
                    }}
                  >
                    Ninguém Respondia
                  </span>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 700,
                    color: '#FEE2E2',
                    lineHeight: 1.3,
                  }}
                >
                  Sem resposta, o cliente desistia ou ia para outro prestador.
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
