import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Transições de borda (fade-in inicial de 10 frames)
  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Zoom contínuo no vídeo do dono (1.00 -> 1.06)
  const zoom = interpolate(frame, [0, 232], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Badge superior aos ~0.3s (frame 10)
  const badgeSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Painel de fluxo: entra aos ~0.7s (frame 22 - "Hoje uso...")
  const panelSpring = spring({
    frame: frame - 22,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Etapa 2 (Vídeo Demo): acende com spring aos ~3.6s (frame 109 - "com vídeo de demonstração")
  const step2Spring = spring({
    frame: frame - 109,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Mensagem síntese: surge aos ~5.0s (frame 150 - "apresenta o produto por mim")
  const summarySpring = spring({
    frame: frame - 150,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Micro pulso contínuo
  const pulse = Math.sin((frame / 30) * Math.PI * 2 * 0.8) * 0.02 + 1;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#000000',
        opacity: fadeIn,
      }}
    >
      {/* Vídeo do Dono em tela cheia com zoom contínuo */}
      <OffthreadVideo
        src={staticFile('dono_2.mp4')}
        muted
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${zoom})`,
        }}
      />

      {/* Véu superior para contraste perfeito no topo */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(180deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.55) 70%, rgba(0,0,0,0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Badge Superior: Como Funciona (y = 165) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring})`,
          opacity: Math.min(badgeSpring, 1),
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 24,
            background: 'rgba(245, 158, 11, 0.22)',
            border: '1.5px solid rgba(245, 158, 11, 0.65)',
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span style={{fontSize: 22}}>✨</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FDE68A',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>
      </div>

      {/* Painel Horizontal de Etapas Conectadas (y = 230 a 400) */}
      <div
        style={{
          position: 'absolute',
          top: 230,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `scale(${panelSpring * pulse}) translateY(${interpolate(
            panelSpring,
            [0, 1],
            [30, 0]
          )}px)`,
          opacity: Math.min(panelSpring, 1),
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: 960,
            padding: '18px 24px',
            borderRadius: 24,
            background: 'rgba(11, 15, 23, 0.94)',
            border: '2px solid rgba(245, 158, 11, 0.45)',
            boxShadow: '0 16px 36px rgba(0, 0, 0, 0.8)',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
          }}
        >
          {/* Linha das duas etapas conectadas */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
            }}
          >
            {/* Etapa 1: Página Pronta */}
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 18px',
                borderRadius: 16,
                background:
                  frame < 109
                    ? 'rgba(245, 158, 11, 0.22)'
                    : 'rgba(255, 255, 255, 0.08)',
                border:
                  frame < 109
                    ? '2px solid #F59E0B'
                    : '1px solid rgba(255, 255, 255, 0.15)',
                boxShadow:
                  frame < 109 ? '0 0 16px rgba(245, 158, 11, 0.35)' : 'none',
              }}
            >
              <span style={{fontSize: 32}}>🌐</span>
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: frame < 109 ? '#FDE68A' : '#FFFFFF',
                  lineHeight: 1.15,
                  textTransform: 'uppercase',
                }}
              >
                Página Pronta
              </div>
            </div>

            {/* Seta conectora */}
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: frame >= 109 ? '#F59E0B' : '#64748B',
                transition: 'color 0.2s ease',
              }}
            >
              ➔
            </div>

            {/* Etapa 2: Vídeo Demo */}
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 18px',
                borderRadius: 16,
                background:
                  frame >= 109
                    ? 'rgba(245, 158, 11, 0.25)'
                    : 'rgba(255, 255, 255, 0.05)',
                border:
                  frame >= 109
                    ? '2px solid #F59E0B'
                    : '1px solid rgba(255, 255, 255, 0.1)',
                boxShadow:
                  frame >= 109
                    ? '0 0 20px rgba(245, 158, 11, 0.45)'
                    : 'none',
                transform: `scale(${frame >= 109 ? step2Spring : 1})`,
              }}
            >
              <span style={{fontSize: 32}}>▶️</span>
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: frame >= 109 ? '#FDE68A' : '#94A3B8',
                  lineHeight: 1.15,
                  textTransform: 'uppercase',
                }}
              >
                Vídeo Demo
              </div>
            </div>
          </div>

          {/* Subtítulo dinâmico */}
          <div
            style={{
              textAlign: 'center',
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              color: frame >= 150 ? '#34D399' : '#CBD5E1',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 10,
              transform: `scale(${frame >= 150 ? summarySpring : 1})`,
            }}
          >
            <span>{frame >= 150 ? '✓' : '⚡'}</span>
            <span>
              {frame >= 150
                ? 'Apresenta o produto por você'
                : 'Solução completa e automatizada'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
