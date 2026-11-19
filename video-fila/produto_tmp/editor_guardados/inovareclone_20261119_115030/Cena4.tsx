import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES, fontFamily} from './constants';

export const Cena4: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (push-in 1.05 -> 1.18)
  const bgScale = interpolate(frame, [0, 120], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada
  const fadeIn = interpolate(frame, [0, 8], [0.85, 1], {
    extrapolateRight: 'clamp',
  });

  // Animação de entrada dos blocos
  const brandSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const cardSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const buttonSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Pulso contínuo ininterrupto do botão CTA (scale 1.00 a 1.08) até o último frame
  const buttonPulse = 1.04 + Math.sin(frame / 6) * 0.04;

  // Brilho metálico/sheen passando pelo botão em loop
  const sheenProgress = (frame % 45) / 45;
  const sheenX = interpolate(sheenProgress, [0, 1], [-200, 700]);

  // Flutuação suave dos elementos da marca
  const floatY = Math.sin(frame / 12) * 5;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: CORES.fundoEscuro,
        overflow: 'hidden',
        fontFamily,
        opacity: fadeIn,
      }}
    >
      {/* Fundo com Img e push-in contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
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
          }}
        />
        {/* Véu escuro da marca */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(139, 92, 246, 0.22) 0%, rgba(11, 13, 20, 0.88) 55%, rgba(11, 13, 20, 0.98) 100%)',
          }}
        />
      </div>

      {/* Luz ambiente giratória em volta da marca */}
      <div
        style={{
          position: 'absolute',
          top: 380,
          left: 540,
          width: 700,
          height: 700,
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(139, 92, 246, 0.2) 0%, rgba(139, 92, 246, 0) 70%)',
          transform: `translate(-50%, -50%) rotate(${frame * 0.6}deg)`,
          pointerEvents: 'none',
        }}
      />

      {/* CONTEÚDO DO CARTÃO FINAL — Safe zone y: 150 a 1580 */}
      <div
        style={{
          position: 'absolute',
          top: 240,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 36,
          zIndex: 20,
        }}
      >
        {/* BLOCO 1: Marca e Produto */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            opacity: Math.max(0, brandSpring),
            transform: `translateY(${(1 - brandSpring) * -30 + floatY}px)`,
          }}
        >
          {/* Logo Badge */}
          <div
            style={{
              width: 90,
              height: 90,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 35px rgba(139, 92, 246, 0.8)',
              border: '2px solid rgba(255, 255, 255, 0.3)',
            }}
          >
            <span style={{fontSize: 42, fontWeight: 900, color: '#FFFFFF'}}>
              IC
            </span>
          </div>

          {/* Nome da Marca */}
          <div
            style={{
              fontSize: 68,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
              textShadow: '0 4px 20px rgba(0, 0, 0, 0.9)',
            }}
          >
            Inovare Clone
          </div>

          {/* Selo do Produto */}
          <div
            style={{
              padding: '8px 24px',
              backgroundColor: 'rgba(139, 92, 246, 0.25)',
              border: '1.5px solid rgba(139, 92, 246, 0.6)',
              borderRadius: 20,
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: CORES.marcaClara,
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              Avatar IA
            </span>
          </div>
        </div>

        {/* BLOCO 2: Proposta de Valor e Benefícios */}
        <div
          style={{
            width: '100%',
            maxWidth: 920,
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            border: '2px solid rgba(139, 92, 246, 0.45)',
            borderRadius: 32,
            padding: '36px 32px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 24,
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.8)',
            opacity: Math.max(0, cardSpring),
            transform: `scale(${Math.max(0.85, cardSpring)})`,
          }}
        >
          {/* Frase de Valor */}
          <div
            style={{
              fontSize: 42,
              fontWeight: 800,
              color: '#FFFFFF',
              textAlign: 'center',
              lineHeight: 1.3,
              textWrap: 'balance',
            }}
          >
            Seu próprio avatar IA postando todo dia nas redes
          </div>

          {/* Pílulas de fatos permitidos */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: 'center',
              gap: 12,
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '10px 18px',
                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                border: '1px solid rgba(139, 92, 246, 0.4)',
                borderRadius: 16,
              }}
            >
              <span style={{fontSize: 32, fontWeight: 700, color: '#FFFFFF'}}>
                ✓ Posturas automáticas
              </span>
            </div>

            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '10px 18px',
                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                border: '1px solid rgba(139, 92, 246, 0.4)',
                borderRadius: 16,
              }}
            >
              <span style={{fontSize: 32, fontWeight: 700, color: '#FFFFFF'}}>
                ✓ Fala em português
              </span>
            </div>

            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '10px 18px',
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                border: '1px solid rgba(16, 185, 129, 0.5)',
                borderRadius: 16,
              }}
            >
              <span style={{fontSize: 32, fontWeight: 700, color: '#34D399'}}>
                ✓ 100% seu
              </span>
            </div>
          </div>
        </div>

        {/* BLOCO 3: Botão de Conversão (CTA) com pulso constante ininterrupto */}
        <div
          style={{
            opacity: Math.max(0, buttonSpring),
            transform: `scale(${Math.max(0.85, buttonSpring) * buttonPulse})`,
            width: '100%',
            maxWidth: 820,
            position: 'relative',
            overflow: 'hidden',
            borderRadius: 44,
            boxShadow:
              '0 18px 50px rgba(139, 92, 246, 0.75), 0 0 30px rgba(139, 92, 246, 0.4)',
          }}
        >
          <div
            style={{
              padding: '28px 40px',
              background: 'linear-gradient(90deg, #8B5CF6 0%, #6D28D9 100%)',
              border: '2px solid rgba(255, 255, 255, 0.35)',
              borderRadius: 44,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
            }}
          >
            <span
              style={{
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
                textShadow: '0 3px 10px rgba(0, 0, 0, 0.4)',
              }}
            >
              Chame no direct
            </span>
            <svg
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </div>

          {/* Efeito Sheen atravessando o botão */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: 120,
              left: sheenX,
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.45) 50%, transparent 100%)',
              transform: 'skewX(-25deg)',
              pointerEvents: 'none',
            }}
          />
        </div>

        {/* BLOCO 4: Perfil Oficial (@inovareclone) — Visível desde o frame 0! */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            backgroundColor: 'rgba(15, 23, 42, 0.88)',
            border: '1.5px solid rgba(255, 255, 255, 0.2)',
            borderRadius: 26,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
          }}
        >
          <svg
            width="34"
            height="34"
            viewBox="0 0 24 24"
            fill="none"
            stroke={CORES.marcaClara}
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
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1,
            }}
          >
            @inovareclone
          </span>
        </div>
      </div>
    </div>
  );
};
