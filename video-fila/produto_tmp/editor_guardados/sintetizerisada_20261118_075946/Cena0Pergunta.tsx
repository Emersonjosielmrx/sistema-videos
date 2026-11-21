import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena0Pergunta: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera no estúdio (0.0s até o final)
  const bgScale = interpolate(frame, [0, 163], [1.04, 1.14], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 163], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge "DÚVIDA FREQUENTE" nos primeiros frames
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Título da pergunta com badge laranja visível e contrastante desde o início
  const titleSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Card focal de dor entra aos 0.2s (frame 6)
  const cardSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Micro-animação contínua de pulso/flutuação
  const cardFloatY = Math.sin(frame / 9) * 6;
  const pulseScale = 1 + Math.sin(frame / 8) * 0.02;

  // Transição fluida do Card 1: slide-out para cima e fade out entre frames 104 e 118
  const card1SlideY = interpolate(frame, [104, 118], [0, -75], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const card1Opacity = interpolate(frame, [104, 118], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Entrada do Card 2 com escala suave e overshoot a partir de frame 112
  const card2Spring = spring({
    frame: frame - 112,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Transição de saída suave no final da cena
  const exitOpacity = interpolate(frame, [145, 163], [1, 0], {
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
        fontFamily,
        opacity: exitOpacity,
      }}
    >
      {/* Fundo com vídeo real do estúdio (consultório/clínica com iluminação moderna e maca de atendimento) */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale * 1.6}) translate(-140px, ${bgTranslateY}px)`,
          transformOrigin: '75% 40%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Overlay escuro elegante com tom da marca para foco nos cards da pergunta */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 38%, rgba(31, 41, 55, 0.78) 0%, rgba(15, 23, 42, 0.94) 85%)',
          }}
        />
      </div>

      {/* Grid sutil de tecnologia com pulso no gradiente para evitar sensação de chapado */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(255, 169, 77, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 169, 77, 0.05) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
          opacity: 0.5 + Math.sin(frame / 10) * 0.15,
          pointerEvents: 'none',
        }}
      />

      {/* Brilho radial pulsante de fundo */}
      <div
        style={{
          position: 'absolute',
          top: 680,
          left: '50%',
          width: 500,
          height: 500,
          transform: 'translateX(-50%)',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255,169,77,0.14) 0%, transparent 70%)',
          opacity: 0.8 + Math.sin(frame / 7) * 0.2,
          pointerEvents: 'none',
        }}
      />

      {/* Badge Superior (y=206 a 266) */}
      <div
        style={{
          position: 'absolute',
          top: 206,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring}) translateY(${badgeSpring < 1 ? (1 - badgeSpring) * 20 : 0}px)`,
          opacity: badgeSpring,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 30,
            background: 'rgba(31, 41, 55, 0.92)',
            border: '1.5px solid rgba(255, 169, 77, 0.7)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.45)',
          }}
        >
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#FFA94D',
              boxShadow: '0 0 10px #FFA94D',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: '#FFA94D',
            }}
          >
            Dúvida Frequente
          </span>
        </div>
      </div>

      {/* Título Cinético no Topo (y=290 a 580) - A pergunta com destaque laranja já visível desde o frame inicial */}
      <div
        style={{
          position: 'absolute',
          top: 290,
          left: 60,
          right: 60,
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
          transform: `scale(${Math.max(0, titleSpring)})`,
          opacity: Math.max(0, titleSpring),
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: 44,
            fontWeight: 900,
            lineHeight: 1.3,
            color: '#FFFFFF',
            textShadow: '0 4px 18px rgba(0,0,0,0.85)',
            maxWidth: 960,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          }}
        >
          {/* Linha 1 */}
          <div style={{display: 'flex', alignItems: 'center', gap: 12, justifyContent: 'center', whiteSpace: 'nowrap'}}>
            <span>Preciso parar</span>
            <span
              style={{
                display: 'inline-block',
                background: '#FFA94D',
                color: '#1F2937',
                padding: '3px 16px',
                borderRadius: 12,
                boxShadow: '0 4px 20px rgba(255,169,77,0.45)',
                fontWeight: 900,
              }}
            >
              meus atendimentos
            </span>
          </div>

          {/* Linha 2 */}
          <div style={{display: 'flex', alignItems: 'center', gap: 12, justifyContent: 'center', whiteSpace: 'nowrap'}}>
            <span>para aprovar</span>
            <span
              style={{
                display: 'inline-block',
                color: '#FFA94D',
                textShadow: '0 2px 10px rgba(0,0,0,0.9)',
              }}
            >
              cada horário marcado?
            </span>
          </div>
        </h1>
      </div>

      {/* Elemento Focal Central com Transição Fluida entre Cards (y=660 a 980) */}
      <div
        style={{
          position: 'absolute',
          top: 660,
          left: 70,
          right: 70,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: 280,
        }}
      >
        {frame < 122 && (
          <div
            style={{
              position: 'absolute',
              width: '100%',
              maxWidth: 920,
              padding: '30px 36px',
              borderRadius: 28,
              background: 'rgba(31, 41, 55, 0.94)',
              border: '2px solid rgba(239, 68, 68, 0.55)',
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.55)',
              transform: `scale(${cardSpring * pulseScale}) translateY(${cardFloatY + card1SlideY}px)`,
              opacity: Math.max(0, cardSpring) * card1Opacity,
              display: 'flex',
              flexDirection: 'column',
              gap: 18,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <span style={{fontSize: 34}}>⚠️</span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#F87171',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}
                >
                  Interrupção Constante
                </span>
              </div>
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#9CA3AF',
                }}
              >
                Rotina Manual
              </span>
            </div>

            <div
              style={{
                padding: '18px 22px',
                borderRadius: 18,
                background: 'rgba(17, 24, 39, 0.88)',
                borderLeft: '5px solid #F87171',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
              }}
            >
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#FFFFFF',
                }}
              >
                💬 Mensagem: &ldquo;Tem horário hoje às 15h?&rdquo;
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#FFA94D',
                }}
              >
                ⏳ Atendimento pausado para conferir agenda...
              </div>
            </div>
          </div>
        )}

        {frame >= 106 && (
          <div
            style={{
              position: 'absolute',
              padding: '28px 48px',
              borderRadius: 24,
              background: '#FFA94D',
              boxShadow: '0 16px 50px rgba(255, 169, 77, 0.55)',
              transform: `scale(${card2Spring}) translateY(${cardFloatY}px)`,
              opacity: Math.max(0, card2Spring),
              textAlign: 'center',
            }}
          >
            <div
              style={{
                fontSize: 42,
                fontWeight: 900,
                color: '#111827',
                letterSpacing: '0.02em',
              }}
            >
              ⚡ A IA FAZ TUDO SOZINHA?
            </div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: '#111827',
                marginTop: 8,
              }}
            >
              Veja o que o dono do estúdio explica a seguir 👇
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
