import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background zoom contínuo
  const bgScale = interpolate(frame, [0, 119], [1.06, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Animação de entrada dos blocos
  const logoSpring = spring({
    frame: Math.max(0, frame - 3),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  const valueSpring = spring({
    frame: Math.max(0, frame - 10),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  const ctaSpring = spring({
    frame: Math.max(0, frame - 16),
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Pulso ativo contínuo no botão CTA até o último frame (scale 1.00 a 1.06)
  const ctaPulse = 1.025 + Math.sin(frame / 5) * 0.035;

  // Efeito shimmer de luz passando pelo botão
  const shimmerPos = ((frame * 12) % 600) - 200;

  // Flutuação sutil da marca
  const logoFloat = Math.sin(frame / 14) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
      }}
    >
      {/* Background com foto desfocada e zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(22px)',
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

      {/* Véu escuro da marca (gradiente slate profundo) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 35%, rgba(2, 132, 199, 0.38) 0%, rgba(15, 23, 42, 0.96) 65%, rgba(11, 15, 25, 0.99) 100%)',
        }}
      />

      {/* CONTEÚDO PRINCIPAL (y = 230 a 1500) */}
      <div
        style={{
          position: 'absolute',
          top: 230,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 20,
        }}
      >
        {/* LOGO & NOME DA MARCA */}
        <div
          style={{
            transform: `translateY(${logoFloat}px) scale(${logoSpring})`,
            opacity: logoSpring,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            marginBottom: 24,
          }}
        >
          {/* Ícone de CRM & IA */}
          <div
            style={{
              width: 105,
              height: 105,
              borderRadius: 28,
              background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)',
              border: '2px solid rgba(56, 189, 248, 0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow:
                '0 16px 40px rgba(2, 132, 199, 0.6), 0 0 35px rgba(56, 189, 248, 0.5)',
              marginBottom: 18,
            }}
          >
            <span style={{fontSize: 52}}>⚡</span>
          </div>

          <h1
            style={{
              fontFamily,
              fontSize: 72,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
              margin: 0,
              textShadow: '0 4px 24px rgba(0,0,0,0.95)',
            }}
          >
            INOVARE CRM
          </h1>

          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: '#38BDF8',
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              marginTop: 6,
            }}
          >
            CRM Chatwoot IA
          </div>
        </div>

        {/* PROPOSTA DE VALOR FACTUAL */}
        <div
          style={{
            transform: `translateY(${(1 - valueSpring) * 25}px) scale(${valueSpring})`,
            opacity: valueSpring,
            maxWidth: 880,
            marginBottom: 38,
          }}
        >
          <p
            style={{
              fontFamily,
              fontSize: 36,
              fontWeight: 600,
              color: '#F1F5F9',
              lineHeight: 1.35,
              margin: '0 0 24px 0',
              textWrap: 'balance',
              textShadow: '0 2px 10px rgba(0,0,0,0.8)',
            }}
          >
            Atendimento, tickets e histórico de cada cliente em um só lugar.
          </p>

          {/* Chips de Destaque Factual */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
              alignItems: 'center',
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 12,
                background: 'rgba(15, 23, 42, 0.85)',
                backdropFilter: 'blur(16px)',
                border: '1.5px solid rgba(56, 189, 248, 0.45)',
                padding: '10px 26px',
                borderRadius: 999,
                boxShadow: '0 8px 20px rgba(0,0,0,0.5)',
              }}
            >
              <span style={{color: '#38BDF8', fontSize: 32}}>✓</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#FFFFFF',
                }}
              >
                CRM personalizado com IA
              </span>
            </div>

            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 12,
                background: 'rgba(15, 23, 42, 0.85)',
                backdropFilter: 'blur(16px)',
                border: '1.5px solid rgba(56, 189, 248, 0.45)',
                padding: '10px 26px',
                borderRadius: 999,
                boxShadow: '0 8px 20px rgba(0,0,0,0.5)',
              }}
            >
              <span style={{color: '#38BDF8', fontSize: 32}}>✓</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#FFFFFF',
                }}
              >
                Integração completa CRM + Tickets
              </span>
            </div>
          </div>
        </div>

        {/* BOTÃO CTA PULSANTE ATIVO COM SHIMMER */}
        <div
          style={{
            transform: `scale(${ctaSpring * ctaPulse})`,
            opacity: ctaSpring,
            width: 760,
            position: 'relative',
            marginBottom: 38,
          }}
        >
          <div
            style={{
              background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)',
              borderRadius: 32,
              padding: '28px 36px',
              border: '2px solid rgba(255, 255, 255, 0.35)',
              boxShadow:
                '0 18px 45px rgba(2, 132, 199, 0.65), 0 0 35px rgba(56, 189, 248, 0.45)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 18,
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Shimmer light pass */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 140,
                transform: `translateX(${shimmerPos}px) skewX(-25deg)`,
                background:
                  'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.4) 50%, transparent 100%)',
                pointerEvents: 'none',
              }}
            />

            <span style={{fontSize: 44}}>💬</span>
            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                textShadow: '0 2px 10px rgba(0,0,0,0.5)',
              }}
            >
              CHAME NO DIRECT
            </span>
          </div>
        </div>

        {/* ARROBA OFICIAL (@inovarecrm) VISÍVEL DESDE O FRAME 0 */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            borderRadius: 999,
            background: 'rgba(15, 23, 42, 0.92)',
            border: '1.5px solid rgba(56, 189, 248, 0.4)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.7)',
          }}
        >
          <span style={{fontSize: 34}}>📸</span>
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.02em',
            }}
          >
            @inovarecrm
          </span>
          <span
            style={{
              width: 24,
              height: 24,
              borderRadius: '50%',
              background: '#38BDF8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 16,
              color: '#0F172A',
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
