import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena4Cartao: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (escala 1.06 a 1.20)
  const bgScale = interpolate(frame, [0, 120], [1.06, 1.2], {
    extrapolateRight: 'clamp',
  });

  // Entrada escalonada (stagger com spring/pop) de cada elemento:
  // 1. Ícone da marca (frame 0)
  const iconSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // 2. Título & Proposta (frame 8)
  const titleSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 3. Benefício 1: Atendimento 24h (frame 20)
  const b1Spring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 4. Benefício 2: Sem Duplo Agendamento (frame 32)
  const b2Spring = spring({
    frame: frame - 32,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 5. Benefício 3: A partir de R$ 199 (frame 44)
  const b3Spring = spring({
    frame: frame - 44,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 6. Botão CTA Chame no Direct (frame 56)
  const buttonSpring = spring({
    frame: frame - 56,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // 7. Arroba Oficial @sintetizerisada (frame 68)
  const handleSpring = spring({
    frame: frame - 68,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Pulsação contínua e suave do botão até o último frame
  const buttonPulse = 1 + Math.sin(frame / 6) * 0.035;
  const buttonFinalScale = Math.max(0, buttonSpring) * buttonPulse;

  // Efeito shimmer/sweep de luz cruzando todo o botão de CTA continuamente
  const shimmerPhase = frame % 42;
  const shimmerPos = interpolate(shimmerPhase, [0, 42], [-350, 850]);

  // Micro-flutuação sutil dos blocos
  const floatY = Math.sin(frame / 9) * 5;
  const glowPulse = 0.8 + Math.sin(frame / 10) * 0.2;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Fundo fotográfico desfocado com push-in */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
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
            filter: 'blur(10px)',
          }}
        />
        {/* Véu escuro da marca */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(31, 41, 55, 0.88) 0%, rgba(15, 23, 42, 0.98) 100%)',
          }}
        />
      </div>

      {/* Brilho radial de fundo em tom quente da marca com pulso */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: '50%',
          width: 700,
          height: 700,
          transform: 'translateX(-50%)',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255,169,77,0.22) 0%, transparent 70%)',
          opacity: glowPulse,
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo Distribuído Harmonicamente ao Longo da Área Útil (y=210 até y=1440) */}
      <div
        style={{
          position: 'absolute',
          top: 220,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
        }}
      >
        {/* Bloco 1: Ícone & Nome da Marca (y≈220 a 530) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            transform: `translateY(${floatY}px)`,
          }}
        >
          {/* Ícone de Agenda Inteligente com pop escalonado */}
          <div
            style={{
              width: 108,
              height: 108,
              borderRadius: 30,
              backgroundColor: '#FFA94D',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 14px 40px rgba(255, 169, 77, 0.55)',
              transform: `scale(${Math.max(0, iconSpring)})`,
              opacity: Math.max(0, iconSpring),
            }}
          >
            <svg
              width="60"
              height="60"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#1F2937"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
              <path d="m9 16 2 2 4-4" />
            </svg>
          </div>

          <div
            style={{
              transform: `scale(${Math.max(0, titleSpring)})`,
              opacity: Math.max(0, titleSpring),
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <h1
              style={{
                margin: 0,
                fontSize: 68,
                fontWeight: 900,
                letterSpacing: '0.04em',
                color: '#FFFFFF',
                textShadow: '0 4px 20px rgba(0,0,0,0.85)',
              }}
            >
              AGENDA <span style={{color: '#FFA94D'}}>IA</span>
            </h1>

            <p
              style={{
                margin: 0,
                fontSize: 38,
                fontWeight: 700,
                color: '#F3F4F6',
                maxWidth: 880,
                lineHeight: 1.35,
                textWrap: 'balance',
              }}
            >
              Agendamentos automáticos com inteligência artificial direto no WhatsApp
            </p>
          </div>
        </div>

        {/* Bloco 2: Os Três Marcadores de Benefícios Ampliados com Entrada Escalonada (y≈590 a 970) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 22,
            width: '100%',
            maxWidth: 900,
            marginTop: 48,
          }}
        >
          {/* Benefício 1: Atendimento 24h */}
          <div
            style={{
              padding: '22px 36px',
              borderRadius: 24,
              background: 'rgba(31, 41, 55, 0.94)',
              border: '1.5px solid rgba(255, 169, 77, 0.55)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              boxShadow: '0 8px 24px rgba(0,0,0,0.45)',
              transform: `scale(${Math.max(0, b1Spring)})`,
              opacity: Math.max(0, b1Spring),
            }}
          >
            <span style={{color: '#10B981', fontSize: 38, fontWeight: 900}}>✓</span>
            <span style={{fontSize: 38, fontWeight: 800, color: '#FFFFFF'}}>
              Atendimento <span style={{color: '#FFA94D'}}>24h</span>
            </span>
          </div>

          {/* Benefício 2: Sem Duplo Agendamento */}
          <div
            style={{
              padding: '22px 36px',
              borderRadius: 24,
              background: 'rgba(31, 41, 55, 0.94)',
              border: '1.5px solid rgba(255, 169, 77, 0.55)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              boxShadow: '0 8px 24px rgba(0,0,0,0.45)',
              transform: `scale(${Math.max(0, b2Spring)})`,
              opacity: Math.max(0, b2Spring),
            }}
          >
            <span style={{color: '#10B981', fontSize: 38, fontWeight: 900}}>✓</span>
            <span style={{fontSize: 38, fontWeight: 800, color: '#FFFFFF'}}>
              Sem <span style={{color: '#FFA94D'}}>Duplo Agendamento</span>
            </span>
          </div>

          {/* Benefício 3: A partir de R$ 199 */}
          <div
            style={{
              padding: '22px 36px',
              borderRadius: 24,
              background: 'rgba(31, 41, 55, 0.94)',
              border: '1.5px solid rgba(255, 169, 77, 0.55)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              boxShadow: '0 8px 24px rgba(0,0,0,0.45)',
              transform: `scale(${Math.max(0, b3Spring)})`,
              opacity: Math.max(0, b3Spring),
            }}
          >
            <span style={{color: '#10B981', fontSize: 38, fontWeight: 900}}>✓</span>
            <span style={{fontSize: 38, fontWeight: 800, color: '#FFFFFF'}}>
              A partir de <span style={{color: '#FFA94D'}}>R$ 199</span>
            </span>
          </div>
        </div>

        {/* Bloco 3: Botão Principal de CTA com Pulso e Shimmer Light Sweep (y≈1050 a 1200) */}
        <div
          style={{
            marginTop: 64,
            transform: `scale(${buttonFinalScale})`,
            opacity: Math.max(0, buttonSpring),
            position: 'relative',
          }}
        >
          <div
            style={{
              position: 'relative',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '32px 96px',
              borderRadius: 32,
              backgroundColor: '#FFA94D',
              boxShadow:
                '0 18px 50px rgba(255, 169, 77, 0.55), 0 0 30px rgba(255, 169, 77, 0.35)',
              overflow: 'hidden',
            }}
          >
            {/* Shimmer Light Bar cruzando o botão */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 90,
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.65), transparent)',
                transform: `translateX(${shimmerPos}px) skewX(-20deg)`,
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontSize: 50,
                fontWeight: 900,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                color: '#1F2937',
              }}
            >
              Chame no Direct
            </span>
          </div>
        </div>

        {/* Bloco 4: Arroba Oficial do Perfil (y≈1280 a 1380) */}
        <div
          style={{
            marginTop: 48,
            transform: `scale(${Math.max(0, handleSpring)})`,
            opacity: Math.max(0, handleSpring),
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 16,
              padding: '16px 42px',
              borderRadius: 24,
              background: 'rgba(31, 41, 55, 0.94)',
              border: '1px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 8px 24px rgba(0,0,0,0.45)',
            }}
          >
            {/* Ícone Instagram */}
            <svg
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFA94D"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
              <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
              <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
            </svg>
            <span
              style={{
                fontSize: 40,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: '0.02em',
              }}
            >
              @sintetizerisada
            </span>
          </div>
        </div>
      </div>
            }}
          >
            {/* Ícone Instagram */}
            <svg
              width="38"
              height="38"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFA94D"
              strokeWidth="2.2"
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
                letterSpacing: '0.02em',
              }}
            >
              @sintetizerisada
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};