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

  // Movimento de câmera contínuo no vídeo do dono (1.00 -> 1.05)
  const videoScale = interpolate(frame, [0, 246], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada e saída da cena
  const sceneOpacity = interpolate(frame, [0, 8, 238, 246], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Animação da Badge Superior de Identificação (item 28a1924f)
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  // Card Fase 1: "Eu perdia venda..." (entra aos ~0.3s = frame 10)
  const card1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  // Transição para Fase 2: "O cliente esperava pouco..." (ocorre por volta de 9.1s no vídeo total, que é frame 138 na cena)
  const isFase2 = frame >= 135;
  const card2Spring = spring({
    frame: frame - 135,
    fps,
    config: {damping: 13, mass: 0.8},
  });

  // Pulso do indicador de alerta
  const alertPulse = Math.sin(frame / 6) * 0.05 + 1.0;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#000000',
        overflow: 'hidden',
        opacity: sceneOpacity,
      }}
    >
      {/* Vídeo do Dono em Tela Cheia com Zoom Leve */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
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
        {/* Camada superior suave para contraste absoluto dos textos no topo (não atinge o rosto) */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(180deg, rgba(11, 13, 19, 0.90) 0%, rgba(11, 13, 19, 0.65) 60%, rgba(11, 13, 19, 0) 100%)',
          }}
        />
      </div>

      {/* ZONA SUPERIOR LIVRE (y = 170 a 430) — ROSTO DO DONO FICA ENTRE y=580 E 1100, NUNCA COBERTO */}

      {/* 1. Badge Translúcido com Corte Diagonal (Aprovado 28a1924f) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'flex-start',
          opacity: Math.max(0, badgeSpring),
          transform: `translateX(${(1 - Math.max(0, badgeSpring)) * -40}px)`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            backgroundColor: 'rgba(15, 23, 42, 0.88)',
            border: '2px solid #A78BFA',
            clipPath: 'polygon(0 0, 100% 0, 94% 100%, 0 100%)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(10px)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#DDD6FE',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            RELATO DO LOJISTA · O PROBLEMA
          </span>
        </div>
      </div>

      {/* 2. Card Informativo de Topo Dinâmico (y = 250 a 410) */}
      <div
        style={{
          position: 'absolute',
          top: 250,
          left: 60,
          right: 60,
          height: 160,
        }}
      >
        {!isFase2 ? (
          /* Fase 1: Perdia venda por demora */
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backgroundColor: 'rgba(15, 23, 42, 0.90)',
              border: '2px solid rgba(239, 68, 68, 0.65)',
              borderRadius: 24,
              padding: '18px 28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.8)',
              backdropFilter: 'blur(12px)',
              opacity: Math.max(0, card1Spring),
              transform: `scale(${Math.max(0.8, card1Spring)})`,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 18,
                  height: 18,
                  borderRadius: '50%',
                  backgroundColor: '#EF4444',
                  boxShadow: '0 0 14px #EF4444',
                  transform: `scale(${alertPulse})`,
                }}
              />
              <span
                style={{
                  fontFamily,
                  fontSize: 40,
                  fontWeight: 900,
                  color: '#EF4444',
                  letterSpacing: 1.5,
                  textTransform: 'uppercase',
                }}
              >
                PERDA DE VENDAS
              </span>
            </div>
            <div style={{marginTop: 8}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#F8FAFC',
                }}
              >
                Demora na resposta = cliente perdido
              </span>
            </div>
          </div>
        ) : (
          /* Fase 2: Cliente compra em outra loja */
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backgroundColor: 'rgba(15, 23, 42, 0.90)',
              border: '2px solid rgba(245, 158, 11, 0.65)',
              borderRadius: 24,
              padding: '18px 28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.8)',
              backdropFilter: 'blur(12px)',
              opacity: Math.max(0, card2Spring),
              transform: `scale(${Math.max(0.8, card2Spring)})`,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 18,
                  height: 18,
                  borderRadius: '50%',
                  backgroundColor: '#F59E0B',
                  boxShadow: '0 0 14px #F59E0B',
                  transform: `scale(${alertPulse})`,
                }}
              />
              <span
                style={{
                  fontFamily,
                  fontSize: 40,
                  fontWeight: 900,
                  color: '#FBBF24',
                  letterSpacing: 1.5,
                  textTransform: 'uppercase',
                }}
              >
                FUGA PARA O CONCORRENTE
              </span>
            </div>
            <div style={{marginTop: 8}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#F8FAFC',
                }}
              >
                Sem resposta rápida, o cliente vai embora
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
