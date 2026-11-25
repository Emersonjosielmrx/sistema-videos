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

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Transições de borda (fade-in inicial de 10 frames)
  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Zoom contínuo no vídeo do dono (1.00 -> 1.06)
  const zoom = interpolate(frame, [0, 245], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Badge superior aos ~0.3s (frame 10)
  const badgeSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card 1: entra aos ~0.8s (frame 25 - "Eu passava o dia...")
  const card1Spring = spring({
    frame: frame - 25,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Saída suave do Card 1 aos ~4.8s (frame 145)
  const card1Exit = interpolate(frame, [142, 150], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Card 2: entra aos ~5.1s (frame 154 - "explicando meu produto...")
  const card2Spring = spring({
    frame: frame - 154,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Sequência '1 por 1'
  const tag1Spring = spring({
    frame: frame - 232, // 'um'
    fps,
    config: {damping: 10, stiffness: 160},
  });
  const tagPorSpring = spring({
    frame: frame - 237, // 'por'
    fps,
    config: {damping: 10, stiffness: 160},
  });
  const tag2Spring = spring({
    frame: frame - 240, // 'um.'
    fps,
    config: {damping: 10, stiffness: 160},
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
        src={staticFile('dono_1.mp4')}
        muted
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${zoom})`,
        }}
      />

      {/* Véu superior sutil para proteger os textos no alto (y: 120 a 440) */}
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

      {/* Elementos no Alto (y: 160 a 410) - Rosto do apresentador totalmente livre */}

      {/* Badge Superior: O Problema (y = 165) */}
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
            background: 'rgba(239, 68, 68, 0.22)',
            border: '1.5px solid rgba(239, 68, 68, 0.6)',
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span style={{fontSize: 22}}>🚨</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FCA5A5',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            O Problema Real
          </span>
        </div>
      </div>

      {/* Card 1: Respondendo as mesmas dúvidas (frames 25 a 150) (y = 230 a 390) */}
      {frame < 152 && (
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
              border: '2px solid rgba(245, 158, 11, 0.35)',
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
              Respondendo As Mesmas Dúvidas
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                color: '#CBD5E1',
                fontFamily,
                fontSize: 32,
                fontWeight: 600,
              }}
            >
              <span>💬</span>
              <span>Mensagens repetitivas no WhatsApp</span>
            </div>
          </div>
        </div>
      )}

      {/* Card 2: Explicando o produto um por um (frames 150 a 245) (y = 230 a 400) */}
      {frame >= 148 && (
        <div
          style={{
            position: 'absolute',
            top: 230,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            transform: `scale(${card2Spring * pulse}) translateY(${interpolate(
              card2Spring,
              [0, 1],
              [30, 0]
            )}px)`,
            opacity: Math.min(card2Spring, 1),
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: 960,
              padding: '16px 28px',
              borderRadius: 24,
              background: 'rgba(11, 15, 23, 0.94)',
              border: '2px solid rgba(239, 68, 68, 0.45)',
              boxShadow: '0 16px 36px rgba(0, 0, 0, 0.8)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 12,
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
              Explicando Meu Produto
            </div>

            {/* Linha com os tags 1 por 1 animados */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
              }}
            >
              {/* Tag 1 */}
              <div
                style={{
                  padding: '8px 24px',
                  borderRadius: 14,
                  background: frame >= 232 ? '#F59E0B' : 'rgba(255,255,255,0.18)',
                  color: frame >= 232 ? '#121216' : '#FFFFFF',
                  border:
                    frame >= 232
                      ? '2px solid #F59E0B'
                      : '1.5px solid rgba(255,255,255,0.4)',
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  transform: `scale(${frame >= 232 ? tag1Spring : 1})`,
                  boxShadow:
                    frame >= 232
                      ? '0 4px 20px rgba(245, 158, 11, 0.7)'
                      : 'none',
                }}
              >
                1
              </div>

              {/* Tag POR */}
              <div
                style={{
                  padding: '8px 20px',
                  borderRadius: 14,
                  background:
                    frame >= 237
                      ? 'rgba(245, 158, 11, 0.3)'
                      : 'rgba(255,255,255,0.12)',
                  color: '#FFFFFF',
                  border:
                    frame >= 237
                      ? '2px solid #F59E0B'
                      : '1.5px solid rgba(255,255,255,0.3)',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  transform: `scale(${frame >= 237 ? tagPorSpring : 1})`,
                }}
              >
                POR
              </div>

              {/* Tag 1 final */}
              <div
                style={{
                  padding: '8px 24px',
                  borderRadius: 14,
                  background: frame >= 240 ? '#F59E0B' : 'rgba(255,255,255,0.18)',
                  color: frame >= 240 ? '#121216' : '#FFFFFF',
                  border:
                    frame >= 240
                      ? '2px solid #F59E0B'
                      : '1.5px solid rgba(255,255,255,0.4)',
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  transform: `scale(${frame >= 240 ? tag2Spring : 1})`,
                  boxShadow:
                    frame >= 240
                      ? '0 4px 20px rgba(245, 158, 11, 0.7)'
                      : 'none',
                }}
              >
                1
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
