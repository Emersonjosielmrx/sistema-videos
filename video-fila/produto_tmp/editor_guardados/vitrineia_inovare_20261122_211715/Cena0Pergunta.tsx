import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

interface Props {
  fontFamily: string;
  marcaCor: string;
  apoioCor: string;
}

export const Cena0Pergunta: React.FC<Props> = ({
  fontFamily,
  marcaCor,
  apoioCor,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo: zoom e pan
  const scaleBg = interpolate(frame, [0, 162], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });
  const translateYBg = interpolate(frame, [0, 162], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Micro-dinâmica senoidal para elementos flutuantes
  const floatY = Math.sin(frame / 12) * 6;
  const pulseDot = 0.6 + 0.4 * Math.sin(frame / 6);

  // Animação de entrada do Badge Superior (y=175)
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  // Linha 1: "PERDE VENDA?" (entra no frame 8 ~ 0.27s, logo antes da palavra aos 0.318s)
  const l1Spring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 12, mass: 0.7},
  });
  const l1Scale = interpolate(l1Spring, [0, 1], [0.82, 1]);
  const l1Opacity = interpolate(l1Spring, [0, 1], [0, 1]);

  // Linha 2: "CLIENTE CHAMA DE MADRUGADA" (entra no frame 36 ~ 1.2s)
  const l2Spring = spring({
    frame: frame - 36,
    fps,
    config: {damping: 14, mass: 0.8},
  });
  const l2Slide = interpolate(l2Spring, [0, 1], [40, 0]);
  const l2Opacity = interpolate(l2Spring, [0, 1], [0, 1]);

  // Linha 3: "E NINGUÉM RESPONDE?" (entra no frame 84 ~ 2.8s)
  const l3Spring = spring({
    frame: frame - 84,
    fps,
    config: {damping: 11, mass: 0.7},
  });
  const l3Scale = interpolate(l3Spring, [0, 1], [0.8, 1]);
  const l3Opacity = interpolate(l3Spring, [0, 1], [0, 1]);

  // Selo Gancho Fixo: "LOJA ABERTA ATÉ DE MADRUGADA?" (entra no frame 110 ~ 3.7s)
  const ganchoSpring = spring({
    frame: frame - 110,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  // Transição de saída suave no final da cena (frames 148 a 162)
  const exitOpacity = interpolate(frame, [148, 162], [1, 0], {
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
          transform: `scale(${scaleBg}) translateY(${translateYBg}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: 1080,
            height: 1920,
            objectFit: 'cover',
          }}
        />
        {/* Camada de Proteção e Vinheta Escura */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 45%, rgba(17, 24, 39, 0.72) 0%, rgba(11, 13, 19, 0.94) 100%)',
          }}
        />
      </div>

      {/* Partículas e Grafismos Luminosos Sutis em Movimento Contínuo */}
      <div
        style={{
          position: 'absolute',
          top: 300 + floatY,
          left: 100,
          width: 380,
          height: 380,
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(167, 139, 250, 0.18) 0%, transparent 70%)',
          filter: 'blur(40px)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 700 - floatY,
          right: 80,
          width: 440,
          height: 440,
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(167, 139, 250, 0.14) 0%, transparent 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />

      {/* ZONA SEGURA: y=150 a y=1580, margens laterais x=60 a 1020 */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Badge Superior: Contexto */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '12px 28px',
            borderRadius: 999,
            background: 'rgba(11, 13, 19, 0.94)',
            border: `1.5px solid ${marcaCor}`,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              boxShadow: `0 0 12px rgba(239, 68, 68, ${pulseDot})`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              letterSpacing: '1px',
              color: '#FFFFFF',
              textTransform: 'uppercase',
            }}
          >
            ATENDIMENTO AO CLIENTE
          </span>
        </div>

        {/* Bloco Central: Texto Cinético Gigante */}
        <div
          style={{
            marginTop: 75,
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 28,
          }}
        >
          {/* Linha 1: "PERDE VENDA?" */}
          {frame >= 8 && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                transform: `scale(${l1Scale}) translateY(${floatY * 0.5}px)`,
                opacity: l1Opacity,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 70,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textShadow: '0 4px 16px rgba(0,0,0,0.9)',
                }}
              >
                PERDE
              </span>
              <div
                style={{
                  padding: '8px 24px',
                  borderRadius: 18,
                  backgroundColor: marcaCor,
                  boxShadow: `0 8px 30px rgba(167, 139, 250, 0.45)`,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 70,
                    fontWeight: 900,
                    color: '#121216',
                    letterSpacing: '-1px',
                  }}
                >
                  VENDA?
                </span>
              </div>
            </div>
          )}

          {/* Linha 2: "QUANDO O CLIENTE CHAMA DE MADRUGADA" */}
          {frame >= 36 && (
            <div
              style={{
                width: '100%',
                maxWidth: 920,
                padding: '22px 32px',
                borderRadius: 24,
                background: 'rgba(11, 13, 19, 0.94)',
                border: '1.5px solid rgba(255, 255, 255, 0.14)',
                boxShadow: '0 12px 36px rgba(0, 0, 0, 0.75)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 16,
                transform: `translateY(${l2Slide}px)`,
                opacity: l2Opacity,
              }}
            >
              <span style={{fontSize: 44}}>🌙</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 44,
                  fontWeight: 800,
                  color: '#F8FAFC',
                  textAlign: 'center',
                  lineHeight: 1.25,
                }}
              >
                QUANDO CHAMA DE MADRUGADA
              </span>
            </div>
          )}

          {/* Linha 3: "E NINGUÉM RESPONDE?" */}
          {frame >= 84 && (
            <div
              style={{
                padding: '20px 36px',
                borderRadius: 24,
                background: 'rgba(239, 68, 68, 0.16)',
                border: '2px solid rgba(239, 68, 68, 0.85)',
                boxShadow: '0 10px 32px rgba(239, 68, 68, 0.3)',
                transform: `scale(${l3Scale})`,
                opacity: l3Opacity,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 50,
                  fontWeight: 900,
                  color: '#FCA5A5',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                ⚠️ E NINGUÉM RESPONDE?
              </span>
            </div>
          )}

          {/* Gancho Fixo: "LOJA ABERTA ATÉ DE MADRUGADA?" */}
          {frame >= 110 && (
            <div
              style={{
                marginTop: 15,
                padding: '16px 32px',
                borderRadius: 999,
                background: 'rgba(15, 23, 42, 0.94)',
                border: `1.5px solid ${marcaCor}`,
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.8)',
                transform: `scale(${ganchoSpring})`,
                opacity: ganchoSpring,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 800,
                  color: marcaCor,
                }}
              >
                LOJA ABERTA ATÉ DE MADRUGADA?
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
