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
  arroba: string;
  convite: string;
}

export const Cena4Cartao: React.FC<Props> = ({
  fontFamily,
  marcaCor,
  apoioCor,
  arroba,
  convite,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo: zoom de 1.05 para 1.18
  const scaleBg = interpolate(frame, [0, 118], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });

  // Micro-dinâmica senoidal de iluminação
  const auraRot = frame * 0.8;
  const auraScale = 1 + 0.05 * Math.sin(frame / 8);

  // Pulso contínuo do CTA: scale 1.00 a 1.08 em ciclo exato de 1.2s (36 frames a 30fps)
  const buttonScale = 1.04 + 0.04 * Math.sin((frame * 2 * Math.PI) / 36);

  // Efeito Shimmer (brilho) passando sobre o botão CTA continuamente
  const shimmerPos = interpolate(frame % 40, [0, 30], [-300, 900], {
    extrapolateRight: 'clamp',
  });

  // Entrada dos elementos
  const entranceSpring = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.8},
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
      }}
    >
      {/* Imagem de Fundo com Zoom Contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${scaleBg})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: 1080,
            height: 1920,
            objectFit: 'cover',
          }}
        />
        {/* Véu Escuro Protetor com Alta Opacidade (94%) */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(17, 24, 39, 0.88) 0%, rgba(11, 13, 19, 0.97) 100%)',
          }}
        />
      </div>

      {/* Aura Luminosa da Marca no Fundo */}
      <div
        style={{
          position: 'absolute',
          top: 340,
          left: '50%',
          width: 600,
          height: 600,
          marginLeft: -300,
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(167, 139, 250, 0.22) 0%, transparent 70%)',
          filter: 'blur(50px)',
          transform: `scale(${auraScale}) rotate(${auraRot}deg)`,
          pointerEvents: 'none',
        }}
      />

      {/* CONTEÚDO PRINCIPAL (Safe Zone: y=150 a y=1580, x=60 a 1020) */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 24,
          pointerEvents: 'none',
          transform: `scale(${entranceSpring})`,
          opacity: entranceSpring,
        }}
      >
        {/* Badge do Produto */}
        <div
          style={{
            padding: '10px 28px',
            borderRadius: 999,
            backgroundColor: 'rgba(11, 13, 19, 0.94)',
            border: `1.5px solid ${marcaCor}`,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
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
            ATENDIMENTO AUTOMATIZADO
          </span>
        </div>

        {/* Logo / Marca */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
            marginTop: 10,
          }}
        >
          <div
            style={{
              width: 100,
              height: 100,
              borderRadius: 28,
              backgroundColor: marcaCor,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: `0 0 35px rgba(167, 139, 250, 0.6)`,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: '#121216',
              }}
            >
              IA
            </span>
          </div>

          <span
            style={{
              fontFamily,
              fontSize: 72,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-1px',
              textShadow: '0 4px 24px rgba(167, 139, 250, 0.5)',
            }}
          >
            Vitrine IA
          </span>
        </div>

        {/* Card de Fatos e Proposta de Valor */}
        <div
          style={{
            width: '100%',
            maxWidth: 900,
            padding: '28px 32px',
            borderRadius: 28,
            backgroundColor: 'rgba(11, 13, 19, 0.94)',
            border: '1.5px solid rgba(255, 255, 255, 0.14)',
            boxShadow: '0 16px 40px rgba(0, 0, 0, 0.8)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            textAlign: 'center',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 42,
              fontWeight: 800,
              color: '#FFFFFF',
              lineHeight: 1.25,
            }}
          >
            Bot com todo o conhecimento da sua loja.
          </span>
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: marcaCor,
            }}
          >
            Atende, recomenda e vende.
          </span>

          {/* Selos de Benefício baseados exclusivamente nos fatos */}
          <div
            style={{
              display: 'flex',
              gap: 16,
              marginTop: 10,
              flexWrap: 'wrap',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                padding: '8px 18px',
                borderRadius: 14,
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.14)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#F1F5F9',
                }}
              >
                ✓ Conhece os produtos
              </span>
            </div>
            <div
              style={{
                padding: '8px 18px',
                borderRadius: 14,
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.14)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#F1F5F9',
                }}
              >
                ✓ Atendimento imediato
              </span>
            </div>
          </div>
        </div>

        {/* BOTÃO DE CTA PULSANTE CONTÍNUO (Com Shimmer) */}
        <div
          style={{
            marginTop: 20,
            transform: `scale(${buttonScale})`,
            transformOrigin: 'center center',
          }}
        >
          <div
            style={{
              position: 'relative',
              width: 840,
              height: 120,
              borderRadius: 36,
              backgroundColor: marcaCor,
              boxShadow: `0 12px 40px rgba(167, 139, 250, 0.6), 0 0 20px rgba(167, 139, 250, 0.4)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'hidden',
            }}
          >
            {/* Shimmer Light Beam */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 180,
                transform: `translateX(${shimmerPos}px) skewX(-25deg)`,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)',
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontFamily,
                fontSize: 50,
                fontWeight: 900,
                color: '#121216',
                letterSpacing: '1px',
                textTransform: 'uppercase',
              }}
            >
              {convite.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Perfil Oficial Arroba */}
        <div
          style={{
            marginTop: 10,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 32px',
            borderRadius: 999,
            backgroundColor: 'rgba(11, 13, 19, 0.94)',
            border: `1.5px solid ${marcaCor}`,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 42,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.5px',
            }}
          >
            {arroba}
          </span>
        </div>

        {/* Sub-CTA Discreto */}
        <span
          style={{
            fontFamily,
            fontSize: 32,
            fontWeight: 600,
            color: '#94A3B8',
          }}
        >
          Envie uma mensagem e comece hoje
        </span>
      </div>
    </div>
  );
};
