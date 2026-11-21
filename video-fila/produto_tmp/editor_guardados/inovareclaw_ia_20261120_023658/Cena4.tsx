import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type CenaProps = {
  fontFamily: string;
};

export const Cena4: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera: slow zoom-in contínuo vigoroso no fundo (1.00x para 1.20x)
  const bgScale = interpolate(frame, [0, 119], [1.0, 1.20], {
    extrapolateRight: 'clamp',
  });

  // Dinâmica de luz contínua de fundo que se desloca em tempo real
  const lightX = 50 + Math.sin(frame * 0.06) * 15;
  const lightY = 45 + Math.cos(frame * 0.06) * 12;

  // Micro push-in contínuo do conteúdo central para manter a energia ativa até o último frame (1.00x para 1.07x)
  const contentScale = interpolate(frame, [0, 119], [1.0, 1.07], {
    extrapolateRight: 'clamp',
  });

  // Entrada imediata dos elementos — @marca e elementos principais presentes desde 0.0s (Regra 9 APRENDIDO)
  const logoSpring = spring({frame, fps, config: {damping: 14, stiffness: 140}});
  const titleSpring = spring({frame: frame - 2, fps, config: {damping: 14, stiffness: 130}});
  const descSpring = spring({frame: frame - 4, fps, config: {damping: 14, stiffness: 120}});
  const ctaSpring = spring({frame: frame - 3, fps, config: {damping: 13, stiffness: 130}});
  const arrobaSpring = spring({frame, fps, config: {damping: 14, stiffness: 140}});

  // Pulso ativo rítmico contínuo (heartbeat de 1.0 para 1.045) no botão 'CHAME NO DIRECT'
  const buttonHeartbeat = 1 + Math.sin(frame * 0.22) * 0.045;
  const buttonGlow = 38 + Math.sin(frame * 0.22) * 22;

  // Pulso e brilho contínuo no ícone de raio central
  const iconPulse = 1 + Math.sin(frame * 0.16) * 0.06;
  const iconGlow = 40 + Math.sin(frame * 0.16) * 20;

  // Shimmer reflexo amplo que cruza o botão em loop contínuo a cada 30 frames
  const shimmerPos = interpolate(frame % 30, [0, 30], [-120, 320], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Rotação suave contínua e expansão do anel de luz tecnológico
  const ringRotate = frame * 2.5;
  const ringScale = 1 + Math.sin(frame * 0.14) * 0.06;

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D13'}}>
      {/* Imagem de Fundo com zoom contínuo e brilho equilibrado */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(0.62) contrast(1.15)',
          }}
        />
        {/* Véu escuro dinâmico da marca */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(circle at ${lightX}% ${lightY}%, rgba(124, 58, 237, 0.42) 0%, rgba(11, 13, 19, 0.92) 75%)`,
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo Central do Cartão Final com micro push-in contínuo */}
      <div
        style={{
          position: 'absolute',
          top: 240,
          bottom: 240,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 36,
          transform: `scale(${contentScale})`,
          transformOrigin: 'center center',
          zIndex: 20,
        }}
      >
        {/* Ícone Tecnológico com Anel Neon Giratório e Pulso Contínuo */}
        <div
          style={{
            position: 'relative',
            width: 130,
            height: 130,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transform: `scale(${logoSpring * iconPulse})`,
            opacity: logoSpring,
          }}
        >
          {/* Anel giratório */}
          <div
            style={{
              position: 'absolute',
              inset: -8,
              borderRadius: '50%',
              border: '2px dashed rgba(167, 139, 250, 0.7)',
              transform: `rotate(${ringRotate}deg)`,
            }}
          />
          {/* Base do ícone com brilho pulsante contínuo */}
          <div
            style={{
              width: 120,
              height: 120,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%)',
              boxShadow: `0 0 ${iconGlow}px rgba(124, 58, 237, 0.95)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 56,
              color: '#FFFFFF',
            }}
          >
            ⚡
          </div>
        </div>

        {/* Nome da Marca */}
        <div
          style={{
            transform: `translateY(${interpolate(titleSpring, [0, 1], [30, 0])}px)`,
            opacity: titleSpring,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 72,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 2,
              textAlign: 'center',
              textShadow: '0 10px 30px rgba(0, 0, 0, 0.9), 0 0 25px rgba(124, 58, 237, 0.6)',
            }}
          >
            INOVARE CLAW
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 700,
              color: '#CBD5E1',
              textAlign: 'center',
              maxWidth: 820,
              lineHeight: 1.25,
            }}
          >
            Seu agente de IA que trabalha sozinho
          </div>
        </div>

        {/* Botão de Chamada para Ação (CTA) — Pulsando Continuamente */}
        <div
          style={{
            transform: `scale(${ctaSpring * buttonPulse}) translateY(${interpolate(
              ctaSpring,
              [0, 1],
              [30, 0]
            )}px)`,
            opacity: ctaSpring,
            width: '100%',
            maxWidth: 820,
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              width: '100%',
              background: 'linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)',
              borderRadius: 28,
              padding: '24px 36px',
              border: '2px solid rgba(255, 255, 255, 0.3)',
              boxShadow: `0 20px 50px rgba(0, 0, 0, 0.8), 0 0 ${buttonGlow}px rgba(124, 58, 237, 0.85)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Shimmer de luz passando pelo botão */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: `${shimmerPos}%`,
                width: 80,
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            <span style={{fontSize: 44}}>✉️</span>
            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                textTransform: 'uppercase',
                textShadow: '0 4px 12px rgba(0,0,0,0.5)',
              }}
            >
              CHAME NO DIRECT
            </span>
          </div>
        </div>

        {/* Arroba Oficial */}
        <div
          style={{
            transform: `translateY(${interpolate(arrobaSpring, [0, 1], [30, 0])}px)`,
            opacity: arrobaSpring,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: 'rgba(15, 23, 42, 0.85)',
            padding: '14px 28px',
            borderRadius: 20,
            border: '1.5px solid rgba(255, 255, 255, 0.15)',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 36,
              fontWeight: 800,
              color: '#F8FAFC',
              letterSpacing: 1,
            }}
          >
            @inovareclaw.ia
          </span>
          <div
            style={{
              width: 26,
              height: 26,
              borderRadius: '50%',
              background: '#3B82F6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 16,
              color: '#FFFFFF',
              fontWeight: 900,
            }}
          >
            ✓
          </div>
        </div>

        {/* Selo de Garantia e Tecnologia — Alto contraste, fonte semibold e nítida em linha única perfeitamente centralizada */}
        <div
          style={{
            fontFamily,
            fontSize: 34,
            fontWeight: 700,
            color: '#F1F5F9',
            letterSpacing: 1.2,
            textTransform: 'uppercase',
            textAlign: 'center',
            whiteSpace: 'nowrap',
            width: '100%',
            opacity: descSpring,
            textShadow: '0 2px 10px rgba(0, 0, 0, 0.8)',
          }}
        >
          Agente Autônomo de Inteligência Artificial
        </div>
      </div>
    </AbsoluteFill>
  );
};
