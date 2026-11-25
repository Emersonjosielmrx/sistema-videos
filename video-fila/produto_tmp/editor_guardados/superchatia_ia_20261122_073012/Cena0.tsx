import React from 'react';
import {
  AbsoluteFill,
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

  // Movimento de câmera contínuo e expressivo no fundo: zoom de 1.05 a 1.24 + panY
  const bgScale = interpolate(frame, [0, 145], [1.05, 1.24], {
    extrapolateRight: 'clamp',
  });
  const bgPanY = interpolate(frame, [0, 145], [0, -45], {
    extrapolateRight: 'clamp',
  });

  // Molas do Gancho Cinético inicial (frames 0 a 48)
  // "Perdendo" aos 0.318s (f=10)
  const springPerdendo = spring({
    frame: frame - 8,
    fps,
    config: {damping: 10, stiffness: 140},
  });

  // "contato de cliente" aos 0.775s (f=23)
  const springContato = spring({
    frame: frame - 22,
    fps,
    config: {damping: 11, stiffness: 120},
  });

  // Mockup celular entra no momento em que a fala cita os canais ("entre", ~1.6s, f=48)
  const springPhone = spring({
    frame: frame - 46,
    fps,
    config: {damping: 12, stiffness: 105},
  });

  // Slow push-in contínuo no cartão a partir da sua entrada (f=48 a 145)
  const cardPushIn = interpolate(frame, [46, 145], [1.0, 1.06], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Notificação WhatsApp aos 2.073s (f=62)
  const springWpp = spring({
    frame: frame - 62,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Notificação Instagram aos 2.794s (f=84)
  const springInsta = spring({
    frame: frame - 84,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Alerta inferior aos 3.5s (f=105)
  const springAlert = spring({
    frame: frame - 105,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Micro-movimentos contínuos de levitação e pulso
  const phoneFloat = Math.sin(frame / 12) * 8;
  const pulseAlert = 1 + 0.04 * Math.sin((frame / 8) * Math.PI);
  const spotX = interpolate(frame, [0, 145], [30, 70], {extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D13', overflow: 'hidden'}}>
      {/* Fundo com zoom e iluminação dinâmica em movimento contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgPanY}px)`,
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
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(circle at ${spotX}% 40%, rgba(91, 108, 255, 0.4) 0%, rgba(15, 23, 42, 0.75) 50%, rgba(11, 13, 19, 0.96) 100%)`,
          }}
        />
      </div>

      {/* Faixa segura: y=150 a y=1580 | margem x=60 a 1020 */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 156,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Pill de Categoria / Contexto no topo */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 9999,
            background: 'rgba(17, 24, 39, 0.95)',
            border: '1.5px solid rgba(91, 108, 255, 0.5)',
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.7)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#5B6CFF',
              boxShadow: '0 0 10px #5B6CFF',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#CBD5E1',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Centralização de Canais
          </span>
        </div>

        {/* Bloco Superior: Gancho Cinético de Alto Impacto */}
        <div
          style={{
            marginTop: 14,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            width: '100%',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              flexWrap: 'wrap',
              justifyContent: 'center',
            }}
          >
            {frame >= 8 && (
              <div
                style={{
                  transform: `scale(${Math.max(0, springPerdendo)})`,
                  opacity: Math.min(1, springPerdendo),
                  padding: '6px 26px',
                  borderRadius: 18,
                  background: '#DC2626',
                  boxShadow: '0 6px 30px rgba(220, 38, 38, 0.65)',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 56,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    letterSpacing: '0.02em',
                    textTransform: 'uppercase',
                  }}
                >
                  PERDENDO
                </span>
              </div>
            )}

            {frame >= 20 && (
              <div
                style={{
                  transform: `scale(${Math.max(0, springContato)})`,
                  opacity: Math.min(1, springContato),
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 50,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    textTransform: 'uppercase',
                    textShadow: '0 4px 18px rgba(0,0,0,0.95)',
                  }}
                >
                  CONTATO DE CLIENTE?
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Mockup de Celular Gigante - Entra aos 1.6s (frame 48) com elastic spring scale e push-in contínuo */}
        {frame >= 46 && (
          <div
            style={{
              marginTop: 18,
              width: 880,
              height: 940,
              background: 'rgba(17, 24, 39, 0.96)',
              borderRadius: 40,
              border: '2.5px solid rgba(255, 255, 255, 0.18)',
              boxShadow:
                '0 25px 60px rgba(0, 0, 0, 0.9), 0 0 35px rgba(91, 108, 255, 0.25)',
              transform: `scale(${Math.max(0, springPhone) * cardPushIn}) translateY(${phoneFloat}px)`,
              opacity: Math.min(1, springPhone),
              display: 'flex',
              flexDirection: 'column',
              padding: '28px 32px',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Topo do Celular: Barra de Status + Selo Simulação */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
                paddingBottom: 16,
                marginBottom: 24,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <div
                  style={{
                    width: 14,
                    height: 14,
                    borderRadius: '50%',
                    backgroundColor: '#5B6CFF',
                    boxShadow: '0 0 8px #5B6CFF',
                  }}
                />
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#CBD5E1',
                  }}
                >
                  Caixa de Entrada Multicanais
                </span>
              </div>

              {/* Selo Simulação */}
              <div
                style={{
                  padding: '4px 16px',
                  borderRadius: 9999,
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid rgba(255, 255, 255, 0.16)',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#94A3B8',
                  }}
                >
                  Simulação
                </span>
              </div>
            </div>

            {/* Notificação 1: WhatsApp (entra aos 2.073s / f=62) */}
            <div
              style={{
                background: frame >= 62 ? 'rgba(37, 211, 102, 0.14)' : 'rgba(255, 255, 255, 0.04)',
                border: frame >= 62 ? '2px solid rgba(37, 211, 102, 0.65)' : '1.5px solid rgba(255, 255, 255, 0.08)',
                borderRadius: 24,
                padding: '24px 28px',
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
                transform: frame >= 62 ? `scale(${Math.max(1, springWpp)})` : 'scale(1)',
                boxShadow: frame >= 62 ? '0 10px 28px rgba(37, 211, 102, 0.25)' : 'none',
                transition: 'all 0.2s',
                marginBottom: 20,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                  <div
                    style={{
                      width: 16,
                      height: 16,
                      borderRadius: '50%',
                      backgroundColor: '#25D366',
                      boxShadow: '0 0 10px #25D366',
                    }}
                  />
                  <span
                    style={{
                      fontFamily,
                      fontSize: 36,
                      fontWeight: 800,
                      color: '#25D366',
                    }}
                  >
                    WhatsApp Comercial
                  </span>
                </div>
                <div
                  style={{
                    padding: '6px 16px',
                    borderRadius: 10,
                    background: 'rgba(239, 68, 68, 0.25)',
                    border: '1.5px solid rgba(239, 68, 68, 0.7)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#FCA5A5',
                    }}
                  >
                    Sem Registro
                  </span>
                </div>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#F1F5F9',
                  lineHeight: 1.3,
                }}
              >
                "Olá, quero fechar o pedido hoje! Como faço o pagamento?"
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#CBD5E1',
                }}
              >
                Aguardando atendimento manual...
              </span>
            </div>

            {/* Notificação 2: Instagram Direct (entra aos 2.794s / f=84) */}
            <div
              style={{
                background: frame >= 84 ? 'rgba(225, 48, 108, 0.14)' : 'rgba(255, 255, 255, 0.04)',
                border: frame >= 84 ? '2px solid rgba(225, 48, 108, 0.65)' : '1.5px solid rgba(255, 255, 255, 0.08)',
                borderRadius: 24,
                padding: '24px 28px',
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
                transform: frame >= 84 ? `scale(${Math.max(1, springInsta)})` : 'scale(1)',
                boxShadow: frame >= 84 ? '0 10px 28px rgba(225, 48, 108, 0.25)' : 'none',
                transition: 'all 0.2s',
                marginBottom: 20,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                  <div
                    style={{
                      width: 16,
                      height: 16,
                      borderRadius: '50%',
                      backgroundColor: '#E1306C',
                      boxShadow: '0 0 10px #E1306C',
                    }}
                  />
                  <span
                    style={{
                      fontFamily,
                      fontSize: 36,
                      fontWeight: 800,
                      color: '#E1306C',
                    }}
                  >
                    Instagram Direct
                  </span>
                </div>
                <div
                  style={{
                    padding: '6px 16px',
                    borderRadius: 10,
                    background: 'rgba(239, 68, 68, 0.25)',
                    border: '1.5px solid rgba(239, 68, 68, 0.7)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#FCA5A5',
                    }}
                  >
                    Lead Perdido
                  </span>
                </div>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#F1F5F9',
                  lineHeight: 1.3,
                }}
              >
                "Mandei mensagem ontem pelo direct, alguém pode me atender?"
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#CBD5E1',
                }}
              >
                Não sincronizado com o CRM...
              </span>
            </div>

            {/* Banner de Alerta na base do celular (entra aos 3.5s / f=105) */}
            {frame >= 105 && (
              <div
                style={{
                  marginTop: 'auto',
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1.5px solid rgba(239, 68, 68, 0.7)',
                  borderRadius: 20,
                  padding: '16px 24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 12,
                  transform: `scale(${Math.max(0, springAlert) * pulseAlert})`,
                  boxShadow: '0 8px 24px rgba(239, 68, 68, 0.3)',
                }}
              >
                <span style={{fontSize: 34}}>⚠️</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FCA5A5',
                  }}
                >
                  Contatos dispersos sem CRM integrado
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
