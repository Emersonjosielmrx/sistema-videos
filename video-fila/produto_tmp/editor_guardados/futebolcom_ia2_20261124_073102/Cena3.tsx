import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
} from 'remotion';
import {COLORS, SAFE_ZONE} from './types';

interface Cena3Props {
  fontFamily: string;
}

export const Cena3: React.FC<Cena3Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo (zoom leve e cinematográfico no vídeo 1.00 -> 1.08)
  const videoScale = interpolate(frame, [0, 234], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Micro-dinâmica residual
  const floatY = Math.sin(frame / 15) * 5;

  // Entrada do rótulo e título
  const rotuloSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const titleSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Checklist dos 3 passos sincronizados com a locução:
  // Passo 1: "pelas fotos" (~21.78s -> frame 49 na cena)
  const step1Spring = spring({
    frame: frame - 48,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Passo 2: "pelo WhatsApp" (~23.16s -> frame 90 na cena)
  const step2Spring = spring({
    frame: frame - 90,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Passo 3: "não perde venda" (~24.72s -> frame 137 na cena)
  const step3Spring = spring({
    frame: frame - 137,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Transições de corte suave
  const enterOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const exitOpacity = interpolate(frame, [222, 234], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#000000',
        fontFamily,
        opacity: Math.min(enterOpacity, exitOpacity),
      }}
    >
      {/* Vídeo Comercial Real em Tela Cheia com Zoom Cinematográfico */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('video_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu protetor moderado no topo e base (preserva os atores no centro límpidos e vivos - Regra 23) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(20,3,7,0.78) 0%, rgba(20,3,7,0.55) 24%, rgba(20,3,7,0.05) 50%, rgba(10,1,3,0.65) 85%, rgba(10,1,3,0.90) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* 1. Rótulo Obrigatório da Cena (y=175) */}
      {frame >= 4 && (
        <div
          style={{
            position: 'absolute',
            top: 175,
            left: SAFE_ZONE.left,
            right: SAFE_ZONE.left,
            display: 'flex',
            justifyContent: 'center',
            opacity: Math.min(rotuloSpring, 1),
            transform: `scale(${Math.max(0.7, rotuloSpring)})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 26px',
              borderRadius: 999,
              backgroundColor: 'rgba(20, 4, 10, 0.94)',
              border: `2px solid ${COLORS.primary}`,
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
            }}
          >
            <span style={{fontSize: 26}}>🚀</span>
            <span
              style={{
                color: COLORS.white,
                fontSize: 34,
                fontWeight: 800,
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              O Resultado
            </span>
          </div>
        </div>
      )}

      {/* 2. Título Superior com Box Protetor Opaco (y=255) - Regras 5 e 6 */}
      {frame >= 12 && (
        <div
          style={{
            position: 'absolute',
            top: 255,
            left: SAFE_ZONE.left,
            right: SAFE_ZONE.left,
            display: 'flex',
            justifyContent: 'center',
            opacity: Math.min(titleSpring, 1),
            transform: `translateY(${interpolate(titleSpring, [0, 1], [25, 0])}px)`,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(20, 4, 10, 0.94)',
              padding: '12px 32px',
              borderRadius: 22,
              border: '2px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 12px 32px rgba(0,0,0,0.85)',
              textAlign: 'center',
            }}
          >
            <h2
              style={{
                margin: 0,
                fontSize: 48,
                fontWeight: 900,
                color: COLORS.white,
                lineHeight: 1.15,
                textTransform: 'uppercase',
                letterSpacing: -0.5,
              }}
            >
              Sua loja{' '}
              <span
                style={{
                  color: COLORS.accent,
                  backgroundColor: 'rgba(250, 204, 21, 0.16)',
                  padding: '2px 12px',
                  borderRadius: 10,
                  border: '1.5px solid rgba(250, 204, 21, 0.4)',
                }}
              >
                não perde venda
              </span>
            </h2>
          </div>
        </div>
      )}

      {/* 3. CHECKLIST DINÂMICO DOS 3 PASSOS SINCRONIZADOS (y=360 a y=530) */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: SAFE_ZONE.left,
          right: SAFE_ZONE.left,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* Passo 1: Fotos */}
        {frame >= 48 && (
          <div
            style={{
              opacity: Math.min(step1Spring, 1),
              transform: `translateX(${interpolate(step1Spring, [0, 1], [-40, 0])}px)`,
              backgroundColor: 'rgba(20, 4, 10, 0.94)',
              borderRadius: 20,
              padding: '14px 22px',
              border: `2px solid ${COLORS.accent}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: '50%',
                backgroundColor: 'rgba(16, 185, 129, 0.3)',
                border: '2px solid #10B981',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#10B981',
                fontWeight: 900,
                fontSize: 24,
              }}
            >
              ✓
            </div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: COLORS.white,
              }}
            >
              1. Cliente escolhe pelas fotos 📸
            </div>
          </div>
        )}

        {/* Passo 2: WhatsApp */}
        {frame >= 90 && (
          <div
            style={{
              opacity: Math.min(step2Spring, 1),
              transform: `translateX(${interpolate(step2Spring, [0, 1], [-40, 0])}px)`,
              backgroundColor: 'rgba(20, 4, 10, 0.94)',
              borderRadius: 20,
              padding: '14px 22px',
              border: `2px solid ${COLORS.primary}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: '50%',
                backgroundColor: 'rgba(16, 185, 129, 0.3)',
                border: '2px solid #10B981',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#10B981',
                fontWeight: 900,
                fontSize: 24,
              }}
            >
              ✓
            </div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: COLORS.white,
              }}
            >
              2. Faz o pedido pelo WhatsApp 💬
            </div>
          </div>
        )}

        {/* Passo 3: Venda Garantida / Sem barreira */}
        {frame >= 137 && (
          <div
            style={{
              opacity: Math.min(step3Spring, 1),
              transform: `translateX(${interpolate(step3Spring, [0, 1], [-40, 0])}px)`,
              backgroundColor: 'rgba(20, 4, 10, 0.94)',
              borderRadius: 20,
              padding: '14px 22px',
              border: `2px solid ${COLORS.success}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: '50%',
                backgroundColor: 'rgba(16, 185, 129, 0.3)',
                border: '2px solid #10B981',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#10B981',
                fontWeight: 900,
                fontSize: 24,
              }}
            >
              ✓
            </div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: COLORS.white,
              }}
            >
              3. Sua loja não perde vendas 🚀
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
