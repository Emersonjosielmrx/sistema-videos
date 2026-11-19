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

  // Background zoom contínuo (1.05 a 1.15)
  const bgScale = interpolate(frame, [0, 145], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Animação de entrada do badge de gancho
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 100},
  });

  // Animação das linhas do título sincronizadas com a fala
  const title1Spring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 120},
  });

  const title2Spring = spring({
    frame: frame - 35,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 120},
  });

  const title3Spring = spring({
    frame: frame - 65,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 120},
  });

  // Mockup do celular
  const phoneSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, mass: 0.8, stiffness: 90},
  });

  // Mensagem 1 do cliente
  const msg1Spring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 110},
  });

  // Alerta de espera prolongada
  const waitSpring = spring({
    frame: frame - 52,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 110},
  });

  // Mensagem 2 de desistência
  const msg2Spring = spring({
    frame: frame - 84,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 110},
  });

  // Microanimação de pulso contínuo no alerta de espera
  const waitPulse = 1 + Math.sin(frame * 0.15) * 0.03;

  // Desmonte suave antes da transição aos 4.46s (frame 134)
  const fadeOut = interpolate(frame, [130, 144], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        fontFamily,
        opacity: fadeOut,
      }}
    >
      {/* Fundo com imagem e zoom lento */}
      <Img
        src={staticFile('img_0.jpg')}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${bgScale})`,
        }}
      />

      {/* Véu de contraste da marca */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 40%, rgba(225, 29, 72, 0.35) 0%, rgba(49, 6, 15, 0.88) 75%, rgba(20, 2, 6, 0.98) 100%)',
        }}
      />

      {/* TOPO INFORMATIVO (y = 160 a 440) */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 20,
        }}
      >
        {/* Badge do gancho */}
        <div
          style={{
            transform: `scale(${Math.max(0, badgeSpring)})`,
            opacity: Math.min(1, badgeSpring),
            background: 'rgba(225, 29, 72, 0.92)',
            padding: '6px 22px',
            borderRadius: 18,
            border: '1.5px solid rgba(250, 204, 21, 0.6)',
            boxShadow: '0 4px 16px rgba(225, 29, 72, 0.4)',
            marginBottom: 10,
          }}
        >
          <span
            style={{
              color: '#FFFFFF',
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            ATENDIMENTO AO CLIENTE
          </span>
        </div>

        {/* Título Cinético Enxuto e Forte (Máx 2 camadas) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 8,
          }}
        >
          {frame >= 8 && (
            <div
              style={{
                transform: `scale(${Math.max(0, title1Spring)})`,
                opacity: Math.min(1, title1Spring),
                display: 'flex',
                alignItems: 'center',
                gap: 12,
              }}
            >
              <span
                style={{
                  color: '#FFFFFF',
                  fontSize: 48,
                  fontWeight: 900,
                  textShadow: '0 3px 12px rgba(0,0,0,0.9)',
                }}
              >
                SEU CLIENTE
              </span>
              <span
                style={{
                  color: '#FFFFFF',
                  fontSize: 48,
                  fontWeight: 900,
                  background: '#E11D48',
                  padding: '2px 14px',
                  borderRadius: 12,
                  boxShadow: '0 4px 14px rgba(225, 29, 72, 0.5)',
                }}
              >
                DESISTE DE PEDIR?
              </span>
            </div>
          )}

          {frame >= 60 && (
            <div
              style={{
                transform: `scale(${Math.max(0, title3Spring)})`,
                opacity: Math.min(1, title3Spring),
                background: 'rgba(49, 6, 15, 0.92)',
                padding: '4px 22px',
                borderRadius: 14,
                border: '1.5px solid #FACC15',
                boxShadow: '0 4px 16px rgba(0,0,0,0.7)',
              }}
            >
              <span
                style={{
                  color: '#FACC15',
                  fontSize: 40,
                  fontWeight: 900,
                  textShadow: '0 2px 10px rgba(0,0,0,0.9)',
                }}
              >
                PORQUE DEMORA PARA RESPONDER?
              </span>
            </div>
          )}
        </div>
      </div>

      {/* CENTRO FOCAL: MOCKUP DE CELULAR COM CONVERSA (y = 480 a 1260) */}
      <div
        style={{
          position: 'absolute',
          top: 480,
          left: 65,
          right: 65,
          height: 770,
          transform: `scale(${Math.max(0, phoneSpring)})`,
          opacity: Math.min(1, phoneSpring),
          background: 'rgba(15, 17, 23, 0.96)',
          borderRadius: 36,
          border: '2px solid rgba(255, 255, 255, 0.15)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.8)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 15,
        }}
      >
        {/* Barra superior do celular */}
        <div
          style={{
            height: 90,
            background: 'rgba(25, 28, 36, 0.98)',
            borderBottom: '1.5px solid rgba(255, 255, 255, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 26px',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 46,
                height: 46,
                borderRadius: 23,
                background: '#E11D48',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFFFFF',
                fontSize: 32,
                fontWeight: 900,
              }}
            >
              🍔
            </div>
            <div>
              <div
                style={{
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 700,
                  lineHeight: 1.1,
                }}
              >
                Delivery & Lanches
              </div>
              <div
                style={{
                  color: '#10B981',
                  fontSize: 32,
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                ● Online
              </div>
            </div>
          </div>

          <div
            style={{
              background: 'rgba(255, 255, 255, 0.12)',
              padding: '6px 14px',
              borderRadius: 12,
              border: '1px solid rgba(255, 255, 255, 0.2)',
            }}
          >
            <span
              style={{
                color: '#CBD5E1',
                fontSize: 32,
                fontWeight: 700,
                textTransform: 'uppercase',
              }}
            >
              Simulação
            </span>
          </div>
        </div>

        {/* Área de mensagens */}
        <div
          style={{
            flex: 1,
            padding: '24px 26px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          {/* Saudação inicial do estabelecimento para evitar tela vazia */}
          <div
            style={{
              alignSelf: 'flex-start',
              maxWidth: '85%',
              background: '#202C33',
              borderRadius: '4px 20px 20px 20px',
              padding: '14px 20px',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <div
              style={{
                color: '#E9EDEF',
                fontSize: 32,
                fontWeight: 500,
                lineHeight: 1.25,
              }}
            >
              Olá! Como posso ajudar você hoje?
            </div>
            <div
              style={{
                color: '#8696A0',
                fontSize: 32,
                textAlign: 'right',
                marginTop: 4,
              }}
            >
              19:40
            </div>
          </div>

          {/* Mensagem 1 do cliente */}
          {frame >= 18 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '85%',
                transform: `scale(${Math.max(0, msg1Spring)})`,
                opacity: Math.min(1, msg1Spring),
                background: '#005C4B',
                borderRadius: '20px 20px 4px 20px',
                padding: '14px 20px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
              }}
            >
              <div
                style={{
                  color: '#FFFFFF',
                  fontSize: 34,
                  fontWeight: 600,
                  lineHeight: 1.25,
                }}
              >
                Boa noite! Tem o cardápio aí?
              </div>
              <div
                style={{
                  color: '#A7F3D0',
                  fontSize: 32,
                  textAlign: 'right',
                  marginTop: 4,
                  fontWeight: 500,
                }}
              >
                19:42 ✓✓
              </div>
            </div>
          )}

          {/* Alerta de espera */}
          {frame >= 52 && (
            <div
              style={{
                alignSelf: 'center',
                transform: `scale(${Math.max(0, waitSpring) * waitPulse})`,
                opacity: Math.min(1, waitSpring),
                background: 'rgba(225, 29, 72, 0.25)',
                border: '2px dashed #E11D48',
                borderRadius: 20,
                padding: '12px 22px',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
              }}
            >
              <span style={{fontSize: 32}}>⏳</span>
              <span
                style={{
                  color: '#FECDD3',
                  fontSize: 32,
                  fontWeight: 700,
                }}
              >
                Sem resposta há 25 min...
              </span>
            </div>
          )}

          {/* Mensagem 2 de desistência */}
          {frame >= 84 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '90%',
                transform: `scale(${Math.max(0, msg2Spring)})`,
                opacity: Math.min(1, msg2Spring),
                background: '#331B24',
                border: '1.5px solid #E11D48',
                borderRadius: '20px 20px 4px 20px',
                padding: '14px 20px',
                boxShadow: '0 6px 18px rgba(225, 29, 72, 0.3)',
              }}
            >
              <div
                style={{
                  color: '#FFFFFF',
                  fontSize: 34,
                  fontWeight: 600,
                  lineHeight: 1.25,
                }}
              >
                Deixa pra lá, demorou muito... já pedi no outro.
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: 6,
                }}
              >
                <span
                  style={{
                    color: '#F87171',
                    fontSize: 32,
                    fontWeight: 800,
                  }}
                >
                  ⚠️ Pedido perdido
                </span>
                <span
                  style={{
                    color: '#9CA3AF',
                    fontSize: 32,
                    fontWeight: 500,
                  }}
                >
                  20:07
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
