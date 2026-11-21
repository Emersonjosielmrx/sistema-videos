import React from 'react';
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Img,
  staticFile,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const totalFrames = 282;

  // Câmera dinâmica contínua
  const bgScale = interpolate(frame, [0, totalFrames], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, totalFrames], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge superior no frame 6
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Movimento 3D suave do celular
  const phoneSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 15, stiffness: 90},
  });

  // Rotação 3D suave e contínua
  const rotateY = interpolate(frame, [0, totalFrames], [12, 4], {
    extrapolateRight: 'clamp',
  });
  const rotateX = interpolate(frame, [0, totalFrames], [4, 1], {
    extrapolateRight: 'clamp',
  });

  // Mensagens sincronizadas com a fala:
  // Msg 1 (Cliente avisa): frame 12 (0.4s)
  const msg1Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Status IA buscando: frame 40 (1.3s)
  const aiThinkingSpring = spring({
    frame: frame - 40,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Msg 2 (IA oferece novos horários): frame 115 (3.8s)
  const msg2Spring = spring({
    frame: frame - 115,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Msg 3 (Cliente escolhe): frame 180 (6.0s)
  const msg3Spring = spring({
    frame: frame - 180,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Msg 4 (IA confirma a troca): frame 212 (7.0s)
  const msg4Spring = spring({
    frame: frame - 212,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Scroll do chat para manter as mensagens visíveis sem cortar o topo
  const chatScrollY = interpolate(
    frame,
    [175, 205, 225, 250],
    [0, -45, -45, -95],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  // Status de etapas no topo do celular
  let etapaTexto = '1. AVISO NO WHATSAPP';
  let etapaCor = '#38BDF8';
  if (frame >= 90 && frame < 195) {
    etapaTexto = '2. IA SUGERE HORÁRIOS LIVRES';
    etapaCor = '#F59E0B';
  } else if (frame >= 195) {
    etapaTexto = '3. REAGENDAMENTO CONFIRMADO';
    etapaCor = '#10B981';
  }

  // Saída suave
  const exitOpacity = interpolate(frame, [totalFrames - 10, totalFrames], [1, 0], {
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
        backgroundColor: '#0B0D13',
        opacity: exitOpacity,
      }}
    >
      {/* Imagem de Fundo Clara e Vibrante (Regra 19) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
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

      {/* Vinheta Suave Apenas para Contraste */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(11, 13, 19, 0.82) 0%, rgba(11, 13, 19, 0.32) 35%, rgba(11, 13, 19, 0.45) 65%, rgba(11, 13, 19, 0.86) 100%)',
        }}
      />

      {/* Conteúdo Seguro (y: 165 a 1380) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 165,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {/* Rótulo Oficial da Cena */}
        {badgeSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${badgeSpring})`,
              opacity: badgeSpring,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 26px',
              borderRadius: 24,
              background: 'rgba(245, 158, 11, 0.22)',
              border: '2px solid #F59E0B',
              boxShadow: '0 8px 24px rgba(245, 158, 11, 0.3)',
              marginBottom: 12,
            }}
          >
            <span style={{fontSize: 32}}>⚡</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FBBF24',
                textTransform: 'uppercase',
                letterSpacing: 1.2,
              }}
            >
              Como Funciona
            </span>
          </div>
        )}

        {/* Indicador Dinâmico de Etapa */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.94)',
            border: `2px solid ${etapaCor}`,
            borderRadius: 20,
            padding: '8px 24px',
            fontFamily,
            fontSize: 32,
            fontWeight: 800,
            color: etapaCor,
            letterSpacing: 1.1,
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.6)',
            marginBottom: 14,
          }}
        >
          {etapaTexto}
        </div>

        {/* Mockup do Celular 3D Inclinado */}
        {phoneSpring > 0.01 && (
          <div
            style={{
              width: 860,
              perspective: 1400,
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                width: 840,
                height: 960,
                background: '#111B21',
                borderRadius: 40,
                border: '3.5px solid #2A3942',
                boxShadow:
                  '0 26px 55px rgba(0, 0, 0, 0.9), 0 0 35px rgba(0, 0, 0, 0.6)',
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
                transform: `rotateY(${rotateY}deg) rotateX(${rotateX}deg) scale(${phoneSpring})`,
                transformStyle: 'preserve-3d',
              }}
            >
              {/* Barra Superior WhatsApp */}
              <div
                style={{
                  background: '#202C33',
                  padding: '16px 22px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                  zIndex: 10,
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                  <div
                    style={{
                      width: 52,
                      height: 52,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #F59E0B, #D97706)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 30,
                      fontWeight: 900,
                      color: '#121216',
                      boxShadow: '0 4px 12px rgba(245, 158, 11, 0.4)',
                    }}
                  >
                    IA
                  </div>
                  <div style={{display: 'flex', flexDirection: 'column'}}>
                    <span
                      style={{
                        fontFamily,
                        fontSize: 34,
                        fontWeight: 800,
                        color: '#E9EDEF',
                      }}
                    >
                      Agenda IA (Inovare)
                    </span>
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 600,
                        color: '#25D366',
                      }}
                    >
                      ● Online agora
                    </span>
                  </div>
                </div>

                {/* Selo Simulação Obrigatório */}
                <div
                  style={{
                    background: 'rgba(255, 255, 255, 0.12)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: 12,
                    padding: '4px 14px',
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#CBD5E1',
                    textTransform: 'uppercase',
                  }}
                >
                  Simulação
                </div>
              </div>

              {/* Área do Chat com Mensagens */}
              <div
                style={{
                  flex: 1,
                  padding: '20px 22px',
                  display: 'flex',
                  flexDirection: 'column',
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
                  }}
                >
                  {/* Msg 1: Cliente avisa imprevisto */}
                  {msg1Spring > 0.01 && (
                    <div
                      style={{
                        alignSelf: 'flex-start',
                        maxWidth: '84%',
                        background: '#202C33',
                        borderRadius: '18px 18px 18px 4px',
                        padding: '16px 22px',
                        transform: `scale(${msg1Spring})`,
                        opacity: msg1Spring,
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
                      }}
                    >
                      <div
                        style={{
                          fontFamily,
                          fontSize: 34,
                          fontWeight: 700,
                          color: '#E9EDEF',
                          lineHeight: 1.35,
                        }}
                      >
                        Oi, tive um imprevisto e não consigo ir hoje às 15h.
                      </div>
                      <div
                        style={{
                          fontFamily,
                          fontSize: 32,
                          color: '#8696A0',
                          textAlign: 'right',
                          marginTop: 6,
                        }}
                      >
                        14:15
                      </div>
                    </div>
                  )}

                  {/* Indicador IA analisando */}
                  {aiThinkingSpring > 0.01 && frame < 125 && (
                    <div
                      style={{
                        alignSelf: 'center',
                        background: 'rgba(245, 158, 11, 0.22)',
                        border: '1.5px solid #F59E0B',
                        borderRadius: 20,
                        padding: '8px 22px',
                        transform: `scale(${aiThinkingSpring})`,
                        opacity: aiThinkingSpring,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 12,
                      }}
                    >
                      <span style={{fontSize: 32}}>🤖</span>
                      <span
                        style={{
                          fontFamily,
                          fontSize: 32,
                          fontWeight: 800,
                          color: '#FBBF24',
                        }}
                      >
                        IA buscando horários livres...
                      </span>
                    </div>
                  )}

                  {/* Msg 2: IA oferece novos horários */}
                  {msg2Spring > 0.01 && (
                    <div
                      style={{
                        alignSelf: 'flex-end',
                        maxWidth: '86%',
                        background: '#005C4B',
                        borderRadius: '18px 18px 4px 18px',
                        padding: '18px 22px',
                        transform: `scale(${msg2Spring})`,
                        opacity: msg2Spring,
                        boxShadow: '0 6px 18px rgba(0, 0, 0, 0.4)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 12,
                      }}
                    >
                      <div
                        style={{
                          fontFamily,
                          fontSize: 34,
                          fontWeight: 700,
                          color: '#E9EDEF',
                          lineHeight: 1.35,
                        }}
                      >
                        Sem problema! Tenho amanhã às 10h ou quinta às 16h. Qual prefere?
                      </div>

                      {/* Opções de Horários */}
                      <div style={{display: 'flex', gap: 10, flexWrap: 'wrap'}}>
                        <div
                          style={{
                            background: '#F59E0B',
                            color: '#121216',
                            fontFamily,
                            fontSize: 32,
                            fontWeight: 800,
                            padding: '6px 16px',
                            borderRadius: 12,
                          }}
                        >
                          Amanhã 10h
                        </div>
                        <div
                          style={{
                            background: '#F59E0B',
                            color: '#121216',
                            fontFamily,
                            fontSize: 32,
                            fontWeight: 800,
                            padding: '6px 16px',
                            borderRadius: 12,
                          }}
                        >
                          Quinta 16h
                        </div>
                      </div>

                      <div
                        style={{
                          fontFamily,
                          fontSize: 32,
                          color: '#8696A0',
                          textAlign: 'right',
                        }}
                      >
                        14:15 ✓✓
                      </div>
                    </div>
                  )}

                  {/* Msg 3: Cliente escolhe */}
                  {msg3Spring > 0.01 && (
                    <div
                      style={{
                        alignSelf: 'flex-start',
                        maxWidth: '80%',
                        background: '#202C33',
                        borderRadius: '18px 18px 18px 4px',
                        padding: '14px 22px',
                        transform: `scale(${msg3Spring})`,
                        opacity: msg3Spring,
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
                      }}
                    >
                      <div
                        style={{
                          fontFamily,
                          fontSize: 34,
                          fontWeight: 700,
                          color: '#E9EDEF',
                          lineHeight: 1.35,
                        }}
                      >
                        Quinta às 16h, por favor.
                      </div>
                      <div
                        style={{
                          fontFamily,
                          fontSize: 32,
                          color: '#8696A0',
                          textAlign: 'right',
                          marginTop: 4,
                        }}
                      >
                        14:16
                      </div>
                    </div>
                  )}

                  {/* Msg 4: IA confirma a troca */}
                  {msg4Spring > 0.01 && (
                    <div
                      style={{
                        alignSelf: 'flex-end',
                        maxWidth: '86%',
                        background: '#005C4B',
                        borderRadius: '18px 18px 4px 18px',
                        padding: '16px 22px',
                        transform: `scale(${msg4Spring})`,
                        opacity: msg4Spring,
                        boxShadow: '0 6px 18px rgba(0, 0, 0, 0.4)',
                        border: '2px solid #25D366',
                      }}
                    >
                      <div
                        style={{
                          fontFamily,
                          fontSize: 34,
                          fontWeight: 800,
                          color: '#FFFFFF',
                          lineHeight: 1.35,
                        }}
                      >
                        ✅ Pronto, reagendado para quinta às 16h. Até lá!
                      </div>
                      <div
                        style={{
                          fontFamily,
                          fontSize: 32,
                          color: '#8696A0',
                          textAlign: 'right',
                          marginTop: 6,
                        }}
                      >
                        14:16 ✓✓
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Barra Inferior WhatsApp (Input Box) */}
              <div
                style={{
                  background: '#202C33',
                  padding: '12px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                }}
              >
                <div
                  style={{
                    flex: 1,
                    background: '#2A3942',
                    borderRadius: 20,
                    padding: '8px 18px',
                    fontFamily,
                    fontSize: 32,
                    color: '#8696A0',
                  }}
                >
                  Mensagem...
                </div>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    background: '#00A884',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 24,
                  }}
                >
                  🎙️
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
