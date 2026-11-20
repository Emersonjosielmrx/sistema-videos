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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background zoom contínuo
  const bgScale = interpolate(frame, [0, 157], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });

  // Saída suave nos últimos frames
  const exitOpacity = interpolate(frame, [142, 156], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Animação de entrada do badge do topo
  const badgeSpring = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Animação do título principal
  const titleSpring = spring({
    frame: Math.max(0, frame - 10),
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Notificação 1 (0.5s - frame 15)
  const card1Spring = spring({
    frame: Math.max(0, frame - 15),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Notificação 2 (1.5s - frame 45)
  const card2Spring = spring({
    frame: Math.max(0, frame - 45),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Card de alerta geral (2.7s - frame 80)
  const card3Spring = spring({
    frame: Math.max(0, frame - 80),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Flutuação contínua viva
  const floatY = Math.sin(frame / 12) * 5;
  const pulseAlert = 1 + Math.sin(frame / 6) * 0.03;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        opacity: exitOpacity,
      }}
    >
      {/* Background com zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
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
        {/* Camada de escurecimento com contraste profissional */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(15, 23, 42, 0.90) 0%, rgba(15, 23, 42, 0.72) 45%, rgba(11, 15, 25, 0.95) 100%)',
          }}
        />
      </div>

      {/* TOPO INFORMATIVO (y = 175 a 480) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 20,
        }}
      >
        {/* Badge / Selo de Dor */}
        <div
          style={{
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 999,
            background: 'rgba(239, 68, 68, 0.16)',
            border: '1.5px solid rgba(239, 68, 68, 0.45)',
            boxShadow: '0 4px 20px rgba(239, 68, 68, 0.25)',
            marginBottom: 20,
          }}
        >
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
              transform: `scale(${pulseAlert})`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: '#FCA5A5',
            }}
          >
            SUPORTE NO WHATSAPP
          </span>
        </div>

        {/* Título Principal Cinético (A pergunta do cliente) */}
        <div
          style={{
            transform: `translateY(${(1 - titleSpring) * 30}px) scale(${titleSpring})`,
            opacity: titleSpring,
            textAlign: 'center',
            maxWidth: 960,
          }}
        >
          <h1
            style={{
              fontFamily,
              fontSize: 52,
              fontWeight: 900,
              lineHeight: 1.18,
              color: '#FFFFFF',
              margin: 0,
              textShadow: '0 4px 16px rgba(0,0,0,0.85)',
              textWrap: 'balance',
            }}
          >
            MENSAGEM DE CLIENTE{' '}
            <span
              style={{
                color: '#38BDF8',
                background: 'rgba(2, 132, 199, 0.22)',
                padding: '2px 14px',
                borderRadius: 12,
                border: '1px solid rgba(56, 189, 248, 0.4)',
                display: 'inline-block',
              }}
            >
              SOME
            </span>{' '}
            E NINGUÉM ABRE CHAMADO?
          </h1>
        </div>
      </div>

      {/* CENTRO FOCAL (y = 520 a 1280): Pilha de Notificações Perdidas */}
      <div
        style={{
          position: 'absolute',
          top: 520,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          gap: 22,
          transform: `translateY(${floatY}px)`,
          zIndex: 10,
        }}
      >
        {/* Notificação 1 */}
        {frame >= 15 && (
          <div
            style={{
              transform: `translateY(${(1 - card1Spring) * 50}px) scale(${card1Spring})`,
              opacity: card1Spring,
              background: 'rgba(15, 23, 42, 0.88)',
              backdropFilter: 'blur(16px)',
              border: '1.5px solid rgba(255, 255, 255, 0.12)',
              borderRadius: 24,
              padding: '24px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 20,
              boxShadow: '0 16px 36px rgba(0, 0, 0, 0.65)',
            }}
          >
            {/* Avatar */}
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #475569 0%, #1E293B 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                border: '1.5px solid rgba(255, 255, 255, 0.18)',
              }}
            >
              <span style={{fontSize: 32}}>👤</span>
            </div>

            {/* Texto */}
            <div style={{flex: 1}}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 6,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#CBD5E1',
                  }}
                >
                  Carlos Lima
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#EF4444',
                    background: 'rgba(239, 68, 68, 0.16)',
                    padding: '4px 12px',
                    borderRadius: 8,
                  }}
                >
                  Sem resposta
                </span>
              </div>
              <p
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  margin: 0,
                  lineHeight: 1.25,
                }}
              >
                "Oi, meu pedido veio errado, preciso de ajuda!"
              </p>
            </div>
          </div>
        )}

        {/* Notificação 2 */}
        {frame >= 45 && (
          <div
            style={{
              transform: `translateY(${(1 - card2Spring) * 50}px) scale(${card2Spring})`,
              opacity: card2Spring,
              background: 'rgba(15, 23, 42, 0.88)',
              backdropFilter: 'blur(16px)',
              border: '1.5px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 24,
              padding: '24px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 20,
              boxShadow: '0 16px 36px rgba(0, 0, 0, 0.65)',
            }}
          >
            {/* Avatar */}
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #475569 0%, #1E293B 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                border: '1.5px solid rgba(255, 255, 255, 0.18)',
              }}
            >
              <span style={{fontSize: 32}}>👤</span>
            </div>

            {/* Texto */}
            <div style={{flex: 1}}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 6,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#CBD5E1',
                  }}
                >
                  Mariana Souza
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#F87171',
                    background: 'rgba(239, 68, 68, 0.16)',
                    padding: '4px 12px',
                    borderRadius: 8,
                  }}
                >
                  Sem chamado
                </span>
              </div>
              <p
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  margin: 0,
                  lineHeight: 1.25,
                }}
              >
                "Alguém pode me responder por aqui?"
              </p>
            </div>
          </div>
        )}

        {/* Card de Alerta Resumo */}
        {frame >= 80 && (
          <div
            style={{
              transform: `translateY(${(1 - card3Spring) * 50}px) scale(${card3Spring})`,
              opacity: card3Spring,
              background: '#1A0E12',
              border: '2px solid rgba(239, 68, 68, 0.75)',
              borderRadius: 24,
              padding: '24px 30px',
              display: 'flex',
              alignItems: 'center',
              gap: 20,
              boxShadow: '0 20px 45px rgba(0, 0, 0, 0.7)',
            }}
          >
            <span style={{fontSize: 48, flexShrink: 0}}>⚠️</span>
            <div>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FCA5A5',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  marginBottom: 6,
                }}
              >
                MENSAGENS PERDIDAS NA FILA
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#E2E8F0',
                  lineHeight: 1.25,
                }}
              >
                Sem ticket aberto e sem histórico registrado
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
