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

  // Fundo com leve zoom cinematográfico
  const bgScale = interpolate(frame, [0, 246], [1.08, 1.18], {
    extrapolateRight: 'clamp',
  });

  // Rótulo superior "⚡ COMO FUNCIONA"
  const tagSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Movimento de câmera 3D do Celular (drift suave de rotação e escala)
  const phoneScale = interpolate(frame, [0, 246], [0.98, 1.03], {
    extrapolateRight: 'clamp',
  });
  const phoneRotateY = interpolate(frame, [0, 246], [-10, -5], {
    extrapolateRight: 'clamp',
  });
  const phoneTranslateY = interpolate(frame, [0, 246], [0, -10], {
    extrapolateRight: 'clamp',
  });

  // Animação de entrada dos balões de WhatsApp (escalonados com a narração)
  // 1. Cliente: "Boa noite! Tem pizza meio a meio?" (frame 10)
  const b1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // 2. Empresa: "Boa noite! Temos sim..." (frame 54)
  const b2Spring = spring({
    frame: frame - 54,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // 3. Cliente: "A de frango vem com catupiry?" (frame 105)
  const b3Spring = spring({
    frame: frame - 105,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // 4. Empresa: "Sim, vai com catupiry. Qual a outra metade..." (frame 148)
  const b4Spring = spring({
    frame: frame - 148,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // 5. Cliente: "Quero metade frango e metade calabresa." (frame 188)
  const b5Spring = spring({
    frame: frame - 188,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Scroll suave dos balões à medida que novas mensagens chegam
  const scrollY = interpolate(
    frame,
    [0, 100, 145, 185, 230],
    [0, 0, -110, -250, -260],
    {extrapolateRight: 'clamp'}
  );

  // Fade suave de saída dos balões superiores para nunca encavalar no cabeçalho
  const b1Fade = interpolate(scrollY, [-90, 0], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const b2Fade = interpolate(scrollY, [-240, -100], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#120205', overflow: 'hidden'}}>
      {/* Imagem de Fundo com desfoque de ambiente e iluminação acolhedora */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          filter: 'blur(14px)',
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

      {/* Véu suave da marca para garantir contraste preservando a luz da cena */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 50%, rgba(49, 6, 15, 0.48) 0%, rgba(18, 2, 5, 0.76) 100%)',
        }}
      />

      {/* Rótulo superior: Como funciona (y=165 a 230) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          fontFamily,
          zIndex: 40,
        }}
      >
        <div
          style={{
            opacity: Math.max(0, tagSpring),
            transform: `translateY(${(1 - tagSpring) * -15}px)`,
            backgroundColor: 'rgba(225, 29, 72, 0.3)',
            border: '2px solid rgba(225, 29, 72, 0.85)',
            padding: '8px 28px',
            borderRadius: 999,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
          }}
        >
          <span style={{fontSize: 34}}>⚡</span>
          <span
            style={{
              color: '#FFFFFF',
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

      {/* Mockup do Celular 3D (largura 880px, centralizado na tela, y=250 a 1350) */}
      <div
        style={{
          position: 'absolute',
          top: 250,
          left: 100,
          width: 880,
          height: 1080,
          perspective: 1200,
          zIndex: 30,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            backgroundColor: '#0B141A',
            borderRadius: 48,
            border: '6px solid #2A3942',
            boxShadow:
              '0 25px 60px rgba(0,0,0,0.85), 0 0 40px rgba(225, 29, 72, 0.25)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            transform: `scale(${phoneScale}) rotateY(${phoneRotateY}deg) rotateX(3deg) translateY(${phoneTranslateY}px)`,
            transformOrigin: 'center center',
            fontFamily,
          }}
        >
          {/* Header do WhatsApp */}
          <div
            style={{
              backgroundColor: '#1F2C34',
              padding: '24px 28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid #2A3942',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 32,
                  backgroundColor: '#E11D48',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 34,
                }}
              >
                🍕
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontSize: 36,
                    fontWeight: 800,
                    color: '#E9EDEF',
                  }}
                >
                  Pizzaria Bella
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#25D366',
                  }}
                >
                  IA Atendente • Online
                </span>
              </div>
            </div>

            {/* Selo OBRIGATÓRIO: SIMULAÇÃO (letra >= 32px) */}
            <div
              style={{
                backgroundColor: 'rgba(250, 204, 21, 0.2)',
                border: '2px solid #FACC15',
                padding: '6px 18px',
                borderRadius: 14,
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#FACC15',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                Simulação
              </span>
            </div>
          </div>

          {/* Área de Mensagens com Wallpaper clássico e scroll dinâmico */}
          <div
            style={{
              flex: 1,
              position: 'relative',
              backgroundColor: '#0B141A',
              padding: '28px 24px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                transform: `translateY(${scrollY}px)`,
                display: 'flex',
                flexDirection: 'column',
                gap: 22,
              }}
            >
              {/* Mensagem 1: Cliente */}
              {frame >= 10 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '82%',
                    backgroundColor: '#005C4B',
                    color: '#E9EDEF',
                    borderRadius: '24px 24px 4px 24px',
                    padding: '18px 24px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                    opacity: Math.max(0, b1Spring) * b1Fade,
                    transform: `scale(${interpolate(b1Spring, [0, 1], [0.8, 1])})`,
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontSize: 34,
                      fontWeight: 600,
                      lineHeight: 1.3,
                    }}
                  >
                    Boa noite! Tem pizza meio a meio?
                  </p>
                  <span
                    style={{
                      display: 'block',
                      textAlign: 'right',
                      fontSize: 32,
                      color: '#8696A0',
                      marginTop: 6,
                    }}
                  >
                    20:01 ✓✓
                  </span>
                </div>
              )}

              {/* Mensagem 2: Empresa/IA */}
              {frame >= 54 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '86%',
                    backgroundColor: '#202C33',
                    color: '#E9EDEF',
                    borderRadius: '24px 24px 24px 4px',
                    padding: '18px 24px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                    opacity: Math.max(0, b2Spring) * b2Fade,
                    transform: `scale(${interpolate(b2Spring, [0, 1], [0.8, 1])})`,
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontSize: 34,
                      fontWeight: 600,
                      lineHeight: 1.3,
                    }}
                  >
                    Boa noite! Temos sim. Você pode ver as fotos dos sabores no
                    cardápio aqui no celular.
                  </p>
                  <span
                    style={{
                      display: 'block',
                      textAlign: 'right',
                      fontSize: 32,
                      color: '#8696A0',
                      marginTop: 6,
                    }}
                  >
                    20:01
                  </span>
                </div>
              )}

              {/* Mensagem 3: Cliente */}
              {frame >= 105 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '82%',
                    backgroundColor: '#005C4B',
                    color: '#E9EDEF',
                    borderRadius: '24px 24px 4px 24px',
                    padding: '18px 24px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                    opacity: Math.max(0, b3Spring),
                    transform: `scale(${interpolate(b3Spring, [0, 1], [0.8, 1])})`,
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontSize: 34,
                      fontWeight: 600,
                      lineHeight: 1.3,
                    }}
                  >
                    A de frango vem com catupiry?
                  </p>
                  <span
                    style={{
                      display: 'block',
                      textAlign: 'right',
                      fontSize: 32,
                      color: '#8696A0',
                      marginTop: 6,
                    }}
                  >
                    20:02 ✓✓
                  </span>
                </div>
              )}

              {/* Mensagem 4: Empresa/IA */}
              {frame >= 148 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '86%',
                    backgroundColor: '#202C33',
                    color: '#E9EDEF',
                    borderRadius: '24px 24px 24px 4px',
                    padding: '18px 24px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                    opacity: Math.max(0, b4Spring),
                    transform: `scale(${interpolate(b4Spring, [0, 1], [0.8, 1])})`,
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontSize: 34,
                      fontWeight: 600,
                      lineHeight: 1.3,
                    }}
                  >
                    Sim, vai com catupiry. Qual a outra metade você prefere?
                  </p>
                  <span
                    style={{
                      display: 'block',
                      textAlign: 'right',
                      fontSize: 32,
                      color: '#8696A0',
                      marginTop: 6,
                    }}
                  >
                    20:02
                  </span>
                </div>
              )}

              {/* Mensagem 5: Cliente */}
              {frame >= 188 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '82%',
                    backgroundColor: '#005C4B',
                    color: '#E9EDEF',
                    borderRadius: '24px 24px 4px 24px',
                    padding: '18px 24px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                    opacity: Math.max(0, b5Spring),
                    transform: `scale(${interpolate(b5Spring, [0, 1], [0.8, 1])})`,
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontSize: 34,
                      fontWeight: 600,
                      lineHeight: 1.3,
                    }}
                  >
                    Quero metade frango e metade calabresa.
                  </p>
                  <span
                    style={{
                      display: 'block',
                      textAlign: 'right',
                      fontSize: 32,
                      color: '#8696A0',
                      marginTop: 6,
                    }}
                  >
                    20:03 ✓✓
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
