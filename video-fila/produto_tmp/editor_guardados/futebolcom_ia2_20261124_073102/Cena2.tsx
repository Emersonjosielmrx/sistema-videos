import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';
import {COLORS, SAFE_ZONE} from './types';

interface Cena2Props {
  fontFamily: string;
}

export const Cena2: React.FC<Cena2Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (scale 1.05 -> 1.16)
  const bgScale = interpolate(frame, [0, 284], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });

  // Micro-dinâmica residual (flutuação 3D contínua do celular)
  const phoneFloatY = Math.sin(frame / 16) * 5;
  const phoneRotateY = -6 + Math.sin(frame / 20) * 1.8;

  // Entrada do rótulo e cabeçalho
  const rotuloSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const titleSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Timing das mensagens do WhatsApp sincronizadas com a narração:
  // Fala 1: "Aqui não tem instalação" (~11.57s -> frame 15 na cena)
  const msg1Spring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Digitando 1 (~12.4s -> frame 38)
  const isTyping1 = frame >= 38 && frame < 58;

  // Fala 2: "O cardápio abre direto no navegador..." (~13.15s -> frame 58)
  const msg2Spring = spring({
    frame: frame - 58,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Transição de fase no chat aos 140 frames (fala "com fotos e a IA responde dúvidas...")
  // Fase 1 desvanece suavemente para a Fase 2 entrar límpida sem corte de texto
  const phase1Opacity = interpolate(frame, [136, 146], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const phase2Opacity = interpolate(frame, [142, 150], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Card do Cardápio com Fotos (~frame 146 / 15.86s "com fotos")
  const cardFotoSpring = spring({
    frame: frame - 146,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Fala 4: "...e a IA responde dúvidas na hora." (~frame 172)
  const msg3Spring = spring({
    frame: frame - 172,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Digitando 2 (~frame 194 a 206)
  const isTyping2 = frame >= 194 && frame < 206;

  // Resposta da IA instantânea (~frame 206)
  const msg4Spring = spring({
    frame: frame - 206,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Confirmação do cliente (~frame 236)
  const msg5Spring = spring({
    frame: frame - 236,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Transições de corte suave
  const enterOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const exitOpacity = interpolate(frame, [270, 284], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#000000',
        fontFamily,
        opacity: Math.min(enterOpacity, exitOpacity),
      }}
    >
      {/* Imagem de Fundo com Zoom Dinâmico e Brilho Preservado (Regra 23) */}
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
      </div>

      {/* Véu de contraste moderado (Regra 23) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(20,3,7,0.76) 0%, rgba(25,4,10,0.25) 28%, rgba(20,3,7,0.30) 65%, rgba(10,1,3,0.90) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* 1. Rótulo Obrigatório da Cena (y=175) */}
      {frame >= 4 && (
        <div
          style={{
            position: 'absolute',
            top: 175,
            left: SAFE_ZONE.left,
            right: SAFE_ZONE.left,
            display: 'flex',
            justifyContent: 'center',
            opacity: Math.min(rotuloSpring, 1),
            transform: `scale(${Math.max(0.7, rotuloSpring)})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 26px',
              borderRadius: 999,
              backgroundColor: 'rgba(20, 4, 10, 0.94)',
              border: `2px solid ${COLORS.success}`,
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
            }}
          >
            <span style={{fontSize: 26}}>💡</span>
            <span
              style={{
                color: COLORS.white,
                fontSize: 34,
                fontWeight: 800,
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              Como Funciona
            </span>
          </div>
        </div>
      )}

      {/* 2. Título Superior com Box Protetor Opaco (y=255) - Regras 5 e 6 */}
      {frame >= 12 && (
        <div
          style={{
            position: 'absolute',
            top: 255,
            left: SAFE_ZONE.left,
            right: SAFE_ZONE.left,
            display: 'flex',
            justifyContent: 'center',
            opacity: Math.min(titleSpring, 1),
            transform: `translateY(${interpolate(titleSpring, [0, 1], [25, 0])}px)`,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(20, 4, 10, 0.94)',
              padding: '12px 32px',
              borderRadius: 22,
              border: '2px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 12px 32px rgba(0,0,0,0.8)',
              textAlign: 'center',
            }}
          >
            <h2
              style={{
                margin: 0,
                fontSize: 48,
                fontWeight: 900,
                color: COLORS.white,
                lineHeight: 1.15,
                textTransform: 'uppercase',
                letterSpacing: -0.5,
              }}
            >
              Abre direto no celular,{' '}
              <span style={{color: COLORS.accent}}>com fotos e IA</span>
            </h2>
          </div>
        </div>
      )}

      {/* 3. MOCKUP DO SMARTPHONE MOBILE NATIVO (y=360 a y=1310) — Regras 13, 57 e 76 */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 100,
          width: 880,
          height: 940,
          perspective: 1200,
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            width: 880,
            height: 940,
            backgroundColor: '#0F172A',
            borderRadius: 48,
            border: '5px solid #334155',
            boxShadow:
              '0 25px 60px rgba(0,0,0,0.95), 0 0 35px rgba(225, 29, 72, 0.25)',
            transform: `rotateY(${phoneRotateY}deg) rotateX(2.5deg) translateY(${phoneFloatY}px)`,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Barra Superior do Smartphone / WhatsApp com Dynamic Island */}
          <div
            style={{
              height: 110,
              backgroundColor: '#1E293B',
              borderBottom: '2px solid #334155',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 28px',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              {/* Avatar da Marca */}
              <div
                style={{
                  width: 60,
                  height: 60,
                  borderRadius: '50%',
                  backgroundColor: COLORS.primary,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: COLORS.white,
                  fontWeight: 900,
                  fontSize: 28,
                  border: '2px solid #FFFFFF',
                  boxShadow: '0 4px 12px rgba(225, 29, 72, 0.5)',
                }}
              >
                🍽️
              </div>
              <div>
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 800,
                    color: COLORS.white,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  Cardápio Digital
                  <span
                    style={{
                      fontSize: 22,
                      backgroundColor: '#10B981',
                      color: '#FFFFFF',
                      padding: '2px 8px',
                      borderRadius: 6,
                      fontWeight: 700,
                    }}
                  >
                    IA
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 28,
                    fontWeight: 600,
                    color: '#34D399',
                  }}
                >
                  Online • Responde na hora
                </div>
              </div>
            </div>

            {/* Selo Obrigatório de Simulação */}
            <div
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.12)',
                padding: '6px 16px',
                borderRadius: 10,
                fontSize: 26,
                fontWeight: 700,
                color: '#CBD5E1',
                letterSpacing: 0.5,
              }}
            >
              Simulação
            </div>
          </div>

          {/* Área de Conversa do Chat (sem texto cortado - Regra 76) */}
          <div
            style={{
              flex: 1,
              backgroundColor: '#090D16',
              padding: '26px 24px',
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'flex-start',
            }}
          >
            {/* ETAPA 1 (Frames 0 a 144): Pergunta sobre instalação & Resposta do navegador */}
            {frame < 148 && (
              <div
                style={{
                  position: 'absolute',
                  inset: '26px 24px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 24,
                  opacity: phase1Opacity,
                }}
              >
                {/* Mensagem 1: Cliente */}
                {frame >= 15 && (
                  <div
                    style={{
                      alignSelf: 'flex-start',
                      maxWidth: 720,
                      opacity: Math.min(msg1Spring, 1),
                      transform: `scale(${Math.max(0.7, msg1Spring)})`,
                      backgroundColor: '#1E293B',
                      padding: '20px 24px',
                      borderRadius: '24px 24px 24px 6px',
                      border: '1.5px solid rgba(255,255,255,0.12)',
                      boxShadow: '0 8px 20px rgba(0,0,0,0.5)',
                    }}
                  >
                    <div
                      style={{
                        fontSize: 34,
                        fontWeight: 700,
                        color: COLORS.white,
                        lineHeight: 1.3,
                      }}
                    >
                      Preciso instalar algum aplicativo para ver o cardápio?
                    </div>
                    <div
                      style={{
                        fontSize: 24,
                        color: '#94A3B8',
                        textAlign: 'right',
                        marginTop: 8,
                      }}
                    >
                      12:01
                    </div>
                  </div>
                )}

                {/* Indicador de Digitando 1 */}
                {isTyping1 && (
                  <div
                    style={{
                      alignSelf: 'flex-end',
                      backgroundColor: '#064E3B',
                      padding: '14px 24px',
                      borderRadius: 20,
                    }}
                  >
                    <span style={{fontSize: 26, color: '#A7F3D0'}}>
                      IA digitando...
                    </span>
                  </div>
                )}

                {/* Mensagem 2: IA/Empresa */}
                {frame >= 58 && (
                  <div
                    style={{
                      alignSelf: 'flex-end',
                      maxWidth: 740,
                      opacity: Math.min(msg2Spring, 1),
                      transform: `scale(${Math.max(0.7, msg2Spring)})`,
                      backgroundColor: '#064E3B',
                      padding: '20px 24px',
                      borderRadius: '24px 24px 6px 24px',
                      border: '1.5px solid rgba(16, 185, 129, 0.4)',
                      boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                    }}
                  >
                    <div
                      style={{
                        fontSize: 34,
                        fontWeight: 700,
                        color: '#ECFDF5',
                        lineHeight: 1.3,
                      }}
                    >
                      Não precisa. O cardápio abre direto no navegador do seu celular. 🍔✨
                    </div>
                    <div
                      style={{
                        fontSize: 24,
                        color: '#A7F3D0',
                        textAlign: 'right',
                        marginTop: 8,
                      }}
                    >
                      12:01 ✓✓
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ETAPA 2 (Frames 142 em diante): Cardápio com Fotos & Atendimento com IA em tempo real */}
            {frame >= 142 && (
              <div
                style={{
                  position: 'absolute',
                  inset: '26px 24px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 20,
                  opacity: phase2Opacity,
                }}
              >
                {/* Card visual do Cardápio com Fotos */}
                <div
                  style={{
                    alignSelf: 'center',
                    width: '96%',
                    opacity: Math.min(cardFotoSpring, 1),
                    transform: `scale(${Math.max(0.7, cardFotoSpring)})`,
                    backgroundColor: '#1E293B',
                    borderRadius: 22,
                    padding: '16px 20px',
                    border: `2px solid ${COLORS.accent}`,
                    boxShadow: '0 10px 28px rgba(0,0,0,0.6)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 16,
                  }}
                >
                  <div
                    style={{
                      fontSize: 48,
                      backgroundColor: 'rgba(250, 204, 21, 0.2)',
                      padding: '8px 12px',
                      borderRadius: 16,
                    }}
                  >
                    📸
                  </div>
                  <div>
                    <div
                      style={{
                        fontSize: 34,
                        fontWeight: 900,
                        color: COLORS.accent,
                        textTransform: 'uppercase',
                      }}
                    >
                      Cardápio com Fotos
                    </div>
                    <div
                      style={{
                        fontSize: 30,
                        fontWeight: 600,
                        color: COLORS.white,
                      }}
                    >
                      Cliente vê as fotos e faz o pedido
                    </div>
                  </div>
                </div>

                {/* Mensagem 3: Dúvida do cliente */}
                {frame >= 172 && (
                  <div
                    style={{
                      alignSelf: 'flex-start',
                      maxWidth: 680,
                      opacity: Math.min(msg3Spring, 1),
                      transform: `scale(${Math.max(0.7, msg3Spring)})`,
                      backgroundColor: '#1E293B',
                      padding: '18px 22px',
                      borderRadius: '22px 22px 22px 6px',
                      border: '1.5px solid rgba(255,255,255,0.12)',
                    }}
                  >
                    <div
                      style={{
                        fontSize: 34,
                        fontWeight: 700,
                        color: COLORS.white,
                        lineHeight: 1.3,
                      }}
                    >
                      Esse lanche vem com batata?
                    </div>
                    <div
                      style={{
                        fontSize: 24,
                        color: '#94A3B8',
                        textAlign: 'right',
                        marginTop: 6,
                      }}
                    >
                      12:02
                    </div>
                  </div>
                )}

                {/* Indicador de Digitando 2 */}
                {isTyping2 && (
                  <div
                    style={{
                      alignSelf: 'flex-end',
                      backgroundColor: '#064E3B',
                      padding: '12px 22px',
                      borderRadius: 18,
                    }}
                  >
                    <span style={{fontSize: 26, color: '#A7F3D0'}}>
                      IA respondendo na hora...
                    </span>
                  </div>
                )}

                {/* Mensagem 4: IA responde instantaneamente */}
                {frame >= 206 && (
                  <div
                    style={{
                      alignSelf: 'flex-end',
                      maxWidth: 720,
                      opacity: Math.min(msg4Spring, 1),
                      transform: `scale(${Math.max(0.7, msg4Spring)})`,
                      backgroundColor: '#064E3B',
                      padding: '18px 22px',
                      borderRadius: '22px 22px 6px 22px',
                      border: '1.5px solid rgba(16, 185, 129, 0.4)',
                    }}
                  >
                    <div
                      style={{
                        fontSize: 34,
                        fontWeight: 700,
                        color: '#ECFDF5',
                        lineHeight: 1.3,
                      }}
                    >
                      Vem sim! Quer que eu anote o pedido? 🍟🤖
                    </div>
                    <div
                      style={{
                        fontSize: 24,
                        color: '#A7F3D0',
                        textAlign: 'right',
                        marginTop: 6,
                      }}
                    >
                      12:02 ✓✓
                    </div>
                  </div>
                )}

                {/* Mensagem 5: Confirmação do cliente (Briefing) */}
                {frame >= 236 && (
                  <div
                    style={{
                      alignSelf: 'flex-start',
                      maxWidth: 680,
                      opacity: Math.min(msg5Spring, 1),
                      transform: `scale(${Math.max(0.7, msg5Spring)})`,
                      backgroundColor: '#1E293B',
                      padding: '16px 22px',
                      borderRadius: '22px 22px 22px 6px',
                      border: '1.5px solid rgba(255,255,255,0.12)',
                    }}
                  >
                    <div
                      style={{
                        fontSize: 34,
                        fontWeight: 700,
                        color: COLORS.white,
                      }}
                    >
                      Quero sim, pode anotar.
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
