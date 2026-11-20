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

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Variação imediata de plano na entrada da Cena 2 (quadro q07): punch-in zoom de 14% (1.14x)
  // e rebaixamento Y de 45px para garantir respiro total do cabelo
  const isTraefikDetailPhase = frame >= 85;

  const videoScale = interpolate(frame, [0, 245], [1.14, 1.18], {
    extrapolateRight: 'clamp',
  });
  const videoY = 45;

  // Transições de overlap
  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(frame, [235, 245], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cenaOpacity = fadeIn * fadeOut;

  // Entrada inicial do badge fixo desde o primeiro frame
  const pillSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Entrada do rótulo limpo superior e lower-third aos ~2.8s (frame 85)
  const detailSpring = spring({
    frame: frame - 85,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Micro-animações contínuas
  const headerFloat = Math.sin(frame / 14) * 2.5;

  // Pulso contínuo das conexões de rede em alta velocidade
  const pulseSpeed = frame * 10;

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
      {/* 1. Vídeo do Apresentador com Punch-In Zoom de 14% Imediato desde o frame 0 (quebrando o molde da Cena 1) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale}) translateY(${videoY}px)`,
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_2.mp4')}
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

      {/* 2. Topo na Fase 1 (frame 0 a 84): Termo Técnico Padrão Corrigido 'GERENCIAMENTO E ROTEAMENTO' */}
      {!isTraefikDetailPhase ? (
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
              border: '2px solid rgba(14, 165, 233, 0.85)',
              padding: '8px 26px',
              borderRadius: 18,
              boxShadow:
                '0 8px 30px rgba(0, 0, 0, 0.85), 0 0 25px rgba(14, 165, 233, 0.35)',
              opacity: Math.max(0, Math.min(1, pillSpring)),
              transform: `translateY(${(1 - Math.min(1, pillSpring)) * -18}px)`,
            }}
          >
            {/* Ícone de Escudo Traefik */}
            <svg
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#0EA5E9"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <rect x="9" y="10" width="6" height="5" rx="1" />
              <path d="M10 10V8a2 2 0 1 1 4 0v2" />
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
              TRAEFIK • GERENCIAMENTO E ROTEAMENTO
            </span>
          </div>
        </div>
      ) : (
        /* 3. Topo na Fase 2 (frame 85+): Rótulo único, limpo e em caixa alta com alta legibilidade (conforme diretor) */
        <div
          style={{
            position: 'absolute',
            top: 162,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            transform: `translateY(${headerFloat}px)`,
            opacity: Math.max(0, Math.min(1, detailSpring)),
            zIndex: 20,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              background: '#111827',
              border: '2px solid rgba(14, 165, 233, 0.85)',
              padding: '8px 26px',
              borderRadius: 18,
              boxShadow:
                '0 8px 30px rgba(0, 0, 0, 0.85), 0 0 25px rgba(14, 165, 233, 0.35)',
            }}
          >
            <span
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#10B981',
                boxShadow: '0 0 8px #10B981',
              }}
            />
            <span
              style={{
                fontSize: 34,
                fontWeight: 900,
                color: '#38BDF8',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              ROTEAMENTO E SSL AUTOMÁTICO
            </span>
          </div>
        </div>
      )}

      {/* 4. Lower-Third Elegante com Respiro Total (y=1250 a 1390):
             Posicionado na altura do peito, deixando o rosto e a barba 100% desobstruídos e respeitando a zona da legenda.
             Contém o diagrama com conexões dinâmicas e pulsos de luz em fluxo contínuo. */}
      {isTraefikDetailPhase && (
        <div
          style={{
            position: 'absolute',
            top: 1250,
            left: 60,
            right: 60,
            background: 'rgba(15, 23, 42, 0.95)',
            border: '2px solid rgba(14, 165, 233, 0.75)',
            borderRadius: 24,
            padding: '16px 24px',
            boxShadow:
              '0 15px 40px rgba(0, 0, 0, 0.85), 0 0 25px rgba(14, 165, 233, 0.3)',
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            opacity: Math.max(0, Math.min(1, detailSpring)),
            transform: `translateY(${(1 - Math.min(1, detailSpring)) * 25}px)`,
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
            <span
              style={{
                fontSize: 28,
                fontWeight: 800,
                color: '#38BDF8',
                letterSpacing: 1,
              }}
            >
              PAINEL TRAEFIK • ROTAS BLINDADAS
            </span>
            <span
              style={{
                fontSize: 26,
                fontWeight: 800,
                color: '#6EE7B7',
                background: 'rgba(16, 185, 129, 0.2)',
                border: '1px solid rgba(16, 185, 129, 0.5)',
                padding: '2px 10px',
                borderRadius: 8,
              }}
            >
              SSL ATIVO
            </span>
          </div>

          {/* Diagrama Esquemático com Motion Contínuo de Pulsos de Luz */}
          <div
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingTop: 2,
            }}
          >
            {/* Nó 1: Tráfego Web */}
            <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
              <span style={{fontSize: 26}}>🌐</span>
              <span
                style={{
                  fontSize: 30,
                  fontWeight: 900,
                  color: '#F1F5F9',
                  letterSpacing: 0.5,
                }}
              >
                TRÁFEGO
              </span>
            </div>

            {/* Linha com partículas animadas */}
            <div
              style={{
                flex: 1,
                position: 'relative',
                height: 6,
                background: 'rgba(14, 165, 233, 0.3)',
                borderRadius: 3,
                margin: '0 12px',
                overflow: 'hidden',
              }}
            >
              {[0, 60, 120].map((offset, idx) => (
                <div
                  key={idx}
                  style={{
                    position: 'absolute',
                    top: 0,
                    bottom: 0,
                    width: 32,
                    borderRadius: 3,
                    background:
                      'linear-gradient(90deg, transparent, #38BDF8, #FFFFFF)',
                    transform: `translateX(${((pulseSpeed + offset) % 200) - 32}px)`,
                    boxShadow: '0 0 8px #38BDF8',
                  }}
                />
              ))}
            </div>

            {/* Nó 2: Traefik */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                background: 'rgba(14, 165, 233, 0.25)',
                border: '1.5px solid #0EA5E9',
                borderRadius: 12,
                padding: '4px 14px',
                boxShadow: '0 0 15px rgba(14, 165, 233, 0.4)',
              }}
            >
              <span style={{fontSize: 24}}>🛡️</span>
              <span
                style={{
                  fontSize: 30,
                  fontWeight: 900,
                  color: '#38BDF8',
                  letterSpacing: 0.5,
                }}
              >
                TRAEFIK
              </span>
            </div>

            {/* Linha com partículas verdes protegidas */}
            <div
              style={{
                flex: 1,
                position: 'relative',
                height: 6,
                background: 'rgba(16, 185, 129, 0.3)',
                borderRadius: 3,
                margin: '0 12px',
                overflow: 'hidden',
              }}
            >
              {[0, 60, 120].map((offset, idx) => (
                <div
                  key={idx}
                  style={{
                    position: 'absolute',
                    top: 0,
                    bottom: 0,
                    width: 32,
                    borderRadius: 3,
                    background:
                      'linear-gradient(90deg, transparent, #10B981, #A7F3D0)',
                    transform: `translateX(${((pulseSpeed + offset) % 200) - 32}px)`,
                    boxShadow: '0 0 8px #10B981',
                  }}
                />
              ))}
            </div>

            {/* Nó 3: Docker */}
            <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
              <span style={{fontSize: 26}}>🐳</span>
              <span
                style={{
                  fontSize: 30,
                  fontWeight: 900,
                  color: '#6EE7B7',
                  letterSpacing: 0.5,
                }}
              >
                DOCKER
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
