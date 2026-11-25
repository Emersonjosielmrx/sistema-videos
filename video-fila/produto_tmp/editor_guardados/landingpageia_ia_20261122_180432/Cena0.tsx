import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera
  const bgScale = interpolate(frame, [0, 155], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });
  const bgPanY = interpolate(frame, [0, 155], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Fade out no corte de cena (frames 145-155)
  const sceneOpacity = interpolate(frame, [145, 155], [1, 0], {
    extrapolateRight: 'clamp',
  });

  // Badge inicial: pop imediato aos ~0.1s (frame 2)
  const badgeSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Título 1: entra aos ~0.2s (frame 6 - "Por que eu repito")
  const title1Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Título 2 (pill amarela): entra aos ~0.35s (frame 10 - "as mesmas respostas")
  const title2Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Balão de WhatsApp: entra imediatamente no segundo 0 (0.0s) com animação ágil preenchendo a tela
  const bubbleSpring = spring({
    frame: frame - 0,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Micro-movimento oscilante nos elementos
  const floatY = Math.sin((frame / 30) * Math.PI * 2 * 0.6) * 4;
  const pulseScale = 1 + Math.sin((frame / 30) * Math.PI * 2 * 0.9) * 0.02;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0F131A',
        opacity: sceneOpacity,
      }}
    >
      {/* Imagem de Fundo com zoom e pan dinâmicos */}
      <Img
        src={staticFile('img_0.jpg')}
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${bgScale}) translateY(${bgPanY}px)`,
          filter: 'brightness(0.7) contrast(1.15)',
        }}
      />

      {/* Gradiente escuro para legibilidade máxima */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 35%, rgba(245, 158, 11, 0.18) 0%, rgba(11, 15, 23, 0.85) 60%, rgba(11, 15, 23, 0.95) 100%)',
        }}
      />

      {/* Elementos dentro da Safe Zone (y: 150 a 1580, x: 60 a 1020) */}

      {/* Badge de Gancho Superior (y = 200) */}
      <div
        style={{
          position: 'absolute',
          top: 200,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring > 0 ? Math.min(badgeSpring, 1) : 0,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            borderRadius: 30,
            background: 'rgba(239, 68, 68, 0.16)',
            border: '1.5px solid rgba(239, 68, 68, 0.45)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
          }}
        >
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              boxShadow: '0 0 12px #EF4444',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FCA5A5',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            Dúvida Frequente
          </span>
        </div>
      </div>

      {/* Título Cinético Gigante (y = 310 a 580) */}
      <div
        style={{
          position: 'absolute',
          top: 310,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 18,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* Linha 1 */}
        <div
          style={{
            transform: `scale(${title1Spring}) translateY(${interpolate(
              title1Spring,
              [0, 1],
              [40, 0]
            )}px)`,
            opacity: Math.min(title1Spring, 1),
          }}
        >
          <h1
            style={{
              margin: 0,
              fontFamily,
              fontSize: 58,
              fontWeight: 900,
              color: '#FFFFFF',
              textAlign: 'center',
              letterSpacing: -0.5,
              textTransform: 'uppercase',
              textShadow: '0 4px 16px rgba(0, 0, 0, 0.9)',
            }}
          >
            Por Que Eu Repito
          </h1>
        </div>

        {/* Linha 2 (Destaque Marca em Pílula Amarela) */}
        <div
          style={{
            transform: `scale(${title2Spring * pulseScale}) translateY(${interpolate(
              title2Spring,
              [0, 1],
              [35, 0]
            )}px)`,
            opacity: Math.min(title2Spring, 1),
          }}
        >
          <div
            style={{
              padding: '10px 32px',
              borderRadius: 20,
              background: '#F59E0B',
              boxShadow: '0 10px 35px rgba(245, 158, 11, 0.45)',
            }}
          >
            <h2
              style={{
                margin: 0,
                fontFamily,
                fontSize: 52,
                fontWeight: 900,
                color: '#121216',
                textAlign: 'center',
                letterSpacing: 0.5,
                textTransform: 'uppercase',
              }}
            >
              As Mesmas Respostas O Dia Inteiro?
            </h2>
          </div>
        </div>
      </div>

      {/* Balão Mobile WhatsApp Nativo (y = 660 a 940) - Entra no frame 0 */}
      <div
        style={{
          position: 'absolute',
          top: 660,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          transform: `scale(${bubbleSpring}) translateY(${interpolate(
            bubbleSpring,
            [0, 1],
            [60, 0]
          )}px)`,
          opacity: Math.min(bubbleSpring, 1),
        }}
      >
          <div
            style={{
              background: 'rgba(17, 27, 24, 0.96)',
              border: '2px solid rgba(37, 211, 102, 0.4)',
              borderRadius: 28,
              padding: '28px 36px',
              boxShadow: '0 20px 45px rgba(0, 0, 0, 0.75)',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
            }}
          >
            {/* Top row do WhatsApp */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: '50%',
                    backgroundColor: '#25D366',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 900,
                    fontSize: 26,
                    color: '#0D1117',
                  }}
                >
                  💬
                </div>
                <div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 36,
                      fontWeight: 800,
                      color: '#25D366',
                    }}
                  >
                    WhatsApp Business
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#94A3B8',
                    }}
                  >
                    Mensagem recebida
                  </div>
                </div>
              </div>
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 24,
                    fontWeight: 700,
                    color: '#25D366',
                    background: 'rgba(37, 211, 102, 0.15)',
                    border: '1px solid rgba(37, 211, 102, 0.35)',
                    padding: '4px 12px',
                    borderRadius: 12,
                    textTransform: 'uppercase',
                    letterSpacing: 0.5,
                  }}
                >
                  Simulação
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 30,
                    fontWeight: 600,
                    color: '#64748B',
                  }}
                >
                  10:42
                </span>
              </div>
            </div>

            {/* Mensagem simulada do cliente */}
            <div
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 600,
                color: '#F8FAFC',
                lineHeight: 1.35,
                background: 'rgba(255, 255, 255, 0.05)',
                padding: '18px 24px',
                borderRadius: 18,
                borderLeft: '4px solid #25D366',
              }}
            >
              "Como funciona? Qual é o valor? Tem vídeo explicando o produto?"
            </div>
          </div>
        </div>
    </div>
  );
};
