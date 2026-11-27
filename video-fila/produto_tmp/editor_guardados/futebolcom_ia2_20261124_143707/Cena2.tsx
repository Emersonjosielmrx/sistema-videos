import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no fundo (zoom suave contínuo)
  const bgScale = interpolate(frame, [0, 244], [1.08, 1.22], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Flutuação 3D sutil do celular
  const floatAngle = Math.sin(frame * 0.05) * 1.5;
  const floatY = Math.cos(frame * 0.05) * 5;

  // Entrada da badge no topo (frame 3)
  const badgeSpring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do celular 3D (frame 5)
  const phoneSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Sincronia das mensagens do chat com a fala:
  // 12.92s (frame 12): "Agora a IA" -> Cliente envia "Oi"
  const msg1Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // 13.5s (frame 28 a 52): "IA digitando..."
  const typingProg = interpolate(frame, [28, 38, 52, 58], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 14.56s (frame 56): "responde o oi na hora" -> Saudação coerente da IA
  const msg2Spring = spring({
    frame: frame - 56,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // 15.87s (frame 96): "tira as dúvidas" -> Cliente pergunta & IA responde sobre cardápio
  const msg3ClientSpring = spring({
    frame: frame - 96,
    fps,
    config: {damping: 12, stiffness: 110},
  });
  const msg3IaSpring = spring({
    frame: frame - 110,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // 16.75s (frame 128): "mostra o cardápio com fotos" -> Card interativo do cardápio com foto
  const cardSpring = spring({
    frame: frame - 128,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // 18.5s (frame 172): "para o cliente pedir" -> Pedido confirmado e enviado
  const msg4Spring = spring({
    frame: frame - 172,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Fade out suave da primeira mensagem ("Oi") antes de qualquer rolagem, evitando clipping sob o cabeçalho
  const msg1Opacity = interpolate(frame, [115, 130], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Scroll suave e contido apenas aos 150 frames para acomodar o cardápio e pedido com folga
  const scrollY = interpolate(
    frame,
    [0, 135, 175],
    [0, 0, -32],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#0F0205',
        fontFamily,
      }}
    >
      {/* Foto de fundo viva com zoom contínuo e véu escuro */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
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
            filter: 'blur(16px)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(15,2,5,0.92) 0%, rgba(49,6,15,0.82) 40%, rgba(15,2,5,0.95) 100%)',
          }}
        />
      </div>

      {/* Topo seguro (y: 170 a 240): Badge e Etapa */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 20,
        }}
      >
        {badgeSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${badgeSpring})`,
              opacity: badgeSpring,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 28px',
              borderRadius: 50,
              backgroundColor: '#0B0D13FA',
              border: '2px solid #E11D48',
              boxShadow: '0 8px 25px rgba(225, 29, 72, 0.4)',
            }}
          >
            <span style={{fontSize: 32}}>🤖</span>
            <span
              style={{
                color: '#FFFFFF',
                fontSize: 34,
                fontWeight: 900,
                letterSpacing: '0.8px',
                textTransform: 'uppercase',
              }}
            >
              COMO FUNCIONA ➔ ATENDIMENTO COM IA
            </span>
          </div>
        )}
      </div>

      {/* Mockup de Smartphone 3D Ampliado e Bem Distribuído (y: 245 a 1320) */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 95,
          width: 890,
          height: 1070,
          perspective: 1200,
          zIndex: 10,
        }}
      >
        {phoneSpring > 0.01 && (
          <div
            style={{
              width: '100%',
              height: '100%',
              transform: `scale(${phoneSpring}) rotateY(${
                -7 + floatAngle
              }deg) rotateX(3deg) translateY(${floatY}px)`,
              transformOrigin: 'center center',
              borderRadius: 44,
              backgroundColor: '#0D1418',
              border: '4px solid #222E35',
              boxShadow:
                '0 30px 70px rgba(0, 0, 0, 0.95), 0 0 0 2px rgba(255, 255, 255, 0.1)',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Header Fixo do WhatsApp no Celular */}
            <div
              style={{
                height: 98,
                backgroundColor: '#1F2C34',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0 24px',
                borderBottom: '2px solid rgba(255, 255, 255, 0.08)',
                flexShrink: 0,
                zIndex: 5,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: '50%',
                    backgroundColor: '#E11D48',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 28,
                    fontWeight: 900,
                    color: '#FFFFFF',
                  }}
                >
                  🍔
                </div>
                <div style={{display: 'flex', flexDirection: 'column'}}>
                  <span
                    style={{
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                      lineHeight: 1.1,
                    }}
                  >
                    Cardápio Digital
                  </span>
                  <div style={{display: 'flex', alignItems: 'center', gap: 8, marginTop: 3}}>
                    <span
                      style={{
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        backgroundColor: '#25D366',
                        display: 'inline-block',
                      }}
                    />
                    <span style={{fontSize: 32, color: '#25D366', fontWeight: 700}}>
                      IA Ativa • Responde na hora
                    </span>
                  </div>
                </div>
              </div>

              {/* Selo Obrigatório: Simulação */}
              <div
                style={{
                  padding: '6px 14px',
                  borderRadius: 8,
                  backgroundColor: 'rgba(255, 255, 255, 0.12)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#CBD5E1',
                  textTransform: 'uppercase',
                }}
              >
                Simulação
              </div>
            </div>

            {/* Container Interno de Mensagens: Espaçoso e sem cortes */}
            <div
              style={{
                flex: 1,
                padding: '22px 24px',
                overflow: 'hidden',
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <div
                style={{
                  transform: `translateY(${scrollY}px)`,
                  transition: 'transform 0.1s ease-out',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16,
                }}
              >
                {/* 1. Mensagem Cliente: "Oi" (12.92s) */}
                {msg1Spring > 0.01 && msg1Opacity > 0.01 && (
                  <div
                    style={{
                      alignSelf: 'flex-end',
                      maxWidth: '75%',
                      backgroundColor: '#005C4B',
                      padding: '14px 20px',
                      borderRadius: '18px 18px 4px 18px',
                      transform: `scale(${msg1Spring})`,
                      opacity: msg1Spring * msg1Opacity,
                      boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                    }}
                  >
                    <span
                      style={{
                        fontSize: 34,
                        fontWeight: 700,
                        color: '#FFFFFF',
                      }}
                    >
                      Oi
                    </span>
                    <div
                      style={{
                        fontSize: 32,
                        color: '#A0D8C8',
                        textAlign: 'right',
                        marginTop: 2,
                      }}
                    >
                      19:02 ✓✓
                    </div>
                  </div>
                )}

                {/* Indicador animado "digitando..." */}
                {typingProg > 0.05 && (
                  <div
                    style={{
                      alignSelf: 'flex-start',
                      backgroundColor: '#202C33',
                      padding: '12px 18px',
                      borderRadius: '18px 18px 18px 4px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      opacity: typingProg,
                    }}
                  >
                    <span style={{fontSize: 32, color: '#25D366', fontWeight: 700}}>
                      IA digitando...
                    </span>
                    <div style={{display: 'flex', gap: 6}}>
                      <div
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          backgroundColor: '#25D366',
                          opacity: Math.sin(frame * 0.3) > 0 ? 1 : 0.3,
                        }}
                      />
                      <div
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          backgroundColor: '#25D366',
                          opacity: Math.sin(frame * 0.3 + 1) > 0 ? 1 : 0.3,
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* 2. Empresa IA responde com saudação coerente (14.56s) */}
                {msg2Spring > 0.01 && (
                  <div
                    style={{
                      alignSelf: 'flex-start',
                      maxWidth: '85%',
                      backgroundColor: '#202C33',
                      padding: '16px 20px',
                      borderRadius: '18px 18px 18px 4px',
                      transform: `scale(${msg2Spring})`,
                      opacity: msg2Spring,
                      boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                      border: '1.5px solid rgba(255,255,255,0.08)',
                    }}
                  >
                    <span
                      style={{
                        fontSize: 34,
                        fontWeight: 700,
                        color: '#FFFFFF',
                        lineHeight: 1.25,
                      }}
                    >
                      Olá! Seja bem-vindo. Como posso te ajudar?
                    </span>
                    <div
                      style={{
                        fontSize: 32,
                        color: '#CBD5E1',
                        textAlign: 'right',
                        marginTop: 4,
                      }}
                    >
                      19:02 • Resposta na hora
                    </div>
                  </div>
                )}

                {/* 3. Pergunta do cliente & Resposta da IA com coerência total (15.87s) */}
                {msg3ClientSpring > 0.01 && (
                  <div
                    style={{
                      alignSelf: 'flex-end',
                      maxWidth: '80%',
                      backgroundColor: '#005C4B',
                      padding: '14px 20px',
                      borderRadius: '18px 18px 4px 18px',
                      transform: `scale(${msg3ClientSpring})`,
                      opacity: msg3ClientSpring,
                    }}
                  >
                    <span
                      style={{
                        fontSize: 34,
                        fontWeight: 700,
                        color: '#FFFFFF',
                      }}
                    >
                      Vocês têm opção sem cebola?
                    </span>
                  </div>
                )}

                {msg3IaSpring > 0.01 && (
                  <div
                    style={{
                      alignSelf: 'flex-start',
                      maxWidth: '86%',
                      backgroundColor: '#202C33',
                      padding: '16px 20px',
                      borderRadius: '18px 18px 18px 4px',
                      transform: `scale(${msg3IaSpring})`,
                      opacity: msg3IaSpring,
                      border: '1.5px solid rgba(255,255,255,0.08)',
                    }}
                  >
                    <span
                      style={{
                        fontSize: 34,
                        fontWeight: 700,
                        color: '#FFFFFF',
                        lineHeight: 1.25,
                      }}
                    >
                      Temos sim! Posso explicar os itens do cardápio:
                    </span>
                  </div>
                )}

                {/* 4. Card interativo do Cardápio com Fotos (16.75s) */}
                {cardSpring > 0.01 && (
                  <div
                    style={{
                      alignSelf: 'center',
                      width: '96%',
                      backgroundColor: '#182229',
                      borderRadius: 20,
                      border: '2px solid #E11D48',
                      overflow: 'hidden',
                      transform: `scale(${cardSpring})`,
                      opacity: cardSpring,
                      boxShadow: '0 8px 24px rgba(225, 29, 72, 0.35)',
                    }}
                  >
                    <div style={{height: 150, position: 'relative', overflow: 'hidden'}}>
                      <Img
                        src={staticFile('img_0.jpg')}
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover',
                          transform: 'scale(1.2)',
                          transformOrigin: '50% 25%',
                        }}
                      />
                      <div
                        style={{
                          position: 'absolute',
                          bottom: 0,
                          left: 0,
                          right: 0,
                          padding: '8px 16px',
                          background: 'linear-gradient(transparent, rgba(0,0,0,0.92))',
                          fontSize: 32,
                          fontWeight: 800,
                          color: '#FFFFFF',
                        }}
                      >
                        📸 Cardápio com Fotos no Celular
                      </div>
                    </div>
                    <div
                      style={{
                        padding: '14px 18px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        backgroundColor: '#1F2C34',
                      }}
                    >
                      <span style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                        Veja os pratos e escolha
                      </span>
                      <div
                        style={{
                          backgroundColor: '#E11D48',
                          padding: '10px 18px',
                          borderRadius: 12,
                          fontSize: 32,
                          fontWeight: 900,
                          color: '#FFFFFF',
                        }}
                      >
                        VER CARDÁPIO
                      </div>
                    </div>
                  </div>
                )}

                {/* 5. Mensagem: Confirmação de Pedido pelo WhatsApp (18.5s) */}
                {msg4Spring > 0.01 && (
                  <div
                    style={{
                      alignSelf: 'flex-start',
                      maxWidth: '92%',
                      backgroundColor: '#005C4B',
                      padding: '16px 22px',
                      borderRadius: 18,
                      transform: `scale(${msg4Spring})`,
                      opacity: msg4Spring,
                      boxShadow: '0 6px 18px rgba(0,0,0,0.5)',
                      border: '1.5px solid #25D366',
                    }}
                  >
                    <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                      <span style={{fontSize: 36}}>✅</span>
                      <span
                        style={{
                          fontSize: 34,
                          fontWeight: 800,
                          color: '#FFFFFF',
                          lineHeight: 1.25,
                        }}
                      >
                        Pedido gerado e enviado direto no WhatsApp!
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
