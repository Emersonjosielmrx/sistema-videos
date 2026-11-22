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

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (push-in suave)
  const scale = interpolate(frame, [0, 118], [1.06, 1.16], {
    extrapolateRight: 'clamp',
  });

  // Entrada ágil de impacto imediato
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  const textSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const ctaSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const handleSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Pulso contínuo do botão CTA (ciclo de 1.2s = 36 frames: scale 1.00 a 1.08) - Regra 10
  const buttonPulse = 1.04 + 0.04 * Math.sin((frame / 36) * Math.PI * 2);

  // Efeito de brilho cruzando o botão continuamente
  const shineProgress = interpolate((frame % 45), [0, 30], [-100, 200], {
    extrapolateRight: 'clamp',
  });

  // Flutuação sutil do bloco de conteúdo
  const floatY = Math.sin((frame / 25) * Math.PI * 2) * 4;

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
      {/* Imagem de Fundo com Zoom Contínuo e Desfoque Elegante */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 1080,
          height: 1920,
          transform: `scale(${scale})`,
          transformOrigin: 'center center',
          filter: 'blur(20px)',
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

      {/* Véu Escuro com Iluminação Central Tecnológica (Azul Inovare `#0284C7` + Slate `#0F172A`) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 45%, rgba(2, 132, 199, 0.32) 0%, rgba(15, 23, 42, 0.94) 65%, rgba(15, 23, 42, 0.98) 100%)',
        }}
      />

      {/* Área Segura de Conteúdo (150 a 1580, x=60 a 1020) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 60px',
        }}
      >
        {/* Bloco Central de Identidade Visual */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            transform: `translateY(${floatY}px)`,
          }}
        >
          {/* Ícone de Marca com Glow */}
          <div
            style={{
              transform: `scale(${logoSpring})`,
              width: 96,
              height: 96,
              borderRadius: 28,
              background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)',
              border: '2px solid rgba(255, 255, 255, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 48,
              boxShadow: '0 12px 35px rgba(2, 132, 199, 0.55)',
              marginBottom: 24,
            }}
          >
            ⚡
          </div>

          {/* Nome da Marca */}
          <div
            style={{
              transform: `scale(${logoSpring})`,
              marginBottom: 12,
            }}
          >
            <span
              style={{
                fontSize: 68,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1,
                textTransform: 'uppercase',
                textShadow: '0 4px 20px rgba(2, 132, 199, 0.6)',
                display: 'block',
              }}
            >
              INOVARE CRM
            </span>
          </div>

          {/* Tag de Produto */}
          <div
            style={{
              transform: `translateY(${interpolate(textSpring, [0, 1], [20, 0])}px)`,
              opacity: textSpring,
              marginBottom: 20,
            }}
          >
            <div
              style={{
                display: 'inline-block',
                background: 'rgba(2, 132, 199, 0.22)',
                border: '1.5px solid #0284C7',
                borderRadius: 20,
                padding: '8px 24px',
              }}
            >
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#38BDF8',
                  letterSpacing: 1,
                  textTransform: 'uppercase',
                }}
              >
                CRM Chatwoot & Inteligência Artificial
              </span>
            </div>
          </div>

          {/* Frase de Valor do Briefing */}
          <div
            style={{
              transform: `translateY(${interpolate(textSpring, [0, 1], [20, 0])}px)`,
              opacity: textSpring,
              maxWidth: 820,
              marginBottom: 50,
            }}
          >
            <span
              style={{
                fontSize: 36,
                fontWeight: 600,
                color: '#E2E8F0',
                lineHeight: 1.35,
                display: 'block',
              }}
            >
              Um CRM feito sob medida para o seu negócio, com atendimento, tickets e histórico em um só lugar.
            </span>
          </div>

          {/* Botão de Chamada para Ação (CTA) com Pulso Contínuo (1.00 a 1.08) e Reflexo Dinâmico */}
          <div
            style={{
              transform: `scale(${ctaSpring * buttonPulse})`,
              opacity: ctaSpring,
              marginBottom: 36,
            }}
          >
            <div
              style={{
                position: 'relative',
                overflow: 'hidden',
                background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)',
                border: '2.5px solid rgba(255, 255, 255, 0.45)',
                borderRadius: 40,
                padding: '24px 56px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                boxShadow: '0 16px 45px rgba(2, 132, 199, 0.7)',
              }}
            >
              {/* Linha de reflexo / brilho passando */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  left: `${shineProgress}%`,
                  width: 80,
                  background:
                    'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.45) 50%, transparent 100%)',
                  transform: 'skewX(-25deg)',
                  pointerEvents: 'none',
                }}
              />

              <span
                style={{
                  fontSize: 44,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: 1.5,
                }}
              >
                CHAME NO DIRECT
              </span>

              <div
                style={{
                  fontSize: 36,
                  color: '#FFFFFF',
                  transform: 'translateX(4px)',
                }}
              >
                ➔
              </div>
            </div>
          </div>

          {/* @ Perfil Oficial - Visível desde o frame 0.0s (Regra 10) */}
          <div
            style={{
              transform: `scale(${handleSpring})`,
              opacity: handleSpring,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                background: 'rgba(15, 23, 42, 0.85)',
                border: '1.5px solid rgba(255, 255, 255, 0.22)',
                borderRadius: 24,
                padding: '12px 32px',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
              }}
            >
              <span
                style={{
                  fontSize: 36,
                  fontWeight: 800,
                  color: '#94A3B8',
                  letterSpacing: 0.5,
                }}
              >
                @inovarecrm
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
