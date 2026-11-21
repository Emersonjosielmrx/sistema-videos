import React from 'react';
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Img,
  staticFile,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const totalFrames = 119;

  // Câmera dinâmica contínua: zoom contínuo de 1.06 a 1.18
  const bgScale = interpolate(frame, [0, totalFrames], [1.06, 1.18], {
    extrapolateRight: 'clamp',
  });

  // Entrada em spring da marca
  const brandSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Card de Proposta
  const cardSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Entrada do Botão CTA
  const btnSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, stiffness: 100},
  });

  // Pulso contínuo do botão CTA (ciclo exato de 1.2s = 36 frames, scale de 1.00 a 1.08)
  const pulseCycle = (frame % 36) / 36;
  const pulse = 1.0 + 0.08 * Math.sin(pulseCycle * Math.PI * 2);

  // Shimmer reflexivo contínuo passando pelo botão
  const shimmerX = interpolate(frame % 42, [0, 42], [-120, 360], {
    extrapolateRight: 'clamp',
  });

  // Flutuação sutil da marca
  const floatY = Math.sin(frame * 0.14) * 5;

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
      {/* Imagem de Fundo Desfocada com Zoom Contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
          filter: 'blur(10px)',
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

      {/* Véu com Gradiente Nobre e Iluminação Âmbar */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 38%, rgba(31, 41, 55, 0.78) 0%, rgba(11, 13, 19, 0.92) 65%, #07090E 100%)',
        }}
      />

      {/* Conteúdo Seguro (y: 200 a 1480) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 210,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 32,
        }}
      >
        {/* Marca & Logo */}
        {brandSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${brandSpring}) translateY(${floatY}px)`,
              opacity: brandSpring,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <div
              style={{
                width: 96,
                height: 96,
                borderRadius: 28,
                background: 'linear-gradient(135deg, #F59E0B, #D97706)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 52,
                boxShadow: '0 12px 32px rgba(245, 158, 11, 0.55)',
              }}
            >
              📅
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 64,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
                textShadow: '0 6px 24px rgba(0, 0, 0, 0.9)',
              }}
            >
              Inovare Agenda
            </div>
            <div
              style={{
                background: 'rgba(245, 158, 11, 0.22)',
                border: '1.5px solid #F59E0B',
                borderRadius: 16,
                padding: '6px 22px',
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FBBF24',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              Agenda IA
            </div>
          </div>
        )}

        {/* Card de Proposta de Valor */}
        {cardSpring > 0.01 && (
          <div
            style={{
              transform: `translateY(${(1 - cardSpring) * 25}px)`,
              opacity: cardSpring,
              width: 880,
              background: 'rgba(17, 24, 39, 0.96)',
              border: '2px solid rgba(245, 158, 11, 0.45)',
              borderRadius: 32,
              padding: '36px 36px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              gap: 16,
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.85)',
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.25,
              }}
            >
              Agendamentos automáticos com IA 24h
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 600,
                color: '#CBD5E1',
                lineHeight: 1.35,
              }}
            >
              IA agenda, confirma e reagenda sozinha direto no WhatsApp, sem conflito e sem duplo agendamento.
            </div>
          </div>
        )}

        {/* Botão de Ação CTA com Pulso e Shimmer */}
        {btnSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${btnSpring * pulse})`,
              opacity: btnSpring,
              marginTop: 10,
              width: 880,
              position: 'relative',
              overflow: 'hidden',
              borderRadius: 28,
              background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
              padding: '28px 36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow:
                '0 18px 45px rgba(245, 158, 11, 0.5), 0 0 30px rgba(245, 158, 11, 0.35)',
            }}
          >
            {/* Shimmer Reflexivo */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: `${shimmerX}%`,
                width: '40%',
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: '#121216',
                textTransform: 'uppercase',
                letterSpacing: 1.5,
              }}
            >
              Chame no direct
            </span>
          </div>
        )}

        {/* Perfil Oficial @inovareagenda — Visível desde o frame 0 da cena */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '14px 32px',
            borderRadius: 22,
            background: 'rgba(31, 41, 55, 0.95)',
            border: '1.5px solid rgba(255, 255, 255, 0.15)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
            marginTop: 10,
          }}
        >
          <span style={{fontSize: 34}}>👉</span>
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.1,
            }}
          >
            @inovareagenda
          </span>
        </div>
      </div>
    </div>
  );
};
