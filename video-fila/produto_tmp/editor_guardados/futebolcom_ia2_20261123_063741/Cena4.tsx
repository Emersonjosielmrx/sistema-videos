import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {BRIEFING} from './constants';

type Props = {
  fontFamily: string;
};

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera e zoom (>= 4%)
  const bgScale = interpolate(frame, [0, 116], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Flutuação contínua e brilho vivo
  const floatY = Math.sin(frame / 10) * 5;

  // Pulso contínuo do botão CTA (ciclo de ~36 frames = 1.2s, scale 1.00 a 1.07)
  const ctaPulse = 1.0 + Math.sin((frame / 36) * Math.PI * 2) * 0.038;

  // Shimmer do botão CTA (varredura contínua de luz a cada 45 frames)
  const shimmerProgress = (frame % 45) / 45;

  // Entradas suaves escalonadas
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const titleSpring = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: {damping: 12, stiffness: 110},
  });

  const descSpring = spring({
    frame: Math.max(0, frame - 8),
    fps,
    config: {damping: 13, stiffness: 100},
  });

  const buttonSpring = spring({
    frame: Math.max(0, frame - 12),
    fps,
    config: {damping: 11, stiffness: 120},
  });

  const arrobaSpring = spring({
    frame: Math.max(0, frame - 16),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        background: BRIEFING.cores.fundo_escuro,
        fontFamily,
      }}
    >
      {/* Fundo com foto e gradiente com zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <img
          src={staticFile('img_4.jpg')}
          alt="Fundo"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: 0.35,
            filter: 'blur(16px) brightness(0.6)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(circle at 50% 45%, rgba(225, 29, 72, 0.4) 0%, rgba(49, 6, 15, 0.98) 75%)`,
          }}
        />
      </div>

      {/* Partículas e brilho volumétrico */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'radial-gradient(rgba(250, 204, 21, 0.12) 1.5px, transparent 1.5px)',
          backgroundSize: '48px 48px',
          opacity: 0.6,
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo Centralizado dentro da Safe Zone (y: 150 a 1580) */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 30,
        }}
      >
        {/* Ícone de Marca Flutuante */}
        <div
          style={{
            transform: `scale(${logoSpring}) translateY(${floatY}px)`,
            opacity: logoSpring,
            width: 120,
            height: 120,
            borderRadius: 36,
            background: `linear-gradient(135deg, ${BRIEFING.cores.marca} 0%, #9F1239 100%)`,
            border: `3px solid ${BRIEFING.cores.apoio}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 64,
            boxShadow: `0 16px 40px rgba(225, 29, 72, 0.6), 0 0 30px ${BRIEFING.cores.apoio}55`,
            marginBottom: 28,
          }}
        >
          📱
        </div>

        {/* Nome da Marca */}
        <div
          style={{
            transform: `scale(${titleSpring})`,
            opacity: titleSpring,
            marginBottom: 20,
          }}
        >
          <h1
            style={{
              margin: 0,
              fontSize: 64,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 2,
              textTransform: 'uppercase',
              textShadow: '0 6px 20px rgba(0, 0, 0, 0.8)',
            }}
          >
            {BRIEFING.marca}
          </h1>
        </div>

        {/* Proposta de Valor Permitida */}
        <div
          style={{
            transform: `scale(${descSpring})`,
            opacity: descSpring,
            maxWidth: 880,
            background: 'rgba(15, 23, 42, 0.94)',
            border: '2px solid rgba(255, 255, 255, 0.15)',
            padding: '22px 34px',
            borderRadius: 24,
            boxShadow: '0 16px 40px rgba(0, 0, 0, 0.75)',
            marginBottom: 36,
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 38,
              fontWeight: 700,
              color: '#F8FAFC',
              lineHeight: 1.35,
              textWrap: 'balance',
            }}
          >
            Cardápio digital para restaurante e lanchonete com pedido pelo
            WhatsApp e atendimento com IA.
          </p>
        </div>

        {/* Destaques Rápidos em Pílulas */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: 16,
            flexWrap: 'wrap',
            marginBottom: 50,
          }}
        >
          <div
            style={{
              padding: '12px 24px',
              borderRadius: 20,
              background: 'rgba(30, 41, 59, 0.94)',
              border: `2px solid ${BRIEFING.cores.marca}`,
              fontSize: 34,
              fontWeight: 700,
              color: '#FFFFFF',
              boxShadow: '0 8px 20px rgba(0,0,0,0.5)',
            }}
          >
            📸 Cardápio com Fotos
          </div>
          <div
            style={{
              padding: '12px 24px',
              borderRadius: 20,
              background: 'rgba(30, 41, 59, 0.94)',
              border: `2px solid ${BRIEFING.cores.apoio}`,
              fontSize: 34,
              fontWeight: 700,
              color: '#FFFFFF',
              boxShadow: '0 8px 20px rgba(0,0,0,0.5)',
            }}
          >
            🤖 IA Tira Dúvidas
          </div>
        </div>

        {/* BOTÃO DE CTA PULSANTE COM SHIMMER */}
        <div
          style={{
            transform: `scale(${buttonSpring * ctaPulse})`,
            opacity: buttonSpring,
            marginBottom: 44,
            position: 'relative',
          }}
        >
          <div
            style={{
              position: 'relative',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 18,
              padding: '24px 56px',
              borderRadius: 36,
              background: `linear-gradient(135deg, ${BRIEFING.cores.marca} 0%, #BE123C 100%)`,
              border: `3px solid ${BRIEFING.cores.apoio}`,
              boxShadow: `0 18px 50px rgba(225, 29, 72, 0.7), 0 0 35px rgba(250, 204, 21, 0.35)`,
              overflow: 'hidden',
            }}
          >
            {/* Shimmer sweep animado */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 120,
                left: `${shimmerProgress * 140 - 20}%`,
                background:
                  'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.4) 50%, transparent 100%)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            <span style={{fontSize: 44}}>👉</span>
            <span
              style={{
                fontSize: 46,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                textTransform: 'uppercase',
                textShadow: '0 3px 10px rgba(0,0,0,0.7)',
              }}
            >
              {BRIEFING.convite}
            </span>
          </div>
        </div>

        {/* Perfil Oficial (@marca) */}
        <div
          style={{
            transform: `scale(${arrobaSpring})`,
            opacity: arrobaSpring,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 14,
              padding: '14px 34px',
              borderRadius: 24,
              background: 'rgba(15, 23, 42, 0.94)',
              border: '2px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.7)',
            }}
          >
            <span style={{fontSize: 38}}>✉️</span>
            <span
              style={{
                fontSize: 42,
                fontWeight: 800,
                color: BRIEFING.cores.apoio,
                letterSpacing: 1,
              }}
            >
              {BRIEFING.arroba}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
