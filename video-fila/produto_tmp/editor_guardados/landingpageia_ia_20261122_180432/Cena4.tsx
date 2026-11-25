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

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Transição de entrada suave (fade-in inicial de 6 frames)
  const fadeIn = interpolate(frame, [0, 6], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Zoom contínuo na foto de fundo (1.05 -> 1.15)
  const bgScale = interpolate(frame, [0, 118], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Animações escalonadas de entrada (stagger de 5 a 6 frames entre elementos)
  const badgeSpring = spring({
    frame: frame - 0,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const titleSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  const descSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const ctaSpring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 10, stiffness: 130},
  });

  const handleSpring = spring({
    frame: frame - 22,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Pulso contínuo do botão CTA (ciclo de ~1.2s, escala 1.00 -> 1.07)
  const pulseScale = 1.0 + 0.05 * Math.sin((frame / 30) * Math.PI * 2 * 0.85);

  // Efeito de brilho/varredura (gloss sweep) no botão CTA
  const sweepProgress = (frame % 45) / 45; // ciclo a cada 1.5s
  const sweepX = interpolate(sweepProgress, [0, 1], [-200, 850]);

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0F131A',
        opacity: fadeIn,
      }}
    >
      {/* Imagem de Fundo com zoom contínuo */}
      <Img
        src={staticFile('img_4.jpg')}
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${bgScale})`,
          filter: 'brightness(0.55) contrast(1.2)',
        }}
      />

      {/* Gradiente e véu escuro da marca */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 45%, rgba(245, 158, 11, 0.22) 0%, rgba(11, 15, 23, 0.88) 55%, rgba(11, 15, 23, 0.98) 100%)',
        }}
      />

      {/* Conteúdo Central Harmoniosamente Distribuído (y: 300 a 1500 na Safe Zone) */}
      <div
        style={{
          position: 'absolute',
          top: 310,
          bottom: 390,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* 1. Badge Superior: Fato Real (stagger frame 0) */}
        <div
          style={{
            transform: `translateY(${interpolate(
              badgeSpring,
              [0, 1],
              [-35, 0]
            )}px)`,
            opacity: Math.min(badgeSpring, 1),
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '14px 32px',
              borderRadius: 30,
              background: 'rgba(245, 158, 11, 0.16)',
              border: '2px solid #F59E0B',
              boxShadow: '0 8px 24px rgba(245, 158, 11, 0.3)',
            }}
          >
            <span style={{fontSize: 26}}>🚀</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: '#FDE68A',
                letterSpacing: 1.2,
                textTransform: 'uppercase',
              }}
            >
              Página Pronta Que Vende
            </span>
          </div>
        </div>

        {/* 2. Nome da Marca Principal (stagger frame 5) */}
        <div
          style={{
            maxWidth: 960,
            transform: `scale(${titleSpring})`,
            opacity: Math.min(titleSpring, 1),
          }}
        >
          <h1
            style={{
              margin: 0,
              fontFamily,
              fontSize: 62,
              fontWeight: 900,
              color: '#FFFFFF',
              textAlign: 'center',
              lineHeight: 1.15,
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              textShadow: '0 6px 24px rgba(0, 0, 0, 0.9)',
            }}
          >
            Landing Page <br />
            <span style={{color: '#F59E0B'}}>E Comunicação</span>
          </h1>
        </div>

        {/* 3. Frase Fato do Briefing (stagger frame 10 - Letra grande e peso destacado) */}
        <div
          style={{
            maxWidth: 900,
            padding: '0 10px',
            transform: `translateY(${interpolate(
              descSpring,
              [0, 1],
              [30, 0]
            )}px)`,
            opacity: Math.min(descSpring, 1),
          }}
        >
          <p
            style={{
              margin: 0,
              fontFamily,
              fontSize: 38,
              fontWeight: 700,
              color: '#F1F5F9',
              textAlign: 'center',
              lineHeight: 1.45,
              textShadow: '0 4px 16px rgba(0, 0, 0, 0.95)',
            }}
          >
            Página de vendas pronta e vídeo de demonstração para apresentar seu
            produto e transformar visita em cliente.
          </p>
        </div>

        {/* 4. Botão de Ação CTA com Pulso Contínuo, Gloss Sweep e Pop Elástico (stagger frame 16) */}
        <div
          style={{
            transform: `scale(${ctaSpring * pulseScale})`,
            opacity: Math.min(ctaSpring, 1),
          }}
        >
          <div
            style={{
              position: 'relative',
              width: 780,
              height: 120,
              borderRadius: 32,
              backgroundColor: '#F59E0B',
              boxShadow:
                '0 16px 45px rgba(245, 158, 11, 0.6), 0 0 30px rgba(245, 158, 11, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 18,
              overflow: 'hidden',
            }}
          >
            {/* Brilho diagonal passando pelo botão */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 100,
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.7), transparent)',
                transform: `translateX(${sweepX}px) skewX(-25deg)`,
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: '#121216',
                textTransform: 'uppercase',
                letterSpacing: 1.2,
              }}
            >
              Chame No Direct
            </span>
            <span
              style={{
                fontSize: 42,
                fontWeight: 900,
                color: '#121216',
                transform: 'translateX(2px)',
              }}
            >
              ➔
            </span>
          </div>
        </div>

        {/* 5. Perfil Oficial da Marca (stagger frame 22) */}
        <div
          style={{
            transform: `translateY(${interpolate(
              handleSpring,
              [0, 1],
              [25, 0]
            )}px)`,
            opacity: Math.min(handleSpring, 1),
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              padding: '16px 38px',
              borderRadius: 24,
              background: 'rgba(255, 255, 255, 0.09)',
              border: '1.5px solid rgba(255, 255, 255, 0.25)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
            }}
          >
            <span style={{fontSize: 34}}>📸</span>
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 0.8,
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
