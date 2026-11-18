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

  // Punch-in digital de 1.15x centralizado no apresentador para quebrar a monotonia de plano
  const videoScale = interpolate(frame, [0, 245], [1.14, 1.18], {
    extrapolateRight: 'clamp',
  });
  // Elevação do enquadramento para manter rosto, boca e barba 100% livres e visíveis
  const videoTranslateY = interpolate(frame, [0, 245], [-145, -155], {
    extrapolateRight: 'clamp',
  });

  // Transição no frame 95 (~15.5s, quando começa "a Agenda IA reagenda meu cliente sozinha direto pelo WhatsApp")
  const isFase2 = frame >= 95;

  const entradaFase1 = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  const entradaFase2 = spring({
    frame: Math.max(0, frame - 95),
    fps,
    config: {damping: 13, mass: 0.75},
  });

  // Mockup animado de smartphone deslizando com spring pela base a partir do frame 95
  const phoneSlide = spring({
    frame: Math.max(0, frame - 95),
    fps,
    config: {damping: 14, mass: 0.85},
  });

  // Balão 1 (Cliente pedindo troca) — entra no frame 105
  const b1Spring = spring({
    frame: Math.max(0, frame - 105),
    fps,
    config: {damping: 13, mass: 0.7},
  });

  // Balão 2 (Agenda IA reagendando sozinha) — entra no frame 135
  const b2Spring = spring({
    frame: Math.max(0, frame - 135),
    fps,
    config: {damping: 12, mass: 0.7},
  });

  // Selo de confirmação — entra no frame 165
  const confirmSpring = spring({
    frame: Math.max(0, frame - 165),
    fps,
    config: {damping: 12, mass: 0.65},
  });

  const pulsoGlow = 1 + Math.sin(frame / 8) * 0.016;
  const phoneFloat = isFase2 ? Math.sin((frame - 95) / 10) * 4 : 0;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0F172A',
      }}
    >
      {/* Vídeo do Dono com Punch-In Digital (1.14x -> 1.19x) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: '50% 25%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_2.mp4')}
          muted
          style={{
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
          }}
        />
        {/* Vinheta superior e inferior suaves para contraste sem cobrir o rosto */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 360,
            background:
              'linear-gradient(180deg, rgba(15, 23, 42, 0.85) 0%, rgba(15, 23, 42, 0.38) 65%, rgba(15, 23, 42, 0) 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Topo Informativo Unificado (y=168 a 295) — Rosto 100% livre no centro */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {!isFase2 ? (
          <div
            style={{
              width: '100%',
              padding: '14px 22px',
              borderRadius: 20,
              backgroundColor: 'rgba(20, 24, 33, 0.92)',
              border: '1.5px solid rgba(255, 169, 77, 0.45)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.55)',
              opacity: interpolate(entradaFase1, [0, 1], [0.9, 1]),
              transform: `translateY(${interpolate(entradaFase1, [0, 1], [-15, 0])}px)`,
              display: 'flex',
              flexDirection: 'column',
              gap: 6,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#FFA94D',
                    boxShadow: '0 0 8px #FFA94D',
                  }}
                />
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FFA94D',
                    textTransform: 'uppercase',
                    letterSpacing: 1.2,
                  }}
                >
                  Como Funciona
                </span>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#CBD5E1',
                }}
              >
                Fora do expediente
              </span>
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 42,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.15,
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              Cliente pede reagendamento à noite
            </div>
          </div>
        ) : (
          <div
            style={{
              width: '100%',
              padding: '14px 22px',
              borderRadius: 20,
              backgroundColor: 'rgba(20, 24, 33, 0.94)',
              border: '2px solid #FFA94D',
              boxShadow: '0 8px 28px rgba(255, 169, 77, 0.35)',
              transform: `translateY(${interpolate(entradaFase2, [0, 1], [14, 0])}px) scale(${pulsoGlow})`,
              display: 'flex',
              flexDirection: 'column',
              gap: 6,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#10B981',
                    boxShadow: '0 0 8px #10B981',
                  }}
                />
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FFA94D',
                    textTransform: 'uppercase',
                    letterSpacing: 1.2,
                  }}
                >
                  Como Funciona • IA Ativa
                </span>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#22C55E',
                }}
              >
                Direto no WhatsApp
              </span>
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 42,
                fontWeight: 900,
                color: '#FFA94D',
                lineHeight: 1.15,
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              Agenda IA reagenda sozinha no WhatsApp
            </div>
          </div>
        )}
      </div>

      {/* Mockup Animado de Smartphone com WhatsApp em Tempo Real — Entra aos 15.5s (frame 95) na base livre */}
      {isFase2 && (
        <div
          style={{
            position: 'absolute',
            top: 1090,
            left: 60,
            right: 60,
            transform: `translateY(${interpolate(phoneSlide, [0, 1], [450, 0]) + phoneFloat}px)`,
            opacity: interpolate(phoneSlide, [0, 0.2, 1], [0, 1, 1]),
            zIndex: 40,
          }}
        >
        <div
          style={{
            borderRadius: 28,
            backgroundColor: 'rgba(15, 23, 42, 0.96)',
            border: '2.5px solid #FFA94D',
            boxShadow:
              '0 20px 50px rgba(0, 0, 0, 0.8), 0 0 28px rgba(255, 169, 77, 0.28)',
            padding: '16px 22px',
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
          }}
        >
          {/* Cabeçalho do Mockup do Celular */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid rgba(255, 255, 255, 0.14)',
              paddingBottom: 8,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <div
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: '50%',
                  backgroundColor: '#22C55E',
                  boxShadow: '0 0 10px #22C55E',
                }}
              />
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                WhatsApp • Agenda IA
              </span>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#FFA94D',
              }}
            >
              Simulação
            </span>
          </div>

          {/* Balão do Cliente (Imprevisto à noite) */}
          <div
            style={{
              alignSelf: 'flex-start',
              maxWidth: '92%',
              padding: '10px 18px',
              borderRadius: '18px 18px 18px 4px',
              backgroundColor: '#1E293B',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              transform: `scale(${interpolate(b1Spring, [0, 1], [0.9, 1])})`,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 600,
                color: '#F8FAFC',
                lineHeight: 1.2,
              }}
            >
              Cliente: Tive um imprevisto hoje, consigo reagendar?
            </span>
          </div>

          {/* Balão da Agenda IA (Reagendando sozinha) */}
          <div
            style={{
              alignSelf: 'flex-end',
              maxWidth: '94%',
              padding: '12px 18px',
              borderRadius: '18px 18px 4px 18px',
              backgroundColor: isFase2 ? '#065F46' : 'rgba(30, 41, 59, 0.85)',
              border: isFase2
                ? '2px solid #10B981'
                : '1.5px solid rgba(255, 169, 77, 0.5)',
              transform: `translateY(${interpolate(b2Spring, [0, 1], [10, 0])}px) scale(${isFase2 ? pulsoGlow : 1})`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                lineHeight: 1.2,
              }}
            >
              {isFase2
                ? '✓ Agenda IA: Reagendado sem conflito!'
                : 'Agenda IA: Verificando horários livres...'}
            </span>
            {frame >= 145 && (
              <div
                style={{
                  padding: '4px 12px',
                  borderRadius: 99,
                  backgroundColor: '#FFA94D',
                  transform: `scale(${interpolate(confirmSpring, [0, 1], [0.8, 1])})`,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 900,
                    color: '#1F2937',
                  }}
                >
                  OK
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
      )}
    </div>
  );
};
