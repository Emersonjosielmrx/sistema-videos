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

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com pan e leve zoom contínuo
  const bgScale = interpolate(frame, [0, 240], [1.06, 1.15], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 240], [-15, 15], {
    extrapolateRight: 'clamp',
  });

  // Entrada do celular em 3D
  const phoneSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Card do prato no cardápio entra aos ~0.4s (frame 12)
  const dishSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Balão 1 (Cliente: "Tem opção sem cebola no lanche?"): entra aos ~1.5s -> frame 45
  const b1Spring = spring({
    frame: frame - 45,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Digitando (entra frame 85 e some frame 125)
  const isTyping = frame >= 85 && frame < 125;

  // Balão 2 (Empresa/IA: "Sim! Você pode retirar a cebola..."): entra aos ~4.2s -> frame 125
  const b2Spring = spring({
    frame: frame - 125,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Balão 3 (Cliente: "Maravilha, vou fechar aqui!"): entra aos ~5.5s -> frame 165
  const b3Spring = spring({
    frame: frame - 165,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Micro animação contínua de inclinação 3D
  const rotY = -8 + Math.sin(frame / 20) * 3;
  const rotX = 3 + Math.cos(frame / 22) * 2;

  // Mudança temática do título do topo sincronizada com a locução
  const topText =
    frame < 68
      ? 'ACESSO DIRETO NO CELULAR 📱'
      : frame < 125
      ? 'CARDÁPIO COM FOTOS DOS PRATOS 📸'
      : 'IA ESCLARECENDO DÚVIDAS 🤖';

  return (
    <AbsoluteFill style={{backgroundColor: '#1E050B', overflow: 'hidden'}}>
      {/* Imagem de Fundo com desfoque e movimento suave */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateX(${bgTranslateX}px)`,
          filter: 'blur(10px) brightness(0.38)',
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

      {/* Header na Safe Zone Superior (y=170 a 320) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 10,
        }}
      >
        <div
          style={{
            backgroundColor: '#E11D48',
            borderRadius: 12,
            padding: '8px 24px',
            border: '2px solid rgba(250, 204, 21, 0.4)',
            boxShadow: '0 8px 20px rgba(225, 29, 72, 0.5)',
            marginBottom: 10,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            COMO FUNCIONA
          </span>
        </div>

        <div
          style={{
            backgroundColor: 'rgba(25, 5, 10, 0.90)',
            borderRadius: 16,
            padding: '10px 28px',
            border: '2px solid rgba(250, 204, 21, 0.5)',
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 900,
              color: '#FACC15',
              textTransform: 'uppercase',
              letterSpacing: 1,
            }}
          >
            {topText}
          </span>
        </div>
      </div>

      {/* Mockup de Celular 3D — Zona Central Segura (y: 350 a 1120, compacto e preenchido) */}
      <div
        style={{
          position: 'absolute',
          top: 350,
          left: 65,
          width: 950,
          height: 760,
          perspective: 1200,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 5,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            backgroundColor: '#111827',
            borderRadius: 42,
            border: '6px solid #374151',
            boxShadow:
              '0 25px 60px rgba(0, 0, 0, 0.95), 0 0 40px rgba(225, 29, 72, 0.25)',
            transform: `scale(${phoneSpring}) rotateY(${rotY}deg) rotateX(${rotX}deg)`,
            transformOrigin: 'center center',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Barra do App Cardápio / WhatsApp */}
          <div
            style={{
              height: 105,
              backgroundColor: '#075E54',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 24px',
              borderBottom: '2px solid rgba(0, 0, 0, 0.25)',
              flexShrink: 0,
            }}
          >
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
                }}
              >
                🍔
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Cardápio Digital
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#86EFAC',
                  }}
                >
                  Atendimento com IA
                </span>
              </div>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(0, 0, 0, 0.4)',
                padding: '8px 16px',
                borderRadius: 12,
                border: '1px solid rgba(255, 255, 255, 0.2)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#E2E8F0',
                  textTransform: 'uppercase',
                }}
              >
                Simulação
              </span>
            </div>
          </div>

          {/* Seção 1: Demonstração do Cardápio Visual com Foto (Elimina container vazio) */}
          <div
            style={{
              backgroundColor: '#1E293B',
              padding: '16px 22px',
              borderBottom: '2px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              alignItems: 'center',
              gap: 18,
              transform: `scale(${dishSpring})`,
              opacity: dishSpring,
              flexShrink: 0,
            }}
          >
            {/* Foto Real do Prato (Miniatura) */}
            <div
              style={{
                width: 140,
                height: 115,
                borderRadius: 16,
                overflow: 'hidden',
                position: 'relative',
                flexShrink: 0,
                border: '2px solid #E11D48',
              }}
            >
              <Img
                src={staticFile('img_0.jpg')}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  transform: 'scale(1.4) translateY(10px)',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  top: 4,
                  left: 4,
                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                  borderRadius: 6,
                  padding: '3px 8px',
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FACC15',
                }}
              >
                FOTO
              </div>
            </div>

            {/* Informações do Prato */}
            <div style={{flex: 1, display: 'flex', flexDirection: 'column'}}>
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  X-Burger Especial
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FACC15',
                  }}
                >
                  R$ 32,90
                </span>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#94A3B8',
                  lineHeight: 1.25,
                  marginBottom: 6,
                }}
              >
                Cardápio interativo com fotos no celular
              </span>
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <span
                  style={{
                    backgroundColor: '#E11D48',
                    color: '#FFFFFF',
                    borderRadius: 8,
                    padding: '4px 12px',
                    fontSize: 32,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                  }}
                >
                  Fotos dos Pratos 📸
                </span>
              </div>
            </div>
          </div>

          {/* Seção 2: Área de Mensagens da Conversa de WhatsApp */}
          <div
            style={{
              flex: 1,
              backgroundColor: '#0B141A',
              padding: '16px 20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'flex-start',
              gap: 14,
              overflow: 'hidden',
            }}
          >
            {/* Aviso de IA no topo da conversa */}
            <div
              style={{
                alignSelf: 'center',
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                padding: '6px 16px',
                borderRadius: 12,
                border: '1px solid rgba(255, 255, 255, 0.1)',
                marginBottom: 4,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#86EFAC',
                }}
              >
                🤖 Atendimento com Inteligência Artificial
              </span>
            </div>

            {/* Balão 1 - Cliente */}
            {frame >= 45 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '85%',
                  backgroundColor: '#202C33',
                  borderRadius: '16px 16px 16px 4px',
                  padding: '14px 20px',
                  transform: `scale(${b1Spring})`,
                  opacity: b1Spring,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2}}>
                  <span style={{fontSize: 26}}>👤</span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#94A3B8',
                    }}
                  >
                    Cliente
                  </span>
                </div>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.3,
                  }}
                >
                  Tem opção sem cebola no lanche?
                </span>
              </div>
            )}

            {/* Indicador de Digitando IA */}
            {isTyping && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  backgroundColor: '#005C4B',
                  borderRadius: '16px 16px 4px 16px',
                  padding: '12px 20px',
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
                    color: '#86EFAC',
                  }}
                >
                  IA esclarecendo dúvidas...
                </span>
              </div>
            )}

            {/* Balão 2 - Empresa com IA */}
            {frame >= 125 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '88%',
                  backgroundColor: '#005C4B',
                  borderRadius: '16px 16px 4px 16px',
                  padding: '14px 20px',
                  transform: `scale(${b2Spring})`,
                  opacity: b2Spring,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                  border: '2px solid rgba(250, 204, 21, 0.4)',
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2}}>
                  <span style={{fontSize: 28}}>🤖</span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#FACC15',
                      textTransform: 'uppercase',
                    }}
                  >
                    Atendimento IA
                  </span>
                </div>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Sim! Você pode retirar a cebola ao montar seu pedido no cardápio.
                </span>
              </div>
            )}

            {/* Balão 3 - Cliente fechando */}
            {frame >= 165 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '85%',
                  backgroundColor: '#202C33',
                  borderRadius: '16px 16px 16px 4px',
                  padding: '14px 20px',
                  transform: `scale(${b3Spring})`,
                  opacity: b3Spring,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.3,
                  }}
                >
                  Maravilha, vou fechar aqui! 🚀
                </span>
              </div>
            )}
          </div>

          {/* Barra de Digitação Inferior do WhatsApp */}
          <div
            style={{
              height: 75,
              backgroundColor: '#1F2C34',
              display: 'flex',
              alignItems: 'center',
              padding: '0 20px',
              gap: 14,
              flexShrink: 0,
            }}
          >
            <span style={{fontSize: 28}}>😊</span>
            <div
              style={{
                flex: 1,
                backgroundColor: '#2A3942',
                borderRadius: 20,
                padding: '8px 18px',
                display: 'flex',
                alignItems: 'center',
              }}
            >
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
                fontSize: 26,
              }}
            >
              🎤
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
