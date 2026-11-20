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

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera no fundo
  const bgScale = interpolate(frame, [0, 204], [1.02, 1.14], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 204], [0, 25], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada e saída da cena
  const sceneOpacity = interpolate(frame, [0, 8, 196, 204], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Header springs
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  const titleSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  // Card 1: "Hoje o bot atende na hora" (frame 15 = 20.7s)
  const card1Spring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 13, mass: 0.7, stiffness: 120},
  });

  // Card 2: "e eu deixo de perder cliente" (frame 68 = 22.5s)
  const card2Spring = spring({
    frame: frame - 68,
    fps,
    config: {damping: 13, mass: 0.7, stiffness: 120},
  });

  // Card 3: "que só queria uma resposta rápida" (frame 114 = 24.0s)
  const card3Spring = spring({
    frame: frame - 114,
    fps,
    config: {damping: 13, mass: 0.7, stiffness: 120},
  });

  // Efeito de brilho / shimmer contínuo
  const shimmerPos = (frame % 45) / 45;

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
      {/* Imagem de Fundo com Movimento Contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateX(${bgTranslateX}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_3.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Camada de escurecimento para alto contraste */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(11, 13, 19, 0.94) 0%, rgba(15, 23, 42, 0.85) 50%, rgba(11, 13, 19, 0.96) 100%)',
          }}
        />
      </div>

      {/* Topo: Tarja com Corte Diagonal (Aprovado 7f4d41fc / 79c80bb8) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.max(0, badgeSpring),
          transform: `translateY(${(1 - Math.max(0, badgeSpring)) * -20}px)`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 28px',
            backgroundColor: 'rgba(17, 24, 39, 0.90)',
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
            O RESULTADO NA PRÁTICA
          </span>
        </div>
      </div>

      {/* Título da Cena */}
      <div
        style={{
          position: 'absolute',
          top: 250,
          left: 60,
          right: 60,
          textAlign: 'center',
          opacity: Math.max(0, titleSpring),
          transform: `translateY(${(1 - Math.max(0, titleSpring)) * 15}px)`,
        }}
      >
        <span
          style={{
            fontFamily,
            fontSize: 46,
            fontWeight: 900,
            color: '#FFFFFF',
            letterSpacing: 1.5,
            textTransform: 'uppercase',
            textShadow: '0 4px 16px rgba(0,0,0,0.8)',
          }}
        >
          COMO FICA SUA LOJA
        </span>
      </div>

      {/* 3 Cards de Resultados Enfileirados (y = 350 a 940) */}
      <div
        style={{
          position: 'absolute',
          top: 345,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 24,
        }}
      >
        {/* Card 1: Resposta Imediata (entra no frame 15) */}
        <div
          style={{
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            border: '2px solid #34D399',
            borderRadius: 24,
            padding: '22px 28px',
            display: 'flex',
            alignItems: 'center',
            gap: 24,
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(12px)',
            opacity: Math.max(0, card1Spring),
            transform: `translateX(${(1 - Math.max(0, card1Spring)) * -40}px) scale(${Math.max(0.85, card1Spring)})`,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Ícone */}
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: 20,
              backgroundColor: 'rgba(52, 211, 153, 0.18)',
              border: '2px solid #34D399',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#34D399"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          {/* Conteúdo */}
          <div style={{flex: 1}}>
            <div
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#34D399',
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              ATENDE NA HORA
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 600,
                color: '#F1F5F9',
                marginTop: 4,
              }}
            >
              Bot com todo o conhecimento da loja
            </div>
          </div>
        </div>

        {/* Card 2: Retenção de Clientes (entra no frame 68) */}
        <div
          style={{
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            border: '2px solid #A78BFA',
            borderRadius: 24,
            padding: '22px 28px',
            display: 'flex',
            alignItems: 'center',
            gap: 24,
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(12px)',
            opacity: Math.max(0, card2Spring),
            transform: `translateX(${(1 - Math.max(0, card2Spring)) * 40}px) scale(${Math.max(0.85, card2Spring)})`,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Ícone */}
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: 20,
              backgroundColor: 'rgba(167, 139, 250, 0.18)',
              border: '2px solid #A78BFA',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg
              width="38"
              height="38"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#A78BFA"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <polyline points="16 11 18 13 22 9" />
            </svg>
          </div>
          {/* Conteúdo */}
          <div style={{flex: 1}}>
            <div
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#C4B5FD',
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              RETÉM O CLIENTE
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 600,
                color: '#F1F5F9',
                marginTop: 4,
              }}
            >
              Deixa de perder cliente para o concorrente
            </div>
          </div>
        </div>

        {/* Card 3: Resposta Rápida (entra no frame 114) */}
        <div
          style={{
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            border: '2px solid #60A5FA',
            borderRadius: 24,
            padding: '22px 28px',
            display: 'flex',
            alignItems: 'center',
            gap: 24,
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(12px)',
            opacity: Math.max(0, card3Spring),
            transform: `scale(${Math.max(0.85, card3Spring)}) translateY(${(1 - Math.max(0, card3Spring)) * 25}px)`,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Ícone */}
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: 20,
              backgroundColor: 'rgba(96, 165, 250, 0.18)',
              border: '2px solid #60A5FA',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg
              width="38"
              height="38"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#60A5FA"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
          </div>
          {/* Conteúdo */}
          <div style={{flex: 1}}>
            <div
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#93C5FD',
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              ATENDE, RECOMENDA E VENDE
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 600,
                color: '#F1F5F9',
                marginTop: 4,
              }}
            >
              Resposta rápida que fecha o pedido
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
