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
import {CORES} from './constants';

interface Cena2Props {
  fontFamily: string;
}

export const Cena2Conversa: React.FC<Cena2Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com zoom contínuo suave (1.00 -> 1.07)
  const bgScale = interpolate(frame, [0, 247], [1.0, 1.07], {
    extrapolateRight: 'clamp',
  });

  // Fade out suave na transição final (frames 232-247)
  const cenaOpacity = interpolate(frame, [232, 247], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Topo: Rótulo "02. O ATENDIMENTO" (frame 4)
  const rotuloSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Container do Smartphone surge no frame 10 (~0.33s)
  const phoneSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Leve flutuação suave do celular para dinamismo
  const phoneFloat = Math.sin(frame / 16) * 5;

  // Sincronização dos balões do WhatsApp:
  // Balão 1 (Cliente): entra no frame 16 (~0.53s)
  const b1Spring = spring({frame: frame - 16, fps, config: {damping: 13, stiffness: 140}});

  // Digitando 1 (Empresa): ativo entre frames 44 e 68
  const digitando1Ativo = frame >= 44 && frame < 68;

  // Balão 2 (Empresa): entra no frame 68 (~2.26s)
  const b2Spring = spring({frame: frame - 68, fps, config: {damping: 13, stiffness: 150}});

  // Balão 3 (Cliente): entra no frame 110 (~3.66s)
  const b3Spring = spring({frame: frame - 110, fps, config: {damping: 13, stiffness: 140}});

  // Digitando 2 (Empresa): ativo entre frames 135 e 156
  const digitando2Ativo = frame >= 135 && frame < 156;

  // Balão 4 (Empresa): entra no frame 156 (~5.20s)
  const b4Spring = spring({frame: frame - 156, fps, config: {damping: 13, stiffness: 150}});

  // Altura dinâmica inteligente do celular: cresce conforme as mensagens entram!
  // Elimina COMPLETAMENTE qualquer container vazio ou espaço escuro inútil!
  const phoneHeight = interpolate(
    frame,
    [10, 65, 75, 110, 120, 155, 168],
    [520, 520, 680, 680, 790, 790, 890],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  // Badges da Solução Completa (Blog SEO + Podcast):
  // Aparecem quando a narração diz: "enquanto o blog com SEO e o podcast rodam"
  const blogSpring = spring({frame: frame - 138, fps, config: {damping: 13, stiffness: 150}});
  const podcastSpring = spring({frame: frame - 168, fps, config: {damping: 13, stiffness: 150}});

  // Rolagem suave do chat interno quando atinge capacidade máxima
  const chatScroll = interpolate(frame, [140, 180], [0, -170], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: cenaOpacity, overflow: 'hidden'}}>
      {/* Imagem de Fundo com Zoom Contínuo */}
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
        {/* Camada de ambientação escura */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(17, 24, 39, 0.45) 0%, rgba(11, 15, 25, 0.92) 100%)',
          }}
        />
      </div>

      {/* Orbs de iluminação colorida */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 40 + Math.sin(frame / 20) * 20,
          width: 440,
          height: 440,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(244,114,182,0.18) 0%, transparent 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 450,
          right: 40 + Math.cos(frame / 20) * 20,
          width: 420,
          height: 420,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(16,185,129,0.14) 0%, transparent 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo Informativo Enxuto: y = 175 a 340 */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 60,
        }}
      >
        {/* Rótulo e Selo Simulação */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            opacity: rotuloSpring,
            transform: `translateY(${(1 - rotuloSpring) * -15}px)`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 22px',
              borderRadius: 24,
              backgroundColor: 'rgba(17, 24, 39, 0.94)',
              border: `1.5px solid ${CORES.bordaCard}`,
              boxShadow: '0 4px 16px rgba(0,0,0,0.6)',
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: CORES.marca,
                boxShadow: `0 0 8px ${CORES.marca}`,
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: CORES.textoPrincipal,
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              02. O ATENDIMENTO
            </span>
          </div>

          <div
            style={{
              padding: '6px 16px',
              borderRadius: 20,
              backgroundColor: 'rgba(55, 65, 81, 0.9)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 26,
                fontWeight: 800,
                color: '#CBD5E1',
                letterSpacing: 1,
                textTransform: 'uppercase',
              }}
            >
              Simulação
            </span>
          </div>
        </div>

        {/* Linha Dinâmica: Inicialmente mostra "Fábrica de Conteúdo"; aos frames 138+, acende os badges Blog SEO & Podcast */}
        {frame < 138 ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              backgroundColor: 'rgba(17, 24, 39, 0.9)',
              padding: '8px 22px',
              borderRadius: 18,
              border: '1px solid rgba(244, 114, 182, 0.35)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: CORES.marca,
                textTransform: 'uppercase',
              }}
            >
              Fábrica de Conteúdo
            </span>
            <span style={{color: 'rgba(255,255,255,0.4)', fontSize: 30}}>•</span>
            <span
              style={{
                fontFamily,
                fontSize: 30,
                fontWeight: 700,
                color: '#FFFFFF',
              }}
            >
              Agente Automático
            </span>
          </div>
        ) : (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            {/* Badge Blog SEO */}
            <div
              style={{
                opacity: Math.max(0, Math.min(1, blogSpring)),
                transform: `scale(${0.9 + blogSpring * 0.1})`,
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 20px',
                borderRadius: 18,
                backgroundColor: 'rgba(17, 24, 39, 0.95)',
                border: '1.5px solid #38BDF8',
                boxShadow: '0 4px 16px rgba(56, 189, 248, 0.35)',
              }}
            >
              <span style={{fontSize: 26}}>✍️</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 28,
                  fontWeight: 800,
                  color: '#38BDF8',
                }}
              >
                Blog SEO Rodando
              </span>
            </div>

            {/* Badge Podcast */}
            <div
              style={{
                opacity: Math.max(0, Math.min(1, podcastSpring)),
                transform: `scale(${0.9 + podcastSpring * 0.1})`,
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 20px',
                borderRadius: 18,
                backgroundColor: 'rgba(17, 24, 39, 0.95)',
                border: `1.5px solid ${CORES.marca}`,
                boxShadow: `0 4px 16px ${CORES.marcaGlow}`,
              }}
            >
              <span style={{fontSize: 26}}>🎙️</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 28,
                  fontWeight: 800,
                  color: CORES.marca,
                }}
              >
                Podcast Rodando
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Mockup do Celular com WhatsApp Completo (Altura Dinâmica Integrada) */}
      <div
        style={{
          position: 'absolute',
          top: 350,
          left: 90,
          right: 90,
          height: phoneHeight,
          opacity: Math.max(0, Math.min(1, phoneSpring)),
          transform: `translateY(${(1 - phoneSpring) * 50 + phoneFloat}px)`,
          zIndex: 40,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            backgroundColor: '#0F172A',
            borderRadius: 36,
            border: '3px solid rgba(244, 114, 182, 0.45)',
            boxShadow:
              '0 25px 60px rgba(0,0,0,0.8), 0 0 30px rgba(244, 114, 182, 0.22), inset 0 0 15px rgba(255,255,255,0.05)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Header do WhatsApp */}
          <div
            style={{
              padding: '16px 22px',
              backgroundColor: '#1E293B',
              borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              zIndex: 10,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #F472B6 0%, #DB2777 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 24,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  boxShadow: `0 0 12px ${CORES.marcaGlow}`,
                }}
              >
                IA
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                  }}
                >
                  Fábrica de Marketing IA
                </div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginTop: 2,
                  }}
                >
                  <div
                    style={{
                      width: 9,
                      height: 9,
                      borderRadius: '50%',
                      backgroundColor: '#10B981',
                      boxShadow: '0 0 8px #10B981',
                    }}
                  />
                  <span
                    style={{
                      fontFamily,
                      fontSize: 26,
                      fontWeight: 700,
                      color: '#10B981',
                    }}
                  >
                    Agente de Respostas • Online
                  </span>
                </div>
              </div>
            </div>

            <div
              style={{
                padding: '6px 14px',
                borderRadius: 16,
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                border: '1px solid rgba(16, 185, 129, 0.5)',
                fontFamily,
                fontSize: 24,
                fontWeight: 800,
                color: '#34D399',
              }}
            >
              ATIVO
            </div>
          </div>

          {/* Área de Mensagens do Chat */}
          <div
            style={{
              flex: 1,
              padding: '20px',
              backgroundColor: '#0A0F1D',
              backgroundImage:
                'radial-gradient(circle at 50% 50%, rgba(255,255,255,0.02) 1px, transparent 1px)',
              backgroundSize: '24px 24px',
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
                transform: `translateY(${chatScroll}px)`,
                transition: 'transform 0.1s ease-out',
              }}
            >
              {/* Balão 1: Cliente */}
              {frame >= 16 && (
                <div
                  style={{
                    opacity: Math.max(0, Math.min(1, b1Spring)),
                    transform: `translateY(${(1 - b1Spring) * 20}px) scale(${0.92 + b1Spring * 0.08})`,
                    alignSelf: 'flex-start',
                    maxWidth: '85%',
                    backgroundColor: '#1E293B',
                    borderRadius: '20px 20px 20px 6px',
                    padding: '16px 20px',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    boxShadow: '0 6px 16px rgba(0,0,0,0.4)',
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 24,
                      fontWeight: 700,
                      color: '#94A3B8',
                      marginBottom: 4,
                    }}
                  >
                    Cliente
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 600,
                      lineHeight: 1.35,
                      color: '#F8FAFC',
                    }}
                  >
                    Olá! Vi a postagem nova. Vocês fazem esse serviço para empresas da região?
                  </div>
                </div>
              )}

              {/* Indicador Digitando 1 */}
              {digitando1Ativo && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    backgroundColor: 'rgba(219, 39, 119, 0.25)',
                    border: '1px solid rgba(244, 114, 182, 0.45)',
                    borderRadius: '20px 20px 6px 20px',
                    padding: '12px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 26,
                      fontWeight: 700,
                      color: CORES.marca,
                    }}
                  >
                    Agente IA digitando
                  </span>
                  <div style={{display: 'flex', gap: 4}}>
                    <div
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        backgroundColor: CORES.marca,
                        opacity: Math.sin(frame / 4) * 0.5 + 0.5,
                      }}
                    />
                    <div
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        backgroundColor: CORES.marca,
                        opacity: Math.sin(frame / 4 + 1) * 0.5 + 0.5,
                      }}
                    />
                    <div
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        backgroundColor: CORES.marca,
                        opacity: Math.sin(frame / 4 + 2) * 0.5 + 0.5,
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Balão 2: Empresa (Agente IA) */}
              {frame >= 68 && (
                <div
                  style={{
                    opacity: Math.max(0, Math.min(1, b2Spring)),
                    transform: `translateY(${(1 - b2Spring) * 20}px) scale(${0.92 + b2Spring * 0.08})`,
                    alignSelf: 'flex-end',
                    maxWidth: '86%',
                    background: 'linear-gradient(135deg, #BE185D 0%, #9D174D 100%)',
                    borderRadius: '20px 20px 6px 20px',
                    padding: '16px 20px',
                    border: '1.5px solid rgba(244, 114, 182, 0.5)',
                    boxShadow: '0 8px 24px rgba(190, 24, 93, 0.35)',
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 24,
                      fontWeight: 800,
                      color: '#FCE7F3',
                      marginBottom: 4,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <span>⚡ Agente IA</span>
                    <span style={{fontSize: 20}}>✓✓</span>
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      lineHeight: 1.35,
                      color: '#FFFFFF',
                    }}
                  >
                    Olá! Fazemos sim. Atendemos empresas com projetos personalizados para a sua necessidade.
                  </div>
                </div>
              )}

              {/* Balão 3: Cliente */}
              {frame >= 110 && (
                <div
                  style={{
                    opacity: Math.max(0, Math.min(1, b3Spring)),
                    transform: `translateY(${(1 - b3Spring) * 20}px) scale(${0.92 + b3Spring * 0.08})`,
                    alignSelf: 'flex-start',
                    maxWidth: '85%',
                    backgroundColor: '#1E293B',
                    borderRadius: '20px 20px 20px 6px',
                    padding: '16px 20px',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    boxShadow: '0 6px 16px rgba(0,0,0,0.4)',
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 24,
                      fontWeight: 700,
                      color: '#94A3B8',
                      marginBottom: 4,
                    }}
                  >
                    Cliente
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 600,
                      lineHeight: 1.35,
                      color: '#F8FAFC',
                    }}
                  >
                    Ótimo, como faço para explicar o que preciso?
                  </div>
                </div>
              )}

              {/* Indicador Digitando 2 */}
              {digitando2Ativo && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    backgroundColor: 'rgba(219, 39, 119, 0.25)',
                    border: '1px solid rgba(244, 114, 182, 0.45)',
                    borderRadius: '20px 20px 6px 20px',
                    padding: '12px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 26,
                      fontWeight: 700,
                      color: CORES.marca,
                    }}
                  >
                    Agente IA digitando
                  </span>
                </div>
              )}

              {/* Balão 4: Empresa (Agente IA) */}
              {frame >= 156 && (
                <div
                  style={{
                    opacity: Math.max(0, Math.min(1, b4Spring)),
                    transform: `translateY(${(1 - b4Spring) * 20}px) scale(${0.92 + b4Spring * 0.08})`,
                    alignSelf: 'flex-end',
                    maxWidth: '86%',
                    background: 'linear-gradient(135deg, #BE185D 0%, #9D174D 100%)',
                    borderRadius: '20px 20px 6px 20px',
                    padding: '16px 20px',
                    border: '1.5px solid rgba(244, 114, 182, 0.5)',
                    boxShadow: '0 8px 24px rgba(190, 24, 93, 0.35)',
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 24,
                      fontWeight: 800,
                      color: '#FCE7F3',
                      marginBottom: 4,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <span>⚡ Agente IA</span>
                    <span style={{fontSize: 20}}>✓✓</span>
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      lineHeight: 1.35,
                      color: '#FFFFFF',
                    }}
                  >
                    Enviei uma mensagem para você com as informações para conversarmos melhor!
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Barra de Entrada de Chat Realista no Rodapé do Mockup (Elimina Caixa Vazia!) */}
          <div
            style={{
              padding: '14px 20px',
              backgroundColor: '#1E293B',
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
            }}
          >
            <div
              style={{
                flex: 1,
                backgroundColor: '#0F172A',
                borderRadius: 20,
                padding: '10px 18px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <span style={{fontSize: 24, color: '#94A3B8'}}>💬</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 26,
                  color: '#64748B',
                }}
              >
                Mensagem...
              </span>
            </div>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: '50%',
                backgroundColor: CORES.marca,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFFFFF',
                fontSize: 22,
                fontWeight: 900,
              }}
            >
              ➤
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
