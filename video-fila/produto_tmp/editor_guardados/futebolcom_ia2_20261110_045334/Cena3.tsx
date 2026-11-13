import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena3Props {
  fontFamily: string;
}

export const Cena3: React.FC<Cena3Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no vídeo de b-roll do pizzaiolo (1.0 -> 1.07)
  const videoScale = interpolate(frame, [0, 220], [1.0, 1.07], {
    extrapolateRight: 'clamp',
  });

  // Tag superior: "🚀 O RESULTADO"
  const tagSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Título fase 1: "CANAL QUE O CLIENTE JÁ CONHECE"
  const t1Spring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Título fase 2: "PEDIDO ORGANIZADO DIRETO NA TELA" (a partir do frame 85, ~2.8s)
  const isFase2 = frame >= 85;
  const t2Spring = spring({
    frame: frame - 85,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Entrada da Comanda Digital (Ticket de Pedido) logo após o título (frame 20)
  const ticketSpring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Animação dos checks dos itens dentro da comanda
  const check1Spring = spring({
    frame: frame - 55,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  const check2Spring = spring({
    frame: frame - 85,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  const statusSpring = spring({
    frame: frame - 115,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Movimento contínuo flutuante do card
  const cardFloatY = Math.sin(frame / 14) * 5;
  const shimmerPos = interpolate(frame % 90, [0, 90], [-100, 200]);

  return (
    <AbsoluteFill style={{backgroundColor: '#000000', overflow: 'hidden'}}>
      {/* Vídeo do Pizzaiolo em ação */}
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

      {/* Gradiente sutil para garantir leitura preservando as cores da cena */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(10, 2, 4, 0.72) 0%, rgba(10, 2, 4, 0.38) 45%, rgba(10, 2, 4, 0.75) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Rótulo superior: O Resultado (y=170) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          fontFamily,
          zIndex: 40,
        }}
      >
        <div
          style={{
            opacity: Math.max(0, tagSpring),
            transform: `translateY(${(1 - tagSpring) * -15}px)`,
            backgroundColor: 'rgba(225, 29, 72, 0.35)',
            border: '2px solid rgba(225, 29, 72, 0.85)',
            padding: '8px 28px',
            borderRadius: 999,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
          }}
        >
          <span style={{fontSize: 34}}>🚀</span>
          <span
            style={{
              color: '#FFFFFF',
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

      {/* Título Dinâmico Superior (y=240 a 380) */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          textAlign: 'center',
          fontFamily,
          zIndex: 40,
        }}
      >
        {!isFase2 ? (
          <div
            style={{
              opacity: Math.max(0, t1Spring),
              transform: `scale(${interpolate(t1Spring, [0, 1], [0.85, 1])}) translateY(${(1 - t1Spring) * 20}px)`,
              backgroundColor: 'rgba(15, 23, 42, 0.85)',
              border: '2px solid rgba(37, 211, 102, 0.7)',
              borderRadius: 22,
              padding: '16px 32px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              boxShadow: '0 8px 30px rgba(0,0,0,0.6)',
            }}
          >
            <span style={{fontSize: 42}}>💬</span>
            <span
              style={{
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: '-0.5px',
              }}
            >
              Canal que o cliente já conhece
            </span>
          </div>
        ) : (
          <div
            style={{
              opacity: Math.max(0, t2Spring),
              transform: `scale(${interpolate(t2Spring, [0, 1], [0.85, 1])}) translateY(${(1 - t2Spring) * 20}px)`,
              backgroundColor: 'rgba(225, 29, 72, 0.90)',
              borderRadius: 22,
              padding: '16px 32px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              boxShadow: '0 10px 35px rgba(225, 29, 72, 0.45)',
            }}
          >
            <span style={{fontSize: 42}}>📲</span>
            <span
              style={{
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: '-0.5px',
              }}
            >
              Pedido organizado direto na tela
            </span>
          </div>
        )}
      </div>

      {/* Comanda Digital / Ticket de Pedido Inteligente (y=430 a 1300) */}
      {frame >= 20 && (
        <div
          style={{
            position: 'absolute',
            top: 430,
            left: 80,
            right: 80,
            opacity: Math.max(0, ticketSpring),
            transform: `translateY(${(1 - ticketSpring) * 80 + cardFloatY}px) scale(${interpolate(ticketSpring, [0, 1], [0.9, 1])})`,
            backgroundColor: 'rgba(15, 20, 28, 0.94)',
            border: '3px solid #22C55E',
            borderRadius: 36,
            padding: '36px 36px',
            boxShadow:
              '0 25px 60px rgba(0,0,0,0.85), 0 0 40px rgba(34, 197, 94, 0.25)',
            fontFamily,
            zIndex: 35,
            overflow: 'hidden',
          }}
        >
          {/* Shimmer sweep effect */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: `${shimmerPos}%`,
              width: '60%',
              height: '100%',
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.08) 50%, transparent 100%)',
              transform: 'skewX(-25deg)',
              pointerEvents: 'none',
            }}
          />

          {/* Header da Comanda */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid rgba(255,255,255,0.12)',
              paddingBottom: 22,
              marginBottom: 24,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 42}}>📋</span>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontSize: 38,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    letterSpacing: 0.5,
                  }}
                >
                  PEDIDO #1042
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#94A3B8',
                  }}
                >
                  Recebido via WhatsApp
                </span>
              </div>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(34, 197, 94, 0.2)',
                border: '2px solid #22C55E',
                padding: '6px 18px',
                borderRadius: 999,
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#22C55E',
                  textTransform: 'uppercase',
                }}
              >
                Organizado
              </span>
            </div>
          </div>

          {/* Item Principal */}
          <div style={{marginBottom: 24}}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 12,
              }}
            >
              <span
                style={{
                  fontSize: 42,
                  fontWeight: 800,
                  color: '#FACC15',
                }}
              >
                1x Pizza Grande Meio a Meio
              </span>
            </div>

            {/* Sabores detalhados com checkmarks animados */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 14,
                paddingLeft: 16,
              }}
            >
              {frame >= 105 && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    opacity: Math.max(0, check1Spring),
                    transform: `translateX(${(1 - check1Spring) * -20}px)`,
                  }}
                >
                  <span
                    style={{fontSize: 34, color: '#22C55E', fontWeight: 900}}
                  >
                    ✓
                  </span>
                  <span
                    style={{
                      fontSize: 36,
                      fontWeight: 700,
                      color: '#E2E8F0',
                    }}
                  >
                    1/2 Frango com Catupiry
                  </span>
                </div>
              )}

              {frame >= 125 && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    opacity: Math.max(0, check2Spring),
                    transform: `translateX(${(1 - check2Spring) * -20}px)`,
                  }}
                >
                  <span
                    style={{fontSize: 34, color: '#22C55E', fontWeight: 900}}
                  >
                    ✓
                  </span>
                  <span
                    style={{
                      fontSize: 36,
                      fontWeight: 700,
                      color: '#E2E8F0',
                    }}
                  >
                    1/2 Calabresa
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Barra de Status Inferior da Comanda */}
          {frame >= 145 && (
            <div
              style={{
                opacity: Math.max(0, statusSpring),
                transform: `scale(${interpolate(statusSpring, [0, 1], [0.95, 1])})`,
                backgroundColor: 'rgba(34, 197, 94, 0.15)',
                border: '2px dashed rgba(34, 197, 94, 0.5)',
                borderRadius: 20,
                padding: '16px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: 14,
              }}
            >
              <span style={{fontSize: 34}}>⚡</span>
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#86EFAC',
                }}
              >
                Atendimento automático pela IA • Pronto para a cozinha
              </span>
            </div>
          )}
        </div>
      )}
    </AbsoluteFill>
  );
};
