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

  // Movimento de câmera no vídeo B-roll de fundo
  const videoScale = interpolate(frame, [0, 276], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });

  // Topo informativo aos 0.1s (frame 3)
  const headerSpring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Selo Chatwoot aos 3.2s (frame 97)
  const chatwootSpring = spring({
    frame: frame - 97,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Card 1: Atendimento (~4.2s / frame 126)
  const card1Spring = spring({
    frame: frame - 126,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Card 2: Tickets (~5.0s / frame 150)
  const card2Spring = spring({
    frame: frame - 150,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Card 3: Histórico (~5.6s / frame 168)
  const card3Spring = spring({
    frame: frame - 168,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Banner Unificado: Um só lugar (~7.1s / frame 215)
  const unifiedSpring = spring({
    frame: frame - 215,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Desmonte final antes do corte (frame 255..276)
  const exitOpacity = interpolate(frame, [255, 276], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const pulse = 1 + Math.sin(frame / 8) * 0.02;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Vídeo B-roll da Equipe em Tela Cheia com movimento de câmera contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: 'center center',
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

      {/* Véu escuro da marca em gradiente translúcido para leitura perfeita dos cards */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.88) 0%, rgba(15, 23, 42, 0.70) 45%, rgba(15, 23, 42, 0.94) 100%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: exitOpacity,
        }}
      >
        {/* Topo Informativo (y=190 — respiro de 40px abaixo da barra) */}
        <div
          style={{
            position: 'absolute',
            top: 190,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 10,
            transform: `scale(${Math.max(0, headerSpring)})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '6px 22px',
              borderRadius: 20,
              background: 'rgba(31, 147, 255, 0.22)',
              border: '1.5px solid rgba(31, 147, 255, 0.55)',
              backdropFilter: 'blur(10px)',
            }}
          >
            <span style={{fontSize: 28}}>⚡</span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#93C5FD',
                textTransform: 'uppercase',
                letterSpacing: 1.1,
              }}
            >
              Como Funciona
            </span>
          </div>

          <div
            style={{
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: -0.5,
              textShadow: '0 4px 16px rgba(0,0,0,0.85)',
            }}
          >
            CRM SOB MEDIDA
          </div>

          {/* Selo Chatwoot */}
          {frame >= 90 && (
            <div
              style={{
                transform: `scale(${Math.max(0, chatwootSpring)})`,
                background: 'rgba(15, 23, 42, 0.88)',
                border: '1.5px solid #1F93FF',
                borderRadius: 14,
                padding: '6px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                backdropFilter: 'blur(8px)',
                boxShadow: '0 4px 16px rgba(31, 147, 255, 0.35)',
              }}
            >
              <span style={{fontSize: 26}}>🚀</span>
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                }}
              >
                A partir do Chatwoot
              </span>
            </div>
          )}
        </div>

        {/* 3 Pilares Dinâmicos que acendem exatamente na hora da fala (y=440..920) */}
        <div
          style={{
            position: 'absolute',
            top: 450,
            left: 70,
            right: 70,
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
          }}
        >
          {/* Pilar 1: Atendimento */}
          {frame >= 120 && (
            <div
              style={{
                transform: `scale(${Math.max(0, card1Spring)})`,
                background: 'rgba(15, 23, 42, 0.88)',
                border: '2px solid #1F93FF',
                borderRadius: 20,
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                boxShadow: '0 10px 28px rgba(31, 147, 255, 0.35)',
                backdropFilter: 'blur(12px)',
              }}
            >
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: 16,
                  background: '#1F93FF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  flexShrink: 0,
                  boxShadow: '0 4px 14px rgba(31, 147, 255, 0.5)',
                }}
              >
                💬
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
                <span
                  style={{
                    fontSize: 36,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                  }}
                >
                  Atendimento Unificado
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#CBD5E1',
                  }}
                >
                  Todas as conversas em tempo real
                </span>
              </div>
            </div>
          )}

          {/* Pilar 2: Tickets */}
          {frame >= 144 && (
            <div
              style={{
                transform: `scale(${Math.max(0, card2Spring)})`,
                background: 'rgba(15, 23, 42, 0.88)',
                border: '2px solid #38BDF8',
                borderRadius: 20,
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                boxShadow: '0 10px 28px rgba(56, 189, 248, 0.35)',
                backdropFilter: 'blur(12px)',
              }}
            >
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: 16,
                  background: '#38BDF8',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  flexShrink: 0,
                  boxShadow: '0 4px 14px rgba(56, 189, 248, 0.5)',
                }}
              >
                🎫
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
                <span
                  style={{
                    fontSize: 36,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                  }}
                >
                  Tickets Integrados
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#CBD5E1',
                  }}
                >
                  Chamados e solicitações organizadas
                </span>
              </div>
            </div>
          )}

          {/* Pilar 3: Histórico */}
          {frame >= 164 && (
            <div
              style={{
                transform: `scale(${Math.max(0, card3Spring)})`,
                background: 'rgba(15, 23, 42, 0.88)',
                border: '2px solid #60A5FA',
                borderRadius: 20,
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                boxShadow: '0 10px 28px rgba(96, 165, 250, 0.35)',
                backdropFilter: 'blur(12px)',
              }}
            >
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: 16,
                  background: '#60A5FA',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  flexShrink: 0,
                  boxShadow: '0 4px 14px rgba(96, 165, 250, 0.5)',
                }}
              >
                📂
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
                <span
                  style={{
                    fontSize: 36,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                  }}
                >
                  Histórico do Cliente
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#CBD5E1',
                  }}
                >
                  Registro completo de cada contato
                </span>
              </div>
            </div>
          )}

          {/* Banner Unificado: Em um só lugar */}
          {frame >= 210 && (
            <div
              style={{
                transform: `scale(${Math.max(0, unifiedSpring) * pulse})`,
                marginTop: 8,
                background:
                  'linear-gradient(90deg, #1F93FF 0%, #2563EB 100%)',
                borderRadius: 20,
                padding: '16px 28px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 14,
                boxShadow: '0 12px 32px rgba(31, 147, 255, 0.5)',
              }}
            >
              <span style={{fontSize: 34}}>🎯</span>
              <span
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: 1.2,
                }}
              >
                Tudo em um só lugar
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
