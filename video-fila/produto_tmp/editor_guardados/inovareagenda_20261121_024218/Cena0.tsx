import React from 'react';
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Img,
  staticFile,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const totalFrames = 157;

  // Câmera dinâmica contínua: zoom 1.05 -> 1.16 e pan vertical sutil
  const bgScale = interpolate(frame, [0, totalFrames], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, totalFrames], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge superior aos 0.12s (frame 4)
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Linha 1 aos 0.25s (frame 8)
  const line1Spring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Linha 2 destacada aos 0.7s (frame 22, na palavra "desmarcou / em cima da hora")
  const line2Spring = spring({
    frame: frame - 22,
    fps,
    config: {damping: 13, stiffness: 100},
  });

  // Linha 3 aos 1.2s (frame 36)
  const line3Spring = spring({
    frame: frame - 36,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Card de Dor / Alerta entra cedo aos 1.5s (frame 46) para garantir retenção e preenchimento
  const cardSpring = spring({
    frame: frame - 46,
    fps,
    config: {damping: 13, stiffness: 95},
  });

  // Pulso contínuo do alerta vermelho/coral
  const pulse = Math.sin(frame * 0.18) * 0.035 + 1.0;

  // Pulso de alerta e atenção no selo CANCELADO
  const canceladoPulse = 1.0 + 0.08 * Math.sin(frame * 0.28);

  // Barra de tempo ocioso crescendo com fluidez no card
  const idleProgress = interpolate(frame, [46, totalFrames], [20, 98], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Saída suave no final
  const exitOpacity = interpolate(frame, [totalFrames - 10, totalFrames], [1, 0], {
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
        backgroundColor: '#0B0D13',
        opacity: exitOpacity,
      }}
    >
      {/* Imagem de Fundo Clara e Vibrante (Regra 19) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Vinheta Suave Apenas para Contraste — Mantendo a foto bem exposta */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(11, 13, 19, 0.78) 0%, rgba(11, 13, 19, 0.28) 35%, rgba(11, 13, 19, 0.40) 65%, rgba(11, 13, 19, 0.82) 100%)',
        }}
      />

      {/* Conteúdo Seguro (y: 175 a 1380) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 175,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {/* Badge Superior */}
        {badgeSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${badgeSpring})`,
              opacity: badgeSpring,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 28px',
              borderRadius: 30,
              background: 'rgba(31, 41, 55, 0.96)',
              border: '2px solid #F59E0B',
              boxShadow: '0 8px 24px rgba(245, 158, 11, 0.3)',
              marginBottom: 20,
            }}
          >
            <span style={{fontSize: 32}}>⚠️</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FBBF24',
                letterSpacing: 1.2,
                textTransform: 'uppercase',
              }}
            >
              Imprevisto na Agenda
            </span>
          </div>
        )}

        {/* Bloco de Título Cinético Ocupando a Parte Superior com Fundo Opaco */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 12,
            background: 'rgba(15, 23, 42, 0.88)',
            padding: '24px 20px',
            borderRadius: 28,
            border: '1.5px solid rgba(255, 255, 255, 0.12)',
            boxShadow: '0 12px 35px rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(12px)',
          }}
        >
          {line1Spring > 0.01 && (
            <div
              style={{
                transform: `translateY(${(1 - line1Spring) * 20}px) scale(${line1Spring})`,
                opacity: line1Spring,
                fontFamily,
                fontSize: 54,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.15,
                textTransform: 'uppercase',
                textShadow: '0 3px 14px rgba(0, 0, 0, 0.9)',
              }}
            >
              Cliente desmarcou
            </div>
          )}

          {line2Spring > 0.01 && (
            <div
              style={{
                transform: `scale(${line2Spring})`,
                opacity: line2Spring,
                background: '#F59E0B',
                color: '#121216',
                fontFamily,
                fontSize: 58,
                fontWeight: 900,
                lineHeight: 1.1,
                padding: '8px 30px',
                borderRadius: 18,
                textTransform: 'uppercase',
                boxShadow: '0 8px 28px rgba(245, 158, 11, 0.45)',
              }}
            >
              Em cima da hora?
            </div>
          )}

          {line3Spring > 0.01 && (
            <div
              style={{
                transform: `translateY(${(1 - line3Spring) * 15}px)`,
                opacity: line3Spring,
                fontFamily,
                fontSize: 44,
                fontWeight: 800,
                color: '#E2E8F0',
                lineHeight: 1.2,
                marginTop: 6,
              }}
            >
              E você ficou com o{' '}
              <span style={{color: '#FF6B6B', fontWeight: 900}}>
                horário vazio?
              </span>
            </div>
          )}
        </div>

        {/* Card de Impacto / Alerta de Vaga Ociosa */}
        {cardSpring > 0.01 && (
          <div
            style={{
              transform: `translateY(${(1 - cardSpring) * 35}px) scale(${cardSpring * pulse})`,
              opacity: cardSpring,
              marginTop: 32,
              width: 880,
              background: 'rgba(17, 24, 39, 0.96)',
              border: '2.5px solid rgba(255, 107, 107, 0.75)',
              borderRadius: 30,
              padding: '28px 34px',
              boxShadow:
                '0 20px 48px rgba(0, 0, 0, 0.85), 0 0 30px rgba(255, 107, 107, 0.25)',
              display: 'flex',
              flexDirection: 'column',
              gap: 18,
            }}
          >
            {/* Topo do Card */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <span style={{fontSize: 36}}>📅</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#CBD5E1',
                    textTransform: 'uppercase',
                  }}
                >
                  Horário Agendado
                </span>
              </div>
              <div
                style={{
                  transform: `scale(${canceladoPulse})`,
                  background: 'rgba(255, 107, 107, 0.22)',
                  border: '2px solid #FF6B6B',
                  borderRadius: 14,
                  padding: '6px 18px',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#FF8787',
                  boxShadow: '0 0 18px rgba(255, 107, 107, 0.45)',
                }}
              >
                CANCELADO
              </div>
            </div>

            {/* Linha de Horário */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'baseline',
                borderBottom: '1.5px solid rgba(255, 255, 255, 0.1)',
                paddingBottom: 14,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 46,
                  fontWeight: 900,
                  color: '#FFFFFF',
                }}
              >
                15:00
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FF6B6B',
                }}
              >
                Cadeira vazia
              </span>
            </div>

            {/* Barra de Tempo Ocioso */}
            <div style={{display: 'flex', flexDirection: 'column', gap: 10}}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#94A3B8',
                }}
              >
                <span>Tempo ocioso acumulando</span>
                <span style={{color: '#F59E0B', fontWeight: 800}}>
                  Prejuízo direto
                </span>
              </div>
              <div
                style={{
                  width: '100%',
                  height: 14,
                  borderRadius: 10,
                  background: 'rgba(255, 255, 255, 0.12)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${idleProgress}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #F59E0B, #FF6B6B)',
                    boxShadow: '0 0 10px rgba(255, 107, 107, 0.6)',
                    borderRadius: 10,
                  }}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
