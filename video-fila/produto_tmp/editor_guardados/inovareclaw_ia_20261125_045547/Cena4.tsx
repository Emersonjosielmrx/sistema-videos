import React from 'react';
import {interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração: ~118 frames (3.94s)
  // Câmera dinâmica contínua: zoom e pan pronunciados no fundo
  const bgScale = interpolate(frame, [0, 118], [1.08, 1.25], {extrapolateRight: 'clamp'});
  const bgX = interpolate(frame, [0, 118], [-35, 35], {extrapolateRight: 'clamp'});
  const bgY = interpolate(frame, [0, 118], [0, -30], {extrapolateRight: 'clamp'});

  // Push-in contínuo em todo o cartão final (escala 1.00 para 1.05) para dinamismo contínuo
  const cardPushIn = interpolate(frame, [0, 118], [1.00, 1.05], {extrapolateRight: 'clamp'});

  // Pulso e Heartbeat contínuo do botão de CTA
  const pulseFactor = (Math.sin((frame / 32) * Math.PI * 2) + 1) / 2;
  const heartbeat = Math.sin(frame * 0.22) * 0.03;
  const btnScale = 1.0 + pulseFactor * 0.06 + heartbeat;

  // Efeito Shimmer / Brilho passando pelo botão
  const shimmerX = interpolate(frame % 36, [0, 36], [-250, 950]);

  // Feixe de luz / Aura dinâmica deslizando pela tela
  const orbX = interpolate(frame, [0, 118], [-100, 350]);
  const orbY = interpolate(frame, [0, 118], [250, 650]);

  // Flutuação suave do ícone
  const iconFloatY = Math.sin(frame * 0.15) * 10;

  // Entrada em mola dos elementos
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const contentSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#070A12',
      }}
    >
      {/* Imagem de fundo com zoom dinâmico */}
      <img
        src={staticFile('img_4.jpg')}
        alt="Fundo"
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          objectFit: 'cover',
          filter: 'blur(8px) brightness(0.45)',
          transform: `scale(${bgScale}) translate(${bgX}px, ${bgY}px)`,
        }}
      />

      {/* Véu escuro da marca (#111827) com gradiente dinâmico */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `linear-gradient(${125 + frame * 0.5}deg, rgba(124, 58, 237, 0.28) 0%, rgba(17, 24, 39, 0.85) 45%, rgba(7, 10, 18, 0.96) 100%)`,
        }}
      />

      {/* Luz ambiente volumétrica roxa em deslocamento constante */}
      <div
        style={{
          position: 'absolute',
          top: orbY,
          left: orbX,
          width: 850,
          height: 850,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(168, 85, 247, 0.35) 0%, transparent 65%)',
          filter: 'blur(60px)',
          pointerEvents: 'none',
        }}
      />

      {/* Container Harmoniosamente Distribuído na Safe Zone (y=310 a y=1400) com push-in lento */}
      <div
        style={{
          position: 'absolute',
          top: 310,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          transform: `scale(${cardPushIn})`,
          transformOrigin: 'center center',
        }}
      >
        {/* Ícone Tecnológico da Garra/IA com flutuação contínua */}
        <div
          style={{
            transform: `scale(${logoSpring}) translateY(${iconFloatY}px)`,
            marginBottom: 32,
            position: 'relative',
          }}
        >
          {/* Anel giratório */}
          <div
            style={{
              position: 'absolute',
              inset: -14,
              borderRadius: '50%',
              border: '2px dashed rgba(168, 85, 247, 0.6)',
              transform: `rotate(${frame * 2.5}deg)`,
            }}
          />
          <div
            style={{
              width: 116,
              height: 116,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #7C3AED 0%, #4C1D95 100%)',
              border: '3px solid #A855F7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 10px 32px rgba(124, 58, 237, 0.75)',
            }}
          >
            <svg width="62" height="62" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h1v2a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-2h1a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z" />
              <circle cx="9" cy="13" r="1.5" fill="#FFFFFF" />
              <circle cx="15" cy="13" r="1.5" fill="#FFFFFF" />
            </svg>
          </div>
        </div>

        {/* Marca Grande em Branco (Fundo escuro) */}
        <div
          style={{
            transform: `scale(${contentSpring})`,
            marginBottom: 20,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 72,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '0.03em',
              textTransform: 'uppercase',
              textShadow: '0 8px 24px rgba(124, 58, 237, 0.55)',
            }}
          >
            INOVARE CLAW
          </span>
        </div>

        {/* 1 Frase do que o produto faz (fiel aos fatos) */}
        <div
          style={{
            maxWidth: 820,
            marginBottom: 52,
            transform: `scale(${contentSpring})`,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 40,
              fontWeight: 700,
              color: '#F1F5F9',
              lineHeight: 1.3,
              textWrap: 'balance',
            }}
          >
            Seu agente de IA que trabalha sozinho
          </span>
        </div>

        {/* Botão de CTA com pulso heartbeat contínuo e brilho metálico */}
        <div
          style={{
            width: 860,
            transform: `scale(${btnScale})`,
            transformOrigin: 'center center',
            marginBottom: 44,
          }}
        >
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              background: 'linear-gradient(135deg, #7C3AED 0%, #9333EA 50%, #6D28D9 100%)',
              border: '2.5px solid rgba(255, 255, 255, 0.4)',
              borderRadius: 32,
              padding: '24px 0',
              boxShadow: '0 16px 45px rgba(124, 58, 237, 0.75), 0 0 25px rgba(168, 85, 247, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
            }}
          >
            {/* Shimmer / Brilho passando */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shimmerX,
                width: 120,
                background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.45), transparent)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontFamily,
                fontSize: 50,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                textShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
              }}
            >
              CHAME NO DIRECT
            </span>

            {/* Ícone de seta / direct */}
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </div>
        </div>

        {/* Perfil Oficial (@marca) Limpo — SEM ARROBA DUPLICADO */}
        <div
          style={{
            marginBottom: 34,
            transform: `scale(${contentSpring})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              background: 'rgba(15, 23, 42, 0.94)',
              border: '1.5px solid rgba(124, 58, 237, 0.65)',
              borderRadius: 999,
              padding: '12px 36px',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.65)',
            }}
          >
            {/* Ícone de avião/direct limpo */}
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#C084FC" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="3 11 22 2 13 21 11 13 3 11" />
            </svg>
            <span
              style={{
                fontFamily,
                fontSize: 40,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: '0.02em',
              }}
            >
              @inovareclaw.ia
            </span>
          </div>
        </div>

        {/* Texto de Apoio de Alto Contraste (#DDD6FE) */}
        <div
          style={{
            marginBottom: 32,
            transform: `scale(${contentSpring})`,
          }}
        >
          <div
            style={{
              background: 'rgba(124, 58, 237, 0.16)',
              border: '1px solid rgba(168, 85, 247, 0.35)',
              padding: '10px 28px',
              borderRadius: 999,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 700,
                color: '#DDD6FE',
                letterSpacing: '0.02em',
              }}
            >
              Tarefas de verdade executadas por IA
            </span>
          </div>
        </div>

        {/* Selo de Referência aos Fatos Permitidos (Hermes e OpenClaw) */}
        <div
          style={{
            transform: `scale(${contentSpring})`,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 600,
              color: '#CBD5E1',
              letterSpacing: '0.02em',
            }}
          >
            Automação no nível do Hermes e OpenClaw
          </span>
        </div>
      </div>
    </div>
  );
};
