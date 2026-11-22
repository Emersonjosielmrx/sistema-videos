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

  // Movimento de câmera contínuo no vídeo b-roll (push-in suave)
  const scale = interpolate(frame, [0, 215], [1.02, 1.14], {
    extrapolateRight: 'clamp',
  });

  // Entrada do badge de etapa (frame 0)
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do título de solução (frame 8)
  const titleSpring = spring({
    frame: Math.max(0, frame - 8),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Entrada progressiva dos cards na lateral (escalonados com a fala)
  // Card 1: Solução sob medida (frame 15 - ~12.6s)
  const card1Spring = spring({
    frame: Math.max(0, frame - 15),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Card 2: Chatwoot (frame 86 - ~14.9s)
  const card2Spring = spring({
    frame: Math.max(0, frame - 86),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Card 3: Inteligência Artificial (frame 108 - ~15.7s)
  const card3Spring = spring({
    frame: Math.max(0, frame - 108),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Card 4: Rotina Adaptada (frame 160 - ~17.4s)
  const card4Spring = spring({
    frame: Math.max(0, frame - 160),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Pulso de status
  const pulse = Math.sin((frame / 20) * Math.PI * 2) * 0.05 + 1.0;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#0F172A',
        fontFamily,
      }}
    >
      {/* Vídeo B-Roll com Câmera Dinâmica e Cores Vivas (Sem escurecimento excessivo do profissional) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 1080,
          height: 1920,
          transform: `scale(${scale})`,
          transformOrigin: 'left center',
        }}
      >
        <OffthreadVideo
          src={staticFile('video_2.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Gradiente Seletivo: Topo para os títulos e Lateral Direita apenas sob a coluna de cards */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 380,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.94) 0%, rgba(15, 23, 42, 0.70) 60%, rgba(15, 23, 42, 0) 100%)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 0,
          right: 0,
          bottom: 0,
          width: 620,
          background:
            'linear-gradient(270deg, rgba(15, 23, 42, 0.94) 0%, rgba(15, 23, 42, 0.80) 65%, rgba(15, 23, 42, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Elementos na Zona Segura (150 a 1580, x=60 a 1020) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          padding: '0 60px',
        }}
      >
        {/* Badge "02 • COMO FUNCIONA" (y=175) */}
        <div
          style={{
            position: 'absolute',
            top: 175,
            left: 60,
            transform: `scale(${badgeSpring})`,
            transformOrigin: 'left center',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: '#0F172A',
            border: '2px solid #0284C7',
            borderRadius: 30,
            padding: '10px 24px',
            boxShadow: '0 8px 24px rgba(2, 132, 199, 0.35)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#0284C7',
              transform: `scale(${pulse})`,
              boxShadow: '0 0 10px #0284C7',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#38BDF8',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            02 • COMO FUNCIONA
          </span>
        </div>

        {/* Título de Solução (y=255) */}
        <div
          style={{
            position: 'absolute',
            top: 255,
            left: 60,
            right: 60,
            transform: `translateY(${interpolate(titleSpring, [0, 1], [30, 0])}px)`,
            opacity: titleSpring,
          }}
        >
          <span
            style={{
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              display: 'block',
              textShadow: '0 4px 16px rgba(0,0,0,0.85)',
            }}
          >
            SOLUÇÃO SOB MEDIDA
          </span>
        </div>

        {/* Pilha de Cards Técnicos na Lateral Direita (x=500 a 1020, y=340 a 860) */}
        <div
          style={{
            position: 'absolute',
            top: 340,
            right: 60,
            width: 530,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          {/* Card 1: Solução Sob Medida */}
          <div
            style={{
              transform: `translateX(${interpolate(card1Spring, [0, 1], [80, 0])}px) scale(${interpolate(card1Spring, [0, 1], [0.9, 1])})`,
              opacity: card1Spring,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2px solid rgba(255, 255, 255, 0.16)',
                borderRadius: 20,
                padding: '16px 22px',
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                boxShadow: '0 12px 30px rgba(0, 0, 0, 0.65)',
              }}
            >
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 14,
                  background: 'rgba(56, 189, 248, 0.18)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                  flexShrink: 0,
                  border: '1px solid #38BDF8',
                }}
              >
                ⚙️
              </div>
              <div>
                <span
                  style={{
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    display: 'block',
                    lineHeight: 1.15,
                  }}
                >
                  Sob Medida
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#94A3B8',
                    display: 'block',
                    marginTop: 2,
                  }}
                >
                  Feito pro seu negócio
                </span>
              </div>
            </div>
          </div>

          {/* Card 2: Chatwoot & Tickets */}
          <div
            style={{
              transform: `translateX(${interpolate(card2Spring, [0, 1], [80, 0])}px) scale(${interpolate(card2Spring, [0, 1], [0.9, 1])})`,
              opacity: card2Spring,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2.5px solid #0284C7',
                borderRadius: 20,
                padding: '16px 22px',
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                boxShadow: '0 14px 35px rgba(2, 132, 199, 0.4)',
              }}
            >
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 14,
                  background: '#0284C7',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                  flexShrink: 0,
                }}
              >
                💬
              </div>
              <div>
                <span
                  style={{
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#38BDF8',
                    display: 'block',
                    lineHeight: 1.15,
                  }}
                >
                  Base Chatwoot
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#E2E8F0',
                    display: 'block',
                    marginTop: 2,
                  }}
                >
                  Atendimento & Tickets
                </span>
              </div>
            </div>
          </div>

          {/* Card 3: Inteligência Artificial */}
          <div
            style={{
              transform: `translateX(${interpolate(card3Spring, [0, 1], [80, 0])}px) scale(${interpolate(card3Spring, [0, 1], [0.9, 1])})`,
              opacity: card3Spring,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2.5px solid #8B5CF6',
                borderRadius: 20,
                padding: '16px 22px',
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                boxShadow: '0 14px 35px rgba(139, 92, 246, 0.35)',
              }}
            >
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 14,
                  background: '#8B5CF6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                  flexShrink: 0,
                }}
              >
                ⚡
              </div>
              <div>
                <span
                  style={{
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#C4B5FD',
                    display: 'block',
                    lineHeight: 1.15,
                  }}
                >
                  Inteligência Artificial
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#E2E8F0',
                    display: 'block',
                    marginTop: 2,
                  }}
                >
                  Automação no CRM
                </span>
              </div>
            </div>
          </div>

          {/* Card 4: Rotina do seu time */}
          <div
            style={{
              transform: `translateX(${interpolate(card4Spring, [0, 1], [80, 0])}px) scale(${interpolate(card4Spring, [0, 1], [0.9, 1])})`,
              opacity: card4Spring,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2px solid #10B981',
                borderRadius: 20,
                padding: '16px 22px',
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                boxShadow: '0 12px 30px rgba(16, 185, 129, 0.35)',
              }}
            >
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 14,
                  background: '#10B981',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                  flexShrink: 0,
                  color: '#FFFFFF',
                  fontWeight: 900,
                }}
              >
                ✓
              </div>
              <div>
                <span
                  style={{
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#6EE7B7',
                    display: 'block',
                    lineHeight: 1.15,
                  }}
                >
                  Para a Sua Rotina
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#F1F5F9',
                    display: 'block',
                    marginTop: 2,
                  }}
                >
                  Fluidez no dia a dia
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
