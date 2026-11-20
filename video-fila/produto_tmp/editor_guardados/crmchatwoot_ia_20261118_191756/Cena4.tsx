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

  // Fundo com movimento contínuo
  const bgScale = interpolate(frame, [0, 120], [1.12, 1.24], {
    extrapolateRight: 'clamp',
  });

  // Entrada em mola do Logo/Marca desde o frame 0
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Entrada do Card de Proposta de Valor aos 0.2s (frame 6)
  const cardSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 90},
  });

  // Entrada do Botão CTA aos 0.35s (frame 10)
  const buttonSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Pulso contínuo obrigatório do botão (scale 1.0 a 1.08 até o frame final)
  const buttonPulse = 1.04 + Math.sin(frame / 6) * 0.04;

  // Feixe de brilho luminoso passando pelo botão de CTA
  const shineProgress = (frame % 45) / 45;
  const shineX = interpolate(shineProgress, [0, 1], [-200, 1000]);

  // Micro flutuação suave do logo e marca
  const logoFloat = Math.sin(frame / 12) * 5;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0A0F1D',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Fundo de foto com desfoque profundo e movimento contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale})`,
          filter: 'blur(30px)',
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

      {/* Véu escuro da marca em gradiente premium */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 30%, rgba(31, 147, 255, 0.22) 0%, rgba(10, 15, 29, 0.94) 70%)',
        }}
      />

      {/* Grade de Luz / Partículas sutis */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage:
            'radial-gradient(rgba(31, 147, 255, 0.15) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
          opacity: 0.4,
        }}
      />

      {/* Container de Elementos (Safe Zone: x=60..1020, y=150..1580) */}
      <div
        style={{
          position: 'absolute',
          top: 200,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 40,
        }}
      >
        {/* Marca / Logotipo Grande (y=200..380) */}
        <div
          style={{
            transform: `translateY(${logoFloat}px) scale(${Math.max(0, logoSpring)})`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
          }}
        >
          {/* Ícone Tecnológico com Anel de Glow */}
          <div
            style={{
              width: 100,
              height: 100,
              borderRadius: 30,
              background: 'linear-gradient(135deg, #1F93FF 0%, #0284C7 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 54,
              boxShadow: '0 12px 36px rgba(31, 147, 255, 0.55)',
              border: '2px solid rgba(255, 255, 255, 0.3)',
            }}
          >
            💬
          </div>

          <div
            style={{
              fontSize: 60,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: -1,
              textTransform: 'uppercase',
              textShadow: '0 6px 24px rgba(0, 0, 0, 0.9)',
              textAlign: 'center',
            }}
          >
            CRM Chatwoot IA
          </div>
        </div>

        {/* Card de Proposta de Valor (y=440..740) */}
        <div
          style={{
            transform: `scale(${Math.max(0, cardSpring)})`,
            maxWidth: 920,
            background: 'rgba(255, 255, 255, 0.05)',
            border: '2px solid rgba(31, 147, 255, 0.4)',
            borderRadius: 28,
            padding: '36px 42px',
            backdropFilter: 'blur(20px)',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            gap: 22,
          }}
        >
          <div
            style={{
              fontSize: 36,
              fontWeight: 700,
              color: '#F1F5F9',
              lineHeight: 1.45,
            }}
          >
            Um CRM feito para o seu negócio a partir do Chatwoot, com
            atendimento, tickets e histórico em um só lugar.
          </div>

          {/* Tags de pilares confirmados */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              flexWrap: 'wrap',
              gap: 12,
            }}
          >
            {['Atendimento', 'Tickets', 'Histórico Unificado'].map((tag, idx) => (
              <span
                key={idx}
                style={{
                  background: 'rgba(31, 147, 255, 0.18)',
                  border: '1.5px solid rgba(31, 147, 255, 0.5)',
                  color: '#93C5FD',
                  fontSize: 32,
                  fontWeight: 800,
                  padding: '6px 18px',
                  borderRadius: 14,
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Botão Oficial de CTA com Pulso Contínuo e Brilho (y=840..1020) */}
        <div
          style={{
            transform: `scale(${Math.max(0, buttonSpring) * buttonPulse})`,
            width: '100%',
            maxWidth: 880,
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              position: 'relative',
              width: '100%',
              height: 110,
              borderRadius: 30,
              background: 'linear-gradient(90deg, #1F93FF 0%, #2563EB 100%)',
              border: '2px solid rgba(255, 255, 255, 0.4)',
              boxShadow: '0 16px 44px rgba(31, 147, 255, 0.55)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 18,
              overflow: 'hidden',
            }}
          >
            {/* Feixe de brilho passando continuamente */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shineX,
                width: 120,
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent)',
                transform: 'skewX(-25deg)',
              }}
            />

            <span style={{fontSize: 44}}>🚀</span>
            <span
              style={{
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 1.2,
                textShadow: '0 2px 10px rgba(0, 0, 0, 0.4)',
              }}
            >
              Chame no Direct
            </span>
            <span style={{fontSize: 40}}>↗</span>
          </div>
        </div>

        {/* Perfil Oficial (@marca) visível desde o frame 0 (y=1080..1180) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: 'rgba(15, 23, 42, 0.75)',
            border: '1.5px solid rgba(255, 255, 255, 0.15)',
            padding: '10px 28px',
            borderRadius: 24,
            backdropFilter: 'blur(10px)',
          }}
        >
          <span
            style={{
              fontSize: 38,
              fontWeight: 800,
              color: '#CBD5E1',
              letterSpacing: 0.5,
            }}
          >
            @crmchatwoot.ia
          </span>
          <span
            style={{
              width: 28,
              height: 28,
              borderRadius: '50%',
              background: '#1F93FF',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 18,
              fontWeight: 900,
            }}
          >
            ✓
          </span>
        </div>
      </div>
    </div>
  );
};
