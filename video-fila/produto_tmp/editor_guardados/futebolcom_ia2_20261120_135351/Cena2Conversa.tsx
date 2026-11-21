import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
  OffthreadVideo,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2Conversa: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no fundo (pan vertical + zoom suave 1.05 -> 1.14)
  const bgScale = interpolate(frame, [0, 208], [1.05, 1.14], {
    extrapolateRight: 'clamp',
  });
  const bgPanY = interpolate(frame, [0, 208], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Movimento sutil de aproximação de câmera em direção à conversa (1.0 -> 1.04)
  const camZoom = interpolate(frame, [0, 208], [1.0, 1.04], {
    extrapolateRight: 'clamp',
  });

  // Entrada e perspectiva sutil do celular
  const phoneSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, mass: 0.8},
  });
  const phoneRotateY = interpolate(frame, [0, 25], [6, 0], {
    extrapolateRight: 'clamp',
  });
  const phoneFloatY = Math.sin(frame * 0.1) * 3;

  // Timings sincronizados estritamente com a fala:
  // 1. Mensagem 1 cliente (frame 6 = ~0.2s relativo)
  const msg1Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, mass: 0.7},
  });

  // 2. Indicador 'IA digitando...' (frame 20 a 43)
  const isTyping = frame >= 20 && frame < 44;

  // 3. Resposta IA com foto real inline (frame 44 = ~1.46s / 13.38s global - no exato instante de 'opções ilustradas')
  const msg2Spring = spring({
    frame: frame - 44,
    fps,
    config: {damping: 14, mass: 0.7},
  });

  // 4. Mensagem 2 confirmação cliente (frame 138 = ~4.6s / 16.5s global - 'esclarece detalhes')
  const msg3Spring = spring({
    frame: frame - 138,
    fps,
    config: {damping: 14, mass: 0.7},
  });

  // Scroll suave e seguro da conversa garantindo que nenhum balão seja cortado
  const chatScrollY = interpolate(frame, [136, 148], [0, -35], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Microinteração de pulso no botão do cardápio inline
  const btnPulse = 1 + Math.sin(frame * 0.18) * 0.03;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#31060F',
      }}
    >
      {/* Fundo dinâmico da lanchonete com desfoque cinematográfico (bokeh) suave, conectando ao ambiente físico */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale}) translateY(${bgPanY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(22px) brightness(0.38) saturate(1.2)',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu escuro da marca para contraste sofisticado com o celular */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 50%, rgba(49, 6, 15, 0.72) 0%, rgba(15, 2, 5, 0.92) 85%)',
        }}
      />

      {/* Topo Informativo Rótulo Fixo (Safe Zone: y = 155 a 245) */}
      <div
        style={{
          position: 'absolute',
          top: 155,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 30,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 20,
            background: 'rgba(20, 5, 10, 0.9)',
            border: '2px solid #E11D48',
            boxShadow: '0 8px 24px rgba(225, 29, 72, 0.35)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>
        <div
          style={{
            marginTop: 8,
            fontFamily,
            fontSize: 42,
            fontWeight: 900,
            color: '#FFFFFF',
            textAlign: 'center',
            textShadow: '0 4px 16px rgba(0,0,0,0.8)',
          }}
        >
          Cardápio Ilustrado + Atendimento IA
        </div>
      </div>

      {/* Mockup Mobile do Celular (Posicionado em y=280 a 1290, liberando espaço total para o Karaoke em y >= 1410) */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: (1080 - 940) / 2, // 70px
          width: 940,
          transform: `perspective(1000px) scale(${camZoom * Math.max(0, phoneSpring)}) translateY(${phoneFloatY}px) rotateY(${phoneRotateY}deg)`,
          opacity: interpolate(phoneSpring, [0, 0.2, 1], [0, 0.8, 1]),
          zIndex: 40,
        }}
      >
        {/* Container do Smartphone */}
        <div
          style={{
            width: 940,
            height: 1010,
            borderRadius: 44,
            border: '8px solid #334155',
            background: '#0B141A',
            boxShadow:
              '0 30px 70px rgba(0, 0, 0, 0.95), 0 0 45px rgba(225, 29, 72, 0.25)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            position: 'relative',
          }}
        >
          {/* Barra Superior WhatsApp Institucional */}
          <div
            style={{
              height: 95,
              background: '#1F2C34',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 24px',
              borderBottom: '1.5px solid #2A3942',
              flexShrink: 0,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              {/* Ícone Vetorial da Marca */}
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: '50%',
                  backgroundColor: '#E11D48',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <svg
                  width="32"
                  height="32"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#FFFFFF"
                  strokeWidth="2.4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="5" y="2" width="14" height="20" rx="3" />
                  <line x1="9" y1="7" x2="15" y2="7" />
                  <line x1="9" y1="12" x2="15" y2="12" />
                  <line x1="9" y1="17" x2="12" y2="17" />
                </svg>
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 800,
                    color: '#E9EDEF',
                  }}
                >
                  Cardápio Digital
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#25D366',
                  }}
                >
                  🟢 Online com IA
                </span>
              </div>
            </div>

            {/* Selo Simulação Legível (≥ 32px) */}
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#94A3B8',
                background: 'rgba(255, 255, 255, 0.08)',
                padding: '4px 16px',
                borderRadius: 14,
                border: '1px solid rgba(255, 255, 255, 0.15)',
              }}
            >
              Simulação
            </div>
          </div>

          {/* Área de Conversa com Continuidade Espacial Perfeita (Sem tela preta ou modal sobreposto) */}
          <div
            style={{
              flex: 1,
              padding: '24px 22px',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              background: '#0B141A',
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
                transform: `translateY(${chatScrollY}px)`,
                transition: 'transform 0.3s ease',
              }}
            >
              {/* Mensagem 1: Cliente */}
              {frame >= 6 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '88%',
                    background: '#202C33',
                    borderRadius: '20px 20px 20px 6px',
                    padding: '16px 22px',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)',
                    transform: `scale(${Math.max(0, msg1Spring)})`,
                    transformOrigin: 'bottom left',
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 38,
                      fontWeight: 600,
                      lineHeight: 1.3,
                      color: '#E9EDEF',
                    }}
                  >
                    Boa noite! Esse lanche vem com molho especial?
                  </div>
                </div>
              )}

              {/* Indicador de Digitando com IA */}
              {isTyping && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    background: '#005C4B',
                    borderRadius: '20px 20px 6px 20px',
                    padding: '14px 24px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#E9EDEF',
                    }}
                  >
                    IA digitando
                  </span>
                  <span
                    style={{
                      display: 'flex',
                      gap: 6,
                      alignItems: 'center',
                    }}
                  >
                    {[0, 1, 2].map((dotIdx) => {
                      const dotScale =
                        1 + Math.sin(frame * 0.35 + dotIdx * 1.2) * 0.4;
                      return (
                        <span
                          key={dotIdx}
                          style={{
                            width: 9,
                            height: 9,
                            borderRadius: '50%',
                            background: '#E9EDEF',
                            transform: `scale(${dotScale})`,
                          }}
                        />
                      );
                    })}
                  </span>
                </div>
              )}

              {/* Mensagem 2: Empresa / IA com Foto Real e Card Inline Contínuo (Entra em 'opções ilustradas') */}
              {frame >= 44 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '94%',
                    background: '#005C4B',
                    borderRadius: '20px 20px 6px 20px',
                    padding: '14px 20px',
                    boxShadow: '0 6px 20px rgba(0, 0, 0, 0.65)',
                    transform: `scale(${Math.max(0, msg2Spring)})`,
                    transformOrigin: 'bottom right',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 10,
                  }}
                >
                  {/* Texto da Mensagem */}
                  <div
                    style={{
                      fontFamily,
                      fontSize: 38,
                      fontWeight: 600,
                      lineHeight: 1.3,
                      color: '#E9EDEF',
                    }}
                  >
                    Boa noite! Sim, acompanha nosso molho da casa. Veja a foto e peça direto aqui:
                  </div>

                  {/* Card Inline de Produto Ilustrado com Foto Real */}
                  <div
                    style={{
                      background: '#0B141A',
                      border: '2px solid rgba(225, 29, 72, 0.65)',
                      borderRadius: 20,
                      overflow: 'hidden',
                      boxShadow: '0 10px 24px rgba(0, 0, 0, 0.8)',
                    }}
                  >
                    {/* Foto Real do Lanche */}
                    <div
                      style={{
                        width: '100%',
                        height: 180,
                        position: 'relative',
                        overflow: 'hidden',
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
                      <div
                        style={{
                          position: 'absolute',
                          top: 10,
                          left: 12,
                          background: 'rgba(0, 0, 0, 0.85)',
                          padding: '6px 16px',
                          borderRadius: 14,
                          border: '1.5px solid rgba(225, 29, 72, 0.7)',
                          fontFamily,
                          fontSize: 34,
                          fontWeight: 900,
                          color: '#FFFFFF',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.6)',
                        }}
                      >
                        <span>📸</span>
                        <span>Cardápio com Fotos</span>
                      </div>
                    </div>

                    {/* Informações do Produto (Sem números inventados, todas as fontes >= 34px) */}
                    <div
                      style={{
                        padding: '14px 18px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        background: 'rgba(15, 23, 42, 0.96)',
                      }}
                    >
                      <div>
                        <div
                          style={{
                            fontFamily,
                            fontSize: 38,
                            fontWeight: 900,
                            color: '#FFFFFF',
                          }}
                        >
                          Burger Artesanal da Casa
                        </div>
                        <div
                          style={{
                            fontFamily,
                            fontSize: 34,
                            fontWeight: 800,
                            color: '#FFFFFF',
                            marginTop: 4,
                            textShadow: '0 2px 8px rgba(0, 0, 0, 0.8)',
                          }}
                        >
                          Acompanha queijo e molho especial
                        </div>
                      </div>

                      {/* Botão de Ação Direta */}
                      <div
                        style={{
                          transform: `scale(${btnPulse})`,
                          fontFamily,
                          fontSize: 34,
                          fontWeight: 900,
                          color: '#FFFFFF',
                          background: '#E11D48',
                          padding: '12px 22px',
                          borderRadius: 16,
                          boxShadow: '0 4px 14px rgba(225, 29, 72, 0.6)',
                          whiteSpace: 'nowrap',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                        }}
                      >
                        <span>Pedir Direto</span>
                        <span>➔</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Mensagem 3: Cliente confirmando (Entra com o chat contínuo) */}
              {frame >= 138 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '88%',
                    background: '#202C33',
                    borderRadius: '20px 20px 20px 6px',
                    padding: '16px 22px',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)',
                    transform: `scale(${Math.max(0, msg3Spring)})`,
                    transformOrigin: 'bottom left',
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 38,
                      fontWeight: 700,
                      lineHeight: 1.3,
                      color: '#E9EDEF',
                    }}
                  >
                    Perfeito, vou querer um com adicionais!
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Barra Inferior de Digitação (WhatsApp Mobile Real - 100% visível, livre do Karaoke) */}
          <div
            style={{
              height: 85,
              background: '#1F2C34',
              display: 'flex',
              alignItems: 'center',
              padding: '0 18px',
              borderTop: '1.5px solid #2A3942',
              gap: 12,
              flexShrink: 0,
            }}
          >
            <div
              style={{
                flex: 1,
                height: 54,
                borderRadius: 27,
                background: '#2A3942',
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
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#8696A0',
                }}
              >
                Mensagem
              </span>
            </div>
            <div
              style={{
                width: 54,
                height: 54,
                borderRadius: '50%',
                background: '#00A884',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 26,
              }}
            >
              🎤
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
