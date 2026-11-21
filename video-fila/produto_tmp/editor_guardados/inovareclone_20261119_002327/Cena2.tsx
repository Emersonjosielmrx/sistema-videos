import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES} from './constants';

interface Cena2Props {
  fontFamily: string;
}

export const Cena2: React.FC<Cena2Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no vídeo
  const videoScale = interpolate(frame, [0, 252], [1.02, 1.10], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada e saída
  const entryOpacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const exitOpacity = interpolate(frame, [242, 252], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Top Badge (entra frame 4)
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Título da Cena (entra frame 8)
  const titleSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card 1: Feito da sua própria pessoa (entra frame 15, ~0.5s)
  const card1Spring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Card 2: Posturas automáticas (entra frame 124, ~4.13s)
  const card2Spring = spring({
    frame: frame - 124,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Card 3: Fala em português (entra frame 174, ~5.8s)
  const card3Spring = spring({
    frame: frame - 174,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Onda de áudio animada para o Card 3
  const wave1 = 12 + Math.sin(frame * 0.4) * 8;
  const wave2 = 18 + Math.cos(frame * 0.5) * 10;
  const wave3 = 14 + Math.sin(frame * 0.6) * 9;
  const wave4 = 20 + Math.cos(frame * 0.45) * 11;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: CORES.fundoEscuro,
        opacity: entryOpacity * exitOpacity,
        fontFamily,
      }}
    >
      {/* Vídeo demonstrativo com zoom contínuo */}
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
        {/* Camada escura cinematográfica para leitura perfeita dos cards */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(15, 23, 42, 0.85) 0%, rgba(15, 23, 42, 0.72) 40%, rgba(15, 23, 42, 0.90) 100%)',
          }}
        />
      </div>

      {/* Conteúdo sobreposto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Badge da Etapa */}
        <div
          style={{
            marginTop: 170,
            opacity: interpolate(badgeSpring, [0, 1], [0, 1]),
            transform: `scale(${badgeSpring})`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 20px',
            borderRadius: 999,
            backgroundColor: 'rgba(15, 23, 42, 0.90)',
            border: `1.5px solid ${CORES.marcaClara}`,
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.5)',
          }}
        >
          <span style={{fontSize: 32}}>✨</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            02 • Como Funciona
          </span>
        </div>

        {/* Título da Seção */}
        <div
          style={{
            marginTop: 16,
            opacity: interpolate(titleSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(titleSpring, [0, 1], [20, 0])}px)`,
            fontSize: 44,
            fontWeight: 900,
            color: '#FFFFFF',
            textTransform: 'uppercase',
            textAlign: 'center',
            letterSpacing: '-0.5px',
            textShadow: '0 4px 15px rgba(0,0,0,0.8)',
          }}
        >
          Tecnologia Inovare Clone
        </div>

        {/* Pilares Tecnológicos (3 Cards sequenciais sincronizados à fala) */}
        <div
          style={{
            marginTop: 30,
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
            width: '100%',
            maxWidth: 920,
          }}
        >
          {/* Card 1: Da sua própria pessoa */}
          {frame >= 12 && (
            <div
              style={{
                opacity: interpolate(card1Spring, [0, 1], [0, 1]),
                transform: `translateX(${interpolate(card1Spring, [0, 1], [-40, 0])}px)`,
                backgroundColor: 'rgba(15, 23, 42, 0.90)',
                backdropFilter: 'blur(12px)',
                borderRadius: 20,
                padding: '18px 24px',
                border: '1.5px solid rgba(139, 92, 246, 0.5)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div
                  style={{
                    width: 58,
                    height: 58,
                    borderRadius: 14,
                    backgroundColor: 'rgba(139, 92, 246, 0.25)',
                    border: '1px solid #8B5CF6',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 34,
                  }}
                >
                  👤
                </div>
                <div>
                  <div
                    style={{
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                      textTransform: 'uppercase',
                    }}
                  >
                    Sua Própria Pessoa
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#CBD5E1',
                      marginTop: 2,
                    }}
                  >
                    Avatar criado a partir de você
                  </div>
                </div>
              </div>
              <div
                style={{
                  padding: '4px 14px',
                  borderRadius: 10,
                  backgroundColor: 'rgba(139, 92, 246, 0.3)',
                  border: '1px solid #8B5CF6',
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#C4B5FD',
                }}
              >
                Cem Por Cento Seu
              </div>
            </div>
          )}

          {/* Card 2: Posturas automáticas */}
          {frame >= 120 && (
            <div
              style={{
                opacity: interpolate(card2Spring, [0, 1], [0, 1]),
                transform: `translateX(${interpolate(card2Spring, [0, 1], [40, 0])}px)`,
                backgroundColor: 'rgba(15, 23, 42, 0.90)',
                backdropFilter: 'blur(12px)',
                borderRadius: 20,
                padding: '18px 24px',
                border: '1.5px solid rgba(139, 92, 246, 0.5)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div
                  style={{
                    width: 58,
                    height: 58,
                    borderRadius: 14,
                    backgroundColor: 'rgba(16, 185, 129, 0.25)',
                    border: '1px solid #10B981',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 34,
                  }}
                >
                  ⚡
                </div>
                <div>
                  <div
                    style={{
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                      textTransform: 'uppercase',
                    }}
                  >
                    Posturas Automáticas
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#CBD5E1',
                      marginTop: 2,
                    }}
                  >
                    Movimentos e gestos naturais
                  </div>
                </div>
              </div>
              <div
                style={{
                  padding: '4px 14px',
                  borderRadius: 10,
                  backgroundColor: 'rgba(16, 185, 129, 0.3)',
                  border: '1px solid #10B981',
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#6EE7B7',
                }}
              >
                ✓ Automático
              </div>
            </div>
          )}

          {/* Card 3: Fala em português */}
          {frame >= 170 && (
            <div
              style={{
                opacity: interpolate(card3Spring, [0, 1], [0, 1]),
                transform: `translateX(${interpolate(card3Spring, [0, 1], [-40, 0])}px)`,
                backgroundColor: 'rgba(15, 23, 42, 0.90)',
                backdropFilter: 'blur(12px)',
                borderRadius: 20,
                padding: '18px 24px',
                border: '1.5px solid rgba(139, 92, 246, 0.5)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div
                  style={{
                    width: 58,
                    height: 58,
                    borderRadius: 14,
                    backgroundColor: 'rgba(59, 130, 246, 0.25)',
                    border: '1px solid #3B82F6',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 34,
                  }}
                >
                  🎙️
                </div>
                <div>
                  <div
                    style={{
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                      textTransform: 'uppercase',
                    }}
                  >
                    Fala em Português
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#CBD5E1',
                      marginTop: 2,
                    }}
                  >
                    Entonação e sincronia labial
                  </div>
                </div>
              </div>
              {/* Indicador de onda de áudio ativa */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '6px 12px',
                  borderRadius: 10,
                  backgroundColor: 'rgba(59, 130, 246, 0.2)',
                  border: '1px solid #3B82F6',
                }}
              >
                <div
                  style={{
                    width: 4,
                    height: wave1,
                    backgroundColor: '#60A5FA',
                    borderRadius: 2,
                  }}
                />
                <div
                  style={{
                    width: 4,
                    height: wave2,
                    backgroundColor: '#60A5FA',
                    borderRadius: 2,
                  }}
                />
                <div
                  style={{
                    width: 4,
                    height: wave3,
                    backgroundColor: '#60A5FA',
                    borderRadius: 2,
                  }}
                />
                <div
                  style={{
                    width: 4,
                    height: wave4,
                    backgroundColor: '#60A5FA',
                    borderRadius: 2,
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
