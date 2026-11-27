import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Câmera dinâmica contínua: plano médio (cintura para cima) com zoom lento Ken Burns
  const scale = interpolate(frame, [0, 215], [1.85, 2.02], {
    extrapolateRight: 'clamp',
  });
  const panX = interpolate(frame, [0, 215], [-15, 15], {
    extrapolateRight: 'clamp',
  });
  const panY = interpolate(frame, [0, 215], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada e saída
  const opacity = interpolate(frame, [0, 10, 200, 215], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Molas dos estágios de benefício sincronizados com a fala (stagger)
  const spring1 = spring({
    frame: frame - 15,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 130},
  });

  const spring2 = spring({
    frame: frame - 72,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 130},
  });

  const spring3 = spring({
    frame: frame - 125,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 130},
  });

  // Micro-interação contínua
  const floatY = Math.sin(frame * 0.12) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0F172A',
        opacity,
      }}
    >
      {/* Imagem do profissional reenquadrada em Plano Médio com slow zoom Ken Burns */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${scale}) translateX(${panX}px) translateY(${panY}px)`,
          transformOrigin: '48% 28%',
        }}
      >
        <Img
          src={staticFile('img_3.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Escurecimento restrito ao topo seguro para preservar o apresentador e o cenário */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 420,
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.92) 0%, rgba(15,23,42,0.75) 70%, rgba(15,23,42,0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Safe Zone container: restrito estritamente à faixa superior y=165 a 440 para não cobrir o rosto */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Rótulo superior */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 999,
            backgroundColor: 'rgba(31, 41, 55, 0.95)',
            border: '1.5px solid rgba(245, 158, 11, 0.6)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#F59E0B',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            ✓ O RESULTADO
          </span>
        </div>

        {/* Cartões em Cascata (Stagger) com Entrada Escalonada e Checks Pulsantes */}
        <div
          style={{
            marginTop: 18,
            width: 880,
            maxWidth: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            alignItems: 'center',
            transform: `translateY(${floatY}px)`,
          }}
        >
          {/* Card 1: Entra aos ~19.3s (frame 12) */}
          {frame >= 12 && (
            <div
              style={{
                width: '100%',
                transform: `translateX(${interpolate(
                  spring1,
                  [0, 1],
                  [-30, 0]
                )}px) scale(${interpolate(spring1, [0, 1], [0.95, 1])})`,
                opacity: interpolate(spring1, [0, 0.4, 1], [0, 1, 1]),
                padding: '12px 24px',
                borderRadius: 16,
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid rgba(245, 158, 11, 0.7)',
                boxShadow: '0 8px 25px rgba(0,0,0,0.6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <span style={{fontSize: 34}}>🌙</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Agendamentos Automáticos 24h
                </span>
              </div>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  backgroundColor: '#10B981',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontWeight: 900,
                  fontSize: 20,
                  boxShadow: `0 0 ${8 * (Math.sin(frame * 0.2) * 0.4 + 0.6)}px #10B981`,
                }}
              >
                ✓
              </div>
            </div>
          )}

          {/* Card 2: Entra aos ~21.2s (frame 70) */}
          {frame >= 70 && (
            <div
              style={{
                width: '100%',
                transform: `translateX(${interpolate(
                  spring2,
                  [0, 1],
                  [30, 0]
                )}px) scale(${interpolate(spring2, [0, 1], [0.95, 1])})`,
                opacity: interpolate(spring2, [0, 0.4, 1], [0, 1, 1]),
                padding: '12px 24px',
                borderRadius: 16,
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid rgba(56, 189, 248, 0.7)',
                boxShadow: '0 8px 25px rgba(0,0,0,0.6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <span style={{fontSize: 34}}>📅</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 800,
                    color: '#F8FAFC',
                  }}
                >
                  Sem Conflito e Sem Duplo Agendamento
                </span>
              </div>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  backgroundColor: '#38BDF8',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#0F172A',
                  fontWeight: 900,
                  fontSize: 20,
                  boxShadow: `0 0 ${8 * (Math.sin(frame * 0.2 + 1) * 0.4 + 0.6)}px #38BDF8`,
                }}
              >
                ✓
              </div>
            </div>
          )}

          {/* Card 3: Entra aos ~23.0s (frame 125) */}
          {frame >= 125 && (
            <div
              style={{
                width: '100%',
                transform: `translateX(${interpolate(
                  spring3,
                  [0, 1],
                  [-30, 0]
                )}px) scale(${interpolate(spring3, [0, 1], [0.95, 1])})`,
                opacity: interpolate(spring3, [0, 0.4, 1], [0, 1, 1]),
                padding: '12px 24px',
                borderRadius: 16,
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid rgba(16, 185, 129, 0.7)',
                boxShadow: '0 8px 25px rgba(0,0,0,0.6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <span style={{fontSize: 34}}>✨</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 800,
                    color: '#F8FAFC',
                  }}
                >
                  IA Agenda Direto no WhatsApp
                </span>
              </div>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  backgroundColor: '#10B981',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontWeight: 900,
                  fontSize: 20,
                  boxShadow: `0 0 ${8 * (Math.sin(frame * 0.2 + 2) * 0.4 + 0.6)}px #10B981`,
                }}
              >
                ✓
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
