import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no vídeo do dono (push suave 1.02 a 1.07)
  const videoScale = interpolate(frame, [0, 235], [1.02, 1.07], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada da cena (overlap com cena 1)
  const sceneOpacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Badge do topo
  const sprBadge = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Timings das etapas (relativos ao início da Cena 2 aos 11.34s)
  // Passo 1: 12.278s global -> frame 28 local
  // Passo 2: 14.538s global -> frame 96 local
  // Passo 3: 16.438s global -> frame 153 local
  const step1Active = frame >= 28;
  const step2Active = frame >= 96;
  const step3Active = frame >= 153;

  const sprStep1 = spring({
    frame: frame - 28,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const sprStep2 = spring({
    frame: frame - 96,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const sprStep3 = spring({
    frame: frame - 153,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Entrada do smartphone mockup ao lado do apresentador (entra aos 0.5s -> frame 15)
  const sprPhone = spring({
    frame: frame - 15,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Flutuação contínua suave no mockup do celular
  const phoneFloatY = Math.sin(frame / 14) * 6;

  // Scroll suave dos pratos no cardápio digital (Passo 2)
  const menuScrollY = interpolate(frame, [96, 140], [0, -140], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Animação de digitação / resposta da IA (Passo 3)
  const sprIaResposta = spring({
    frame: frame - 170,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  const sprIaConfirmacao = spring({
    frame: frame - 195,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        fontFamily,
        opacity: sceneOpacity,
      }}
    >
      {/* Vídeo do Dono posicionado à esquerda (translateX -250px) para resguardar o rosto com folga ampla */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale}) translateX(-250px)`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_2.mp4')}
          muted
          style={{
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
          }}
        />
        {/* Vinheta escura no topo */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(to bottom, rgba(11, 13, 19, 0.94) 0%, rgba(11, 13, 19, 0.55) 75%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
        {/* Vinheta escura na base para a legenda */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 450,
            background:
              'linear-gradient(to top, rgba(11, 13, 19, 0.95) 0%, rgba(11, 13, 19, 0.5) 70%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Faixa Superior (Safe Zone y = 155 a 420) — Respiro garantido acima do apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 30,
        }}
      >
        {/* Pill Badge: COMO FUNCIONA */}
        <div
          style={{
            transform: `scale(${sprBadge})`,
            opacity: sprBadge,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 30,
            background: '#31060F',
            border: '1.5px solid #E11D48',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.75)',
          }}
        >
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            COMO FUNCIONA · 3 ETAPAS
          </span>
        </div>

        {/* Painel com as 3 Etapas 1-2-3 Sequenciais */}
        <div
          style={{
            width: '100%',
            maxWidth: 960,
            background: 'rgba(11, 13, 19, 0.94)',
            borderRadius: 22,
            border: '1.5px solid rgba(255, 255, 255, 0.15)',
            padding: '16px 20px',
            boxShadow: '0 15px 35px rgba(0, 0, 0, 0.85)',
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
          }}
        >
          {/* As 3 Abas Horizontais */}
          <div
            style={{
              display: 'flex',
              gap: 12,
              width: '100%',
            }}
          >
            {/* Etapa 1 */}
            <div
              style={{
                flex: 1,
                padding: '10px 8px',
                borderRadius: 14,
                background: step1Active ? '#E11D48' : 'rgba(255, 255, 255, 0.06)',
                border: step1Active
                  ? '1.5px solid #FACC15'
                  : '1px solid rgba(255, 255, 255, 0.1)',
                transform: step1Active
                  ? `scale(${interpolate(sprStep1, [0, 1], [0.95, 1.02])})`
                  : 'scale(1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: step1Active
                  ? '0 6px 18px rgba(225, 29, 72, 0.6)'
                  : 'none',
              }}
            >
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: step1Active ? '#FFFFFF' : '#94A3B8',
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                }}
              >
                1. LINK
              </span>
            </div>

            {/* Etapa 2 */}
            <div
              style={{
                flex: 1,
                padding: '10px 8px',
                borderRadius: 14,
                background: step2Active ? '#E11D48' : 'rgba(255, 255, 255, 0.06)',
                border: step2Active
                  ? '1.5px solid #FACC15'
                  : '1px solid rgba(255, 255, 255, 0.1)',
                transform: step2Active
                  ? `scale(${interpolate(sprStep2, [0, 1], [0.95, 1.02])})`
                  : 'scale(1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: step2Active
                  ? '0 6px 18px rgba(225, 29, 72, 0.6)'
                  : 'none',
              }}
            >
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: step2Active ? '#FFFFFF' : '#94A3B8',
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                }}
              >
                2. FOTOS
              </span>
            </div>

            {/* Etapa 3 */}
            <div
              style={{
                flex: 1,
                padding: '10px 8px',
                borderRadius: 14,
                background: step3Active ? '#E11D48' : 'rgba(255, 255, 255, 0.06)',
                border: step3Active
                  ? '1.5px solid #FACC15'
                  : '1px solid rgba(255, 255, 255, 0.1)',
                transform: step3Active
                  ? `scale(${interpolate(sprStep3, [0, 1], [0.95, 1.02])})`
                  : 'scale(1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: step3Active
                  ? '0 6px 18px rgba(225, 29, 72, 0.6)'
                  : 'none',
              }}
            >
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: step3Active ? '#FFFFFF' : '#94A3B8',
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                }}
              >
                3. IA & PEDE
              </span>
            </div>
          </div>

          {/* Linha de Destaque da Etapa Ativa (Padronizada rigorosamente em branco #FFFFFF) */}
          <div
            style={{
              textAlign: 'center',
              padding: '6px 0',
            }}
          >
            {step3Active ? (
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textShadow: '0 2px 6px rgba(0,0,0,0.8)',
                }}
              >
                ✓ Tira dúvidas com a IA e fecha o pedido
              </span>
            ) : step2Active ? (
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textShadow: '0 2px 6px rgba(0,0,0,0.8)',
                }}
              >
                ✓ Vê as fotos dos pratos direto no celular
              </span>
            ) : step1Active ? (
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textShadow: '0 2px 6px rgba(0,0,0,0.8)',
                }}
              >
                ✓ Cliente recebe o link no WhatsApp
              </span>
            ) : (
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#FFFFFF',
                }}
              >
                Cardápio digital com pedido no WhatsApp
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Mockup Flutuante de Smartphone com Demonstração Real do Produto (x=630 a 1040, y=490 a 1380) */}
      <div
        style={{
          position: 'absolute',
          top: 490,
          right: 35,
          width: 410,
          height: 860,
          transform: `scale(${sprPhone}) translateY(${phoneFloatY}px)`,
          opacity: Math.min(sprPhone, 1),
          borderRadius: 44,
          background: '#0B0D13',
          border: '3px solid rgba(255, 255, 255, 0.22)',
          boxShadow: '0 25px 65px rgba(0, 0, 0, 0.95), 0 0 35px rgba(225, 29, 72, 0.3)',
          overflow: 'hidden',
          zIndex: 25,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Notch / Barra Superior do Smartphone */}
        <div
          style={{
            height: 52,
            background: '#1F2937',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 18px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <span style={{fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
            {step3Active ? 'WhatsApp' : 'Cardápio'}
          </span>
          <div
            style={{
              padding: '2px 10px',
              borderRadius: 8,
              background: '#E11D48',
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
            }}
          >
            DEMO
          </div>
        </div>

        {/* Conteúdo Dinâmico do Celular Sincronizado com a Locução */}
        <div
          style={{
            flex: 1,
            position: 'relative',
            background: step3Active ? '#111827' : '#0B0D13',
            overflow: 'hidden',
            padding: 16,
          }}
        >
          {/* ETAPA 1: RECEBE O LINK NO WHATSAPP */}
          {!step2Active && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
                paddingTop: 10,
              }}
            >
              <div
                style={{
                  background: '#1F2937',
                  padding: 16,
                  borderRadius: 20,
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                }}
              >
                <div style={{fontSize: 32, fontWeight: 700, color: '#FFFFFF', lineHeight: 1.3}}>
                  Olá! Acesse nosso cardápio digital:
                </div>
                <div
                  style={{
                    marginTop: 12,
                    background: '#E11D48',
                    padding: '12px 16px',
                    borderRadius: 14,
                    textAlign: 'center',
                    boxShadow: '0 6px 16px rgba(225, 29, 72, 0.5)',
                  }}
                >
                  <span style={{fontSize: 32, fontWeight: 900, color: '#FFFFFF'}}>
                    👉 VER CARDÁPIO
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* ETAPA 2: VÊ AS FOTOS DOS PRATOS (Cardápio com fotos apetitosas rolando) */}
          {step2Active && !step3Active && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
                transform: `translateY(${menuScrollY}px)`,
                transition: 'transform 0.1s linear',
              }}
            >
              {/* Card Prato 1: Burger Gourmet */}
              <div
                style={{
                  background: '#1E293B',
                  borderRadius: 20,
                  border: '1.5px solid rgba(225, 29, 72, 0.5)',
                  overflow: 'hidden',
                  boxShadow: '0 8px 20px rgba(0,0,0,0.7)',
                }}
              >
                <div
                  style={{
                    height: 140,
                    background: 'linear-gradient(135deg, #78350F 0%, #451A03 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                  }}
                >
                  <span style={{fontSize: 68}}>🍔</span>
                  <div
                    style={{
                      position: 'absolute',
                      top: 10,
                      right: 10,
                      background: '#E11D48',
                      padding: '4px 10px',
                      borderRadius: 10,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    FOTO REAL
                  </div>
                </div>
                <div style={{padding: 14}}>
                  <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                    Burger Artesanal
                  </div>
                  <div style={{fontSize: 32, color: '#FACC15', fontWeight: 700, marginTop: 4}}>
                    Blend 180g & Queijo
                  </div>
                </div>
              </div>

              {/* Card Prato 2: Pizza Forno a Lenha */}
              <div
                style={{
                  background: '#1E293B',
                  borderRadius: 20,
                  border: '1.5px solid rgba(250, 204, 21, 0.4)',
                  overflow: 'hidden',
                  boxShadow: '0 8px 20px rgba(0,0,0,0.7)',
                }}
              >
                <div
                  style={{
                    height: 140,
                    background: 'linear-gradient(135deg, #991B1B 0%, #7F1D1D 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                  }}
                >
                  <span style={{fontSize: 68}}>🍕</span>
                  <div
                    style={{
                      position: 'absolute',
                      top: 10,
                      right: 10,
                      background: '#FACC15',
                      padding: '4px 10px',
                      borderRadius: 10,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#000000',
                    }}
                  >
                    DESTAQUE
                  </div>
                </div>
                <div style={{padding: 14}}>
                  <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                    Pizza Artesanal
                  </div>
                  <div style={{fontSize: 32, color: '#FACC15', fontWeight: 700, marginTop: 4}}>
                    Forno a Lenha
                  </div>
                </div>
              </div>

              {/* Card Prato 3: Sobremesa */}
              <div
                style={{
                  background: '#1E293B',
                  borderRadius: 20,
                  border: '1.5px solid rgba(225, 29, 72, 0.4)',
                  overflow: 'hidden',
                  boxShadow: '0 8px 20px rgba(0,0,0,0.7)',
                }}
              >
                <div
                  style={{
                    height: 130,
                    background: 'linear-gradient(135deg, #581C87 0%, #3B0764 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <span style={{fontSize: 64}}>🍧</span>
                </div>
                <div style={{padding: 14}}>
                  <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                    Açaí na Tigela
                  </div>
                  <div style={{fontSize: 32, color: '#FACC15', fontWeight: 700, marginTop: 4}}>
                    Frutas Frescas
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ETAPA 3: TIRA DÚVIDAS COM A IA E PEDE */}
          {step3Active && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 14,
                paddingTop: 8,
              }}
            >
              {/* Pergunta do Cliente */}
              <div
                style={{
                  alignSelf: 'flex-start',
                  background: '#374151',
                  padding: '12px 16px',
                  borderRadius: '16px 16px 16px 4px',
                  maxWidth: '88%',
                }}
              >
                <div style={{fontSize: 32, fontWeight: 700, color: '#FFFFFF'}}>
                  Acompanha molho especial?
                </div>
              </div>

              {/* Resposta da IA com Balão e Badge */}
              <div
                style={{
                  alignSelf: 'flex-end',
                  transform: `scale(${sprIaResposta})`,
                  opacity: Math.min(sprIaResposta, 1),
                  background: 'linear-gradient(135deg, #15803D, #166534)',
                  padding: '12px 16px',
                  borderRadius: '16px 16px 4px 16px',
                  border: '1.5px solid #86EFAC',
                  maxWidth: '92%',
                  boxShadow: '0 8px 20px rgba(0,0,0,0.6)',
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4}}>
                  <span style={{fontSize: 32}}>🤖</span>
                  <span style={{fontSize: 32, fontWeight: 900, color: '#FACC15'}}>
                    IA RESPONDE:
                  </span>
                </div>
                <div style={{fontSize: 32, fontWeight: 700, color: '#FFFFFF', lineHeight: 1.25}}>
                  Sim! Vai com molho especial. Deseja pedir?
                </div>
              </div>

              {/* Confirmação do Pedido */}
              {frame >= 195 && (
                <div
                  style={{
                    alignSelf: 'center',
                    transform: `scale(${sprIaConfirmacao})`,
                    opacity: Math.min(sprIaConfirmacao, 1),
                    background: '#E11D48',
                    padding: '10px 18px',
                    borderRadius: 16,
                    border: '1.5px solid #FACC15',
                    textAlign: 'center',
                    boxShadow: '0 8px 20px rgba(225, 29, 72, 0.6)',
                  }}
                >
                  <div style={{fontSize: 32, fontWeight: 900, color: '#FFFFFF'}}>
                    ✓ PEDIDO ENVIADO!
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
