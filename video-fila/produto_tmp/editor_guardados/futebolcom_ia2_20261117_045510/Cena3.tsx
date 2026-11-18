import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Push-in suave no vídeo do apresentador (1.00 -> 1.05)
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge do topo (y ~ 170)
  const rotuloSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Card 1: "PEDIDO CHEGA PRONTO NO WHATSAPP" (~frame 10 a 115)
  const card1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Card 2: "DELIVERY MUITO MAIS ÁGIL" (frame 115 em diante)
  const card2Spring = spring({
    frame: frame - 115,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Movimento constante para não ficar estático
  const microFloat = Math.sin(frame / 14) * 4;

  return (
    <AbsoluteFill style={{backgroundColor: '#000000', overflow: 'hidden'}}>
      {/* Vídeo do dono em tela cheia com leve push-in */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: 'center 40%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Vinheta superior suave para legibilidade dos cards sem cobrir o rosto */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(180deg, rgba(15, 2, 5, 0.85) 0%, rgba(15, 2, 5, 0.45) 60%, rgba(15, 2, 5, 0) 100%)',
          }}
        />
        {/* Vinheta inferior sutil para a legenda */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 420,
            background:
              'linear-gradient(0deg, rgba(0, 0, 0, 0.75) 0%, rgba(0, 0, 0, 0) 100%)',
          }}
        />
      </div>

      {/* Faixa superior (Safe Zone: y=160 a 420, estritamente acima da cabeça) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `translateY(${microFloat}px)`,
        }}
      >
        {/* Rótulo da cena: O RESULTADO */}
        {frame >= 5 && (
          <div
            style={{
              transform: `scale(${rotuloSpring})`,
              opacity: rotuloSpring,
              backgroundColor: '#16A34A',
              borderRadius: 12,
              padding: '8px 22px',
              border: '2px solid rgba(255, 255, 255, 0.3)',
              boxShadow: '0 6px 20px rgba(22, 163, 74, 0.6)',
              marginBottom: 14,
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
              O RESULTADO
            </span>
          </div>
        )}

        {/* Card Dinâmico 1 (Frame 10 a 115): Pedido finalizado pronto no WhatsApp */}
        {frame >= 10 && frame < 115 && (
          <div
            style={{
              transform: `scale(${card1Spring})`,
              opacity: card1Spring,
              backgroundColor: 'rgba(15, 30, 20, 0.94)',
              border: '2px solid #22C55E',
              borderRadius: 18,
              padding: '14px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.85)',
            }}
          >
            <span style={{fontSize: 38}}>📲✨</span>
            <div style={{display: 'flex', flexDirection: 'column'}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.15,
                }}
              >
                PEDIDO PRONTO NO WHATSAPP
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#86EFAC',
                  textTransform: 'uppercase',
                }}
              >
                Chega formatado direto na sua tela
              </span>
            </div>
          </div>
        )}

        {/* Card Dinâmico 2 (Frame 115 em diante): Delivery muito mais ágil */}
        {frame >= 115 && (
          <div
            style={{
              transform: `scale(${card2Spring})`,
              opacity: card2Spring,
              backgroundColor: 'rgba(25, 10, 15, 0.94)',
              border: '2px solid #E11D48',
              borderRadius: 18,
              padding: '14px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              boxShadow: '0 10px 30px rgba(225, 29, 72, 0.5)',
            }}
          >
            <span style={{fontSize: 38}}>⚡🚀</span>
            <div style={{display: 'flex', flexDirection: 'column'}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.15,
                }}
              >
                DELIVERY MUITO MAIS ÁGIL
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#FACC15',
                  textTransform: 'uppercase',
                }}
              >
                Mais velocidade e eficiência no dia a dia
              </span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
