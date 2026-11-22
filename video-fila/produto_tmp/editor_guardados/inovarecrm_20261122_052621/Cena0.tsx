import React from 'react';
import {
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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo (push-in suave de 1.05 a 1.15)
  const scale = interpolate(frame, [0, 144], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });
  const translateY = interpolate(frame, [0, 144], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Entrada do selo de gancho no topo
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Card 1: Cansado de adaptar (0.3s -> frame 9)
  const card1Spring = spring({
    frame: Math.max(0, frame - 9),
    fps,
    config: {damping: 15, stiffness: 110},
  });

  // Entrada do Card 2: o seu trabalho (1.5s -> frame 45)
  const card2Spring = spring({
    frame: Math.max(0, frame - 45),
    fps,
    config: {damping: 15, stiffness: 110},
  });

  // Entrada do Clímax: A FERRAMENTAS TRAVADAS? (2.6s -> frame 78)
  const lockSpring = spring({
    frame: Math.max(0, frame - 78),
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Pulso de alerta contínuo
  const pulse = Math.sin((frame / 22) * Math.PI * 2) * 0.04 + 1.0;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#0F172A',
        fontFamily,
      }}
    >
      {/* Fotografia Real Clara e Vibrante com Zoom Dinâmico */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 1080,
          height: 1920,
          transform: `scale(${scale}) translateY(${translateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Camada de Proteção Seletiva: Gradiente moderado APENAS sob os textos no topo e na base (Regra 19) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 820,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.94) 0%, rgba(15, 23, 42, 0.82) 65%, rgba(15, 23, 42, 0) 100%)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 520,
          background:
            'linear-gradient(0deg, rgba(15, 23, 42, 0.92) 0%, rgba(15, 23, 42, 0.70) 60%, rgba(15, 23, 42, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo na Safe Zone (y=150 a y=1580, x=60 a 1020) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          padding: '0 60px',
        }}
      >
        {/* Badge do Gancho no Topo (y=175) */}
        <div
          style={{
            position: 'absolute',
            top: 175,
            left: 60,
            transform: `scale(${badgeSpring})`,
            transformOrigin: 'left center',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            background: 'rgba(15, 23, 42, 0.95)',
            border: '2px solid #0284C7',
            borderRadius: 30,
            padding: '10px 24px',
            boxShadow: '0 8px 24px rgba(2, 132, 199, 0.35)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              transform: `scale(${pulse})`,
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#38BDF8',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            SEU CRM PARECE ENGESSADO?
          </span>
        </div>

        {/* Bloco Cinético Central (y=280 a 640) */}
        <div
          style={{
            position: 'absolute',
            top: 275,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
          }}
        >
          {/* Linha 1: Cansado de adaptar */}
          <div
            style={{
              transform: `translateY(${interpolate(card1Spring, [0, 1], [35, 0])}px) scale(${interpolate(card1Spring, [0, 1], [0.94, 1])})`,
              opacity: card1Spring,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.94)',
                border: '2px solid rgba(255, 255, 255, 0.16)',
                borderRadius: 22,
                padding: '18px 28px',
                boxShadow: '0 12px 30px rgba(0, 0, 0, 0.65)',
              }}
            >
              <span
                style={{
                  fontSize: 46,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.15,
                  textTransform: 'uppercase',
                  display: 'block',
                }}
              >
                Cansado de adaptar
              </span>
            </div>
          </div>

          {/* Linha 2: o seu trabalho... */}
          <div
            style={{
              transform: `translateY(${interpolate(card2Spring, [0, 1], [35, 0])}px) scale(${interpolate(card2Spring, [0, 1], [0.94, 1])})`,
              opacity: card2Spring,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.94)',
                border: '2px solid rgba(255, 255, 255, 0.16)',
                borderRadius: 22,
                padding: '18px 28px',
                boxShadow: '0 12px 30px rgba(0, 0, 0, 0.65)',
              }}
            >
              <span
                style={{
                  fontSize: 44,
                  fontWeight: 800,
                  color: '#94A3B8',
                  lineHeight: 1.15,
                  textTransform: 'uppercase',
                  display: 'block',
                }}
              >
                o seu trabalho...
              </span>
            </div>
          </div>

          {/* Linha 3: Clímax - A FERRAMENTAS TRAVADAS? */}
          <div
            style={{
              transform: `translateY(${interpolate(lockSpring, [0, 1], [40, 0])}px) scale(${interpolate(lockSpring, [0, 1], [0.88, 1]) * (frame >= 78 ? pulse : 1)})`,
              opacity: lockSpring,
            }}
          >
            <div
              style={{
                background:
                  'linear-gradient(135deg, rgba(239, 68, 68, 0.28) 0%, rgba(15, 23, 42, 0.96) 100%)',
                border: '2.5px solid #EF4444',
                borderRadius: 22,
                padding: '22px 28px',
                boxShadow: '0 16px 40px rgba(239, 68, 68, 0.4)',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
              }}
            >
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 14,
                  background: '#EF4444',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                  flexShrink: 0,
                  boxShadow: '0 6px 16px rgba(239, 68, 68, 0.6)',
                }}
              >
                🔒
              </div>
              <span
                style={{
                  fontSize: 46,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.15,
                  textTransform: 'uppercase',
                }}
              >
                A FERRAMENTAS TRAVADAS?
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
