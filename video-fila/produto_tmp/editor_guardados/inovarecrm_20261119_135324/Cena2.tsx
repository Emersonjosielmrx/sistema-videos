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

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background zoom contínuo
  const bgScale = interpolate(frame, [0, 278], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Saída suave nos últimos frames
  const exitOpacity = interpolate(frame, [264, 278], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Entrada do celular e cabeçalho
  const phoneSpring = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Topo badge e título
  const badgeSpring = spring({
    frame: Math.max(0, frame - 8),
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const titleSpring = spring({
    frame: Math.max(0, frame - 18),
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Balão 1: Cliente (frame 15 / ~12.5s)
  const b1Spring = spring({
    frame: Math.max(0, frame - 15),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Balão 2: Empresa (frame 100 / ~15.4s)
  const b2Spring = spring({
    frame: Math.max(0, frame - 100),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Pop do Card de Ticket (frame 142 / ~16.8s na fala "vira ticket de suporte")
  const ticketSpring = spring({
    frame: Math.max(0, frame - 142),
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Balão 3: Cliente (frame 165 / ~17.5s)
  const b3Spring = spring({
    frame: Math.max(0, frame - 165),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Balão 4: Empresa (frame 198 / ~18.6s na fala "com o histórico dele")
  const b4Spring = spring({
    frame: Math.max(0, frame - 198),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Chip de Histórico (frame 215 / ~19.2s na fala "no mesmo lugar")
  const histSpring = spring({
    frame: Math.max(0, frame - 215),
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Flutuação sutil viva
  const floatY = Math.sin(frame / 14) * 4;
  const pulseTicket = 1 + Math.sin(frame / 6) * 0.03;

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
      {/* Background com zoom e blur elegante */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(8px)',
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Camada de ambient escuro azul profundo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(11, 15, 25, 0.94) 0%, rgba(15, 23, 42, 0.86) 50%, rgba(11, 15, 25, 0.96) 100%)',
        }}
      />

      {/* TOPO INFORMATIVO (y = 165 a 360) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 25,
        }}
      >
        {/* Badge "COMO FUNCIONA • CRM CHATWOOT IA" */}
        <div
          style={{
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 999,
            background: 'rgba(2, 132, 199, 0.20)',
            border: '1.5px solid rgba(56, 189, 248, 0.5)',
            boxShadow: '0 4px 20px rgba(2, 132, 199, 0.3)',
            marginBottom: 12,
          }}
        >
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: '#38BDF8',
              boxShadow: '0 0 10px #38BDF8',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: '#BAE6FD',
            }}
          >
            COMO FUNCIONA • CRM CHATWOOT IA
          </span>
        </div>

        {/* Título Principal */}
        <div
          style={{
            transform: `translateY(${(1 - titleSpring) * 20}px) scale(${titleSpring})`,
            opacity: titleSpring,
            textAlign: 'center',
            maxWidth: 960,
          }}
        >
          <h2
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              lineHeight: 1.18,
              color: '#FFFFFF',
              margin: 0,
              textWrap: 'balance',
            }}
          >
            A MENSAGEM VIRA{' '}
            <span
              style={{
                color: '#38BDF8',
                background: 'rgba(2, 132, 199, 0.25)',
                padding: '2px 12px',
                borderRadius: 10,
                border: '1px solid rgba(56, 189, 248, 0.4)',
              }}
            >
              TICKET
            </span>{' '}
            NO MESMO LUGAR
          </h2>
        </div>
      </div>

      {/* CENTRO FOCAL (y = 370 a 1300): MOCKUP DE CELULAR MODERNO COM CONVERSA */}
      <div
        style={{
          position: 'absolute',
          top: 375,
          left: 110,
          right: 110,
          transform: `translateY(${floatY}px) scale(${phoneSpring})`,
          opacity: phoneSpring,
          zIndex: 20,
        }}
      >
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.94)',
            backdropFilter: 'blur(20px)',
            borderRadius: 36,
            border: '2px solid rgba(56, 189, 248, 0.3)',
            boxShadow:
              '0 25px 60px rgba(0, 0, 0, 0.8), 0 0 35px rgba(2, 132, 199, 0.25)',
            overflow: 'hidden',
            paddingBottom: 24,
          }}
        >
          {/* Header do Chat */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '18px 24px',
              background: 'rgba(30, 41, 59, 0.85)',
              borderBottom: '1.5px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 800,
                  fontSize: 28,
                  color: '#FFFFFF',
                  border: '1.5px solid rgba(56, 189, 248, 0.5)',
                }}
              >
                IC
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Inovare CRM
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#34D399',
                  }}
                >
                  ● Online • Suporte IA
                </div>
              </div>
            </div>

            {/* Selo Simulação Obrigatório */}
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#94A3B8',
                background: 'rgba(255, 255, 255, 0.08)',
                padding: '4px 14px',
                borderRadius: 999,
                border: '1px solid rgba(255, 255, 255, 0.12)',
              }}
            >
              Simulação
            </div>
          </div>

          {/* Área das Mensagens */}
          <div
            style={{
              padding: '24px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: 18,
            }}
          >
            {/* Mensagem 1: Cliente (frame >= 15) */}
            {frame >= 15 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  background: '#1E293B',
                  borderRadius: '20px 20px 20px 4px',
                  padding: '16px 20px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  transform: `scale(${b1Spring})`,
                  opacity: b1Spring,
                  boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.25,
                  }}
                >
                  Oi, meu pedido veio com defeito.
                </div>
              </div>
            )}

            {/* Digitando 1 (frames 65 a 99) */}
            {frame >= 65 && frame < 100 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  background: 'rgba(2, 132, 199, 0.3)',
                  padding: '12px 20px',
                  borderRadius: 20,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span style={{fontFamily, fontSize: 32, color: '#BAE6FD'}}>
                  digitando...
                </span>
              </div>
            )}

            {/* Mensagem 2: Empresa (frame >= 100) */}
            {frame >= 100 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '84%',
                  background: '#0284C7',
                  borderRadius: '20px 20px 4px 20px',
                  padding: '16px 20px',
                  transform: `scale(${b2Spring})`,
                  opacity: b2Spring,
                  boxShadow: '0 6px 20px rgba(2, 132, 199, 0.35)',
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.25,
                  }}
                >
                  Sinto muito! Já abri um ticket de suporte para você.
                </div>
              </div>
            )}

            {/* CARD POP: TICKET ABERTO (frame >= 142) */}
            {frame >= 142 && (
              <div
                style={{
                  alignSelf: 'center',
                  transform: `scale(${ticketSpring * pulseTicket})`,
                  opacity: ticketSpring,
                  background:
                    'linear-gradient(135deg, rgba(2, 132, 199, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%)',
                  border: '2px solid #38BDF8',
                  borderRadius: 18,
                  padding: '14px 24px',
                  boxShadow:
                    '0 10px 30px rgba(2, 132, 199, 0.5), 0 0 20px rgba(56, 189, 248, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}
              >
                <span style={{fontSize: 34}}>🎫</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    letterSpacing: '0.02em',
                  }}
                >
                  TICKET #1042 GERADO AUTOMATICAMENTE
                </span>
              </div>
            )}

            {/* Mensagem 3: Cliente (frame >= 165) */}
            {frame >= 165 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  background: '#1E293B',
                  borderRadius: '20px 20px 20px 4px',
                  padding: '16px 20px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  transform: `scale(${b3Spring})`,
                  opacity: b3Spring,
                  boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.25,
                  }}
                >
                  Obrigado! Alguém vai me responder?
                </div>
              </div>
            )}

            {/* Digitando 2 (frames 184 a 197) */}
            {frame >= 184 && frame < 198 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  background: 'rgba(2, 132, 199, 0.3)',
                  padding: '12px 20px',
                  borderRadius: 20,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span style={{fontFamily, fontSize: 32, color: '#BAE6FD'}}>
                  digitando...
                </span>
              </div>
            )}

            {/* Mensagem 4: Empresa (frame >= 198) */}
            {frame >= 198 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '86%',
                  background: '#0284C7',
                  borderRadius: '20px 20px 4px 20px',
                  padding: '16px 20px',
                  transform: `scale(${b4Spring})`,
                  opacity: b4Spring,
                  boxShadow: '0 6px 20px rgba(2, 132, 199, 0.35)',
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.25,
                  }}
                >
                  Sim, o atendente já vê todo o seu histórico e dá sequência.
                </div>
              </div>
            )}

            {/* CHIP: HISTÓRICO NO MESMO LUGAR (frame >= 215) */}
            {frame >= 215 && (
              <div
                style={{
                  alignSelf: 'center',
                  transform: `scale(${histSpring})`,
                  opacity: histSpring,
                  background: 'rgba(16, 185, 129, 0.22)',
                  border: '1.5px solid rgba(52, 211, 153, 0.6)',
                  borderRadius: 999,
                  padding: '8px 24px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <span style={{fontSize: 28}}>📁</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#6EE7B7',
                  }}
                >
                  HISTÓRICO UNIFICADO NO MESMO LUGAR
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
