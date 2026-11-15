import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

interface Cena4Props {
  fontFamily: string;
  destaque: string;
  marca: string;
  arroba: string;
}

export const Cena4: React.FC<Cena4Props> = ({
  fontFamily,
  destaque,
  marca,
  arroba,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (zoom in lento)
  const bgScale = interpolate(frame, [0, 119], [1.02, 1.12], {
    extrapolateRight: 'clamp',
  });

  // Entrada dos blocos com spring rápida para cartão final de 3.9s
  const brandSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const buttonSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const handleSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Pulso contínuo do botão CTA até o último frame (1.0 a 1.06)
  const buttonPulse = 1.03 + Math.sin(frame * 0.16) * 0.035;

  // Brilho metálico passando no botão
  const shineOffset = interpolate((frame * 2.5) % 90, [0, 90], [-150, 400]);

  // Flutuação sutil da marca
  const brandFloat = Math.sin(frame * 0.09) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* Imagem de Fundo Desfocada com Zoom */}
      <div
        style={{
          position: 'absolute',
          inset: -40,
          transform: `scale(${bgScale})`,
          filter: 'blur(24px) brightness(0.4) contrast(1.15)',
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

      {/* Véu escuro da marca com gradiente sofisticado */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 50%, rgba(245, 158, 11, 0.15) 0%, rgba(17, 24, 39, 0.88) 55%, rgba(10, 14, 23, 0.98) 100%)',
        }}
      />

      {/* Círculos concêntricos e grade decorativa viva */}
      <div
        style={{
          position: 'absolute',
          top: 880,
          left: 540,
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            width: 820,
            height: 820,
            borderRadius: '50%',
            border: '2px dashed rgba(245, 158, 11, 0.22)',
            transform: `rotate(${frame * 0.35}deg)`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: 70,
            left: 70,
            width: 680,
            height: 680,
            borderRadius: '50%',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            transform: `rotate(${-frame * 0.25}deg)`,
          }}
        />
      </div>

      {/* Bloco Superior: Marca e Proposta de Valor (y=300 a 700) */}
      <div
        style={{
          position: 'absolute',
          top: 310,
          left: 60,
          width: 960,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          transform: `scale(${brandSpring}) translateY(${brandFloat}px)`,
          opacity: brandSpring,
        }}
      >
        {/* Badge da Oferta */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 24px',
            borderRadius: 20,
            backgroundColor: 'rgba(245, 158, 11, 0.16)',
            border: `2px solid ${destaque}`,
            boxShadow: `0 0 16px rgba(245, 158, 11, 0.25)`,
            marginBottom: 20,
          }}
        >
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: destaque,
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            Estrutura Comercial Pronta
          </span>
        </div>

        {/* Nome da Marca */}
        <h1
          style={{
            margin: 0,
            fontSize: 58,
            fontWeight: 900,
            color: '#FFFFFF',
            lineHeight: 1.18,
            textWrap: 'balance',
            textShadow: '0 4px 18px rgba(0,0,0,0.85)',
          }}
        >
          {marca}
        </h1>

        {/* Frase Fato do Briefing */}
        <p
          style={{
            marginTop: 20,
            marginBottom: 0,
            fontSize: 36,
            fontWeight: 600,
            color: '#CBD5E1',
            lineHeight: 1.35,
            maxWidth: 860,
            textWrap: 'balance',
          }}
        >
          Página de vendas pronta e vídeo de demonstração para apresentar seu
          produto e transformar visita em cliente.
        </p>
      </div>

      {/* Bloco Central: Botão CTA com pulso contínuo (y=860 a 980) */}
      <div
        style={{
          position: 'absolute',
          top: 880,
          left: 60,
          width: 960,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${buttonSpring * buttonPulse})`,
          opacity: buttonSpring,
        }}
      >
        <div
          style={{
            position: 'relative',
            width: 820,
            height: 122,
            borderRadius: 30,
            backgroundColor: destaque,
            boxShadow: `0 18px 45px rgba(245, 158, 11, 0.5), 0 8px 24px rgba(0, 0, 0, 0.7)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 18,
            overflow: 'hidden',
          }}
        >
          {/* Efeito de brilho / sweep luminoso */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: 90,
              background:
                'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent)',
              transform: `translateX(${shineOffset}px) skewX(-25deg)`,
            }}
          />

          <span
            style={{
              fontSize: 48,
              fontWeight: 900,
              color: '#121216',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            Chame no Direct
          </span>

          <svg
            width="42"
            height="42"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#121216"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M5 12h14" />
            <path d="m12 5 7 7-7 7" />
          </svg>
        </div>
      </div>

      {/* Bloco Inferior: @Arroba Oficial (y=1080 a 1250) */}
      <div
        style={{
          position: 'absolute',
          top: 1080,
          left: 60,
          width: 960,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          transform: `scale(${handleSpring})`,
          opacity: handleSpring,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '16px 36px',
            borderRadius: 24,
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            border: `2px solid ${destaque}`,
            boxShadow: '0 8px 30px rgba(0,0,0,0.6)',
          }}
        >
          {/* Ícone Instagram/Direct */}
          <svg
            width="42"
            height="42"
            viewBox="0 0 24 24"
            fill="none"
            stroke={destaque}
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect width="20" height="20" x="2" y="2" rx="5" ry="5" />
            <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
            <line x1="17.5" x2="17.51" y1="6.5" y2="6.5" />
          </svg>

          <span
            style={{
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1,
            }}
          >
            {arroba}
          </span>
        </div>

        <span
          style={{
            fontSize: 34,
            fontWeight: 700,
            color: '#E2E8F0',
          }}
        >
          Envie sua mensagem agora
        </span>
      </div>
    </div>
  );
};
