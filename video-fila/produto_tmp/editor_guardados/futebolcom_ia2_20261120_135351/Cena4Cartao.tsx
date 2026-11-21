import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena4Cartao: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo com zoom lento ativo (1.12 -> 1.25)
  const bgScale = interpolate(frame, [0, 116], [1.12, 1.25], {
    extrapolateRight: 'clamp',
  });

  // Slow zoom contínuo (push-in suave de 100% para 105%) em todo o cartão
  const cardPushIn = interpolate(frame, [0, 116], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Animação sequencial escalonada (stagger) na entrada dos blocos
  const brandSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, mass: 0.8},
  });
  const sloganSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 14, mass: 0.8},
  });
  const tag1Spring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 13, mass: 0.7},
  });
  const tag2Spring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 13, mass: 0.7},
  });
  const btnSpring = spring({
    frame: frame - 26,
    fps,
    config: {damping: 13, mass: 0.7},
  });
  const handleSpring = spring({
    frame: frame - 32,
    fps,
    config: {damping: 13, mass: 0.7},
  });

  // Microflutuação contínua suave
  const cardFloat = Math.sin(frame * 0.14) * 4;

  // Animação contínua de respiração/pulso no botão de CTA
  const buttonPulse = 1.02 + 0.025 * Math.sin(frame * 0.22);

  // Efeito shimmer sweep contínuo deslizando diagonalmente pela superfície do botão
  const shimmerOffset = ((frame * 28) % 1600) - 500;

  // Microinterações na seta do CTA e badges
  const arrowX = Math.sin(frame * 0.25) * 8;
  const badgeFloat = Math.sin(frame * 0.12) * 3;

  // Pulso do brilho de fundo
  const glowOpacity = 0.2 + 0.08 * Math.sin(frame * 0.15);

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0F0205',
      }}
    >
      {/* Ambiente autêntico do balcão/loja ao fundo com desfoque elegante (blur 18px) e zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale})`,
          transformOrigin: '50% 40%',
          filter: 'blur(18px)',
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
      </div>

      {/* Véu escuro da marca para contraste sofisticado corporativo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 50%, rgba(20, 3, 7, 0.86) 0%, rgba(10, 1, 3, 0.96) 85%)',
        }}
      />

      {/* Brilho institucional dinâmico pulsante ao fundo */}
      <div
        style={{
          position: 'absolute',
          top: 420,
          left: 180,
          width: 720,
          height: 720,
          borderRadius: '50%',
          background: `radial-gradient(circle, rgba(225, 29, 72, ${glowOpacity}) 0%, rgba(0, 0, 0, 0) 70%)`,
          pointerEvents: 'none',
        }}
      />

      {/* Container Central do Cartão com Slow Zoom Contínuo (push-in 100% para 105%) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          textAlign: 'center',
          padding: '0 60px',
          transform: `scale(${cardPushIn}) translateY(${cardFloat}px)`,
          zIndex: 50,
        }}
      >
        {/* Bloco 1: Marca com Logotipo Minimalista Vetorial e Proposta de Valor */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          {/* Logotipo Minimalista / Vetorial da Cardápio Digital (Entrada Stagger f=2) */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              marginBottom: 18,
              transform: `scale(${Math.max(0, brandSpring)})`,
              opacity: interpolate(brandSpring, [0, 0.2, 1], [0, 0.8, 1]),
            }}
          >
            <div
              style={{
                width: 76,
                height: 76,
                borderRadius: 22,
                backgroundColor: '#E11D48',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 8px 24px rgba(225, 29, 72, 0.45)',
              }}
            >
              <svg
                width="42"
                height="42"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#FFFFFF"
                strokeWidth="2.4"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="5" y="2" width="14" height="20" rx="3" />
                <line x1="9" y1="7" x2="15" y2="7" />
                <line x1="9" y1="12" x2="15" y2="12" />
                <line x1="9" y1="17" x2="13" y2="17" />
              </svg>
            </div>
            <h1
              style={{
                margin: 0,
                fontFamily,
                fontSize: 66,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: -1,
                textShadow: '0 4px 18px rgba(0, 0, 0, 0.85)',
              }}
            >
              Cardápio Digital
            </h1>
          </div>

          {/* Proposta de Valor Factual Autorizada (Entrada Stagger f=8) */}
          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 700,
              color: '#F1F5F9',
              lineHeight: 1.35,
              maxWidth: 880,
              textShadow: '0 2px 10px rgba(0,0,0,0.7)',
              textWrap: 'balance',
              transform: `scale(${Math.max(0, sloganSpring)})`,
              opacity: interpolate(sloganSpring, [0, 0.2, 1], [0, 0.8, 1]),
            }}
          >
            Cardápio com fotos no WhatsApp e atendimento inteligente com IA
          </div>
        </div>

        {/* Bloco 2: Badges com Animação Sequencial Stagger (f=14 e f=20) */}
        <div
          style={{
            display: 'flex',
            gap: 16,
            marginTop: 32,
            marginBottom: 44,
            flexWrap: 'wrap',
            justifyContent: 'center',
            transform: `translateY(${badgeFloat}px)`,
          }}
        >
          <div
            style={{
              padding: '12px 26px',
              borderRadius: 20,
              background: 'rgba(225, 29, 72, 0.18)',
              border: '1.5px solid rgba(225, 29, 72, 0.55)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              boxShadow: '0 8px 20px rgba(0, 0, 0, 0.5)',
              transform: `scale(${Math.max(0, tag1Spring)})`,
              opacity: interpolate(tag1Spring, [0, 0.2, 1], [0, 0.8, 1]),
            }}
          >
            <span style={{fontSize: 32}}>📸</span>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
              }}
            >
              Fotos no Celular
            </span>
          </div>

          <div
            style={{
              padding: '12px 26px',
              borderRadius: 20,
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1.5px solid rgba(255, 255, 255, 0.22)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              boxShadow: '0 8px 20px rgba(0, 0, 0, 0.5)',
              transform: `scale(${Math.max(0, tag2Spring)})`,
              opacity: interpolate(tag2Spring, [0, 0.2, 1], [0, 0.8, 1]),
            }}
          >
            <span style={{fontSize: 32}}>🤖</span>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
              }}
            >
              Atendimento com IA
            </span>
          </div>
        </div>

        {/* Bloco 3: Botão de CTA Institucional com Pulso Energético e Stagger (f=26) */}
        <div
          style={{
            transform: `scale(${Math.max(0, btnSpring) * buttonPulse})`,
            opacity: interpolate(btnSpring, [0, 0.2, 1], [0, 0.8, 1]),
            width: '100%',
            maxWidth: 880,
          }}
        >
          <div
            style={{
              position: 'relative',
              width: '100%',
              height: 136,
              borderRadius: 36,
              background: 'linear-gradient(135deg, #E11D48 0%, #BE123C 100%)',
              border: '2px solid rgba(255, 255, 255, 0.35)',
              boxShadow: '0 16px 40px rgba(225, 29, 72, 0.45)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 18,
              overflow: 'hidden',
            }}
          >
            {/* Shimmer sweep contínuo deslizando diagonalmente pela superfície do botão */}
            <div
              style={{
                position: 'absolute',
                top: -40,
                bottom: -40,
                width: 140,
                background:
                  'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.45) 50%, rgba(255,255,255,0) 100%)',
                transform: `translateX(${shimmerOffset}px) rotate(25deg)`,
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
                textShadow: '0 2px 8px rgba(0,0,0,0.5)',
              }}
            >
              Chame no Direct
            </span>
            <span
              style={{
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: '#FFFFFF',
                transform: `translateX(${arrowX}px)`,
                display: 'inline-block',
              }}
            >
              ➔
            </span>
          </div>
        </div>

        {/* Bloco 4: Identificador Obrigatório (@cardapiodigital) com Stagger (f=32) */}
        <div
          style={{
            marginTop: 36,
            transform: `scale(${Math.max(0, handleSpring)})`,
            opacity: interpolate(handleSpring, [0, 0.2, 1], [0, 0.8, 1]),
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              padding: '14px 34px',
              borderRadius: 24,
              background: 'rgba(20, 4, 8, 0.94)',
              border: '1.5px solid rgba(255, 255, 255, 0.22)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.8)',
            }}
          >
            <svg
              width="36"
              height="36"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#E11D48"
              strokeWidth="2.3"
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
                fontSize: 42,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 0.5,
              }}
            >
              @cardapiodigital
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
