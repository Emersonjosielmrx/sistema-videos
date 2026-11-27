import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {fontFamily} from './fontes';

const CORES = {
  marca: '#E11D48',
  apoio: '#FACC15',
  fundo_escuro: '#31060F',
  card_fundo: 'rgba(18, 4, 8, 0.94)',
  borda_card: 'rgba(255, 255, 255, 0.16)',
};

export const Cena4: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com zoom contínuo cinematográfico (1.00 -> 1.15)
  const bgScale = interpolate(frame, [0, 3.84 * fps], [1.0, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Slow zoom in sutil e constante em todo o conjunto do cartão (0.98 -> 1.04)
  const cardSlowZoom = interpolate(frame, [0, 3.84 * fps], [0.98, 1.04], {
    extrapolateRight: 'clamp',
  });

  // ENTRADA SINCRONIZADA DESDE O PRIMEIRO FRAME (Elimina o atraso do @ e do botão)
  const enterSpring = spring({frame, fps, config: {damping: 16, stiffness: 180}});
  const enterOpacity = interpolate(frame, [0, 4], [0.4, 1], {extrapolateRight: 'clamp'});

  // Pulso contínuo (breathing scale de 1.00 para 1.06) no botão CTA para evitar congelamento
  const buttonPulse = 1.02 + Math.sin(frame * 0.20) * 0.045;

  // Brilho deslizante contínuo (sweep shimmer) em loop a cada 1.1s correndo pelo botão
  const loopFrames = Math.round(1.1 * fps);
  const shimmerProgress = (frame % loopFrames) / loopFrames;
  const shimmerPos = interpolate(shimmerProgress, [0, 1], [-80, 180]);

  // Micro-movimento de flutuação no ícone da marca
  const logoFloat = Math.sin(frame * 0.16) * 6;

  // Pulso sutil no brilho da borda do botão
  const borderGlow = 25 + Math.sin(frame * 0.20) * 12;

  return (
    <AbsoluteFill style={{backgroundColor: CORES.fundo_escuro, overflow: 'hidden'}}>
      {/* Imagem de fundo com véu escuro e push-in contínuo */}
      <img
        src={staticFile('img_4.jpg')}
        alt="Fundo"
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${bgScale})`,
          opacity: 0.35,
        }}
      />

      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(circle at 50% 50%, rgba(225, 29, 72, 0.35) 0%, rgba(40, 5, 12, 0.96) 80%)`,
        }}
      />

      {/* Conteúdo do cartão final distribuído harmoniosamente na Safe Zone (y = 190 a 1540) com slow zoom in */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          bottom: 210,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 32,
          zIndex: 20,
          transform: `scale(${cardSlowZoom})`,
          transformOrigin: '50% 50%',
        }}
      >
        {/* Bloco 1: Marca Oficial com flutuação contínua */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 14,
            transform: `translateY(${logoFloat}px) scale(${enterSpring})`,
            opacity: enterOpacity,
          }}
        >
          <div
            style={{
              width: 104,
              height: 104,
              borderRadius: 30,
              backgroundColor: CORES.marca,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 12px 35px rgba(225, 29, 72, 0.6)',
              border: '2.5px solid rgba(255, 255, 255, 0.3)',
            }}
          >
            <svg
              width="58"
              height="58"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M18 8h1a4 4 0 0 1 0 8h-1" />
              <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" />
              <line x1="6" y1="1" x2="6" y2="4" />
              <line x1="10" y1="1" x2="10" y2="4" />
              <line x1="14" y1="1" x2="14" y2="4" />
            </svg>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 54,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '0.02em',
              textTransform: 'uppercase',
              textShadow: '0 4px 16px rgba(0,0,0,0.8)',
            }}
          >
            CARDÁPIO DIGITAL
          </div>
        </div>

        {/* Bloco 2: Badges de Destaques / Funcionalidades */}
        <div
          style={{
            display: 'flex',
            gap: 12,
            flexWrap: 'wrap',
            justifyContent: 'center',
            transform: `scale(${enterSpring})`,
            opacity: enterOpacity,
          }}
        >
          <div
            style={{
              padding: '10px 18px',
              backgroundColor: 'rgba(255, 255, 255, 0.12)',
              border: '1.5px solid rgba(255, 255, 255, 0.2)',
              borderRadius: 24,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span style={{fontSize: 24}}>📸</span>
            <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
              Fotos no Celular
            </span>
          </div>

          <div
            style={{
              padding: '10px 18px',
              backgroundColor: 'rgba(255, 255, 255, 0.12)',
              border: '1.5px solid rgba(255, 255, 255, 0.2)',
              borderRadius: 24,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span style={{fontSize: 24}}>💬</span>
            <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
              Pedido no WhatsApp
            </span>
          </div>

          <div
            style={{
              padding: '10px 18px',
              backgroundColor: 'rgba(255, 255, 255, 0.12)',
              border: '1.5px solid rgba(255, 255, 255, 0.2)',
              borderRadius: 24,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span style={{fontSize: 24}}>🤖</span>
            <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
              Atendimento com IA
            </span>
          </div>
        </div>

        {/* Bloco 3: Frase estritamente factual */}
        <div
          style={{
            maxWidth: 920,
            padding: '22px 32px',
            backgroundColor: CORES.card_fundo,
            border: `1.5px solid ${CORES.borda_card}`,
            borderRadius: 24,
            textAlign: 'center',
            boxShadow: '0 16px 40px rgba(0,0,0,0.85)',
            transform: `scale(${enterSpring})`,
            opacity: enterOpacity,
          }}
        >
          <p
            style={{
              margin: 0,
              fontFamily,
              fontSize: 34,
              fontWeight: 700,
              color: '#F1F5F9',
              lineHeight: 1.4,
            }}
          >
            Cardápio com fotos no celular e pedido direto pelo WhatsApp com IA respondendo dúvidas na hora.
          </p>
        </div>

        {/* Bloco 4: Botão de CTA com pulso contínuo e brilho deslizante em loop (sem congelar!) */}
        <div
          style={{
            position: 'relative',
            marginTop: 6,
            transform: `scale(${buttonPulse * enterSpring})`,
            opacity: enterOpacity,
          }}
        >
          <div
            style={{
              position: 'relative',
              padding: '24px 56px',
              borderRadius: 40,
              background: `linear-gradient(135deg, ${CORES.marca} 0%, #BE123C 100%)`,
              border: `2.5px solid ${CORES.apoio}`,
              boxShadow: `0 16px 45px rgba(225, 29, 72, 0.65), 0 0 ${borderGlow}px rgba(250, 204, 21, 0.4)`,
              display: 'flex',
              alignItems: 'center',
              gap: 18,
              overflow: 'hidden',
            }}
          >
            {/* Efeito sweep shimmer contínuo */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: `${shimmerPos}%`,
                width: '45%',
                background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            <span style={{fontSize: 40}}>👉</span>
            <span
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                textShadow: '0 2px 8px rgba(0,0,0,0.5)',
              }}
            >
              CHAME A GENTE NO DIRECT
            </span>
          </div>
        </div>

        {/* Bloco 5: @arroba oficial do nicho de alimentação e delivery exibido DESDE O PRIMEIRO FRAME */}
        <div
          style={{
            padding: '12px 32px',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            border: `1.5px solid ${CORES.apoio}`,
            borderRadius: 30,
            transform: `scale(${enterSpring})`,
            opacity: enterOpacity,
            backdropFilter: 'blur(10px)',
            boxShadow: '0 6px 20px rgba(0,0,0,0.5)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: CORES.apoio,
              letterSpacing: '0.04em',
            }}
          >
            @cardapiodigital.ia
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
