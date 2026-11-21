import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com zoom contínuo (1.05 -> 1.15)
  const bgScale = interpolate(frame, [0, 274], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Entrada do celular e do selo superior
  const phoneSpring = spring({
    frame,
    fps,
    config: {damping: 15, stiffness: 100},
  });

  const badgeSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada das mensagens sincronizadas com a fala
  // Fala aos 12.11s (frame 15 do vídeo = frame 15 da cena)
  // Msg 1: frame 30
  const msg1Spring = spring({
    frame: frame - 30,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Msg 2: frame 55
  const msg2Spring = spring({
    frame: frame - 55,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Rotação de instâncias ativa a partir do frame 115
  const chipRotated = frame >= 115;
  const chipPulse = 1 + Math.sin(frame * 0.2) * 0.03;
  const chipBadgeSpring = spring({
    frame: frame - 115,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Msg 3: frame 130
  const msg3Spring = spring({
    frame: frame - 130,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Msg 4: frame 170
  const msg4Spring = spring({
    frame: frame - 170,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Msg 5: frame 215
  const msg5Spring = spring({
    frame: frame - 215,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Scroll suave e contido dos balões (máximo -120px) para manter todos visíveis e a tela cheia
  const scrollY = interpolate(
    frame,
    [0, 110, 150, 200, 240],
    [0, 0, -40, -90, -125],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Micro rotação 3D e flutuação contínua
  const rotY = 4 + Math.sin(frame * 0.05) * 2;
  const floatY = Math.sin(frame * 0.08) * 5;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
      }}
    >
      {/* Fundo com Zoom Contínuo */}
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
          src={staticFile('img_2.jpg')}
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
            background:
              'radial-gradient(circle at 50% 30%, rgba(17, 24, 39, 0.45) 0%, rgba(17, 24, 39, 0.92) 100%)',
          }}
        />
      </div>

      {/* Grid cibernético sutil */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(34, 197, 94, 0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(34, 197, 94, 0.06) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
          pointerEvents: 'none',
        }}
      />

      {/* TOPO INFORMATIVO (y = 165 a 265) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          zIndex: 40,
        }}
      >
        {/* Selo Etapa: 02 • COMO FUNCIONA */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 999,
            background: 'rgba(17, 24, 39, 0.94)',
            border: '1.5px solid rgba(34, 197, 94, 0.6)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: '#22C55E',
              boxShadow: '0 0 10px #22C55E',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            02 • Como Funciona
          </span>
        </div>

        {/* Status da Rotação Inteligente */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 22px',
            borderRadius: 999,
            background: chipRotated
              ? 'rgba(34, 197, 94, 0.25)'
              : 'rgba(59, 130, 246, 0.22)',
            border: `1.5px solid ${chipRotated ? '#22C55E' : '#3B82F6'}`,
            transform: `scale(${chipRotated ? chipPulse : 1})`,
          }}
        >
          <span style={{fontSize: 28}}>{chipRotated ? '🔄' : '⚡'}</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: chipRotated ? '#86EFAC' : '#93C5FD',
            }}
          >
            {chipRotated ? 'Instância #02 Ativa' : 'Instância #01 Ativa'}
          </span>
        </div>
      </div>

      {/* MOCKUP DO SMARTPHONE (y = 275 a 1280) */}
      <div
        style={{
          position: 'absolute',
          top: 275,
          left: 75,
          width: 930,
          height: 1000,
          transform: `translateY(${floatY}px) perspective(1200px) rotateY(${rotY}deg) scale(${phoneSpring})`,
          opacity: phoneSpring,
          zIndex: 30,
        }}
      >
        {/* Moldura do Smartphone */}
        <div
          style={{
            width: '100%',
            height: '100%',
            borderRadius: 44,
            background: '#0B0F17',
            border: '4px solid #1F2937',
            boxShadow:
              '0 30px 80px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.1), inset 0 0 20px rgba(0, 0, 0, 0.5)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Header do WhatsApp Mockup */}
          <div
            style={{
              height: 120,
              background: '#111827',
              borderBottom: '2px solid rgba(255, 255, 255, 0.08)',
              padding: '0 28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexShrink: 0,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #22C55E, #15803D)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 14px rgba(34, 197, 94, 0.4)',
                }}
              >
                <span style={{fontSize: 34}}>💬</span>
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    Disparo em Massa IA
                  </span>
                  <span style={{fontSize: 26, color: '#22C55E'}}>✓</span>
                </div>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#4ADE80',
                  }}
                >
                  ● Rotação de Instâncias Ativa
                </span>
              </div>
            </div>

            {/* Selo Obrigatório: Simulação */}
            <div
              style={{
                padding: '6px 16px',
                borderRadius: 10,
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#E2E8F0',
                textTransform: 'uppercase',
              }}
            >
              Simulação
            </div>
          </div>

          {/* Área de Conversa com Fundo Temático */}
          <div
            style={{
              flex: 1,
              background: '#0B141A',
              padding: '20px 24px',
              position: 'relative',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
                transform: `translateY(${scrollY}px)`,
                transition: 'transform 0.25s ease-out',
              }}
            >
              {/* Aviso Seguro do WhatsApp */}
              <div
                style={{
                  alignSelf: 'center',
                  maxWidth: '92%',
                  background: 'rgba(30, 41, 59, 0.85)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: 16,
                  padding: '10px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 10,
                  marginBottom: 6,
                  opacity: interpolate(scrollY, [-35, 0], [0, 1], {
                    extrapolateLeft: 'clamp',
                    extrapolateRight: 'clamp',
                  }),
                }}
              >
                <span style={{fontSize: 26}}>🔒</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#CBD5E1',
                    textAlign: 'center',
                  }}
                >
                  Campanha protegida por rotação de instâncias
                </span>
              </div>

              {/* Indicador de Digitando antes da Mensagem 1 */}
              {frame >= 10 && frame < 30 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    background: '#1E293B',
                    borderRadius: '20px 20px 20px 6px',
                    padding: '12px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  <span style={{fontSize: 24}}>🟢</span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#94A3B8',
                    }}
                  >
                    Digitando mensagem...
                  </span>
                </div>
              )}

              {/* Mensagem 1: Empresa (frame 30+) */}
              {frame >= 30 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '82%',
                    background: '#1E293B',
                    border: '1.5px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '24px 24px 24px 6px',
                    padding: '16px 22px',
                    boxShadow: '0 6px 18px rgba(0, 0, 0, 0.4)',
                    transform: `scale(${msg1Spring})`,
                    opacity: msg1Spring,
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#4ADE80',
                      marginBottom: 4,
                    }}
                  >
                    Instância #01 (Campanha)
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#F8FAFC',
                      lineHeight: 1.35,
                    }}
                  >
                    Olá, Marina! Sua encomenda já está disponível para retirada.
                  </div>
                </div>
              )}

              {/* Mensagem 2: Cliente (frame 55+) */}
              {frame >= 55 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '75%',
                    background: '#166534',
                    border: '1.5px solid rgba(34, 197, 94, 0.4)',
                    borderRadius: '24px 24px 6px 24px',
                    padding: '16px 22px',
                    boxShadow: '0 6px 18px rgba(0, 0, 0, 0.4)',
                    transform: `scale(${msg2Spring})`,
                    opacity: msg2Spring,
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#FFFFFF',
                      lineHeight: 1.35,
                    }}
                  >
                    Que ótimo! Já passo aí hoje.
                  </div>
                </div>
              )}

              {/* Indicador de Rotação Automática de Chip (frame 115+) */}
              {frame >= 115 && (
                <div
                  style={{
                    alignSelf: 'center',
                    padding: '10px 24px',
                    borderRadius: 16,
                    background: 'rgba(34, 197, 94, 0.18)',
                    border: '1.5px solid #22C55E',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    boxShadow: '0 4px 16px rgba(34, 197, 94, 0.3)',
                    transform: `scale(${chipBadgeSpring})`,
                    opacity: chipBadgeSpring,
                  }}
                >
                  <span style={{fontSize: 28}}>🔄</span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 900,
                      color: '#86EFAC',
                      textTransform: 'uppercase',
                    }}
                  >
                    Rotação Automática: Instância #02
                  </span>
                </div>
              )}

              {/* Mensagem 3: Empresa (frame 130+) */}
              {frame >= 130 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '82%',
                    background: '#1E293B',
                    border: '1.5px solid rgba(34, 197, 94, 0.3)',
                    borderRadius: '24px 24px 24px 6px',
                    padding: '16px 22px',
                    boxShadow: '0 6px 18px rgba(0, 0, 0, 0.4)',
                    transform: `scale(${msg3Spring})`,
                    opacity: msg3Spring,
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#86EFAC',
                      marginBottom: 4,
                    }}
                  >
                    Instância #02 (Campanha)
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#F8FAFC',
                      lineHeight: 1.35,
                    }}
                  >
                    Este aviso saiu de um dos nossos números de campanha.
                  </div>
                </div>
              )}

              {/* Mensagem 4: Empresa (frame 170+) */}
              {frame >= 170 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '85%',
                    background: '#1E293B',
                    border: '1.5px solid rgba(34, 197, 94, 0.3)',
                    borderRadius: '24px 24px 24px 6px',
                    padding: '16px 22px',
                    boxShadow: '0 6px 18px rgba(0, 0, 0, 0.4)',
                    transform: `scale(${msg4Spring})`,
                    opacity: msg4Spring,
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#86EFAC',
                      marginBottom: 4,
                    }}
                  >
                    Instância #02 (Campanha)
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#F8FAFC',
                      lineHeight: 1.35,
                    }}
                  >
                    Para qualquer dúvida, fale com nosso atendimento principal.
                  </div>
                </div>
              )}

              {/* Mensagem 5: Cliente (frame 215+) */}
              {frame >= 215 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '75%',
                    background: '#166534',
                    border: '1.5px solid rgba(34, 197, 94, 0.4)',
                    borderRadius: '24px 24px 6px 24px',
                    padding: '16px 22px',
                    boxShadow: '0 6px 18px rgba(0, 0, 0, 0.4)',
                    transform: `scale(${msg5Spring})`,
                    opacity: msg5Spring,
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#FFFFFF',
                      lineHeight: 1.35,
                    }}
                  >
                    Perfeito, obrigada!
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Barra de Entrada de Mensagem do WhatsApp */}
          <div
            style={{
              height: 84,
              background: '#111827',
              borderTop: '1px solid rgba(255, 255, 255, 0.08)',
              padding: '0 20px',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              flexShrink: 0,
            }}
          >
            <div
              style={{
                flex: 1,
                height: 52,
                borderRadius: 26,
                background: '#1F2937',
                display: 'flex',
                alignItems: 'center',
                padding: '0 18px',
                gap: 10,
              }}
            >
              <span style={{fontSize: 26}}>😊</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 500,
                  color: '#94A3B8',
                }}
              >
                Mensagem
              </span>
            </div>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                background: '#22C55E',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span style={{fontSize: 26, color: '#111827'}}>🎙️</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
