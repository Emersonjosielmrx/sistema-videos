import React from 'react';
import {
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

export const Cena0Pergunta: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo: push-in suave + pan vertical (Ken Burns)
  const scale = interpolate(frame, [0, 140], [1.02, 1.10], {
    extrapolateRight: 'clamp',
  });
  const translateY = interpolate(frame, [0, 140], [0, -18], {
    extrapolateRight: 'clamp',
  });

  // Microdinâmica constante
  const floatY = Math.sin(frame / 12) * 5;

  // Entrada do Badge superior (frame 4)
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Entrada do Bloco Bicolor (frame 9 - ~0.3s)
  const blockSpring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 11, stiffness: 120},
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
      {/* Vídeo dinâmico de fundo (restaurante movimentado no almoço com luz natural) com Ken Burns */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${scale}) translateY(${translateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('veo_abertura.mp4')}
          muted
          style={{
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
            filter: 'brightness(1.08) contrast(1.05) saturate(1.12)',
          }}
        />
      </div>

      {/* Véu protetor sutil: protege o badge e a legenda, mantendo a luz do dia do almoço clara e com energia */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(11, 13, 19, 0.72) 0%, rgba(11, 13, 19, 0.18) 22%, rgba(11, 13, 19, 0.15) 60%, rgba(11, 13, 19, 0.85) 100%)',
        }}
      />

      {/* Conteúdo na Safe Zone (y=150 a y=1580, x=60 a x=1020) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 200,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 30,
        }}
      >
        {/* Badge da cena: Pergunta de restaurante */}
        {badgeSpring > 0 && (
          <div
            style={{
              transform: `scale(${badgeSpring})`,
              opacity: badgeSpring,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 28px',
              borderRadius: 999,
              backgroundColor: '#E11D48',
              boxShadow: '0 8px 24px rgba(225, 29, 72, 0.5)',
              border: '1.5px solid rgba(255, 255, 255, 0.3)',
              marginBottom: 36,
            }}
          >
            <svg
              width="26"
              height="26"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              Dúvida de Restaurante
            </span>
          </div>
        )}

        {/* Faixa central bicolor de gancho e pergunta (apenas uma interrogação no final da oração) */}
        {blockSpring > 0 && (
          <div
            style={{
              transform: `scale(${blockSpring}) translateY(${floatY}px)`,
              opacity: blockSpring,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
              maxWidth: 960,
              marginTop: 30,
            }}
          >
            {/* Bloco Amarelo com texto preto pesado */}
            <div
              style={{
                backgroundColor: '#FACC15',
                padding: '24px 44px',
                borderRadius: '24px 24px 6px 6px',
                width: '100%',
                boxSizing: 'border-box',
                textAlign: 'center',
                boxShadow: '0 16px 36px rgba(0, 0, 0, 0.6)',
                border: '3px solid #000000',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 54,
                  fontWeight: 900,
                  color: '#000000',
                  lineHeight: 1.15,
                  letterSpacing: -0.5,
                  display: 'block',
                  textTransform: 'uppercase',
                }}
              >
                FUNCIONA NO ALMOÇO
              </span>
            </div>

            {/* Bloco Preto com texto amarelo em contraste invertido */}
            <div
              style={{
                backgroundColor: '#0B0D13',
                padding: '22px 36px',
                borderRadius: '6px 6px 24px 24px',
                width: '95%',
                boxSizing: 'border-box',
                textAlign: 'center',
                boxShadow: '0 20px 45px rgba(0, 0, 0, 0.8)',
                border: '3px solid #FACC15',
                marginTop: -4,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 48,
                  fontWeight: 900,
                  color: '#FACC15',
                  lineHeight: 1.15,
                  letterSpacing: 0,
                  display: 'block',
                  textTransform: 'uppercase',
                }}
              >
                DO RESTAURANTE LOTADO?
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
