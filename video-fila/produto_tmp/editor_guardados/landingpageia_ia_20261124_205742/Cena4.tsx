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
};

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  // Push-in contínuo e pan vertical no fundo desfocado (1.06 a 1.24)
  const bgScale = interpolate(frame, [0, durationInFrames], [1.06, 1.24], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, durationInFrames], [0, -40], {
    extrapolateRight: 'clamp',
  });

  // Movimento contínuo do brilho radial ambiente
  const ambientScale = interpolate(frame, [0, durationInFrames], [0.9, 1.25], {
    extrapolateRight: 'clamp',
  });
  const ambientY = interpolate(frame, [0, durationInFrames], [32, 40], {
    extrapolateRight: 'clamp',
  });

  // Fade-in inicial suave
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Animações dos elementos do cartão final
  // 1. Marca no topo
  const brandSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 2. Headline principal
  const headlineSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // 3. Botão de CTA
  const buttonSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 4. Arroba oficial
  const arrobaSpring = spring({
    frame: frame - 25,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Pulso contínuo do botão de CTA (1.00 a 1.07 em ciclos de ~1.2s / 36 frames)
  const pulseCycle = (frame % 36) / 36;
  const pulseScale = 1.0 + Math.sin(pulseCycle * Math.PI * 2) * 0.04;

  // Reflexo de luz (sheen sweep) atravessando o botão
  const sheenPos = interpolate(frame % 45, [0, 45], [-150, 450], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#111827',
        opacity: fadeIn,
      }}
    >
      {/* Background desfocado com zoom contínuo e pan */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          filter: 'blur(20px)',
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu escuro da marca para contraste absoluto */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at center, rgba(17, 24, 39, 0.82) 0%, rgba(15, 23, 42, 0.95) 100%)',
        }}
      />

      {/* Brilho radial âmbar dinâmico no centro */}
      <div
        style={{
          position: 'absolute',
          top: `${ambientY}%`,
          left: '50%',
          transform: `translate(-50%, -50%) scale(${ambientScale})`,
          width: 680,
          height: 680,
          background:
            'radial-gradient(circle, rgba(245, 158, 11, 0.22) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo Central na Safe Zone (y: 150 a 1580, laterais: 60px) */}
      <div
        style={{
          position: 'absolute',
          top: 220,
          bottom: 220,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontFamily,
        }}
      >
        {/* Topo: Nome da Marca */}
        <div
          style={{
            opacity: brandSpring,
            transform: `scale(${brandSpring})`,
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '14px 32px',
            borderRadius: 30,
            background: 'rgba(17, 24, 39, 0.95)',
            border: '2px solid rgba(245, 158, 11, 0.55)',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.7)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#F59E0B',
              boxShadow: '0 0 12px #F59E0B',
            }}
          />
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#F59E0B',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            Landing Page e Comunicação
          </span>
        </div>

        {/* Centro: Gancho Forte e Promessa */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 24,
            opacity: headlineSpring,
            transform: `scale(${interpolate(headlineSpring, [0, 1], [0.9, 1])}) translateY(${interpolate(
              headlineSpring,
              [0, 1],
              [30, 0]
            )}px)`,
            maxWidth: 920,
            textAlign: 'center',
          }}
        >
          <div
            style={{
              background: 'rgba(17, 24, 39, 0.94)',
              padding: '18px 36px',
              borderRadius: 24,
              border: '1.5px solid rgba(255, 255, 255, 0.14)',
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.75)',
            }}
          >
            <span
              style={{
                fontSize: 54,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '-0.5px',
                textTransform: 'uppercase',
              }}
            >
              Página e Vídeo
            </span>
          </div>

          <div
            style={{
              background: '#F59E0B',
              padding: '20px 42px',
              borderRadius: 26,
              boxShadow: '0 20px 50px rgba(245, 158, 11, 0.45)',
            }}
          >
            <span
              style={{
                fontSize: 62,
                fontWeight: 900,
                color: '#121216',
                letterSpacing: '-1px',
                textTransform: 'uppercase',
              }}
            >
              Prontos Para Vender
            </span>
          </div>

          <p
            style={{
              fontSize: 34,
              fontWeight: 600,
              color: '#CBD5E1',
              maxWidth: 780,
              lineHeight: 1.35,
              marginTop: 10,
            }}
          >
            Estrutura completa para apresentar seu produto e transformar visita em cliente.
          </p>
        </div>

        {/* Base: CTA Gigante Pulsante + Perfil */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 28,
            width: '100%',
          }}
        >
          {/* Botão de CTA com pulso contínuo */}
          <div
            style={{
              opacity: buttonSpring,
              transform: `scale(${buttonSpring * pulseScale})`,
              background: '#F59E0B',
              borderRadius: 34,
              padding: '24px 56px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              boxShadow: '0 16px 50px rgba(245, 158, 11, 0.55)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Brilho passando pelo botão */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 70,
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent)',
                transform: `translateX(${sheenPos}px) skewX(-20deg)`,
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontSize: 48,
                fontWeight: 900,
                color: '#121216',
                textTransform: 'uppercase',
                letterSpacing: '1px',
              }}
            >
              Chame no Direct ➔
            </span>
          </div>

          {/* Arroba Oficial */}
          <div
            style={{
              opacity: arrobaSpring,
              transform: `scale(${arrobaSpring})`,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 28px',
              borderRadius: 24,
              background: 'rgba(17, 24, 39, 0.94)',
              border: '1.5px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
            }}
          >
            <span style={{fontSize: 32}}>💬</span>
            <span
              style={{
                fontSize: 36,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: '0.5px',
              }}
            >
              @landingpageia.ia
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
