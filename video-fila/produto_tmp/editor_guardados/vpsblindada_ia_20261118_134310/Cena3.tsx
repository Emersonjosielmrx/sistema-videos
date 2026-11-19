import React from 'react';
import {
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

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Transição fluida de entrada: Cyber Wipe temático da marca (frames 0 a 12)
  // eliminando o corte seco (jump cut) repetitivo vindo da Cena 2
  const wipeProgress = interpolate(frame, [0, 12], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Fase em que os módulos Portainer & Bot Sentinela são exibidos (frame 70 a 246)
  const isPortainerPhase = frame >= 70;

  // Enquadramento do apresentador: retorno ao plano médio e rebaixamento Y de 45px para garantir respiro total do cabelo
  const videoScale = interpolate(frame, [0, 246], [1.04, 1.08], {
    extrapolateRight: 'clamp',
  });
  const videoY = 45;

  // Transições de overlap
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(frame, [236, 246], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cenaOpacity = fadeIn * fadeOut;

  // Entrada inicial do selo superior
  const pillSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Entrada suave do Lower-Third Portainer aos ~2.3s (frame 70)
  const portainerSpring = spring({
    frame: frame - 70,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Entradas escalonadas com mola suave dos 3 módulos (sem cortes secos e sem aperto)
  const mod1Spring = spring({
    frame: frame - 75,
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const mod2Spring = spring({
    frame: frame - 105,
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const mod3Spring = spring({
    frame: frame - 135,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Micro-animações contínuas
  const headerFloat = Math.sin(frame / 14) * 2.5;
  const pulseLoop = Math.sin(frame / 4.5) * 0.12;
  const sentinelaRadar = (frame * 6) % 360;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        opacity: cenaOpacity,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Transição Fluida Inicial: Cyber Wipe com linha de corte neon ciano da marca */}
      {frame <= 12 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `linear-gradient(${135}deg, rgba(14, 165, 233, 0.95) 0%, rgba(10, 15, 28, 0.98) ${
              wipeProgress * 100
            }%, transparent ${wipeProgress * 100 + 15}%)`,
            zIndex: 50,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* 1. Vídeo do Apresentador com enquadramento limpo e rebaixamento Y */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale}) translateY(${videoY}px)`,
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Véu sutil de contraste superior */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 300,
            background:
              'linear-gradient(180deg, rgba(10, 15, 28, 0.82) 0%, rgba(10, 15, 28, 0.3) 65%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* 2. Topo Único: Selo fixo com respiro total em relação ao cabelo (> 110px de folga) */}
      <div
        style={{
          position: 'absolute',
          top: 162,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `translateY(${headerFloat}px)`,
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            background: '#111827',
            border: '2px solid rgba(16, 185, 129, 0.85)',
            padding: '8px 28px',
            borderRadius: 18,
            boxShadow:
              '0 8px 30px rgba(0, 0, 0, 0.85), 0 0 25px rgba(16, 185, 129, 0.35)',
            opacity: Math.max(0, Math.min(1, pillSpring)),
            transform: `translateY(${(1 - Math.min(1, pillSpring)) * -18}px)`,
          }}
        >
          {/* Ícone de Sucesso */}
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#10B981"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <polyline points="9 12 11 14 15 10" />
          </svg>
          <span
            style={{
              fontSize: 34,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1,
              textTransform: 'uppercase',
            }}
          >
            SISTEMA ONLINE • TRÁFEGO PROTEGIDO
          </span>
        </div>
      </div>

      {/* 3. Lower-Third Elegante de Infraestrutura Portainer & Bot Sentinela (y=1250 a 1395):
             Posicionado na altura do peito, deixando o rosto e a barba 100% desobstruídos.
             Contém os 3 módulos com espaçamento uniforme e margem lateral limpa de ambos os lados. */}
      {isPortainerPhase && (
        <div
          style={{
            position: 'absolute',
            top: 1250,
            left: 60,
            right: 60,
            background: 'rgba(15, 23, 42, 0.96)',
            border: '2px solid rgba(16, 185, 129, 0.75)',
            borderRadius: 24,
            padding: '16px 20px',
            boxShadow:
              '0 15px 40px rgba(0, 0, 0, 0.85), 0 0 25px rgba(16, 185, 129, 0.3)',
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            opacity: Math.max(0, Math.min(1, portainerSpring)),
            transform: `translateY(${(1 - Math.min(1, portainerSpring)) * 25}px)`,
            zIndex: 25,
          }}
        >
          {/* Header do Lower-Third */}
          <div
            style={{
              width: '100%',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              paddingBottom: 8,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <span
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  background: '#10B981',
                  boxShadow: '0 0 10px #10B981',
                  transform: `scale(${1 + pulseLoop})`,
                }}
              />
              <span
                style={{
                  fontSize: 28,
                  fontWeight: 800,
                  color: '#6EE7B7',
                  letterSpacing: 1,
                }}
              >
                PAINEL PORTAINER • INFRAESTRUTURA
              </span>
            </div>
            <span
              style={{
                fontSize: 26,
                fontWeight: 800,
                color: '#38BDF8',
                background: 'rgba(14, 165, 233, 0.15)',
                border: '1px solid rgba(14, 165, 233, 0.5)',
                padding: '2px 10px',
                borderRadius: 8,
              }}
            >
              SERVIDOR SEGURO
            </span>
          </div>

          {/* Cards dos 3 Módulos Ativos com Espaçamento Amplo e Padding Lateral Uniforme */}
          <div
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 10,
              paddingTop: 2,
            }}
          >
            {/* Módulo 1: Docker + Traefik */}
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 6,
                background: 'rgba(16, 185, 129, 0.18)',
                border: '1.5px solid rgba(16, 185, 129, 0.6)',
                borderRadius: 14,
                padding: '8px 10px',
                opacity: Math.max(0, Math.min(1, mod1Spring)),
                transform: `scale(${interpolate(mod1Spring, [0, 1], [0.92, 1])})`,
              }}
            >
              <span style={{fontSize: 24}}>🐳</span>
              <span
                style={{
                  fontSize: 26,
                  fontWeight: 800,
                  color: '#A7F3D0',
                  letterSpacing: 0.5,
                  whiteSpace: 'nowrap',
                }}
              >
                DOCKER+TRAEFIK
              </span>
            </div>

            {/* Módulo 2: Backup Automático */}
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 6,
                background: 'rgba(14, 165, 233, 0.18)',
                border: '1.5px solid rgba(14, 165, 233, 0.65)',
                borderRadius: 14,
                padding: '8px 10px',
                opacity: Math.max(0, Math.min(1, mod2Spring)),
                transform: `scale(${interpolate(mod2Spring, [0, 1], [0.92, 1])})`,
              }}
            >
              <span style={{fontSize: 24}}>🔄</span>
              <span
                style={{
                  fontSize: 26,
                  fontWeight: 800,
                  color: '#7DD3FC',
                  letterSpacing: 0.5,
                  whiteSpace: 'nowrap',
                }}
              >
                BACKUP ATIVO
              </span>
            </div>

            {/* Módulo 3: Bot Sentinela com entrada suave e margem interna garantida */}
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 6,
                background: 'rgba(16, 185, 129, 0.22)',
                border: '1.5px solid rgba(16, 185, 129, 0.8)',
                borderRadius: 14,
                padding: '8px 10px',
                boxShadow: '0 0 12px rgba(16, 185, 129, 0.3)',
                opacity: Math.max(0, Math.min(1, mod3Spring)),
                transform: `scale(${interpolate(mod3Spring, [0, 1], [0.92, 1])})`,
              }}
            >
              <span style={{fontSize: 24}}>🤖</span>
              <span
                style={{
                  fontSize: 26,
                  fontWeight: 800,
                  color: '#6EE7B7',
                  letterSpacing: 0.5,
                  whiteSpace: 'nowrap',
                }}
              >
                BOT SENTINELA
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
