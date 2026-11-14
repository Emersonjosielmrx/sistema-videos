import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena1Props {
  fontFamily: string;
}

export const Cena1: React.FC<Cena1Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Transições de entrada e saída
  const sceneOpacity = interpolate(
    frame,
    [0, 10, 192, 205],
    [0, 1, 1, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  // Entrada do título simplificado
  const titleSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do celular B-Roll
  const phoneSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Scroll contínuo e escalonado da lista de conversas conforme chegam novas mensagens
  const chatScrollY = interpolate(frame, [0, 60, 120, 200], [0, -25, -60, -90], {
    extrapolateRight: 'clamp',
  });

  // Notificação pop no topo do celular aos ~70 frames ("digitando sabores")
  const notif1Spring = spring({
    frame: frame - 68,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Notificação pop aos ~120 frames ("tirando dúvidas de clientes")
  const notif2Spring = spring({
    frame: frame - 120,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Contador de mensagens acumuladas subindo (14 -> 22 -> 29)
  const unreadCount =
    frame < 50 ? 14 : frame < 110 ? 19 : frame < 160 ? 24 : 28;

  // Pulso e flutuação suave do celular para ritmo orgânico
  const floatY = Math.sin(frame * 0.1) * 5;
  const badgePulse = 1.0 + 0.06 * Math.sin(frame * 0.25);

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#140206'}}>
      {/* Fundo Atmosférico de Alto Contraste com Gradiente Dinâmico */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(circle at 50% 35%, rgba(180, 20, 50, 0.28) 0%, rgba(30, 4, 10, 0.95) 65%, #100104 100%)',
        }}
      />

      {/* Título Principal Simplificado e Integrado (y=175 a 280) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
          transform: `scale(${Math.min(titleSpring, 1)}) translateY(${(1 - titleSpring) * 15}px)`,
          opacity: titleSpring,
          zIndex: 30,
        }}
      >
        <div
          style={{
            fontFamily,
            fontSize: 32,
            fontWeight: 800,
            color: '#FFFFFF',
            backgroundColor: 'rgba(225, 29, 72, 0.45)',
            border: '2px solid #E11D48',
            padding: '6px 22px',
            borderRadius: 50,
            letterSpacing: 1.2,
            textTransform: 'uppercase',
            boxShadow: '0 8px 20px rgba(225, 29, 72, 0.35)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <span>⚠️</span>
          <span>O PROBLEMA: ATENDIMENTO MANUAL</span>
        </div>

        <div
          style={{
            fontFamily,
            fontSize: 44,
            fontWeight: 900,
            color: '#FFFFFF',
            letterSpacing: -0.5,
            textShadow: '0 4px 18px rgba(0,0,0,0.85)',
          }}
        >
          HORAS PERDIDAS NO WHATSAPP
        </div>
      </div>

      {/* B-Roll Vivo: Mockup de Celular com Tela de WhatsApp Lotada de Mensagens Sem Resposta (y=325 a 1165) */}
      <div
        style={{
          position: 'absolute',
          top: 325,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 10,
        }}
      >
        <div
          style={{
            width: 860,
            height: 840,
            backgroundColor: '#111B21',
            borderRadius: 40,
            border: '5px solid #2A2F38',
            boxShadow:
              '0 24px 60px rgba(0,0,0,0.85), 0 0 35px rgba(225, 29, 72, 0.2)',
            transform: `scale(${Math.min(phoneSpring, 1)}) translateY(${floatY}px)`,
            opacity: phoneSpring,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Header WhatsApp Business */}
          <div
            style={{
              height: 100,
              backgroundColor: '#1F2C34',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 24px',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
              flexShrink: 0,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 34}}>💬</span>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#E9EDEF',
                  }}
                >
                  WhatsApp Pizzaria
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    color: '#EF4444',
                    fontWeight: 700,
                  }}
                >
                  Atendimento sobrecarregado
                </div>
              </div>
            </div>

            {/* Contador de Mensagens Pendentes em Alerta Vermelho Pulsante */}
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                backgroundColor: '#EF4444',
                padding: '6px 16px',
                borderRadius: 20,
                boxShadow: '0 4px 14px rgba(239, 68, 68, 0.6)',
                transform: `scale(${badgePulse})`,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span>🔴</span>
              <span>{unreadCount} pendentes</span>
            </div>
          </div>

          {/* Banner de Notificação Flutuante no Topo da Conversa */}
          {frame >= 68 && (
            <div
              style={{
                backgroundColor: '#2A1016',
                borderBottom: '2px solid #EF4444',
                padding: '12px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                transform: `translateY(${(1 - notif1Spring) * -30}px)`,
                opacity: notif1Spring,
                zIndex: 15,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <span style={{fontSize: 30}}>⏳</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FCA5A5',
                  }}
                >
                  {frame < 120
                    ? 'Digitando sabores e preços manualmente...'
                    : 'Clientes aguardando resposta há mais de 15 min'}
                </span>
              </div>
              <span style={{fontSize: 28}}>⚠️</span>
            </div>
          )}

          {/* Lista de Mensagens do WhatsApp Acumuladas */}
          <div
            style={{
              flex: 1,
              padding: '16px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
              transform: `translateY(${chatScrollY}px)`,
            }}
          >
            {/* Conversa 1 */}
            <div
              style={{
                backgroundColor: '#1E2A30',
                borderRadius: 18,
                padding: '16px 20px',
                borderLeft: '5px solid #EF4444',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 54,
                    height: 54,
                    borderRadius: '50%',
                    backgroundColor: '#374151',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 26,
                    color: '#FFFFFF',
                    fontWeight: 700,
                  }}
                >
                  MC
                </div>
                <div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    Marcos Cliente
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 500,
                      color: '#CBD5E1',
                      marginTop: 2,
                    }}
                  >
                    Qual o cardápio e os sabores de hoje?
                  </div>
                </div>
              </div>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: '50%',
                  backgroundColor: '#EF4444',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFF',
                  fontWeight: 900,
                  fontSize: 32,
                }}
              >
                3
              </div>
            </div>

            {/* Conversa 2 */}
            <div
              style={{
                backgroundColor: '#1E2A30',
                borderRadius: 18,
                padding: '16px 20px',
                borderLeft: '5px solid #FACC15',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 54,
                    height: 54,
                    borderRadius: '50%',
                    backgroundColor: '#1E3A8A',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 26,
                    color: '#FFFFFF',
                    fontWeight: 700,
                  }}
                >
                  CL
                </div>
                <div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    Camila Lima
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 500,
                      color: '#CBD5E1',
                      marginTop: 2,
                    }}
                  >
                    A pizza de calabresa vem com cebola?
                  </div>
                </div>
              </div>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: '50%',
                  backgroundColor: '#EF4444',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFF',
                  fontWeight: 900,
                  fontSize: 32,
                }}
              >
                2
              </div>
            </div>

            {/* Conversa 3 */}
            <div
              style={{
                backgroundColor: '#1E2A30',
                borderRadius: 18,
                padding: '16px 20px',
                borderLeft: '5px solid #EF4444',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 54,
                    height: 54,
                    borderRadius: '50%',
                    backgroundColor: '#065F46',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 26,
                    color: '#FFFFFF',
                    fontWeight: 700,
                  }}
                >
                  LD
                </div>
                <div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    Lucas Delivery
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 500,
                      color: '#CBD5E1',
                      marginTop: 2,
                    }}
                  >
                    Tem foto das pizzas doces?
                  </div>
                </div>
              </div>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: '50%',
                  backgroundColor: '#EF4444',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFF',
                  fontWeight: 900,
                  fontSize: 32,
                }}
              >
                4
              </div>
            </div>

            {/* Conversa 4 */}
            <div
              style={{
                backgroundColor: '#1E2A30',
                borderRadius: 18,
                padding: '16px 20px',
                borderLeft: '5px solid #FACC15',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 54,
                    height: 54,
                    borderRadius: '50%',
                    backgroundColor: '#7C2D12',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 26,
                    color: '#FFFFFF',
                    fontWeight: 700,
                  }}
                >
                  AS
                </div>
                <div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    Amanda Silva
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 500,
                      color: '#CBD5E1',
                      marginTop: 2,
                    }}
                  >
                    Demora quanto tempo para entregar?
                  </div>
                </div>
              </div>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: '50%',
                  backgroundColor: '#EF4444',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFF',
                  fontWeight: 900,
                  fontSize: 32,
                }}
              >
                2
              </div>
            </div>

            {/* Conversa 5 */}
            <div
              style={{
                backgroundColor: '#1E2A30',
                borderRadius: 18,
                padding: '16px 20px',
                borderLeft: '5px solid #EF4444',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 54,
                    height: 54,
                    borderRadius: '50%',
                    backgroundColor: '#581C87',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 26,
                    color: '#FFFFFF',
                    fontWeight: 700,
                  }}
                >
                  PR
                </div>
                <div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    Pedro Rocha
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 500,
                      color: '#CBD5E1',
                      marginTop: 2,
                    }}
                  >
                    Ainda estão aceitando pedidos hoje?
                  </div>
                </div>
              </div>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: '50%',
                  backgroundColor: '#EF4444',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFF',
                  fontWeight: 900,
                  fontSize: 32,
                }}
              >
                5
              </div>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

