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

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera progressivo no vídeo do dono (push progressivo de 1.00 a 1.10)
  // Aumenta a velocidade de push a partir do frame 108 para criar tensão dramática na dor relatada
  const videoScale = interpolate(frame, [0, 108, 234], [1.0, 1.04, 1.10], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada da cena (overlap com a cena 0)
  const sceneOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Badge no topo (entra rápido em 0.2s)
  const sprBadge = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Card Fase 1: entra quando a fala começa (4.788s no vídeo global -> ~frame 26 local)
  const sprCard1 = spring({
    frame: frame - 26,
    fps,
    config: {damping: 15, stiffness: 120},
  });

  // Card Fase 2: entra na fala de espera/desistência (7.5s no vídeo global -> ~frame 108 local)
  const sprCard2 = spring({
    frame: frame - 108,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Pulso sutil no ponto de alerta (a cada 30 frames)
  const pulseScale = 1 + 0.15 * Math.sin((frame * Math.PI) / 15);

  // Micro-respiração e pulso contínuo de cor no card de desistência para não ficar congelado
  const card2Breath =
    frame >= 108 ? 1.0 + 0.02 * Math.sin(((frame - 108) * Math.PI) / 14) : 1.0;
  const glowIntensity =
    frame >= 108 ? 0.5 + 0.3 * Math.sin(((frame - 108) * Math.PI) / 12) : 0.4;
  const hourglassRot =
    frame >= 108 ? Math.sin(((frame - 108) * Math.PI) / 15) * 15 : 0;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        fontFamily,
        opacity: sceneOpacity,
      }}
    >
      {/* Vídeo do Dono em Tela Cheia */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
          }}
        />
        {/* Vinheta escura no topo para resguardar o contraste dos textos */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(to bottom, rgba(11, 13, 19, 0.94) 0%, rgba(11, 13, 19, 0.5) 75%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
        {/* Vinheta escura na base para resguardar a legenda */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 450,
            background:
              'linear-gradient(to top, rgba(11, 13, 19, 0.95) 0%, rgba(11, 13, 19, 0.5) 70%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Faixa Superior (Safe Zone y = 160 a 420) — Rosto do apresentador totalmente livre */}
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
          zIndex: 20,
        }}
      >
        {/* Pill Badge: O PROBLEMA */}
        <div
          style={{
            transform: `scale(${sprBadge})`,
            opacity: sprBadge,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 30,
            background: '#31060F',
            border: '1.5px solid #E11D48',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.75)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              background: '#E11D48',
              transform: `scale(${pulseScale})`,
              boxShadow: '0 0 10px #E11D48',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O PROBLEMA
          </span>
        </div>

        {/* Card Dinâmico Superior (respiro garantido > 60px acima da cabeça) */}
        <div
          style={{
            width: '100%',
            maxWidth: 960,
            background: 'rgba(11, 13, 19, 0.94)',
            borderRadius: 22,
            border:
              frame < 108
                ? '1.5px solid rgba(225, 29, 72, 0.45)'
                : '2px solid rgba(250, 204, 21, 0.8)',
            padding: '16px 28px',
            boxShadow:
              frame < 108
                ? '0 15px 35px rgba(0, 0, 0, 0.85)'
                : `0 18px 45px rgba(225, 29, 72, ${glowIntensity})`,
            minHeight: 110,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transform: `scale(${card2Breath})`,
            transition: 'box-shadow 0.2s ease',
          }}
        >
          {frame < 108 ? (
            <div
              style={{
                transform: `scale(${sprCard1})`,
                opacity: sprCard1,
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  fontSize: 48,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.15,
                }}
              >
                CLIENTE MANDA UM OI...
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#E2E8F0',
                  marginTop: 6,
                }}
              >
                Espera atendimento manual e desiste
              </div>
            </div>
          ) : (
            <div
              style={{
                transform: `scale(${sprCard2})`,
                opacity: sprCard2,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center',
                gap: 6,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 12,
                }}
              >
                <span
                  style={{
                    fontSize: 40,
                    display: 'inline-block',
                    transform: `rotate(${hourglassRot}deg)`,
                  }}
                >
                  ⏳
                </span>
                <span
                  style={{
                    fontSize: 48,
                    fontWeight: 900,
                    color: '#FACC15',
                    textTransform: 'uppercase',
                    lineHeight: 1.15,
                    textShadow: '0 0 20px rgba(250, 204, 21, 0.4)',
                  }}
                >
                  ...E DESISTE ANTES DE PEDIR
                </span>
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FDA4AF',
                }}
              >
                Venda perdida por demora no retorno
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
