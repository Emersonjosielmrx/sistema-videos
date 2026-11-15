import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
  cores: {
    marca: string;
    destaque: string;
    apoio: string;
    fundo_escuro: string;
  };
};

export const Cena0: React.FC<Props> = ({fontFamily, cores}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera na foto (push-in)
  const scale = interpolate(frame, [0, 155], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });
  const panY = interpolate(frame, [0, 155], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Fade out suave na transição
  const opacidadeSaida = interpolate(frame, [142, 155], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Entradas escalonadas com mola
  const animBadge = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Palavra "CLIENTE DESMARCOU" (entra ~0.3s -> frame 9)
  const animLinha1 = spring({
    frame: frame - 9,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Palavra "DE ÚLTIMA HORA?" (entra ~1.48s -> frame 44)
  const animLinha2 = spring({
    frame: frame - 44,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // "BURACO NA AGENDA" Card (entra ~2.66s -> frame 80)
  const animCard = spring({
    frame: frame - 80,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Pulso contínuo de alerta
  const pulsoAlerta = 1 + 0.05 * Math.sin(frame * 0.15);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: cores.fundo_escuro,
        overflow: 'hidden',
        opacity: opacidadeSaida,
      }}
    >
      {/* Foto de Fundo com Movimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${scale}) translateY(${panY}px)`,
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

      {/* Véu Escuro com Vinheta de Foco */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 40%, rgba(15, 23, 42, 0.45) 0%, rgba(15, 23, 42, 0.88) 75%, rgba(10, 15, 28, 0.96) 100%)',
        }}
      />

      {/* Conteúdo Gráfico Alinhado na Safe Zone */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
          zIndex: 10,
        }}
      >
        {/* Badge do Gancho */}
        <div
          style={{
            opacity: animBadge,
            transform: `translateY(${interpolate(animBadge, [0, 1], [-20, 0])}px) scale(${animBadge})`,
            backgroundColor: 'rgba(31, 41, 55, 0.9)',
            border: `2px solid ${cores.destaque}`,
            borderRadius: 30,
            padding: '10px 24px',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            boxShadow: `0 4px 20px rgba(0,0,0,0.5), 0 0 15px rgba(255, 169, 77, 0.3)`,
            marginBottom: 26,
          }}
        >
          <span style={{fontSize: 34}}>⚠️</span>
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Alerta de Atendimento
          </span>
        </div>

        {/* Linha 1 Cinética: CLIENTE DESMARCOU */}
        <div
          style={{
            opacity: animLinha1,
            transform: `translateY(${interpolate(animLinha1, [0, 1], [30, 0])}px) scale(${interpolate(animLinha1, [0, 1], [0.92, 1])})`,
            fontSize: 58,
            fontWeight: 900,
            color: '#FFFFFF',
            textAlign: 'center',
            lineHeight: 1.15,
            textShadow: '0 4px 16px rgba(0,0,0,0.85)',
            textTransform: 'uppercase',
            marginBottom: 14,
          }}
        >
          Cliente Desmarcou
        </div>

        {/* Linha 2 Cinética com Destaque: DE ÚLTIMA HORA? */}
        <div
          style={{
            opacity: animLinha2,
            transform: `translateY(${interpolate(animLinha2, [0, 1], [30, 0])}px) scale(${interpolate(animLinha2, [0, 1], [0.9, 1])})`,
            backgroundColor: cores.destaque,
            color: cores.apoio,
            fontSize: 62,
            fontWeight: 900,
            padding: '6px 26px',
            borderRadius: 18,
            boxShadow: '0 8px 30px rgba(0,0,0,0.6)',
            textTransform: 'uppercase',
            letterSpacing: '-0.01em',
            marginBottom: 36,
          }}
        >
          De Última Hora?
        </div>

        {/* Card Alerta de Horário Vago (Entra no avental quando fala "buraco na agenda", preservando o rosto 100% livre) */}
        <div
          style={{
            marginTop: 360,
            opacity: animCard,
            transform: `translateY(${interpolate(animCard, [0, 1], [40, 0])}px) scale(${interpolate(animCard, [0, 1], [0.9, 1]) * pulsoAlerta})`,
            width: '100%',
            maxWidth: 920,
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: '2px solid rgba(239, 68, 68, 0.7)',
            borderRadius: 24,
            padding: '24px 30px',
            boxShadow: '0 12px 35px rgba(0,0,0,0.7), 0 0 25px rgba(239, 68, 68, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 38}}>📅</span>
              <span
                style={{
                  fontSize: 36,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                14:00 • Horário Vago
              </span>
            </div>
            <div
              style={{
                backgroundColor: '#EF4444',
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 800,
                padding: '6px 16px',
                borderRadius: 12,
                textTransform: 'uppercase',
                letterSpacing: '0.02em',
              }}
            >
              Cancelado
            </div>
          </div>

          <div
            style={{
              fontSize: 34,
              fontWeight: 500,
              color: '#D1D5DB',
              lineHeight: 1.3,
            }}
          >
            Buraco inesperado que prejudica o faturamento do dia.
          </div>
        </div>
      </div>
    </div>
  );
};
