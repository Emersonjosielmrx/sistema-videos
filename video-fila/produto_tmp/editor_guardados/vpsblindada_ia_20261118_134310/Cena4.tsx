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

  // Movimento contínuo de câmera / fundo
  const bgScale = interpolate(frame, [0, 119], [1.08, 1.25], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(frame, [0, 119], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Entrada suave de overlap
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Entradas em spring escalonadas (stagger amplo ao longo da cena para evitar cena estática)
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const titleSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const subtitleSpring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Stagger escalonado dos 3 benefícios
  const item1Spring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const item2Spring = spring({
    frame: frame - 32,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const item3Spring = spring({
    frame: frame - 44,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Entrada sincronizada do botão de CTA no momento da fala (~28.5s / frame 42)
  const buttonSpring = spring({
    frame: frame - 42,
    fps,
    config: {damping: 11, stiffness: 150},
  });

  const profileSpring = spring({
    frame: frame - 54,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const sealSpring = spring({
    frame: frame - 64,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Micro-animações contínuas ao longo de toda a duração
  const shieldFloat = Math.sin(frame / 7) * 5;

  // Pulsação sutil contínua (pulse) no botão de conversão
  const buttonPulse = 1 + Math.sin(frame / 4.5) * 0.035;

  // Efeito de luz correndo (shimmer/sweep) suave e contínuo ao longo do botão sem ofuscar as letras
  const shimmerX = interpolate(frame % 32, [0, 32], [-200, 1100]);

  // Micro-pulsação contínua nos cards de benefícios
  const item1Pulse = 1 + Math.sin(frame / 6) * 0.015;
  const item2Pulse = 1 + Math.sin((frame + 10) / 6) * 0.015;
  const item3Pulse = 1 + Math.sin((frame + 20) / 6) * 0.015;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        opacity: fadeIn,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Fundo Desfocado com Push-in */}
      <div
        style={{
          position: 'absolute',
          inset: -20,
          transform: `scale(${bgScale}) translateY(${bgY}px)`,
          filter: 'blur(16px)',
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

      {/* Véu Escuro da Marca */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 35%, rgba(14, 165, 233, 0.24) 0%, rgba(10, 15, 28, 0.95) 75%)',
        }}
      />

      {/* Partículas de Ambiência Tecnológica em Movimento Contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.24,
          backgroundImage:
            'radial-gradient(rgba(14, 165, 233, 0.55) 1.5px, transparent 1.5px)',
          backgroundSize: '54px 54px',
          transform: `translateY(${(frame * 1.2) % 54}px)`,
        }}
      />

      {/* Bloco Superior: Logo + Marca + Proposta de Valor (y=175 a 455) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 20,
        }}
      >
        {/* Ícone de Escudo Tecnológico com flutuação contínua */}
        <div
          style={{
            opacity: Math.max(0, Math.min(1, logoSpring)),
            transform: `translateY(${shieldFloat}px) scale(${interpolate(
              logoSpring,
              [0, 1],
              [0.85, 1]
            )})`,
            width: 96,
            height: 96,
            borderRadius: 24,
            background:
              'linear-gradient(135deg, rgba(14, 165, 233, 0.35) 0%, rgba(15, 23, 42, 0.94) 100%)',
            border: '2px solid rgba(14, 165, 233, 0.7)',
            boxShadow:
              '0 0 35px rgba(14, 165, 233, 0.45), inset 0 0 20px rgba(14, 165, 233, 0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <svg
            width="50"
            height="50"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#0EA5E9"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <polyline points="9 12 11 14 15 10" />
          </svg>
        </div>

        {/* Nome da Marca */}
        <div
          style={{
            opacity: Math.max(0, Math.min(1, titleSpring)),
            transform: `scale(${interpolate(titleSpring, [0, 1], [0.9, 1])})`,
            fontSize: 66,
            fontWeight: 900,
            color: '#FFFFFF',
            letterSpacing: 3,
            textTransform: 'uppercase',
            textShadow:
              '0 4px 30px rgba(14, 165, 233, 0.65), 0 0 50px rgba(14, 165, 233, 0.35)',
          }}
        >
          VPS Blindada
        </div>

        {/* Frase Síntese do Produto */}
        <div
          style={{
            opacity: Math.max(0, Math.min(1, subtitleSpring)),
            fontSize: 38,
            fontWeight: 600,
            color: '#E2E8F0',
            textAlign: 'center',
            maxWidth: 820,
            lineHeight: 1.3,
          }}
        >
          Sua VPS pronta, segura e com backup
        </div>
      </div>

      {/* Bloco Central: 3 Pilares Tecnológicos com Entrada Escalonada (Stagger) */}
      <div
        style={{
          position: 'absolute',
          top: 485,
          left: 70,
          right: 70,
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
          zIndex: 20,
        }}
      >
        {/* Pilar 1 - Entrada aos ~0.66s (frame 20) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 18,
            background: 'rgba(15, 23, 42, 0.94)',
            border: '1.5px solid rgba(14, 165, 233, 0.55)',
            borderRadius: 20,
            padding: '16px 26px',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.5)',
            opacity: Math.max(0, Math.min(1, item1Spring)),
            transform: `translateY(${(1 - Math.min(1, item1Spring)) * 30}px) scale(${item1Pulse})`,
          }}
        >
          <span style={{fontSize: 34}}>⚙️</span>
          <span
            style={{
              fontSize: 36,
              fontWeight: 800,
              color: '#F1F5F9',
              letterSpacing: 1,
            }}
          >
            DOCKER + PORTAINER + TRAEFIK
          </span>
        </div>

        {/* Pilar 2 - Entrada aos ~1.06s (frame 32) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 18,
            background: 'rgba(15, 23, 42, 0.94)',
            border: '1.5px solid rgba(14, 165, 233, 0.55)',
            borderRadius: 20,
            padding: '16px 26px',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.5)',
            opacity: Math.max(0, Math.min(1, item2Spring)),
            transform: `translateY(${(1 - Math.min(1, item2Spring)) * 30}px) scale(${item2Pulse})`,
          }}
        >
          <span style={{fontSize: 34}}>🔄</span>
          <span
            style={{
              fontSize: 36,
              fontWeight: 800,
              color: '#F1F5F9',
              letterSpacing: 1,
            }}
          >
            BACKUP AUTOMÁTICO CONFIGURADO
          </span>
        </div>

        {/* Pilar 3 - Entrada aos ~1.46s (frame 44) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 18,
            background: 'rgba(15, 23, 42, 0.94)',
            border: '1.5px solid rgba(14, 165, 233, 0.55)',
            borderRadius: 20,
            padding: '16px 26px',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.5)',
            opacity: Math.max(0, Math.min(1, item3Spring)),
            transform: `translateY(${(1 - Math.min(1, item3Spring)) * 30}px) scale(${item3Pulse})`,
          }}
        >
          <span style={{fontSize: 34}}>🤖</span>
          <span
            style={{
              fontSize: 36,
              fontWeight: 800,
              color: '#F1F5F9',
              letterSpacing: 1,
            }}
          >
            BOT SENTINELA VIGIANDO ERROS
          </span>
        </div>
      </div>

      {/* Bloco Inferior: CTA com Alto Contraste (tipografia escura sobre ciano) + Pulsação + Shimmer */}
      <div
        style={{
          position: 'absolute',
          top: 890,
          left: 70,
          right: 70,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 22,
          zIndex: 25,
        }}
      >
        {/* Botão de Ação CTA:
            - Tipografia escura (#0B132B azul-marinho profundo) garantindo contraste perfeito AAA
            - Shimmer suave em fluxo contínuo
            - Pulsação contínua (buttonPulse) */}
        <div
          style={{
            position: 'relative',
            width: '100%',
            height: 120,
            borderRadius: 28,
            background:
              'linear-gradient(135deg, #00D2FF 0%, #0EA5E9 50%, #38BDF8 100%)',
            boxShadow: `0 12px 40px rgba(14, 165, 233, 0.65), 0 0 ${
              18 + Math.sin(frame / 4.5) * 12
            }px rgba(56, 189, 248, 0.75)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
            opacity: Math.max(0, Math.min(1, buttonSpring)),
            transform: `scale(${
              interpolate(buttonSpring, [0, 1], [0.88, 1]) * buttonPulse
            }) translateY(${(1 - Math.min(1, buttonSpring)) * 25}px)`,
          }}
        >
          {/* Brilho Shimmer com opacidade atenuada (0.35) que varre continuamente sem ofuscar o texto */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: 180,
              transform: `translateX(${shimmerX}px) skewX(-25deg)`,
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.35) 50%, transparent 100%)',
              pointerEvents: 'none',
            }}
          />

          <span
            style={{
              fontSize: 52,
              fontWeight: 900,
              color: '#071527',
              letterSpacing: 2,
              textTransform: 'uppercase',
              textShadow: '0 1px 3px rgba(255, 255, 255, 0.4)',
            }}
          >
            CHAME NO DIRECT
          </span>
        </div>

        {/* Perfil Oficial (@marca) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: 'rgba(15, 23, 42, 0.94)',
            border: '1.5px solid rgba(14, 165, 233, 0.7)',
            borderRadius: 999,
            padding: '12px 34px',
            boxShadow: '0 6px 22px rgba(0, 0, 0, 0.55)',
            opacity: Math.max(0, Math.min(1, profileSpring)),
            transform: `translateY(${(1 - Math.min(1, profileSpring)) * 15}px)`,
          }}
        >
          <svg
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#38BDF8"
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
              fontSize: 42,
              fontWeight: 800,
              color: '#38BDF8',
              letterSpacing: 1,
            }}
          >
            @vpsblindada.ia
          </span>
        </div>

        {/* Selo de Fechamento: Fonte aumentada (33px), em linha única e clareada (#F8FAFC) com alto contraste */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1.5px solid rgba(14, 165, 233, 0.75)',
            borderRadius: 999,
            padding: '10px 24px',
            boxShadow: '0 4px 18px rgba(0, 0, 0, 0.6)',
            opacity: Math.max(0, Math.min(1, sealSpring)),
            transform: `translateY(${(1 - Math.min(1, sealSpring)) * 15}px)`,
            whiteSpace: 'nowrap',
          }}
        >
          <span style={{fontSize: 26}}>🛡️</span>
          <span
            style={{
              fontSize: 33,
              fontWeight: 800,
              color: '#F8FAFC',
              letterSpacing: 0.5,
              textTransform: 'uppercase',
              whiteSpace: 'nowrap',
            }}
          >
            INFRAESTRUTURA CONFIGURADA E SEGURA
          </span>
        </div>
      </div>
    </div>
  );
};
