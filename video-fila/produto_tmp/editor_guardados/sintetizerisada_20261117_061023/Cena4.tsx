import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
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

  // Background zoom contínuo do frame 0 ao 120 (movimento contínuo orgânico)
  const bgScale = interpolate(frame, [0, 120], [1.02, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Fade in de entrada suave geral
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Entrada escalonada (stagger slide-up com fade) nos blocos
  // 1. Bloco da marca (frame 0)
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // 2. Headline da proposta (frame 8)
  const headlineSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // 3. Chips de benefícios (frame 18)
  const chipsSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // 4. Comparador de preços (frame 28)
  const tableSpring = spring({
    frame: frame - 28,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Animação do risco vermelho passando sobre 'R$ 2.500/mês' (frame 42 a 58)
  const strikeProgress = interpolate(frame, [42, 58], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 5. Botão CTA (frame 54)
  const ctaSpring = spring({
    frame: frame - 54,
    fps,
    config: {damping: 10, stiffness: 130},
  });

  // Pulso contínuo vivo do botão CTA (loop de escala 1.0 a 1.048)
  const pulseButton = 1 + 0.045 * Math.sin(frame * 0.22);

  // Varredura contínua de brilho (shimmer effect): loop suave a cada 36 frames (-40% a 120%)
  const shimmerLoop = (frame * 4.5) % 160;
  const shimmerLeft = shimmerLoop - 40;

  // Pulso de iluminação no card de preço da Agenda IA
  const priceGlow = 0.25 + 0.12 * Math.sin(frame * 0.2);

  // Leve flutuação do bloco da marca
  const floatBrand = 2.5 * Math.sin(frame * 0.18);

  return (
    <AbsoluteFill
      style={{
        opacity: fadeIn,
        overflow: 'hidden',
        background: '#0F172A',
      }}
    >
      {/* Fundo em vídeo da barbearia com desfoque suave e escurecimento (preserva continuidade orgânica) */}
      <AbsoluteFill style={{transform: `scale(${bgScale})`}}>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(14px) brightness(0.45)',
          }}
        />
      </AbsoluteFill>

      {/* Véu escuro da marca para contraste absoluto */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(circle at 50% 50%, rgba(31, 41, 55, 0.72) 0%, rgba(15, 23, 42, 0.92) 100%)',
        }}
      />

      {/* Conteúdo com distribuição vertical equilibrada na Safe Zone (y=220 a 1440) */}
      <div
        style={{
          position: 'absolute',
          top: 220,
          left: 60,
          right: 60,
          bottom: 380,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          textAlign: 'center',
        }}
      >
        {/* Bloco 1: Marca com leve flutuação viva (y ~ 220 a 380) */}
        <div
          style={{
            transform: `scale(${Math.max(0, logoSpring)}) translateY(${floatBrand}px)`,
            opacity: logoSpring,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <div
            style={{
              padding: '6px 22px',
              borderRadius: 999,
              background: 'rgba(255, 169, 77, 0.15)',
              border: '1.5px solid rgba(255, 169, 77, 0.6)',
              boxShadow: '0 4px 16px rgba(255, 169, 77, 0.2)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFA94D',
                textTransform: 'uppercase',
                letterSpacing: 2,
              }}
            >
              Tecnologia com IA
            </span>
          </div>

          <h1
            style={{
              margin: 0,
              fontFamily,
              fontSize: 88,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
              textShadow: '0 8px 32px rgba(255, 169, 77, 0.45)',
            }}
          >
            Agenda <span style={{color: '#FFA94D'}}>IA</span>
          </h1>
        </div>

        {/* Bloco 2: Frase do produto enxuta sem redundância de 24h/WhatsApp (y ~ 430) */}
        <div
          style={{
            transform: `translateY(${(1 - headlineSpring) * 20}px)`,
            opacity: headlineSpring,
            maxWidth: 920,
          }}
        >
          <p
            style={{
              margin: 0,
              fontFamily,
              fontSize: 40,
              fontWeight: 800,
              color: '#F8FAFC',
              lineHeight: 1.3,
              textShadow: '0 4px 16px rgba(0,0,0,0.85)',
            }}
          >
            Agendamentos automáticos direto no WhatsApp
          </p>
        </div>

        {/* Bloco 3: Chips de Benefícios com texto branco e '24h' apenas na pílula única (y ~ 560) */}
        <div
          style={{
            transform: `translateY(${(1 - chipsSpring) * 20}px)`,
            opacity: chipsSpring,
            display: 'flex',
            justifyContent: 'center',
            gap: 14,
            flexWrap: 'wrap',
          }}
        >
          <div
            style={{
              padding: '10px 22px',
              borderRadius: 16,
              background: 'rgba(31, 41, 55, 0.88)',
              border: '1px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
              }}
            >
              <span style={{color: '#22C55E'}}>✓</span> Sem Conflito
            </span>
          </div>
          <div
            style={{
              padding: '10px 22px',
              borderRadius: 16,
              background: 'rgba(31, 41, 55, 0.88)',
              border: '1px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
              }}
            >
              <span style={{color: '#22C55E'}}>✓</span> 100% Automático
            </span>
          </div>
          <div
            style={{
              padding: '10px 22px',
              borderRadius: 16,
              background: 'rgba(31, 41, 55, 0.88)',
              border: '1px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
              }}
            >
              <span style={{color: '#22C55E'}}>✓</span> 24h Ativo
            </span>
          </div>
        </div>

        {/* Bloco 4: Comparativo de economia com risco animado (y ~ 700 a 940) */}
        <div
          style={{
            transform: `translateY(${(1 - tableSpring) * 25}px)`,
            opacity: tableSpring,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            width: '100%',
            maxWidth: 920,
          }}
        >
          {/* Recepção tradicional com risco vermelho passando animado */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '18px 28px',
              borderRadius: 20,
              background: 'rgba(31, 41, 55, 0.95)',
              border: '1.5px solid rgba(255, 255, 255, 0.25)',
              boxShadow: '0 6px 20px rgba(0,0,0,0.4)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 800,
                color: '#E2E8F0',
              }}
            >
              Recepção tradicional
            </span>
            <div style={{position: 'relative', display: 'inline-block'}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 800,
                  color: '#CBD5E1',
                }}
              >
                R$ 2.500 /mês
              </span>
              {/* Risco vermelho desenhado dinamicamente */}
              <div
                style={{
                  position: 'absolute',
                  top: '52%',
                  left: -6,
                  width: `${strikeProgress}%`,
                  maxWidth: 'calc(100% + 12px)',
                  height: 4,
                  background: '#EF4444',
                  borderRadius: 2,
                  transform: 'translateY(-50%) rotate(-2deg)',
                  boxShadow: '0 0 8px rgba(239, 68, 68, 0.7)',
                }}
              />
            </div>
          </div>

          {/* Agenda IA (sem redundância de '24 horas') com destaque visual */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '20px 28px',
              borderRadius: 20,
              background: 'rgba(255, 169, 77, 0.18)',
              border: '2.5px solid #FFA94D',
              boxShadow: `0 8px 28px rgba(255, 169, 77, ${priceGlow})`,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <span style={{fontSize: 36}}>⚡</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                }}
              >
                Agenda IA
              </span>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 40,
                fontWeight: 900,
                color: '#FFA94D',
                textShadow: '0 2px 10px rgba(255, 169, 77, 0.4)',
              }}
            >
              a partir de R$ 199
            </span>
          </div>
        </div>

        {/* Bloco 5: Botão CTA com stagger slide-up e loop contínuo de pulsar (y ~ 1060) */}
        <div
          style={{
            transform: `translateY(${(1 - ctaSpring) * 20}px) scale(${pulseButton})`,
            opacity: ctaSpring,
            width: '100%',
            maxWidth: 880,
            position: 'relative',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              padding: '24px 44px',
              borderRadius: 26,
              background: '#FFA94D',
              border: '3px solid #FFE8CC',
              boxShadow:
                '0 16px 48px rgba(255, 169, 77, 0.6), 0 0 26px rgba(255, 169, 77, 0.45)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Shimmer / reflexo luminoso correndo continuamente pelo botão */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: `${shimmerLeft}%`,
                width: '55%',
                height: '100%',
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.55), transparent)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            <svg
              width="44"
              height="44"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#1F2937"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
              <polyline points="22,6 12,13 2,6" />
            </svg>
            <span
              style={{
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: '#1F2937',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              Chame no Direct
            </span>
          </div>
        </div>
      </div>

      {/* Perfil oficial (@sintetizerisada) visível desde o frame 0 (y ~ 1380, safe zone) */}
      <div
        style={{
          position: 'absolute',
          bottom: 240,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 50,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 34px',
            borderRadius: 999,
            background: 'rgba(15, 23, 42, 0.90)',
            border: '2px solid rgba(255, 255, 255, 0.3)',
            boxShadow: '0 6px 20px rgba(0,0,0,0.5)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 36,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
            }}
          >
            @sintetizerisada
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
