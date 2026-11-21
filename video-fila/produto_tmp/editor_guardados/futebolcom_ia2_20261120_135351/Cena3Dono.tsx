import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
  Img,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3Dono: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Parte 1 (frames 0 a 95): Apresentador com enquadramento Close-Up
  const videoScale = interpolate(frame, [0, 95], [1.25, 1.32], {
    extrapolateRight: 'clamp',
  });

  // Notificação de Pedido Confirmado no WhatsApp (frame 15)
  const notifSpring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 13, mass: 0.7},
  });

  // Parte 2 (frame 96 a 240, ~4.8s): Corte em B-roll de produção contínua da cozinha
  const isBroll = frame >= 96;
  const brollTransition = spring({
    frame: frame - 96,
    fps,
    config: {damping: 14, mass: 0.7},
  });

  const brollScale = interpolate(frame, [96, 240], [1.06, 1.22], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Badges escalonados de prova visual no B-roll da cozinha
  const badge1Spring = spring({
    frame: frame - 110,
    fps,
    config: {damping: 13, mass: 0.7},
  });
  const badge2Spring = spring({
    frame: frame - 145,
    fps,
    config: {damping: 13, mass: 0.7},
  });
  const badge3Spring = spring({
    frame: frame - 180,
    fps,
    config: {damping: 13, mass: 0.7},
  });

  // Entrada do Card de Topo
  const cardSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 15, mass: 0.8},
  });

  // Microflutuação contínua do HUD
  const hudFloat = Math.sin(frame * 0.12) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#000000',
      }}
    >
      {/* 1. VÍDEO DO APRESENTADOR (Parte 1: frames 0 a 95 em tela cheia) */}
      {!isBroll && (
        <div
          style={{
            position: 'absolute',
            width: 1080,
            height: 1920,
            transform: `scale(${videoScale})`,
            transformOrigin: '50% 36%',
          }}
        >
          <OffthreadVideo
            src={staticFile('dono_3.mp4')}
            muted
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        </div>
      )}

      {/* 2. CORTE EM B-ROLL DA COZINHA EM PLENO FUNCIONAMENTO (Parte 2: frames 96 a 240) */}
      {isBroll && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: interpolate(brollTransition, [0, 0.2, 1], [0, 0.8, 1]),
          }}
        >
          {/* Foto apetitosa e dinâmica do produto sendo preparado/montado na cozinha */}
          <div
            style={{
              position: 'absolute',
              width: 1080,
              height: 1920,
              transform: `scale(${brollScale})`,
              transformOrigin: '50% 50%',
            }}
          >
            <Img
              src={staticFile('burger.jpg')}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />
          </div>

          {/* Vinheta escura cinematográfica para manter foco na chapa/lanche e legibilidade das informações */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background:
                'linear-gradient(180deg, rgba(15, 2, 5, 0.90) 0%, rgba(15, 2, 5, 0.35) 45%, rgba(15, 2, 5, 0.92) 100%)',
            }}
          />

          {/* Picture-in-Picture do dono falando no canto superior direito (mantém autenticidade da voz) */}
          <div
            style={{
              position: 'absolute',
              top: 300,
              right: 60,
              width: 210,
              height: 210,
              borderRadius: '50%',
              border: '4px solid #E11D48',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.85)',
              overflow: 'hidden',
              zIndex: 35,
            }}
          >
            <OffthreadVideo
              src={staticFile('dono_3.mp4')}
              muted
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />
          </div>

          {/* Badges animados comprovando a cozinha trabalhando sem interrupções */}
          <div
            style={{
              position: 'absolute',
              top: 310,
              left: 60,
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              zIndex: 35,
            }}
          >
            {frame >= 110 && (
              <div
                style={{
                  transform: `scale(${Math.max(0, badge1Spring)})`,
                  background: 'rgba(20, 5, 10, 0.94)',
                  border: '2px solid #E11D48',
                  borderRadius: 18,
                  padding: '12px 22px',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.85)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}
              >
                <span style={{fontSize: 34}}>🔥</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FFFFFF',
                  }}
                >
                  Cozinha a todo vapor
                </span>
              </div>
            )}

            {frame >= 145 && (
              <div
                style={{
                  transform: `scale(${Math.max(0, badge2Spring)})`,
                  background: 'rgba(20, 5, 10, 0.94)',
                  border: '2px solid #25D366',
                  borderRadius: 18,
                  padding: '12px 22px',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.85)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}
              >
                <span style={{fontSize: 34}}>⚡</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#86EFAC',
                  }}
                >
                  Pedidos automáticos via IA
                </span>
              </div>
            )}

            {frame >= 180 && (
              <div
                style={{
                  transform: `scale(${Math.max(0, badge3Spring)})`,
                  background: 'rgba(49, 6, 15, 0.95)',
                  border: '2px solid #FACC15',
                  borderRadius: 18,
                  padding: '12px 22px',
                  boxShadow: '0 8px 24px rgba(250, 204, 21, 0.35)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}
              >
                <span style={{fontSize: 34}}>✅</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FACC15',
                  }}
                >
                  Sem parar a produção
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Leve vinheta superior */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(180deg, rgba(15, 2, 5, 0.85) 0%, rgba(15, 2, 5, 0.4) 65%, rgba(0, 0, 0, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo Exclusivo Informativo (Safe Zone: y = 165 a 290) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          transform: `translateY(${hudFloat}px) scale(${Math.max(0, cardSpring)})`,
          opacity: interpolate(cardSpring, [0, 0.2, 1], [0, 0.8, 1]),
          zIndex: 40,
        }}
      >
        <div
          style={{
            background: 'rgba(20, 5, 10, 0.92)',
            border: '2px solid rgba(225, 29, 72, 0.65)',
            borderRadius: 26,
            padding: '20px 28px',
            boxShadow:
              '0 16px 36px rgba(0, 0, 0, 0.85), 0 0 25px rgba(225, 29, 72, 0.25)',
            display: 'flex',
            alignItems: 'center',
            gap: 20,
          }}
        >
          <div
            style={{
              padding: '10px 18px',
              borderRadius: 14,
              background: isBroll ? '#25D366' : '#E11D48',
              color: '#FFFFFF',
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              textTransform: 'uppercase',
              letterSpacing: 1.1,
              whiteSpace: 'nowrap',
              transition: 'background 0.3s ease',
            }}
          >
            {isBroll ? 'Cozinha a Todo Vapor' : 'O Resultado'}
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 40,
              fontWeight: 800,
              color: '#FFFFFF',
              lineHeight: 1.2,
              textWrap: 'balance',
            }}
          >
            {isBroll
              ? 'Trabalhando sem interrupções'
              : 'Pedido chega confirmado no WhatsApp'}
          </div>
        </div>
      </div>

      {/* Overlay animado com notificação de pedido confirmado do WhatsApp (frames 15 a 95 - Rosto livre) */}
      {!isBroll && frame >= 15 && (
        <div
          style={{
            position: 'absolute',
            top: 305,
            left: 60,
            right: 60,
            transform: `scale(${Math.max(0, notifSpring)})`,
            opacity: interpolate(notifSpring, [0, 0.3, 1], [0, 0.8, 1]),
            zIndex: 35,
          }}
        >
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.96)',
              border: '2.5px solid #25D366',
              borderRadius: 22,
              padding: '16px 24px',
              boxShadow:
                '0 12px 36px rgba(0, 0, 0, 0.85), 0 0 24px rgba(37, 211, 102, 0.35)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: '50%',
                  background: '#25D366',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontSize: 30,
                  fontWeight: 900,
                }}
              >
                ✓
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FFFFFF',
                  }}
                >
                  Pedido Confirmado no WhatsApp!
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#86EFAC',
                    marginTop: 2,
                  }}
                >
                  Burger Artesanal • Direto para a cozinha
                </div>
              </div>
            </div>
            <div
              style={{
                background: 'rgba(37, 211, 102, 0.2)',
                border: '1px solid #25D366',
                padding: '6px 14px',
                borderRadius: 12,
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                whiteSpace: 'nowrap',
              }}
            >
              IA ➔ Cozinha
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
