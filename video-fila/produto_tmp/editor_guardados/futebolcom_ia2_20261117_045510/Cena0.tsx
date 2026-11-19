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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera na foto (push-in)
  const bgScale = interpolate(frame, [0, 135], [1.0, 1.09], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 135], [0, -18], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge superior (0.1s)
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Fase 1: "SEU CLIENTE AINDA ESPERA" (entra aos ~0.3s -> frame 9)
  const f1Spring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Fase 2: "FOTO DE CARDÁPIO?" (entra aos ~1.5s -> frame 45)
  const f2Spring = spring({
    frame: frame - 45,
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // Fase 3: Gancho "CHEGA DE PDF PESADO" (entra aos ~2.6s -> frame 78)
  const f3Spring = spring({
    frame: frame - 78,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Micro-flutuação para manter a cena sempre viva
  const floatY = Math.sin(frame / 12) * 5;

  return (
    <AbsoluteFill style={{backgroundColor: '#110206', overflow: 'hidden'}}>
      {/* Imagem de Fundo com zoom e pan constante */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
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
        {/* Overlay em degradê para garantir contraste do texto superior e karaokê inferior */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(17, 2, 6, 0.88) 0%, rgba(17, 2, 6, 0.45) 30%, rgba(17, 2, 6, 0.25) 55%, rgba(17, 2, 6, 0.90) 100%)',
          }}
        />
      </div>

      {/* Conteúdo na Safe Zone (y: 180 a 540) */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* Badge / Rótulo da Linha */}
        {frame >= 4 && (
          <div
            style={{
              transform: `scale(${badgeSpring})`,
              opacity: badgeSpring,
              backgroundColor: '#E11D48',
              borderRadius: 14,
              padding: '10px 24px',
              border: '2px solid rgba(250, 204, 21, 0.4)',
              boxShadow: '0 8px 24px rgba(225, 29, 72, 0.5)',
              marginBottom: 20,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 2,
              }}
            >
              CARDÁPIO DIGITAL
            </span>
          </div>
        )}

        {/* Bloco 1: Pergunta inicial */}
        {frame >= 9 && (
          <div
            style={{
              transform: `scale(${f1Spring})`,
              opacity: f1Spring,
              textAlign: 'center',
              marginBottom: 16,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 52,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                lineHeight: 1.15,
                textShadow: '0 4px 16px rgba(0, 0, 0, 0.95)',
              }}
            >
              SEU CLIENTE AINDA ESPERA
            </span>
          </div>
        )}

        {/* Bloco 2: Destaque na dor */}
        {frame >= 45 && (
          <div
            style={{
              transform: `scale(${f2Spring})`,
              opacity: f2Spring,
              backgroundColor: 'rgba(49, 6, 15, 0.92)',
              border: '3px solid #E11D48',
              borderRadius: 22,
              padding: '16px 36px',
              boxShadow: '0 12px 36px rgba(225, 29, 72, 0.65)',
              textAlign: 'center',
              marginBottom: 18,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 60,
                fontWeight: 900,
                color: '#FACC15',
                textTransform: 'uppercase',
                letterSpacing: 1,
                lineHeight: 1.1,
                textShadow: '0 4px 18px rgba(0, 0, 0, 0.9)',
              }}
            >
              FOTO DE CARDÁPIO?
            </span>
          </div>
        )}

        {/* Bloco 3: Gancho da Solução */}
        {frame >= 78 && (
          <div
            style={{
              transform: `scale(${f3Spring})`,
              opacity: f3Spring,
              backgroundColor: 'rgba(15, 23, 42, 0.95)',
              border: '2px solid #FACC15',
              borderRadius: 16,
              padding: '12px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              boxShadow: '0 8px 28px rgba(0, 0, 0, 0.8)',
            }}
          >
            <span style={{fontSize: 34}}>📄🚫</span>
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              CHEGA DE PDF PESADO
            </span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
