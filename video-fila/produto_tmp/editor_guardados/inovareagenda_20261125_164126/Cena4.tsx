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

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Câmera dinâmica contínua no fundo desfocado (evita cartão final estático)
  const scale = interpolate(frame, [0, 120], [1.08, 1.25], {
    extrapolateRight: 'clamp',
  });
  const panY = interpolate(frame, [0, 120], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada da cena (frame 0 a 8)
  const opacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Entradas sequenciais com mola (stagger) para dinamizar o cartão final
  const brandSpring = spring({
    frame,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 140},
  });

  const cardSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 130},
  });

  const btnSpring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 11, mass: 0.5, stiffness: 140},
  });

  const contactSpring = spring({
    frame: frame - 22,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 130},
  });

  const footerSpring = spring({
    frame: frame - 28,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 130},
  });

  // Pulso contínuo vivo do botão CTA (scale breath de 0.98 a 1.08)
  const btnBreath = 1.03 + Math.sin(frame * 0.22) * 0.05;
  const btnScaleTotal = frame >= 14 ? btnSpring * btnBreath : 0;
  const glowIntensity = 0.55 + Math.sin(frame * 0.22) * 0.35;
  const glowRadius = 35 + Math.sin(frame * 0.22) * 20;

  // Brilho intenso (sheen / shimmer sweep) correndo continuamente a cada 28 frames
  const shimmerPos = interpolate(frame % 28, [0, 28], [-120, 240]);

  // Micro-interação contínua da logo e cards
  const logoFloat = Math.sin(frame * 0.14) * 6;

  // Movimento de luz ambiente contínuo no fundo (garante variação >4% entre início e fim)
  const lightX = interpolate(frame, [0, 119], [25, 75]);
  const lightY = interpolate(frame, [0, 119], [30, 65]);

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0F172A',
        opacity,
      }}
    >
      {/* Background Image com Desfoque e Zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${scale}) translateY(${panY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(16px) brightness(0.70)',
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

      {/* Spot de Luz Dinâmica da Marca correndo suavemente pelo fundo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(circle at ${lightX}% ${lightY}%, rgba(245, 158, 11, 0.32) 0%, rgba(31, 41, 55, 0.88) 55%, rgba(15, 23, 42, 0.96) 100%)`,
          pointerEvents: 'none',
        }}
      />

      {/* Safe Zone Container — Distribuição vertical harmoniosa entre y=200 e y=1500 */}
      <div
        style={{
          position: 'absolute',
          top: 220,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Bloco da Marca e Produto com Entrada com Mola */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            transform: `scale(${brandSpring}) translateY(${logoFloat}px)`,
            opacity: interpolate(brandSpring, [0, 0.3, 1], [0, 1, 1]),
          }}
        >
          {/* Pílula do Produto */}
          <div
            style={{
              padding: '12px 32px',
              borderRadius: 999,
              backgroundColor: '#F59E0B',
              boxShadow: '0 8px 25px rgba(245, 158, 11, 0.55)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 900,
                color: '#121216',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              AGENDA IA
            </span>
          </div>

          {/* Nome da Marca Grande */}
          <h1
            style={{
              marginTop: 18,
              margin: '18px 0 0 0',
              fontFamily,
              fontSize: 68,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 2,
              textTransform: 'uppercase',
              textAlign: 'center',
              textShadow: '0 6px 20px rgba(0,0,0,0.8)',
            }}
          >
            INOVARE AGENDA
          </h1>
        </div>

        {/* Card de Proposta de Valor Baseado Estritamente nos Fatos */}
        <div
          style={{
            marginTop: 50,
            width: 860,
            padding: '38px 44px',
            borderRadius: 28,
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            border: '2px solid rgba(245, 158, 11, 0.5)',
            boxShadow: '0 20px 50px rgba(0,0,0,0.85)',
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
            transform: `scale(${cardSpring})`,
            opacity: interpolate(cardSpring, [0, 0.3, 1], [0, 1, 1]),
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 46,
              fontWeight: 900,
              color: '#F59E0B',
              lineHeight: 1.25,
              textAlign: 'center',
            }}
          >
            Agendamentos Automáticos 24h
          </div>

          <div
            style={{
              height: 2,
              backgroundColor: 'rgba(255,255,255,0.12)',
              margin: '4px 0',
            }}
          />

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span style={{color: '#10B981', fontSize: 36, fontWeight: 900}}>
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
              Direto no seu WhatsApp
            </span>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span style={{color: '#10B981', fontSize: 36, fontWeight: 900}}>
              ✓
            </span>
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 600,
                color: '#CBD5E1',
              }}
            >
              Sem conflito e sem duplo agendamento
            </span>
          </div>
        </div>

        {/* Botão de CTA com Escala Viva (Breath), Pulso e Shimmer Sweep Intenso */}
        {frame >= 14 && (
          <div
            style={{
              marginTop: 60,
              width: 860,
              transform: `scale(${btnScaleTotal})`,
              transformOrigin: 'center center',
              borderRadius: 28,
              padding: '26px 32px',
              background:
                'linear-gradient(135deg, #FBBF24 0%, #F59E0B 50%, #D97706 100%)',
              border: '2px solid #FEF3C7',
              boxShadow: `0 20px 50px rgba(245, 158, 11, ${glowIntensity}), 0 0 ${glowRadius}px rgba(245, 158, 11, 0.45), inset 0 2px 4px rgba(255,255,255,0.4)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Shimmer sweep intenso e contínuo */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: `${shimmerPos}%`,
                width: '60%',
                height: '100%',
                background:
                  'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.65) 50%, rgba(255,255,255,0) 100%)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontFamily,
                fontSize: 54,
                fontWeight: 900,
                color: '#121216',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              CHAME NO DIRECT
            </span>
          </div>
        )}

        {/* Perfil Oficial (@marca) Visível Com Entrada Suave */}
        {frame >= 22 && (
          <div
            style={{
              marginTop: 50,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 14,
              padding: '16px 44px',
              borderRadius: 999,
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: '2px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 10px 30px rgba(0,0,0,0.7)',
              transform: `scale(${contactSpring})`,
              opacity: interpolate(contactSpring, [0, 0.3, 1], [0, 1, 1]),
            }}
          >
            <span style={{color: '#F59E0B', fontSize: 38}}>✉️</span>
            <span
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1.5,
              }}
            >
              @inovareagenda
            </span>
          </div>
        )}

        {/* Tag de Confiança no Rodapé da Safe Zone */}
        {frame >= 28 && (
          <div
            style={{
              marginTop: 40,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 26px',
              borderRadius: 999,
              backgroundColor: 'rgba(15, 23, 42, 0.88)',
              border: '1px solid rgba(245, 158, 11, 0.35)',
              transform: `scale(${footerSpring})`,
              opacity: interpolate(footerSpring, [0, 0.3, 1], [0, 1, 1]),
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 700,
                color: '#E2E8F0',
                letterSpacing: 1,
              }}
            >
              ⚡ Atendimento 24h • Direto no WhatsApp
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
