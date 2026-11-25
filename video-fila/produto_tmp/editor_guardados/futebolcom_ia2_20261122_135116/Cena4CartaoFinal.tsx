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

export const Cena4CartaoFinal: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com zoom contínuo e pan vertical (garante variação visual contínua > 4% em toda a cena)
  const bgScale = interpolate(frame, [0, 116], [1.06, 1.22], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 116], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Microdinâmica constante de flutuação
  const floatY = Math.sin(frame / 10) * 5;

  // Botão com pulso contínuo (scale suave 1.0 a 1.045 em ciclo contínuo)
  const buttonPulse = 1 + Math.sin((frame * Math.PI * 2) / 32) * 0.04;

  // Brilho/shimmer de alta intensidade deslizando continuamente pelo botão (ciclo contínuo de 36 frames)
  const shineOffset = interpolate((frame % 36), [0, 26], [-140, 280], {
    extrapolateRight: 'clamp',
  });

  // Halo luminoso pulsante atrás do botão para engajamento contínuo
  const glowScale = 1 + Math.sin(frame / 7) * 0.08;
  const glowOpacity = 0.5 + Math.sin(frame / 7) * 0.25;

  // Entradas suaves em spring escalonadas (stagger)
  const logoSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const badgeSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const ctaSpring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 11, stiffness: 115},
  });

  const arrobaSpring = spring({
    frame: frame - 28,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#31060F',
      }}
    >
      {/* Imagem de fundo com desfoque, pan e zoom contínuo para evitar tela congelada */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(20px)',
          opacity: 0.45,
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

      {/* Véu escuro da marca (#31060F e #0B0D13) com gradiente radial rico */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 50%, rgba(225, 29, 72, 0.32) 0%, rgba(49, 6, 15, 0.94) 55%, rgba(11, 13, 19, 0.98) 100%)',
        }}
      />

      {/* Elementos distribuídos harmonicamente pela Safe Zone (y=230 a y=1520) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 230,
          bottom: 400,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          zIndex: 30,
        }}
      >
        {/* Bloco 1: Símbolo de Restaurante + Marca + Frase factual (Topo y=230 a y=600) */}
        {logoSpring > 0 && (
          <div
            style={{
              transform: `scale(${logoSpring}) translateY(${floatY}px)`,
              opacity: logoSpring,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
            }}
          >
            {/* Ícone Estilizado de Gastronomia / Cloche de Restaurante */}
            <div
              style={{
                width: 120,
                height: 120,
                borderRadius: 36,
                backgroundColor: '#E11D48',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow:
                  '0 18px 45px rgba(225, 29, 72, 0.65), 0 0 45px rgba(250, 204, 21, 0.35)',
                border: '3px solid rgba(255, 255, 255, 0.4)',
                marginBottom: 20,
              }}
            >
              <svg
                width="68"
                height="68"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#FFFFFF"
                strokeWidth="2.3"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                {/* Cloche / Prato de Restaurante com tampa */}
                <path d="M3 18h18" />
                <path d="M4 18a8 8 0 0 1 16 0" />
                <path d="M12 10V6" />
                <circle cx="12" cy="5" r="1.5" fill="#FFFFFF" />
                <line x1="2" y1="21" x2="22" y2="21" />
              </svg>
            </div>

            {/* Nome da Marca Grande em Branco com Alto Contraste */}
            <h1
              style={{
                fontFamily,
                fontSize: 68,
                fontWeight: 900,
                color: '#FFFFFF',
                margin: 0,
                lineHeight: 1.1,
                letterSpacing: 2,
                textAlign: 'center',
                textTransform: 'uppercase',
                textShadow: '0 8px 30px rgba(0, 0, 0, 0.9)',
              }}
            >
              CARDÁPIO DIGITAL
            </h1>

            {/* 1 Frase do que o produto faz (estritamente factual) */}
            <p
              style={{
                fontFamily,
                fontSize: 40,
                fontWeight: 700,
                color: '#F1F5F9',
                margin: '18px 0 0 0',
                lineHeight: 1.35,
                textAlign: 'center',
                maxWidth: 920,
                textWrap: 'balance',
              }}
            >
              Cardápio no celular com fotos, pedidos no WhatsApp e atendimento com IA
            </p>
          </div>
        )}

        {/* Bloco 2: Selo Factual de Nicho (Centro y=720 a y=800) */}
        {badgeSpring > 0 && (
          <div
            style={{
              transform: `scale(${badgeSpring})`,
              opacity: badgeSpring,
              backgroundColor: 'rgba(15, 23, 42, 0.92)',
              border: '2.5px solid rgba(250, 204, 21, 0.7)',
              padding: '16px 40px',
              borderRadius: 999,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              boxShadow: '0 10px 28px rgba(0, 0, 0, 0.7)',
            }}
          >
            <span style={{fontSize: 34}}>⚡</span>
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 800,
                color: '#FACC15',
                letterSpacing: 0.5,
              }}
            >
              Para Restaurantes e Lanchonetes
            </span>
          </div>
        )}

        {/* Bloco 3: BOTÃO CTA PULSANTE COM SHIMMER CONTÍNUO (y=980 a y=1180) */}
        {ctaSpring > 0 && (
          <div
            style={{
              transform: `scale(${ctaSpring * buttonPulse})`,
              position: 'relative',
              width: '100%',
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            {/* Halo de luz pulsante contínuo atrás do botão */}
            <div
              style={{
                position: 'absolute',
                inset: -20,
                borderRadius: 40,
                background:
                  'radial-gradient(circle, rgba(225, 29, 72, 0.6) 0%, transparent 70%)',
                transform: `scale(${glowScale})`,
                opacity: glowOpacity,
                pointerEvents: 'none',
              }}
            />

            <div
              style={{
                backgroundColor: '#E11D48',
                borderRadius: 32,
                padding: '34px 76px',
                boxShadow:
                  '0 24px 60px rgba(225, 29, 72, 0.85), 0 0 45px rgba(250, 204, 21, 0.5)',
                border: '3.5px solid #FFFFFF',
                display: 'flex',
                alignItems: 'center',
                gap: 22,
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              {/* Efeito Shine/Shimmer contínuo deslizando pelo botão */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  width: 90,
                  transform: `translateX(${shineOffset}%) skewX(-24deg)`,
                  background:
                    'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.65), transparent)',
                  pointerEvents: 'none',
                }}
              />

              <svg
                width="50"
                height="50"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#FFFFFF"
                strokeWidth="2.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>

              <span
                style={{
                  fontFamily,
                  fontSize: 54,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: 2,
                }}
              >
                CHAME NO DIRECT
              </span>
            </div>
          </div>
        )}

        {/* Bloco 4: @Perfil Oficial da Conta bem posicionado no terço inferior (y=1380 a y=1480) */}
        {arrobaSpring > 0 && (
          <div
            style={{
              transform: `scale(${arrobaSpring})`,
              opacity: arrobaSpring,
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: '2.5px solid #FACC15',
              padding: '18px 46px',
              borderRadius: 24,
              boxShadow: '0 12px 35px rgba(0, 0, 0, 0.85)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <svg
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FACC15"
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
                fontSize: 46,
                fontWeight: 900,
                color: '#FACC15',
                letterSpacing: 1.2,
              }}
            >
              @futebolcom.ia2
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
