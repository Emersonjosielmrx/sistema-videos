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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera sobre a foto de fundo
  const bgScale = interpolate(frame, [0, 210], [1.06, 1.18], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(frame, [0, 210], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Entrada do selo inicial aos 0.15s (frame 5)
  const badgeSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Beat 1: "MEU NEGÓCIO É PEQUENO" (~0.3s a 1.6s / frames 9 a 48)
  const beat1Spring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 12, stiffness: 90},
  });

  // Beat 2: "CRM COM IA" (~1.7s a 3.7s / frames 52 a 110)
  const beat2Spring = spring({
    frame: frame - 52,
    fps,
    config: {damping: 12, stiffness: 95},
  });

  // Beat 3: "NÃO VAI SER COMPLICADO DEMAIS?" (~3.8s a 5.5s / frames 114 a 180)
  const beat3Spring = spring({
    frame: frame - 114,
    fps,
    config: {damping: 11, stiffness: 100},
  });

  const floatY = Math.sin(frame / 14) * 5;

  // Desmonte fluido antes da transição para o Dono
  const exitOpacity = interpolate(frame, [185, 207], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#111827',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Foto viva com push-in contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(${bgY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu escuro em gradiente suave para contraste absoluto */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(17, 24, 39, 0.90) 0%, rgba(17, 24, 39, 0.65) 45%, rgba(17, 24, 39, 0.92) 100%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: exitOpacity,
        }}
      >
        {/* Topo Informativo (y=195 — respiro de 45px abaixo da barra em y=150) */}
        <div
          style={{
            position: 'absolute',
            top: 195,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            transform: `scale(${Math.max(0, badgeSpring)})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 26px',
              borderRadius: 30,
              background: 'rgba(31, 147, 255, 0.22)',
              border: '2px solid rgba(31, 147, 255, 0.55)',
              backdropFilter: 'blur(12px)',
              boxShadow: '0 8px 24px rgba(31, 147, 255, 0.25)',
            }}
          >
            <span style={{fontSize: 32}}>💡</span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#93C5FD',
                textTransform: 'uppercase',
                letterSpacing: 1.1,
              }}
            >
              Dúvida Frequente
            </span>
          </div>
        </div>

        {/* Título Cinético Sincronizado com os Momentos Exatos da Fala (y=280..520) */}
        <div
          style={{
            position: 'absolute',
            top: 290,
            left: 60,
            right: 60,
            textAlign: 'center',
            transform: `translateY(${floatY}px)`,
          }}
        >
          {/* Beat 1: Meu negócio é pequeno (0 a 50 frames) */}
          {frame < 52 && (
            <div
              style={{
                transform: `scale(${Math.max(0, beat1Spring)})`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 12,
              }}
            >
              <div
                style={{
                  fontSize: 52,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.2,
                  textShadow: '0 4px 18px rgba(0, 0, 0, 0.9)',
                }}
              >
                MEU NEGÓCIO É
              </div>
              <div
                style={{
                  display: 'inline-block',
                  background: '#1F93FF',
                  color: '#FFFFFF',
                  padding: '8px 24px',
                  borderRadius: 16,
                  fontSize: 56,
                  fontWeight: 900,
                  textTransform: 'uppercase',
                  boxShadow: '0 10px 28px rgba(31, 147, 255, 0.5)',
                }}
              >
                PEQUENO
              </div>
            </div>
          )}

          {/* Beat 2: CRM com inteligência artificial (52 a 112 frames) */}
          {frame >= 52 && frame < 114 && (
            <div
              style={{
                transform: `scale(${Math.max(0, beat2Spring)})`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 12,
              }}
            >
              <div
                style={{
                  fontSize: 50,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.2,
                  textShadow: '0 4px 18px rgba(0, 0, 0, 0.9)',
                }}
              >
                UM CRM COM
              </div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 12,
                  background: 'rgba(31, 147, 255, 0.25)',
                  border: '2px solid #1F93FF',
                  color: '#60A5FA',
                  padding: '8px 26px',
                  borderRadius: 16,
                  fontSize: 52,
                  fontWeight: 900,
                  textTransform: 'uppercase',
                  boxShadow: '0 10px 30px rgba(31, 147, 255, 0.35)',
                  backdropFilter: 'blur(10px)',
                }}
              >
                <span>🤖</span>
                <span>INTELIGÊNCIA ARTIFICIAL</span>
              </div>
            </div>
          )}

          {/* Beat 3: Não vai ser complicado demais? (114 a 185 frames) */}
          {frame >= 114 && (
            <div
              style={{
                transform: `scale(${Math.max(0, beat3Spring)})`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 14,
              }}
            >
              <div
                style={{
                  fontSize: 48,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.2,
                  textShadow: '0 4px 18px rgba(0, 0, 0, 0.9)',
                }}
              >
                NÃO VAI SER...
              </div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 12,
                  background: 'rgba(239, 68, 68, 0.22)',
                  border: '2.5px solid #EF4444',
                  color: '#FCA5A5',
                  padding: '10px 28px',
                  borderRadius: 18,
                  fontSize: 48,
                  fontWeight: 900,
                  textTransform: 'uppercase',
                  boxShadow: '0 12px 32px rgba(239, 68, 68, 0.4)',
                  backdropFilter: 'blur(10px)',
                }}
              >
                <span>⚠️</span>
                <span>COMPLICADO DEMAIS?</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
