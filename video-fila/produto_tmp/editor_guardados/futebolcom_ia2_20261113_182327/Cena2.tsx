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

interface Cena2Props {
  fontFamily: string;
}

export const Cena2: React.FC<Cena2Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com movimento
  const bgScale = interpolate(frame, [0, 224], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada e saída
  const sceneOpacity = interpolate(
    frame,
    [0, 10, 212, 224],
    [0, 1, 1, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  // Top Badge
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Mockup entrada
  const phoneSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 13, stiffness: 100},
  });

  // Scroll vertical dinâmico da conversa com a chegada dos balões (mantém itens inteiros na tela)
  const chatScrollY = interpolate(
    frame,
    [0, 14, 80, 104, 160, 175],
    [0, 0, -15, -35, -35, -55],
    {
      extrapolateRight: 'clamp',
    }
  );

  // Balão 1: Cliente (~frame 12)
  const b1Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Digitando (~frame 50 a 84)
  const typingVisible = frame >= 50 && frame < 84;
  const typingDots = Math.floor((frame / 6) % 3) + 1;

  // Balão 2: IA / Empresa (~frame 84)
  const b2Spring = spring({
    frame: frame - 84,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Entrada do Cardápio Digital com Fotos no Celular (~frame 98 a 165)
  // Momento em que a fala cita "O cliente consulta o cardápio com fotos no celular"
  const menuModalSpring = spring({
    frame: frame - 96,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Balão 3: Cliente pedido (~frame 168)
  const b3Spring = spring({
    frame: frame - 168,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Flutuação 3D sutil contínua
  const rotY = -4 + Math.sin(frame * 0.08) * 1.5;
  const floatY = Math.sin(frame * 0.1) * 4;

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#1A0307'}}>
      {/* Imagem de Fundo Desfocada com Movimento */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(10px)',
            transform: `scale(${bgScale})`,
          }}
        />
        {/* Overlay escuro elegante */}
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(22, 3, 7, 0.88) 0%, rgba(49, 6, 15, 0.8) 50%, rgba(15, 2, 4, 0.9) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Rótulo / Top Badge (y=180 a 240) */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring,
          zIndex: 20,
        }}
      >
        <div
          style={{
            fontFamily,
            fontSize: 32,
            fontWeight: 800,
            color: '#111111',
            backgroundColor: '#FACC15',
            padding: '10px 28px',
            borderRadius: 50,
            letterSpacing: 1.2,
            textTransform: 'uppercase',
            boxShadow: '0 8px 24px rgba(250, 204, 21, 0.35)',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <span>✨</span>
          <span>COMO FUNCIONA: CARDÁPIO + IA</span>
        </div>
      </div>

      {/* Mockup de Celular 3D (y=260 a 1180) */}
      <div
        style={{
          position: 'absolute',
          top: 260,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          perspective: 1200,
          zIndex: 10,
        }}
      >
        <div
          style={{
            width: 880,
            height: 940,
            backgroundColor: '#111B21',
            borderRadius: 44,
            border: '6px solid #2A2F38',
            boxShadow:
              '0 24px 60px rgba(0,0,0,0.85), 0 0 35px rgba(225, 29, 72, 0.25)',
            transform: `scale(${Math.min(phoneSpring, 1)}) rotateY(${rotY}deg) translateY(${floatY}px)`,
            opacity: phoneSpring,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Header WhatsApp com Selo Simulação */}
          <div
            style={{
              height: 96,
              backgroundColor: '#202C33',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 24px',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
              flexShrink: 0,
            }}
          >
            {/* Foto e Nome */}
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: '50%',
                  backgroundColor: '#E11D48',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 32,
                  boxShadow: '0 4px 12px rgba(225, 29, 72, 0.5)',
                }}
              >
                🍕
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                  }}
                >
                  Cardápio Digital Pizzaria
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#25D366',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <span>●</span>
                  <span>IA Atendimento Online</span>
                </div>
              </div>
            </div>

            {/* Selo Simulação Obrigatório */}
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#CBD5E1',
                backgroundColor: 'rgba(255,255,255,0.14)',
                border: '1px solid rgba(255,255,255,0.25)',
                padding: '6px 16px',
                borderRadius: 14,
                letterSpacing: 0.5,
              }}
            >
              Simulação
            </div>
          </div>

          {/* Área de Conversa com Scroll Suave */}
          <div
            style={{
              flex: 1,
              padding: '20px 22px',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              justifyContent: 'flex-start',
              transform: `translateY(${chatScrollY}px)`,
              transition: 'transform 0.2s ease',
            }}
          >
            {/* Balão 1: Cliente */}
            {frame >= 10 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  backgroundColor: '#202C33',
                  borderRadius: '20px 20px 20px 4px',
                  padding: '16px 22px',
                  boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  transform: `scale(${Math.min(b1Spring, 1)}) translateX(${(1 - b1Spring) * -30}px)`,
                  opacity: b1Spring,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.25,
                  }}
                >
                  Boa noite, a pizza de calabresa vem com cebola?
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 500,
                    color: '#8696A0',
                    textAlign: 'right',
                    marginTop: 4,
                  }}
                >
                  19:42
                </div>
              </div>
            )}

            {/* Indicador IA Digitando */}
            {typingVisible && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  backgroundColor: 'rgba(0, 92, 75, 0.4)',
                  border: '1px solid #25D366',
                  borderRadius: 18,
                  padding: '10px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span style={{fontSize: 28}}>🤖</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#25D366',
                  }}
                >
                  IA digitando{'.'.repeat(typingDots)}
                </span>
              </div>
            )}

            {/* Balão 2: Empresa / IA com Prova Visual do Cardápio Digital */}
            {frame >= 84 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '92%',
                  backgroundColor: '#005C4B',
                  borderRadius: '20px 20px 4px 20px',
                  padding: '16px 20px',
                  boxShadow: '0 6px 18px rgba(0,0,0,0.5)',
                  border: '2px solid rgba(250, 204, 21, 0.45)',
                  transform: `scale(${Math.min(b2Spring, 1)}) translateX(${(1 - b2Spring) * 30}px)`,
                  opacity: b2Spring,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 6,
                  }}
                >
                  <span style={{fontSize: 26}}>🤖</span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#FACC15',
                      letterSpacing: 0.5,
                    }}
                  >
                    Resposta Automática IA
                  </span>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.25,
                  }}
                >
                  Olá! Sim, leva calabresa fatiada e cebola. Você pode conferir as
                  fotos no cardápio.
                </div>

                {/* Prova Visual do Cardápio Digital com Fotos no Celular */}
                <div
                  style={{
                    marginTop: 12,
                    backgroundColor: '#1A272F',
                    borderRadius: 16,
                    border: '2px solid rgba(250, 204, 21, 0.5)',
                    overflow: 'hidden',
                    boxShadow: '0 6px 18px rgba(0,0,0,0.4)',
                  }}
                >
                  {/* Foto Real da Pizza no Cardápio com Foco Apetitoso */}
                  <div style={{height: 155, width: '100%', overflow: 'hidden', position: 'relative'}}>
                    <Img
                      src={staticFile('img_0.jpg')}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        objectPosition: '39% 73%',
                        transform: 'scale(2.5)',
                      }}
                    />
                    <div
                      style={{
                        position: 'absolute',
                        top: 8,
                        left: 10,
                        backgroundColor: 'rgba(22, 3, 7, 0.88)',
                        border: '1.5px solid #FACC15',
                        borderRadius: 12,
                        padding: '4px 12px',
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 800,
                        color: '#FACC15',
                      }}
                    >
                      🍕 Cardápio Digital
                    </div>
                  </div>

                  {/* Informações do Produto no Cardápio */}
                  <div style={{padding: '12px 16px'}}>
                    <div
                      style={{
                        fontFamily,
                        fontSize: 34,
                        fontWeight: 800,
                        color: '#FFFFFF',
                      }}
                    >
                      Pizza Calabresa com Cebola
                    </div>
                    <div
                      style={{
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 600,
                        color: '#CBD5E1',
                        marginTop: 2,
                      }}
                    >
                      Calabresa fatiada, cebola e azeitonas
                    </div>
                    <div
                      style={{
                        marginTop: 8,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <span
                        style={{
                          fontFamily,
                          fontSize: 32,
                          fontWeight: 700,
                          color: '#25D366',
                        }}
                      >
                        ✓ Foto real no celular
                      </span>
                      <span
                        style={{
                          fontFamily,
                          fontSize: 32,
                          fontWeight: 800,
                          color: '#FACC15',
                          textDecoration: 'underline',
                        }}
                      >
                        Ver cardápio ↗
                      </span>
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#53BDEB',
                    textAlign: 'right',
                    marginTop: 6,
                  }}
                >
                  19:42 ✓✓
                </div>
              </div>
            )}

            {/* Balão 3: Cliente */}
            {frame >= 165 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  backgroundColor: '#202C33',
                  borderRadius: '20px 20px 20px 4px',
                  padding: '16px 22px',
                  boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  transform: `scale(${Math.min(b3Spring, 1)}) translateX(${(1 - b3Spring) * -30}px)`,
                  opacity: b3Spring,
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.25,
                  }}
                >
                  Perfeito, vou fazer o pedido por aqui.
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 500,
                    color: '#8696A0',
                    textAlign: 'right',
                    marginTop: 4,
                  }}
                >
                  19:43
                </div>
              </div>
            )}
          </div>

          {/* Barra de Input WhatsApp Nativa */}
          <div
            style={{
              height: 76,
              backgroundColor: '#202C33',
              display: 'flex',
              alignItems: 'center',
              padding: '0 18px',
              gap: 12,
              borderTop: '1px solid rgba(255,255,255,0.08)',
              flexShrink: 0,
            }}
          >
            <div
              style={{
                flex: 1,
                height: 48,
                backgroundColor: '#2A3942',
                borderRadius: 24,
                display: 'flex',
                alignItems: 'center',
                padding: '0 18px',
                gap: 10,
              }}
            >
              <span style={{fontSize: 26, opacity: 0.7}}>😊</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  color: '#8696A0',
                }}
              >
                Mensagem
              </span>
            </div>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                backgroundColor: '#00A884',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 24,
                color: '#FFFFFF',
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
