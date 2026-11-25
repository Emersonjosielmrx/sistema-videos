import React from 'react';
import {
  Img,
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

export const Cena2ComoFunciona: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Reenquadramento do vídeo de fundo (leve zoom + pan para afastar atores do centro e desobstruir o rosto)
  const bgScale = interpolate(frame, [0, 215], [1.18, 1.25], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 215], [-140, -165], {
    extrapolateRight: 'clamp',
  });

  // Microdinâmica constante de elevação
  const floatY = Math.sin(frame / 12) * 4;

  // Header superior
  const headerSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Entrada do Celular Mockup (~11.1s) -> frame 16
  const phoneSpring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Rolagem suave simulando navegação ("vê as fotos dos pratos", frame 65 a 115)
  // Desloca exatamente 1 card inteiro (144px + 16px gap = 160px) para parar com itens 100% inteiros
  const scrollY = interpolate(frame, [65, 115], [0, -160], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Destaque de seleção no prato (~13.5s -> frame 75)
  const dishSelected = frame >= 75;

  // Botão WhatsApp "faz o pedido pelo WhatsApp" (~14.8s -> frame 128)
  const orderSpring = spring({
    frame: frame - 128,
    fps,
    config: {damping: 10, stiffness: 130},
  });
  const orderPulse = 1 + Math.sin(Math.max(0, frame - 128) / 7) * 0.035;

  // 3D rotation sutil do celular
  const rotateY = interpolate(frame, [16, 75, 215], [8, 0, -2], {
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
      }}
    >
      {/* Vídeo B-roll comercial com enquadramento corrigido para desobstruir 100% o rosto do homem */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale}) translate(${bgTranslateX}px, -20px)`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('video_2.mp4')}
          muted
          style={{
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu protetor de alto contraste para destacar o celular e títulos */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(11, 13, 19, 0.92) 0%, rgba(11, 13, 19, 0.65) 28%, rgba(11, 13, 19, 0.70) 70%, rgba(11, 13, 19, 0.96) 100%)',
        }}
      />

      {/* Conteúdo na Safe Zone (y=150 a y=1580, x=60 a x=1020) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 165,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 30,
        }}
      >
        {/* Header superior */}
        {headerSpring > 0 && (
          <div
            style={{
              transform: `scale(${headerSpring})`,
              opacity: headerSpring,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              marginBottom: 20,
            }}
          >
            {/* Badge Rótulo "COMO FUNCIONA" */}
            <div
              style={{
                backgroundColor: '#FACC15',
                padding: '10px 26px',
                borderRadius: 999,
                boxShadow: '0 8px 24px rgba(250, 204, 21, 0.45)',
                border: '2px solid #000000',
                marginBottom: 12,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#000000',
                  letterSpacing: 1.5,
                  textTransform: 'uppercase',
                }}
              >
                COMO FUNCIONA
              </span>
            </div>

            {/* Título Principal */}
            <div
              style={{
                backgroundColor: 'rgba(11, 13, 19, 0.94)',
                border: '2px solid rgba(255, 255, 255, 0.15)',
                padding: '14px 34px',
                borderRadius: 18,
                textAlign: 'center',
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.8)',
              }}
            >
              <h2
                style={{
                  fontFamily,
                  fontSize: 46,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  margin: 0,
                  lineHeight: 1.15,
                  textTransform: 'uppercase',
                }}
              >
                CARDÁPIO DIGITAL NO CELULAR
              </h2>
            </div>
          </div>
        )}

        {/* Smartphone Mockup Realista com Screencast Premium (largura ampliada para 720px) */}
        {phoneSpring > 0 && (
          <div
            style={{
              transform: `perspective(1200px) rotateY(${rotateY}deg) scale(${phoneSpring}) translateY(${floatY}px)`,
              opacity: phoneSpring,
              width: 720,
              height: 870,
              borderRadius: 44,
              backgroundColor: '#090D16',
              border: '4px solid #334155',
              boxShadow:
                '0 30px 70px rgba(0, 0, 0, 0.92), 0 0 45px rgba(225, 29, 72, 0.3)',
              padding: '18px 22px',
              display: 'flex',
              flexDirection: 'column',
              boxSizing: 'border-box',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Notch / Câmera superior */}
            <div
              style={{
                width: 160,
                height: 22,
                borderRadius: 12,
                backgroundColor: '#1E293B',
                margin: '0 auto 14px auto',
              }}
            />

            {/* Cabeçalho do App dentro do mockup */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                paddingBottom: 14,
                borderBottom: '2px solid rgba(255, 255, 255, 0.12)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <span style={{fontSize: 34}}>🍽️</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FFFFFF',
                  }}
                >
                  Cardápio Digital
                </span>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#22C55E',
                  backgroundColor: 'rgba(34, 197, 94, 0.18)',
                  padding: '4px 14px',
                  borderRadius: 10,
                }}
              >
                Online
              </span>
            </div>

            {/* Screencast Gastronômico com Fotos Reais e Rolagem Vertical Animada */}
            <div
              style={{
                marginTop: 16,
                flex: 1,
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              <div
                style={{
                  transform: `translateY(${scrollY}px)`,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16,
                }}
              >
                {/* Card do Prato 1: Almoço do Dia com Foto Real de Alta Fidelidade */}
                <div
                  style={{
                    backgroundColor: 'rgba(30, 41, 59, 0.92)',
                    border: dishSelected
                      ? '3px solid #FACC15'
                      : '2px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: 22,
                    padding: '16px',
                    boxShadow: dishSelected
                      ? '0 10px 30px rgba(250, 204, 21, 0.35)'
                      : '0 8px 24px rgba(0, 0, 0, 0.5)',
                    transform: `scale(${dishSelected ? 1.02 : 1.0})`,
                    transition: 'all 0.2s ease',
                  }}
                >
                  <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
                    <div
                      style={{
                        width: 105,
                        height: 105,
                        borderRadius: 18,
                        overflow: 'hidden',
                        flexShrink: 0,
                        border: '2px solid rgba(255, 255, 255, 0.25)',
                      }}
                    >
                      <Img
                        src={staticFile('foto_prato_1.jpg')}
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover',
                        }}
                      />
                    </div>
                    <div style={{flex: 1}}>
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
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
                          Almoço do Dia
                        </span>
                        {dishSelected && (
                          <span
                            style={{
                              fontFamily,
                              fontSize: 32,
                              fontWeight: 900,
                              color: '#FACC15',
                              backgroundColor: 'rgba(250, 204, 21, 0.2)',
                              padding: '2px 10px',
                              borderRadius: 8,
                            }}
                          >
                            ✓ Escolhido
                          </span>
                        )}
                      </div>
                      <span
                        style={{
                          fontFamily,
                          fontSize: 32,
                          fontWeight: 700,
                          color: '#FACC15',
                          display: 'block',
                          marginTop: 4,
                        }}
                      >
                        Fotos e Detalhes
                      </span>
                    </div>
                  </div>
                </div>

                {/* Card do Prato 2: Prato Executivo com Foto Real */}
                <div
                  style={{
                    backgroundColor: 'rgba(30, 41, 59, 0.85)',
                    border: '2px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: 22,
                    padding: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 18,
                  }}
                >
                  <div
                    style={{
                      width: 105,
                      height: 105,
                      borderRadius: 18,
                      overflow: 'hidden',
                      flexShrink: 0,
                      border: '2px solid rgba(255, 255, 255, 0.25)',
                    }}
                  >
                    <Img
                      src={staticFile('foto_prato_2.jpg')}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                      }}
                    />
                  </div>
                  <div>
                    <span
                      style={{
                        fontFamily,
                        fontSize: 34,
                        fontWeight: 900,
                        color: '#FFFFFF',
                        display: 'block',
                      }}
                    >
                      Prato Executivo
                    </span>
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 700,
                        color: '#CBD5E1',
                        display: 'block',
                        marginTop: 4,
                      }}
                    >
                      Escolha de guarnições
                    </span>
                  </div>
                </div>

                {/* Card do Prato 3: Feijoada com Foto Real */}
                <div
                  style={{
                    backgroundColor: 'rgba(30, 41, 59, 0.85)',
                    border: '2px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: 22,
                    padding: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 18,
                  }}
                >
                  <div
                    style={{
                      width: 105,
                      height: 105,
                      borderRadius: 18,
                      overflow: 'hidden',
                      flexShrink: 0,
                      border: '2px solid rgba(255, 255, 255, 0.25)',
                    }}
                  >
                    <Img
                      src={staticFile('foto_prato_3.jpg')}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                      }}
                    />
                  </div>
                  <div>
                    <span
                      style={{
                        fontFamily,
                        fontSize: 34,
                        fontWeight: 900,
                        color: '#FFFFFF',
                        display: 'block',
                      }}
                    >
                      Feijoada Especial
                    </span>
                    <span
                      style={{
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 700,
                        color: '#CBD5E1',
                        display: 'block',
                        marginTop: 4,
                      }}
                    >
                      Completa com acompanhamentos
                    </span>
                  </div>
                </div>

                {/* Selo de Atendimento com IA */}
                <div
                  style={{
                    backgroundColor: 'rgba(225, 29, 72, 0.28)',
                    border: '2px solid #E11D48',
                    borderRadius: 18,
                    padding: '14px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                  }}
                >
                  <span style={{fontSize: 34}}>🤖</span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    IA tira dúvidas na hora
                  </span>
                </div>
              </div>
            </div>

            {/* Botão de Ação Inferior: Alto contraste garantido desde o início */}
            <div
              style={{
                marginTop: 'auto',
                paddingTop: 14,
              }}
            >
              {frame < 128 ? (
                <div
                  style={{
                    backgroundColor: '#1E293B',
                    border: '2.5px solid #FACC15',
                    borderRadius: 20,
                    padding: '18px',
                    textAlign: 'center',
                    boxShadow: '0 8px 20px rgba(0, 0, 0, 0.6)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      letterSpacing: 0.5,
                    }}
                  >
                    Monte seu Pedido
                  </span>
                </div>
              ) : (
                <div
                  style={{
                    transform: `scale(${orderSpring * orderPulse})`,
                    backgroundColor: '#22C55E',
                    borderRadius: 20,
                    padding: '20px 24px',
                    textAlign: 'center',
                    boxShadow: '0 12px 35px rgba(34, 197, 94, 0.75)',
                    border: '3px solid #FFFFFF',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 12,
                  }}
                >
                  <svg
                    width="34"
                    height="34"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#FFFFFF"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      textTransform: 'uppercase',
                      letterSpacing: 0.5,
                    }}
                  >
                    PEDIR NO WHATSAPP
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
