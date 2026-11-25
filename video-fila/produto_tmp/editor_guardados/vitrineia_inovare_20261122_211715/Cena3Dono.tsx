import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Props {
  fontFamily: string;
  marcaCor: string;
}

export const Cena3Dono: React.FC<Props> = ({fontFamily, marcaCor}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera: push suave de 1.00 para 1.07
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.07], {
    extrapolateRight: 'clamp',
  });
  const videoTranslateY = interpolate(frame, [0, 245], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Micro-dinâmica
  const pulseDot = 0.5 + 0.5 * Math.sin(frame / 6);

  // Entrada do Badge "O RESULTADO"
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  // Fase 1: "CLIENTE É ATENDIDO NA HORA" (frames 0 a 148)
  // Fase 2: "ACORDA COM A VENDA ENCAMINHADA" (frames 149 a 245)
  const isPhase2 = frame >= 149;

  const cardSpringPhase1 = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, mass: 0.8},
  });

  const cardSpringPhase2 = spring({
    frame: frame - 149,
    fps,
    config: {damping: 13, mass: 0.8},
  });

  // Transição de saída nos últimos 15 frames
  const exitOpacity = interpolate(frame, [230, 245], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#000000',
        opacity: exitOpacity,
      }}
    >
      {/* Vídeo do Dono em Tela Cheia com Push Dinâmico */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: '50% 45%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: 1080,
            height: 1920,
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu protetor discreto SOMENTE no topo (y <= 420) para contraste dos títulos */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 440,
          background:
            'linear-gradient(to bottom, rgba(11, 13, 19, 0.88) 0%, rgba(11, 13, 19, 0.6) 240px, transparent 440px)',
          pointerEvents: 'none',
        }}
      />

      {/* ELEMENTOS EXCLUSIVAMENTE NA FAIXA SUPERIOR: y=165 a y=400 (Rosto 100% livre) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
          pointerEvents: 'none',
        }}
      >
        {/* Badge do Rótulo: O RESULTADO */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 26px',
            borderRadius: 999,
            background: 'rgba(11, 13, 19, 0.94)',
            border: '1.5px solid #4ADE80',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#4ADE80',
              boxShadow: `0 0 10px rgba(74, 222, 128, ${pulseDot})`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              letterSpacing: '1px',
              color: '#4ADE80',
              textTransform: 'uppercase',
            }}
          >
            O RESULTADO
          </span>
        </div>

        {/* Card Superior Cinético */}
        <div
          style={{
            width: '100%',
            maxWidth: 960,
            padding: '20px 32px',
            borderRadius: 24,
            background: 'rgba(11, 13, 19, 0.94)',
            border: '1.5px solid rgba(255, 255, 255, 0.14)',
            boxShadow: '0 12px 36px rgba(0, 0, 0, 0.8)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 8,
          }}
        >
          {!isPhase2 ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 8,
                transform: `scale(${cardSpringPhase1})`,
                opacity: cardSpringPhase1,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 48,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textAlign: 'center',
                  lineHeight: 1.2,
                }}
              >
                CLIENTE ATENDIDO NA HORA
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#4ADE80',
                  textAlign: 'center',
                }}
              >
                MESMO QUANDO ESTOU DORMINDO
              </span>
            </div>
          ) : (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 8,
                transform: `scale(${cardSpringPhase2})`,
                opacity: cardSpringPhase2,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 48,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textAlign: 'center',
                  lineHeight: 1.2,
                }}
              >
                ACORDA COM A VENDA ENCAMINHADA
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: marcaCor,
                  textAlign: 'center',
                }}
              >
                ✓ ATENDIMENTO COMPLETO E AUTOMÁTICO
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
