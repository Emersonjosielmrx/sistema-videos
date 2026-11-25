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
  marcaCor: string;
  apoioCor: string;
}

export const Cena2Conversa: React.FC<Props> = ({
  fontFamily,
  marcaCor,
  apoioCor,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de fundo
  const scaleBg = interpolate(frame, [0, 270], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });

  // Micro-dinâmica do celular (flutuação 3D suave)
  const floatPhoneY = Math.sin(frame / 16) * 5;
  const rotY = -5 + Math.sin(frame / 20) * 1.5;

  // Entrada do Celular com mola elástica
  const phoneSpring = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.9},
  });
  const phoneScale = interpolate(phoneSpring, [0, 1], [0.85, 1]);
  const phoneOpacity = interpolate(phoneSpring, [0, 1], [0, 1]);

  // Mensagens com entrada escalonada
  const m1Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Digitando (ativo entre frames 62 e 92)
  const isTyping = frame >= 62 && frame < 92;

  const m2Spring = spring({
    frame: frame - 92,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  const m3Spring = spring({
    frame: frame - 138,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  const m4Spring = spring({
    frame: frame - 180,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Rolagem suave do chat conforme novas mensagens entram
  const scrollOffset = interpolate(
    frame,
    [0, 12, 92, 138, 180, 240],
    [0, 0, 40, 120, 220, 240],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Transição de saída nos últimos 15 frames
  const exitOpacity = interpolate(frame, [255, 270], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: apoioCor,
        opacity: exitOpacity,
      }}
    >
      {/* Imagem de Fundo com Câmera Dinâmica */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${scaleBg})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: 1080,
            height: 1920,
            objectFit: 'cover',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 50%, rgba(15, 23, 42, 0.88) 0%, rgba(11, 13, 19, 0.96) 100%)',
          }}
        />
      </div>

      {/* Top Header Seguro (y=165 a 300) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            padding: '8px 24px',
            borderRadius: 999,
            background: 'rgba(11, 13, 19, 0.94)',
            border: `1.5px solid ${marcaCor}`,
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: marcaCor,
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            COMO FUNCIONA
          </span>
        </div>

        <span
          style={{
            fontFamily,
            fontSize: 48,
            fontWeight: 900,
            color: '#FFFFFF',
            textAlign: 'center',
            textShadow: '0 4px 16px rgba(0,0,0,0.8)',
          }}
        >
          BOT QUE CONHECE SUA LOJA
        </span>
      </div>

      {/* MOCKUP MOBILE 3D (y=320 a y=1280, altura 950px, largura 840px) */}
      <div
        style={{
          position: 'absolute',
          top: 320,
          left: 120,
          width: 840,
          height: 950,
          perspective: 1200,
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            borderRadius: 44,
            backgroundColor: '#0F172A',
            border: '4px solid #334155',
            boxShadow:
              '0 30px 70px rgba(0,0,0,0.85), 0 0 35px rgba(167, 139, 250, 0.25)',
            transform: `scale(${phoneScale}) rotateY(${rotY}deg) translateY(${floatPhoneY}px)`,
            opacity: phoneOpacity,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Barra de Status do Celular */}
          <div
            style={{
              height: 52,
              padding: '0 32px',
              backgroundColor: '#0F172A',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#CBD5E1',
              }}
            >
              02:45
            </span>
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <span style={{fontSize: 26, color: '#94A3B8'}}>📶</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#CBD5E1',
                }}
              >
                100%
              </span>
            </div>
          </div>

          {/* Cabeçalho do WhatsApp da Loja */}
          <div
            style={{
              padding: '16px 28px',
              backgroundColor: '#1E293B',
              borderBottom: '1.5px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: '50%',
                  backgroundColor: marcaCor,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: `0 0 16px rgba(167, 139, 250, 0.5)`,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 900,
                    color: '#121216',
                  }}
                >
                  IA
                </span>
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Vitrine IA
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#4ADE80',
                  }}
                >
                  ● Online agora
                </span>
              </div>
            </div>

            {/* Selo Simulação Obrigatório */}
            <div
              style={{
                padding: '6px 16px',
                borderRadius: 12,
                backgroundColor: 'rgba(255, 255, 255, 0.12)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#E2E8F0',
                }}
              >
                Simulação
              </span>
            </div>
          </div>

          {/* Área de Conversa do Chat com Rolagem Fluida */}
          <div
            style={{
              flex: 1,
              padding: '24px 24px',
              backgroundColor: '#090D16',
              display: 'flex',
              flexDirection: 'column',
              gap: 20,
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 20,
                transform: `translateY(-${scrollOffset}px)`,
                transition: 'transform 0.1s linear',
              }}
            >
              {/* Balão 1: Cliente */}
              {frame >= 12 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '82%',
                    padding: '16px 24px',
                    borderRadius: '24px 24px 24px 6px',
                    backgroundColor: '#1E293B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    boxShadow: '0 6px 18px rgba(0, 0, 0, 0.4)',
                    transform: `scale(${interpolate(m1Spring, [0, 1], [0.8, 1])})`,
                    opacity: m1Spring,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#F8FAFC',
                      lineHeight: 1.3,
                    }}
                  >
                    Oi, vocês ainda têm tênis para caminhada?
                  </span>
                  <div
                    style={{
                      marginTop: 6,
                      textAlign: 'right',
                      fontFamily,
                      fontSize: 32,
                      color: '#94A3B8',
                    }}
                  >
                    02:45
                  </div>
                </div>
              )}

              {/* Indicador de Digitando */}
              {isTyping && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    padding: '12px 24px',
                    borderRadius: '24px 24px 6px 24px',
                    backgroundColor: 'rgba(88, 28, 135, 0.7)',
                    border: `1.5px solid ${marcaCor}`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#DDD6FE',
                    }}
                  >
                    Vitrine IA digitando...
                  </span>
                </div>
              )}

              {/* Balão 2: Bot Empresa */}
              {frame >= 92 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '86%',
                    padding: '16px 24px',
                    borderRadius: '24px 24px 6px 24px',
                    backgroundColor: '#4C1D95',
                    border: `1.5px solid ${marcaCor}`,
                    boxShadow: '0 8px 24px rgba(124, 58, 237, 0.35)',
                    transform: `scale(${interpolate(m2Spring, [0, 1], [0.8, 1])})`,
                    opacity: m2Spring,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#FFFFFF',
                      lineHeight: 1.3,
                    }}
                  >
                    Temos sim! Você prefere um modelo mais leve ou com mais amortecimento?
                  </span>
                  <div
                    style={{
                      marginTop: 6,
                      textAlign: 'right',
                      fontFamily,
                      fontSize: 32,
                      color: '#C4B5FD',
                    }}
                  >
                    02:46 ✓✓
                  </div>
                </div>
              )}

              {/* Balão 3: Cliente */}
              {frame >= 138 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '82%',
                    padding: '16px 24px',
                    borderRadius: '24px 24px 24px 6px',
                    backgroundColor: '#1E293B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    boxShadow: '0 6px 18px rgba(0, 0, 0, 0.4)',
                    transform: `scale(${interpolate(m3Spring, [0, 1], [0.8, 1])})`,
                    opacity: m3Spring,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#F8FAFC',
                      lineHeight: 1.3,
                    }}
                  >
                    Mais amortecimento. Uso todo dia.
                  </span>
                  <div
                    style={{
                      marginTop: 6,
                      textAlign: 'right',
                      fontFamily,
                      fontSize: 32,
                      color: '#94A3B8',
                    }}
                  >
                    02:46
                  </div>
                </div>
              )}

              {/* Balão 4: Bot Empresa Recomenda */}
              {frame >= 180 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '86%',
                    padding: '16px 24px',
                    borderRadius: '24px 24px 6px 24px',
                    backgroundColor: '#4C1D95',
                    border: `1.5px solid ${marcaCor}`,
                    boxShadow: '0 8px 24px rgba(124, 58, 237, 0.35)',
                    transform: `scale(${interpolate(m4Spring, [0, 1], [0.8, 1])})`,
                    opacity: m4Spring,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#FFFFFF',
                      lineHeight: 1.3,
                    }}
                  >
                    Então o modelo com solado macio é o ideal para você. Posso te mostrar?
                  </span>
                  <div
                    style={{
                      marginTop: 6,
                      textAlign: 'right',
                      fontFamily,
                      fontSize: 32,
                      color: '#C4B5FD',
                    }}
                  >
                    02:47 ✓✓
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
