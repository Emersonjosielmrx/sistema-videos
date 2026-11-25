import React from 'react';
import {
  AbsoluteFill,
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

  // Transição para o B-Roll de Motion Design aos ~15.34s (f=95, quando a fala diz "WhatsApp")
  const isBRoll = frame >= 95;

  // Câmera contínua da parte com o apresentador (frames 0 a 95)
  const videoScale = interpolate(frame, [0, 95], [1.08, 1.14], {
    extrapolateRight: 'clamp',
  });
  const videoTranslateY = interpolate(frame, [0, 95], [125, 132], {
    extrapolateRight: 'clamp',
  });

  // Animações do B-Roll de Demonstração do Produto SuperChat IA + CRM (frames 95 a 246)
  const springBRollIn = spring({
    frame: frame - 95,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Slow push-in contínuo no B-Roll
  const bRollPushIn = interpolate(frame, [95, 246], [1.0, 1.06], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Entrada sincronizada das mensagens no B-roll:
  // "WhatsApp" aos 15.34s (frame 95)
  const springMsgWpp = spring({
    frame: frame - 95,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // "Telegram" aos 16.32s (frame 125)
  const springMsgTg = spring({
    frame: frame - 125,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // "Instagram" aos 16.90s (frame 142)
  const springMsgIg = spring({
    frame: frame - 142,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // "CRM com IA sozinha" ativação a partir de frame 160
  const isCrmActive = frame >= 160;
  const springCrm = spring({
    frame: frame - 160,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Pulso contínuo do CRM
  const crmPulse = isCrmActive ? 1 + 0.04 * Math.sin((frame / 8) * Math.PI) : 1;
  const shineCRM = interpolate((frame % 50), [0, 50], [-100, 200]);

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D13', overflow: 'hidden'}}>
      {/* ============================================================== */}
      {/* PARTE 1: Apresentador no escritório moderno (frames 0 a 94)    */}
      {/* ============================================================== */}
      {!isBRoll && (
        <>
          {/* Vídeo do apresentador posicionado com enquadramento limpo */}
          <div
            style={{
              position: 'absolute',
              width: '100%',
              height: '100%',
              transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
              transformOrigin: 'center 40%',
            }}
          >
            <OffthreadVideo
              src={staticFile('dono_2.mp4')}
              muted
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />

            {/* Gradiente escuro no topo para contraste seguro */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 340,
                background:
                  'linear-gradient(180deg, rgba(11, 13, 19, 0.95) 0%, rgba(11, 13, 19, 0.6) 200px, transparent 340px)',
                pointerEvents: 'none',
              }}
            />
          </div>

          {/* Faixa segura superior: y=156 a y=310 */}
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
            {/* Rótulo de contexto */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '6px 24px',
                borderRadius: 9999,
                background: 'rgba(17, 24, 39, 0.95)',
                border: '1.5px solid rgba(91, 108, 255, 0.55)',
                boxShadow: '0 6px 18px rgba(0, 0, 0, 0.7)',
              }}
            >
              <div
                style={{
                  width: 12,
                  height: 12,
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
                Como Funciona • SuperChat IA
              </span>
            </div>

            {/* Linha de fluxo ampliada e espaçosa com tipografia grande e legível */}
            <div
              style={{
                marginTop: 14,
                width: '100%',
                maxWidth: 960,
                background: 'rgba(17, 24, 39, 0.96)',
                border: '1.5px solid rgba(255, 255, 255, 0.16)',
                borderRadius: 20,
                padding: '12px 24px',
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.8)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              {/* Canais com ícones coloridos */}
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
                  <div
                    style={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: '#25D366',
                    }}
                  />
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#F1F5F9',
                    }}
                  >
                    WhatsApp
                  </span>
                </div>
                <span style={{color: '#64748B', fontSize: 28}}>•</span>
                <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
                  <div
                    style={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: '#229ED9',
                    }}
                  />
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#F1F5F9',
                    }}
                  >
                    Telegram
                  </span>
                </div>
                <span style={{color: '#64748B', fontSize: 28}}>•</span>
                <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
                  <div
                    style={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: '#E1306C',
                    }}
                  />
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#F1F5F9',
                    }}
                  >
                    Instagram
                  </span>
                </div>
              </div>

              {/* Seta e Destino CRM com IA destacado */}
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <span style={{color: '#5B6CFF', fontSize: 32, fontWeight: 900}}>➔</span>
                <div
                  style={{
                    padding: '8px 18px',
                    borderRadius: 12,
                    background: 'linear-gradient(135deg, #5B6CFF, #4338CA)',
                    boxShadow: '0 0 18px rgba(91, 108, 255, 0.5)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 900,
                      color: '#FFFFFF',
                    }}
                  >
                    CRM com IA
                  </span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* ============================================================== */}
      {/* PARTE 2: B-ROLL EM MOTION DESIGN DEMONSTRANDO O PRODUTO REAL   */}
      {/* Substitui o talking head por mockup vivo de mensagens no CRM   */}
      {/* (frames 95 a 246)                                             */}
      {/* ============================================================== */}
      {isBRoll && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            transform: `scale(${bRollPushIn})`,
            transformOrigin: 'center center',
          }}
        >
          {/* Fundo dinâmico com atmosfera de plataforma tech */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background:
                'radial-gradient(circle at 50% 35%, rgba(91, 108, 255, 0.28) 0%, rgba(15, 23, 42, 0.85) 50%, #0B0D13 100%)',
            }}
          />

          {/* Container de conteúdo do B-Roll dentro da safe zone (y=156 a y=1480) */}
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
              transform: `scale(${Math.max(0, springBRollIn)})`,
              opacity: Math.min(1, springBRollIn),
            }}
          >
            {/* Tag de topo do B-roll */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '6px 24px',
                borderRadius: 9999,
                background: 'rgba(17, 24, 39, 0.96)',
                border: '1.5px solid rgba(91, 108, 255, 0.6)',
                boxShadow: '0 6px 20px rgba(0, 0, 0, 0.7)',
                marginBottom: 14,
              }}
            >
              <div
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  backgroundColor: '#10B981',
                  boxShadow: '0 0 10px #10B981',
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
                Demonstração • CRM com IA Ativo
              </span>
            </div>

            {/* Painel Central do SuperChat IA simulando a plataforma */}
            <div
              style={{
                width: '100%',
                maxWidth: 960,
                background: 'rgba(17, 24, 39, 0.96)',
                borderRadius: 36,
                border: '2px solid rgba(91, 108, 255, 0.45)',
                boxShadow:
                  '0 25px 65px rgba(0, 0, 0, 0.92), 0 0 45px rgba(91, 108, 255, 0.25)',
                padding: '28px 32px',
                display: 'flex',
                flexDirection: 'column',
                gap: 20,
              }}
            >
              {/* Header do Painel */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
                  paddingBottom: 16,
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                  <div
                    style={{
                      width: 16,
                      height: 16,
                      borderRadius: '50%',
                      backgroundColor: '#5B6CFF',
                      boxShadow: '0 0 10px #5B6CFF',
                    }}
                  />
                  <span
                    style={{
                      fontFamily,
                      fontSize: 36,
                      fontWeight: 900,
                      color: '#FFFFFF',
                    }}
                  >
                    SuperChat IA • Painel de Entrada
                  </span>
                </div>
                <div
                  style={{
                    padding: '6px 18px',
                    borderRadius: 9999,
                    background: 'rgba(16, 185, 129, 0.18)',
                    border: '1px solid rgba(16, 185, 129, 0.6)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#34D399',
                    }}
                  >
                    IA Ativa 24h
                  </span>
                </div>
              </div>

              {/* Mensagem 1: WhatsApp (entra no frame 95) */}
              <div
                style={{
                  background: 'rgba(37, 211, 102, 0.14)',
                  border: '1.5px solid rgba(37, 211, 102, 0.65)',
                  borderRadius: 22,
                  padding: '18px 24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transform: `scale(${Math.max(0, springMsgWpp)})`,
                  opacity: Math.min(1, springMsgWpp),
                  boxShadow: '0 8px 24px rgba(37, 211, 102, 0.2)',
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                  <div
                    style={{
                      padding: '6px 14px',
                      borderRadius: 12,
                      background: '#25D366',
                      color: '#FFFFFF',
                      fontSize: 28,
                      fontWeight: 900,
                    }}
                  >
                    WA
                  </div>
                  <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
                    <span
                      style={{
                        fontFamily,
                        fontSize: 34,
                        fontWeight: 800,
                        color: '#FFFFFF',
                      }}
                    >
                      WhatsApp Comercial
                    </span>
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 600,
                        color: '#CBD5E1',
                      }}
                    >
                      "Olá, quero saber os valores do serviço!"
                    </span>
                  </div>
                </div>
                <div
                  style={{
                    padding: '6px 16px',
                    borderRadius: 10,
                    background: isCrmActive
                      ? 'rgba(16, 185, 129, 0.25)'
                      : 'rgba(255, 255, 255, 0.1)',
                    border: isCrmActive
                      ? '1px solid #10B981'
                      : '1px solid rgba(255, 255, 255, 0.2)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: isCrmActive ? '#34D399' : '#CBD5E1',
                    }}
                  >
                    {isCrmActive ? '✓ No CRM' : 'Recebido'}
                  </span>
                </div>
              </div>

              {/* Mensagem 2: Telegram (entra no frame 125) */}
              {frame >= 125 && (
                <div
                  style={{
                    background: 'rgba(34, 158, 217, 0.14)',
                    border: '1.5px solid rgba(34, 158, 217, 0.65)',
                    borderRadius: 22,
                    padding: '18px 24px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transform: `scale(${Math.max(0, springMsgTg)})`,
                    opacity: Math.min(1, springMsgTg),
                    boxShadow: '0 8px 24px rgba(34, 158, 217, 0.2)',
                  }}
                >
                  <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                    <div
                      style={{
                        padding: '6px 14px',
                        borderRadius: 12,
                        background: '#229ED9',
                        color: '#FFFFFF',
                        fontSize: 28,
                        fontWeight: 900,
                      }}
                    >
                      TG
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
                      <span
                        style={{
                          fontFamily,
                          fontSize: 34,
                          fontWeight: 800,
                          color: '#FFFFFF',
                        }}
                      >
                        Telegram
                      </span>
                      <span
                        style={{
                          fontFamily,
                          fontSize: 32,
                          fontWeight: 600,
                          color: '#CBD5E1',
                        }}
                      >
                        "Como configuro o multiatendimento?"
                      </span>
                    </div>
                  </div>
                  <div
                    style={{
                      padding: '6px 16px',
                      borderRadius: 10,
                      background: isCrmActive
                        ? 'rgba(16, 185, 129, 0.25)'
                        : 'rgba(255, 255, 255, 0.1)',
                      border: isCrmActive
                        ? '1px solid #10B981'
                        : '1px solid rgba(255, 255, 255, 0.2)',
                    }}
                  >
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 800,
                        color: isCrmActive ? '#34D399' : '#CBD5E1',
                      }}
                    >
                      {isCrmActive ? '✓ No CRM' : 'Recebido'}
                    </span>
                  </div>
                </div>
              )}

              {/* Mensagem 3: Instagram Direct (entra no frame 142) */}
              {frame >= 142 && (
                <div
                  style={{
                    background: 'rgba(225, 48, 108, 0.14)',
                    border: '1.5px solid rgba(225, 48, 108, 0.65)',
                    borderRadius: 22,
                    padding: '18px 24px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transform: `scale(${Math.max(0, springMsgIg)})`,
                    opacity: Math.min(1, springMsgIg),
                    boxShadow: '0 8px 24px rgba(225, 48, 108, 0.2)',
                  }}
                >
                  <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                    <div
                      style={{
                        padding: '6px 14px',
                        borderRadius: 12,
                        background: '#E1306C',
                        color: '#FFFFFF',
                        fontSize: 28,
                        fontWeight: 900,
                      }}
                    >
                      IG
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
                      <span
                        style={{
                          fontFamily,
                          fontSize: 34,
                          fontWeight: 800,
                          color: '#FFFFFF',
                        }}
                      >
                        Instagram Direct
                      </span>
                      <span
                        style={{
                          fontFamily,
                          fontSize: 32,
                          fontWeight: 600,
                          color: '#CBD5E1',
                        }}
                      >
                        "Quero fechar a contratação hoje!"
                      </span>
                    </div>
                  </div>
                  <div
                    style={{
                      padding: '6px 16px',
                      borderRadius: 10,
                      background: isCrmActive
                        ? 'rgba(16, 185, 129, 0.25)'
                        : 'rgba(255, 255, 255, 0.1)',
                      border: isCrmActive
                        ? '1px solid #10B981'
                        : '1px solid rgba(255, 255, 255, 0.2)',
                    }}
                  >
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 800,
                        color: isCrmActive ? '#34D399' : '#CBD5E1',
                      }}
                    >
                      {isCrmActive ? '✓ No CRM' : 'Recebido'}
                    </span>
                  </div>
                </div>
              )}

              {/* Caixa de Automação do CRM com IA (ativa aos 17.44s / f=160) */}
              <div
                style={{
                  marginTop: 6,
                  background: isCrmActive
                    ? 'linear-gradient(135deg, rgba(91, 108, 255, 0.25) 0%, rgba(67, 56, 202, 0.4) 100%)'
                    : 'rgba(255, 255, 255, 0.05)',
                  border: isCrmActive
                    ? '2px solid #818CF8'
                    : '1.5px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: 24,
                  padding: '20px 24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  boxShadow: isCrmActive
                    ? '0 12px 35px rgba(91, 108, 255, 0.4), 0 0 25px rgba(91, 108, 255, 0.25)'
                    : 'none',
                  transform: `scale(${crmPulse * Math.max(1, springCrm)})`,
                  position: 'relative',
                  overflow: 'hidden',
                  transition: 'all 0.25s',
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                  <span style={{fontSize: 38}}>⚡</span>
                  <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
                    <span
                      style={{
                        fontFamily,
                        fontSize: 36,
                        fontWeight: 900,
                        color: '#FFFFFF',
                      }}
                    >
                      Alimentando o CRM com IA
                    </span>
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 700,
                        color: isCrmActive ? '#C7D2FE' : '#94A3B8',
                      }}
                    >
                      {isCrmActive
                        ? 'Contatos criados e organizados automaticamente'
                        : 'Aguardando fluxo de mensagens...'}
                    </span>
                  </div>
                </div>

                <div
                  style={{
                    padding: '8px 20px',
                    borderRadius: 14,
                    background: isCrmActive ? '#10B981' : 'rgba(255, 255, 255, 0.1)',
                    boxShadow: isCrmActive ? '0 0 16px #10B981' : 'none',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 900,
                      color: '#FFFFFF',
                    }}
                  >
                    {isCrmActive ? 'AUTOMÁTICO' : 'STANDBY'}
                  </span>
                </div>

                {/* Brilho passando no card do CRM */}
                {isCrmActive && (
                  <div
                    style={{
                      position: 'absolute',
                      top: 0,
                      bottom: 0,
                      left: `${shineCRM}%`,
                      width: 50,
                      background:
                        'linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent)',
                      transform: 'skewX(-25deg)',
                    }}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
