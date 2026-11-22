import React from 'react';
import {useCurrentFrame, useVideoConfig, spring, interpolate, Img, staticFile} from 'remotion';
import {BRIEFING} from './constants';

type Props = {
  fontFamily: string;
};

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração da cena: 29.17s a 33.11s (~119 frames)
  // Zoom contínuo do fundo para garantir ≥ 4% de movimento contínuo
  const bgScale = interpolate(frame, [0, 119], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });

  const bgTranslateY = interpolate(frame, [0, 119], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Fade in da cena no início
  const cenaOpacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Animação de entrada dos blocos
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const valueSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  const featuresSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  const ctaSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Pulso contínuo do botão de CTA (1.00 a 1.07 em ciclos de ~1.2s = 36 frames)
  const ctaPulse = (Math.sin((frame * Math.PI * 2) / 36) + 1) / 2; // 0 a 1
  const ctaScale = 1.0 + ctaPulse * 0.07;

  // Brilho passando pelo botão (shimmer sweep)
  const shimmerPos = interpolate(frame % 45, [0, 30], [-100, 200], {
    extrapolateRight: 'clamp',
  });

  // Flutuação sutil do logo
  const floatY = Math.sin(frame / 10) * 6;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        opacity: cenaOpacity,
        overflow: 'hidden',
        backgroundColor: '#0B0D13',
      }}
    >
      {/* Imagem de Fundo Desfocada com zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: -60,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(22px)',
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

      {/* Véu Escuro da Marca com Gradiente */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 35%, rgba(31, 41, 55, 0.88) 0%, rgba(11, 13, 19, 0.96) 80%)',
        }}
      />

      {/* Partículas / Linhas de Luz Futuristas */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.15,
          backgroundImage:
            'radial-gradient(circle, rgba(139, 92, 246, 0.4) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
          transform: `translateY(${frame % 40}px)`,
        }}
      />

      {/* Container Central com Conteúdo */}
      <div
        style={{
          position: 'absolute',
          top: 195,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 30,
        }}
      >
        {/* Selo Superior de Categoria */}
        <div
          style={{
            marginBottom: 24,
            transform: `scale(${logoSpring})`,
            opacity: logoSpring,
          }}
        >
          <div
            style={{
              padding: '6px 20px',
              borderRadius: 20,
              backgroundColor: 'rgba(139, 92, 246, 0.2)',
              border: `1.5px solid ${BRIEFING.cores.marca}`,
              boxShadow: '0 4px 14px rgba(139, 92, 246, 0.3)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: BRIEFING.cores.destaque_claro,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
              }}
            >
              AVATAR IA DE PRODUTO
            </span>
          </div>
        </div>

        {/* Logo / Marca */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            marginBottom: 28,
            transform: `translateY(${floatY}px) scale(${logoSpring})`,
            opacity: logoSpring,
          }}
        >
          {/* Ícone de Avatar IA */}
          <div
            style={{
              width: 100,
              height: 100,
              borderRadius: 30,
              background: `linear-gradient(135deg, ${BRIEFING.cores.marca}, #6D28D9)`,
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              marginBottom: 16,
              boxShadow: '0 12px 30px rgba(139, 92, 246, 0.6)',
              border: '2px solid rgba(255, 255, 255, 0.3)',
            }}
          >
            <span style={{fontSize: 52}}>🤖</span>
          </div>

          {/* Nome da Marca em Branco Legível */}
          <span
            style={{
              fontFamily,
              fontSize: 68,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
              textTransform: 'uppercase',
              textShadow: '0 4px 20px rgba(0,0,0,0.9)',
            }}
          >
            {BRIEFING.marca}
          </span>
        </div>

        {/* Frase do que o produto faz */}
        <div
          style={{
            maxWidth: 880,
            marginBottom: 36,
            transform: `scale(${valueSpring})`,
            opacity: valueSpring,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 700,
              lineHeight: 1.3,
              color: '#F1F5F9',
              textShadow: '0 3px 12px rgba(0,0,0,0.8)',
            }}
          >
            Tenha seu próprio avatar IA postando todo dia nas redes.
          </span>
        </div>

        {/* Benefícios em Pílulas Alinhadas */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
            width: '100%',
            maxWidth: 720,
            marginBottom: 44,
            transform: `scale(${featuresSpring})`,
            opacity: featuresSpring,
          }}
        >
          {[
            {texto: 'Posturas automáticas', icone: '⚡'},
            {texto: 'Fala em português', icone: '🇧🇷'},
            {texto: '100% seu', icone: '🔒'},
          ].map((item, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                backgroundColor: 'rgba(15, 23, 42, 0.88)',
                border: '1.5px solid rgba(139, 92, 246, 0.35)',
                padding: '12px 24px',
                borderRadius: 18,
                boxShadow: '0 6px 18px rgba(0,0,0,0.5)',
              }}
            >
              <span style={{fontSize: 34}}>{item.icone}</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  letterSpacing: '0.02em',
                }}
              >
                {item.texto}
              </span>
            </div>
          ))}
        </div>

        {/* Super Botão de CTA com Pulsação Contínua e Shimmer */}
        <div
          style={{
            marginBottom: 32,
            transform: `scale(${ctaSpring * ctaScale})`,
            opacity: ctaSpring,
          }}
        >
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 18,
              background: `linear-gradient(135deg, ${BRIEFING.cores.marca}, #7C3AED)`,
              border: `2px solid #C4B5FD`,
              padding: '20px 48px',
              borderRadius: 36,
              boxShadow: `0 14px 40px rgba(139, 92, 246, ${0.5 + ctaPulse * 0.3})`,
            }}
          >
            {/* Efeito Shimmer Sweep */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 80,
                left: `${shimmerPos}%`,
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.45), transparent)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                textShadow: '0 2px 8px rgba(0,0,0,0.5)',
              }}
            >
              {BRIEFING.convite.toUpperCase()}
            </span>

            {/* Ícone de Seta/Direct */}
            <svg
              width="44"
              height="44"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </div>
        </div>

        {/* Perfil Oficial (@marca) — Visível desde o frame 0.0s */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 20,
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
          }}
        >
          <svg
            width="34"
            height="34"
            viewBox="0 0 24 24"
            fill="none"
            stroke={BRIEFING.cores.destaque_brilho}
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
            <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
            <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
          </svg>
          <span
            style={{
              fontFamily,
              fontSize: 36,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.04em',
            }}
          >
            {BRIEFING.arroba}
          </span>
        </div>
      </div>
    </div>
  );
};
