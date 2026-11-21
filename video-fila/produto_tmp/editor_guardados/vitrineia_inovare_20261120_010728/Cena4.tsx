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
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (Zoom + Pan para dinamismo constante)
  const bgScale = interpolate(frame, [0, 119], [1.02, 1.20], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 119], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada da cena final
  const sceneOpacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Animação de entrada dos blocos
  const logoSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 13, mass: 0.8},
  });

  const valueSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  const btnSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 140},
  });

  const arrobaSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  // Pulso contínuo e ativo do botão CTA (scale de 1.00 a 1.08 até o último frame)
  const buttonPulse = 1.04 + Math.sin(frame / 4.5) * 0.04;

  // Brilho passando continuamente pelo botão CTA
  const shimmerOffset = ((frame * 6) % 360) - 100;

  // Flutuação leve da marca
  const logoFloat = Math.sin(frame / 8) * 6;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0B0D13',
        overflow: 'hidden',
        opacity: sceneOpacity,
      }}
    >
      {/* Imagem de Fundo Desfocada com Movimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          filter: 'blur(20px)',
          opacity: 0.40,
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

      {/* Véu Escuro e Iluminação Radial com a cor da marca */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 45%, rgba(167, 139, 250, 0.25) 0%, rgba(15, 23, 42, 0.95) 75%)',
        }}
      />

      {/* 1. Logotipo e Nome da Marca (y = 360 a 540) */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          opacity: Math.max(0, logoSpring),
          transform: `translateY(${logoFloat + (1 - Math.max(0, logoSpring)) * -25}px)`,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 18,
          }}
        >
          {/* Ícone estilizado da Vitrine IA */}
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: 22,
              backgroundColor: '#A78BFA',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 25px rgba(167, 139, 250, 0.6)',
            }}
          >
            <svg
              width="44"
              height="44"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#121216"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="3" y="11" width="18" height="10" rx="2" />
              <circle cx="12" cy="5" r="2" />
              <path d="M12 7v4" />
              <line x1="8" y1="16" x2="8" y2="16" />
              <line x1="16" y1="16" x2="16" y2="16" />
            </svg>
          </div>
          <span
            style={{
              fontFamily,
              fontSize: 82,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 2,
              textShadow: '0 4px 20px rgba(0,0,0,0.8)',
            }}
          >
            Vitrine IA
          </span>
        </div>

        <div
          style={{
            padding: '8px 24px',
            backgroundColor: 'rgba(167, 139, 250, 0.15)',
            border: '1.5px solid rgba(167, 139, 250, 0.5)',
            borderRadius: 20,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#DDD6FE',
              letterSpacing: 3,
              textTransform: 'uppercase',
            }}
          >
            ATENDIMENTO INTELIGENTE
          </span>
        </div>
      </div>

      {/* 2. Proposta de Valor Oficial do Briefing (y = 600 a 860) */}
      <div
        style={{
          position: 'absolute',
          top: 600,
          left: 70,
          right: 70,
          backgroundColor: 'rgba(15, 23, 42, 0.88)',
          border: '2px solid rgba(167, 139, 250, 0.35)',
          borderRadius: 28,
          padding: '36px 40px',
          textAlign: 'center',
          boxShadow: '0 12px 36px rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(12px)',
          opacity: Math.max(0, valueSpring),
          transform: `scale(${Math.max(0.85, valueSpring)})`,
        }}
      >
        <div
          style={{
            fontFamily,
            fontSize: 44,
            fontWeight: 800,
            color: '#FFFFFF',
            lineHeight: 1.35,
          }}
        >
          Bot com todo o conhecimento da sua loja.
        </div>
        <div
          style={{
            marginTop: 14,
            fontFamily,
            fontSize: 40,
            fontWeight: 700,
            color: '#C4B5FD',
            lineHeight: 1.3,
          }}
        >
          Atende, recomenda e vende.
        </div>
      </div>

      {/* 3. Botão CTA Magnético Pulsante (y = 960 a 1110) */}
      <div
        style={{
          position: 'absolute',
          top: 960,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.max(0, btnSpring),
        }}
      >
        <div
          style={{
            width: 860,
            height: 116,
            backgroundColor: '#A78BFA',
            borderRadius: 32,
            border: '3px solid #DDD6FE',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 18,
            boxShadow:
              '0 16px 45px rgba(167, 139, 250, 0.65), 0 0 20px rgba(167, 139, 250, 0.4)',
            transform: `scale(${buttonPulse})`,
            transformOrigin: 'center center',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Brilho Shimmer que passa pelo botão */}
          <div
            style={{
              position: 'absolute',
              top: -50,
              bottom: -50,
              width: 90,
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.7) 50%, transparent 100%)',
              transform: `translateX(${shimmerOffset * 3}px) rotate(25deg)`,
              pointerEvents: 'none',
            }}
          />

          <svg
            width="46"
            height="46"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#121216"
            strokeWidth="2.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <span
            style={{
              fontFamily,
              fontSize: 52,
              fontWeight: 900,
              color: '#121216',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            CHAME NO DIRECT
          </span>
        </div>
      </div>

      {/* 4. Arroba Oficial (@vitrineia_inovare) (y = 1200 a 1300) */}
      <div
        style={{
          position: 'absolute',
          top: 1200,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.max(0, arrobaSpring),
          transform: `translateY(${(1 - Math.max(0, arrobaSpring)) * 20}px)`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 16,
            padding: '16px 36px',
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
            border: '2px solid rgba(255, 255, 255, 0.22)',
            borderRadius: 24,
            backdropFilter: 'blur(10px)',
          }}
        >
          <svg
            width="38"
            height="38"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#C4B5FD"
            strokeWidth="2.5"
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
              fontSize: 40,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
            }}
          >
            @vitrineia_inovare
          </span>
        </div>
      </div>

      {/* 5. Nota Secundária de Fechamento */}
      <div
        style={{
          position: 'absolute',
          top: 1370,
          left: 60,
          right: 60,
          textAlign: 'center',
        }}
      >
        <span
          style={{
            fontFamily,
            fontSize: 32,
            fontWeight: 600,
            color: '#94A3B8',
          }}
        >
          Pare de perder vendas por demora no atendimento
        </span>
      </div>
    </div>
  );
};
