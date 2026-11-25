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

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Transições de borda (fade-in inicial de 10 frames)
  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Zoom contínuo no vídeo do dono (1.00 -> 1.06)
  const zoom = interpolate(frame, [0, 246], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Badge superior aos ~0.3s (frame 10)
  const badgeSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card 1: entra aos ~0.8s (frame 25 - "Agora o cliente já chega...")
  const card1Spring = spring({
    frame: frame - 25,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Saída do Card 1 aos ~3.6s (frame 108)
  const card1Exit = interpolate(frame, [105, 112], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Card 2 (Comparativo Antes x Depois): entra aos ~3.8s (frame 112 - "e eu uso meu tempo...")
  const compareSpring = spring({
    frame: frame - 112,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Destaque explosivo na palavra 'Vender' aos ~5.6s (frame 168)
  const sellSpring = spring({
    frame: frame - 168,
    fps,
    config: {damping: 10, stiffness: 150},
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
        src={staticFile('dono_3.mp4')}
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

      {/* Badge Superior: O Resultado (y = 165) */}
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
            background: 'rgba(16, 185, 129, 0.22)',
            border: '1.5px solid rgba(16, 185, 129, 0.65)',
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span style={{fontSize: 22}}>📈</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#6EE7B7',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            O Resultado
          </span>
        </div>
      </div>

      {/* Fase 1: Cliente já chega entendendo (frames 25 a 110) (y = 230 a 390) */}
      {frame < 114 && (
        <div
          style={{
            position: 'absolute',
            top: 230,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            transform: `scale(${card1Spring * pulse}) translateY(${interpolate(
              card1Spring,
              [0, 1],
              [30, 0]
            )}px)`,
            opacity: Math.min(card1Spring, 1) * card1Exit,
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: 960,
              padding: '18px 28px',
              borderRadius: 24,
              background: 'rgba(11, 15, 23, 0.94)',
              border: '2px solid rgba(16, 185, 129, 0.4)',
              boxShadow: '0 16px 36px rgba(0, 0, 0, 0.8)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#FFFFFF',
                textAlign: 'center',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              Cliente Já Chega Entendendo
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                color: '#6EE7B7',
                fontFamily,
                fontSize: 32,
                fontWeight: 600,
              }}
            >
              <span>✓</span>
              <span>Processo claro e direto ao ponto</span>
            </div>
          </div>
        </div>
      )}

      {/* Fase 2: Comparativo Antes x Depois (frames 112 a 246) (y = 230 a 400) */}
      {frame >= 110 && (
        <div
          style={{
            position: 'absolute',
            top: 230,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            transform: `scale(${compareSpring * pulse}) translateY(${interpolate(
              compareSpring,
              [0, 1],
              [30, 0]
            )}px)`,
            opacity: Math.min(compareSpring, 1),
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: 960,
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            {/* Antes: Menos Explicar */}
            <div
              style={{
                flex: 1,
                padding: '18px 20px',
                borderRadius: 20,
                background: 'rgba(239, 68, 68, 0.14)',
                border: '1.5px solid rgba(239, 68, 68, 0.35)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#EF4444',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                Antes
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#F87171',
                  textAlign: 'center',
                  textTransform: 'uppercase',
                  textDecoration: frame >= 168 ? 'line-through' : 'none',
                  opacity: frame >= 168 ? 0.7 : 1,
                }}
              >
                ❌ Explicar
              </div>
            </div>

            {/* Depois: Mais Vender */}
            <div
              style={{
                flex: 1.15,
                padding: '18px 20px',
                borderRadius: 20,
                background:
                  frame >= 168
                    ? 'rgba(16, 185, 129, 0.28)'
                    : 'rgba(16, 185, 129, 0.16)',
                border:
                  frame >= 168
                    ? '2.5px solid #10B981'
                    : '1.5px solid rgba(16, 185, 129, 0.5)',
                boxShadow:
                  frame >= 168
                    ? '0 0 25px rgba(16, 185, 129, 0.5)'
                    : 'none',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 6,
                transform: `scale(${frame >= 168 ? sellSpring : 1})`,
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#34D399',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                Agora
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textAlign: 'center',
                  textTransform: 'uppercase',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span>✅</span>
                <span
                  style={{
                    color: '#FDE68A',
                    textShadow: '0 0 16px rgba(245, 158, 11, 0.8)',
                  }}
                >
                  Vender!
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
