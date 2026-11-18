import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena4Props {
  fontFamily: string;
}

export const Cena4: React.FC<Cena4Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração: ~119 frames
  const zoom = interpolate(frame, [0, 119], [1.02, 1.10], {
    extrapolateRight: 'clamp',
  });

  // Entrada em cascata rápida e viva
  const sprMarca = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  const sprCard = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const sprBtn = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  const sprArroba = spring({
    frame: frame - 14,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Pulso contínuo e vivo do botão até o último frame (exigência do manual)
  const btnPulse = 1 + 0.045 * Math.sin((frame / 16) * Math.PI);

  // Efeito shimmer contínuo sobre o botão
  const shimmerBtn = (frame * 12) % 1100;

  // Flutuação sutil da marca
  const floatBrand = Math.sin((frame / 20) * Math.PI) * 4;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        background: '#111827',
      }}
    >
      {/* Imagem de Fundo com blur e zoom */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${zoom})`,
          transformOrigin: 'center center',
          filter: 'blur(14px)',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu Escuro da Marca */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 35%, rgba(17, 24, 39, 0.82) 0%, rgba(17, 24, 39, 0.96) 100%)',
        }}
      />

      {/* Grafismo com brilho verde no centro */}
      <div
        style={{
          position: 'absolute',
          top: 300,
          left: 240,
          width: 600,
          height: 600,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(34, 197, 94, 0.12) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo Centralizado dentro da Safe Zone (y=150 a y=1580) */}
      <div
        style={{
          position: 'absolute',
          top: 220,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: 36,
          zIndex: 30,
        }}
      >
        {/* Bloco 1: Identidade da Marca (y ~ 240 a 440) */}
        <div
          style={{
            opacity: sprMarca,
            transform: `translateY(${
              (1 - sprMarca) * 25 + floatBrand
            }px) scale(${0.9 + sprMarca * 0.1})`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
          }}
        >
          {/* Ícone Estilizado da Marca */}
          <div
            style={{
              width: 86,
              height: 86,
              borderRadius: 24,
              background: 'linear-gradient(135deg, #22C55E 0%, #15803D 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 30px rgba(34, 197, 94, 0.5)',
            }}
          >
            <span style={{fontSize: 46}}>⚡</span>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 62,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
              textShadow: '0 4px 20px rgba(0, 0, 0, 0.9)',
            }}
          >
            DISPARO EM MASSA IA
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 36,
              fontWeight: 600,
              color: '#CBD5E1',
              maxWidth: 860,
              lineHeight: 1.3,
            }}
          >
            Disparo em massa inteligente no WhatsApp com rotação de instâncias
          </div>
        </div>

        {/* Bloco 2: Benefícios Comprovados (y ~ 500 a 860) */}
        {frame >= 5 && (
          <div
            style={{
              opacity: sprCard,
              transform: `scale(${0.92 + sprCard * 0.08}) translateY(${
                (1 - sprCard) * 20
              }px)`,
              width: '100%',
              maxWidth: 900,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '2px solid rgba(255, 255, 255, 0.12)',
              borderRadius: 32,
              padding: '30px 36px',
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.6)',
              display: 'flex',
              flexDirection: 'column',
              gap: 22,
              textAlign: 'left',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 14,
                  background: 'rgba(34, 197, 94, 0.2)',
                  border: '2px solid #22C55E',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#22C55E',
                  fontSize: 26,
                  fontWeight: 900,
                }}
              >
                ✓
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 700,
                  color: '#F8FAFC',
                }}
              >
                Envio automático para milhares de contatos
              </span>
            </div>

            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 14,
                  background: 'rgba(34, 197, 94, 0.2)',
                  border: '2px solid #22C55E',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#22C55E',
                  fontSize: 26,
                  fontWeight: 900,
                }}
              >
                ✓
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 700,
                  color: '#F8FAFC',
                }}
              >
                Rotação de instâncias e números
              </span>
            </div>

            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <span
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 14,
                  background: 'rgba(34, 197, 94, 0.2)',
                  border: '2px solid #22C55E',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#22C55E',
                  fontSize: 26,
                  fontWeight: 900,
                }}
              >
                ✓
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 700,
                  color: '#F8FAFC',
                }}
              >
                Mensagens personalizadas no WhatsApp
              </span>
            </div>
          </div>
        )}

        {/* Bloco 3: Botão de Ação CTA (y ~ 940 a 1180) */}
        {frame >= 8 && (
          <div
            style={{
              opacity: sprBtn,
              transform: `scale(${
                (0.9 + sprBtn * 0.1) * btnPulse
              }) translateY(${(1 - sprBtn) * 20}px)`,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 16,
              marginTop: 10,
            }}
          >
            {/* Botão Pulsante com Shimmer */}
            <div
              style={{
                position: 'relative',
                width: 840,
                height: 120,
                borderRadius: 60,
                background: '#22C55E',
                boxShadow:
                  '0 14px 45px rgba(34, 197, 94, 0.5), 0 0 25px rgba(34, 197, 94, 0.35)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 20,
                overflow: 'hidden',
                cursor: 'pointer',
              }}
            >
              {/* Shimmer passando no botão */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  left: -200 + shimmerBtn,
                  width: 140,
                  background:
                    'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.35), transparent)',
                  transform: 'skewX(-25deg)',
                  pointerEvents: 'none',
                }}
              />

              <span
                style={{
                  fontFamily,
                  fontSize: 50,
                  fontWeight: 900,
                  color: '#111827',
                  letterSpacing: 2,
                  textTransform: 'uppercase',
                }}
              >
                CHAME NO DIRECT
              </span>
              <span
                style={{
                  fontSize: 46,
                  color: '#111827',
                  fontWeight: 900,
                }}
              >
                ➔
              </span>
            </div>

            <div
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 600,
                color: '#94A3B8',
              }}
            >
              Tire suas dúvidas e reative clientes
            </div>
          </div>
        )}

        {/* Bloco 4: Arroba Oficial (y ~ 1380) */}
        {frame >= 12 && (
          <div
            style={{
              opacity: sprArroba,
              transform: `scale(${0.9 + sprArroba * 0.1}) translateY(${
                (1 - sprArroba) * 15
              }px)`,
              marginTop: 12,
              padding: '12px 34px',
              borderRadius: 30,
              background: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <span style={{fontSize: 32}}>📸</span>
            <span
              style={{
                fontFamily,
                fontSize: 40,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 1,
              }}
            >
              @disparoemmassa.ia
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
