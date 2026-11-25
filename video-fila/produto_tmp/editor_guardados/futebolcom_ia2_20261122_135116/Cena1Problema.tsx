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

export const Cena1Problema: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no vídeo do salão em almoço (push-in suave)
  const scale = interpolate(frame, [0, 200], [1.02, 1.10], {
    extrapolateRight: 'clamp',
  });

  // Microdinâmica constante
  const floatY = Math.sin(frame / 14) * 4;

  // Header superior
  const headerSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Entrada do Card Principal de WhatsApp (~4.6s -> frame 16)
  const cardSpring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 12, stiffness: 115},
  });

  // Fase 2: "fila de mensagens crescia" (~6.0s -> frame 54)
  const queueSpring = spring({
    frame: frame - 54,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Fase 3: "não conseguia atender" (~7.5s -> frame 98)
  const overloadSpring = spring({
    frame: frame - 98,
    fps,
    config: {damping: 11, stiffness: 125},
  });
  const overloadPulse = 1 + Math.sin(Math.max(0, frame - 98) / 8) * 0.03;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0B0D13',
      }}
    >
      {/* Vídeo dinâmico de restaurante movimentado no almoço (movimento real de salão) */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${scale})`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('veo_cartao.mp4')}
          muted
          style={{
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
            filter: 'brightness(0.92) contrast(1.08)',
          }}
        />
      </div>

      {/* Véu escuro equilibrado para garantir contraste impecável */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(11, 13, 19, 0.88) 0%, rgba(11, 13, 19, 0.65) 25%, rgba(11, 13, 19, 0.65) 65%, rgba(11, 13, 19, 0.95) 100%)',
        }}
      />

      {/* Conteúdo na Safe Zone (y=150 a y=1580, x=60 a x=1020) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 180,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 30,
        }}
      >
        {/* Header superior */}
        {headerSpring > 0 && (
          <div
            style={{
              transform: `scale(${headerSpring})`,
              opacity: headerSpring,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
            }}
          >
            {/* Badge Rótulo "O PROBLEMA" */}
            <div
              style={{
                backgroundColor: 'rgba(225, 29, 72, 0.95)',
                padding: '10px 24px',
                borderRadius: 999,
                border: '1.5px solid rgba(255, 255, 255, 0.3)',
                boxShadow: '0 6px 20px rgba(225, 29, 72, 0.4)',
                marginBottom: 16,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  letterSpacing: 2,
                  textTransform: 'uppercase',
                }}
              >
                O PROBLEMA
              </span>
            </div>

            {/* Título Principal */}
            <div
              style={{
                backgroundColor: 'rgba(11, 13, 19, 0.94)',
                border: '2px solid rgba(255, 255, 255, 0.15)',
                padding: '18px 36px',
                borderRadius: 20,
                textAlign: 'center',
                boxShadow: '0 12px 30px rgba(0, 0, 0, 0.8)',
                maxWidth: 920,
              }}
            >
              <h2
                style={{
                  fontFamily,
                  fontSize: 48,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  margin: 0,
                  lineHeight: 1.15,
                  textTransform: 'uppercase',
                }}
              >
                FILA DE MENSAGENS NO ALMOÇO
              </h2>
            </div>
          </div>
        )}

        {/* Notificação Elegante Única de WhatsApp com Evolução Dinâmica */}
        {cardSpring > 0 && (
          <div
            style={{
              width: '100%',
              maxWidth: 920,
              marginTop: 40,
              transform: `scale(${cardSpring}) translateY(${floatY}px)`,
              opacity: cardSpring,
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: '2.5px solid rgba(34, 197, 94, 0.65)',
              borderRadius: 28,
              padding: '28px 32px',
              boxShadow:
                '0 20px 50px rgba(0, 0, 0, 0.85), 0 0 35px rgba(34, 197, 94, 0.25)',
              display: 'flex',
              flexDirection: 'column',
              gap: 22,
            }}
          >
            {/* Cabeçalho da Notificação: App WhatsApp + Selo Obrigatório 'Simulação' */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
                paddingBottom: 16,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: 16,
                    backgroundColor: '#22C55E',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 4px 14px rgba(34, 197, 94, 0.45)',
                  }}
                >
                  <svg
                    width="30"
                    height="30"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#FFFFFF"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>
                </div>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    letterSpacing: 0.5,
                  }}
                >
                  WhatsApp
                </span>
              </div>

              {/* Selo Simulação Obrigatório com letra >= 32px */}
              <div
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  border: '1.5px solid rgba(255, 255, 255, 0.25)',
                  borderRadius: 10,
                  padding: '4px 14px',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#CBD5E1',
                    textTransform: 'uppercase',
                    letterSpacing: 1,
                  }}
                >
                  Simulação
                </span>
              </div>
            </div>

            {/* Mensagem do Cliente */}
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 8,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#22C55E',
                  }}
                >
                  Cliente no Restaurante
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#94A3B8',
                  }}
                >
                  Agora
                </span>
              </div>
              <p
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  margin: 0,
                  lineHeight: 1.25,
                }}
              >
                "Cadê o cardápio? Queremos pedir agora!"
              </p>
            </div>

            {/* Indicador Dinâmico 2: Mensagens acumulando na fila (sem inventar números) */}
            {frame >= 54 && queueSpring > 0 && (
              <div
                style={{
                  transform: `scale(${queueSpring})`,
                  opacity: queueSpring,
                  backgroundColor: 'rgba(250, 204, 21, 0.12)',
                  border: '2px solid #FACC15',
                  borderRadius: 18,
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 12,
                    backgroundColor: '#FACC15',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <svg
                    width="26"
                    height="26"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#000000"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                  </svg>
                </div>
                <div>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 900,
                      color: '#FACC15',
                      display: 'block',
                      textTransform: 'uppercase',
                    }}
                  >
                    Fila de Mensagens Crescendo
                  </span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#F8FAFC',
                      display: 'block',
                      marginTop: 2,
                    }}
                  >
                    Muitos pedidos entrando ao mesmo tempo
                  </span>
                </div>
              </div>
            )}

            {/* Indicador Dinâmico 3: Sobrecarga no atendimento (frame >= 98, sem artefato prematuro) */}
            {frame >= 98 && overloadSpring > 0 && (
              <div
                style={{
                  transform: `scale(${overloadSpring * overloadPulse})`,
                  opacity: overloadSpring,
                  backgroundColor: 'rgba(225, 29, 72, 0.22)',
                  border: '2px solid #E11D48',
                  borderRadius: 18,
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  boxShadow: '0 8px 24px rgba(225, 29, 72, 0.4)',
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 12,
                    backgroundColor: '#E11D48',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <span style={{fontSize: 26}}>⚠️</span>
                </div>
                <div>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      display: 'block',
                      textTransform: 'uppercase',
                    }}
                  >
                    Atendimento Sobrecarregado
                  </span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#FDE047',
                      display: 'block',
                      marginTop: 2,
                    }}
                  >
                    Sem conseguir atender todo mundo com calma
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
