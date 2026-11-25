import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
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

  // Movimento de câmera expressivo no fundo: zoom 1.08 a 1.28 + panY
  const bgScale = interpolate(frame, [0, 119], [1.08, 1.28], {
    extrapolateRight: 'clamp',
  });
  const bgPanY = interpolate(frame, [0, 119], [0, -55], {
    extrapolateRight: 'clamp',
  });

  // Spotlight dinâmico que percorre a tela continuamente até o fim
  const spotX = interpolate(frame, [0, 119], [25, 75], {
    extrapolateRight: 'clamp',
  });
  const spotY = interpolate(frame, [0, 119], [25, 68], {
    extrapolateRight: 'clamp',
  });

  // Slow push-in contínuo no cartão até o último frame do anúncio
  const cardPushIn = interpolate(frame, [0, 119], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Animação contínua de pulso ('heartbeat' suave) no botão 'CHAME NO DIRECT'
  // Ciclo duplo de batimento cardíaco contínuo
  const ctaHeartbeat = 1.0 + 0.045 * Math.sin((frame / 14) * Math.PI * 2);

  // Flutuação elegante contínua do card central
  const cardFloatY = Math.sin(frame / 12) * 8;

  // Brilho contínuo percorrendo o botão CTA a cada 36 frames sem interrupção
  const shineProgress = interpolate((frame % 36), [0, 36], [-150, 260]);

  // Rotação do anel tecnológico de fundo
  const ringRotate = frame * 1.1;

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D13', overflow: 'hidden'}}>
      {/* Fundo de foto inédita com câmera em movimento forte */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgPanY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(3px)',
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

      {/* Lâmpada de iluminação ambiente dinâmica em movimento contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(circle at ${spotX}% ${spotY}%, rgba(91, 108, 255, 0.45) 0%, rgba(17, 24, 39, 0.78) 45%, rgba(11, 13, 19, 0.96) 100%)`,
          pointerEvents: 'none',
        }}
      />

      {/* Grafismo decorativo de anel tecnológico sutil em rotação contínua */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          width: 1000,
          height: 1000,
          marginLeft: -500,
          marginTop: -500,
          borderRadius: '50%',
          border: '1.5px dashed rgba(91, 108, 255, 0.25)',
          transform: `rotate(${ringRotate}deg)`,
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo do Cartão Final rigorosamente centralizado verticalmente na safe zone (y=150 a y=1580) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 260,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          pointerEvents: 'none',
          transform: `scale(${cardPushIn}) translateY(${cardFloatY}px)`,
          transformOrigin: 'center center',
        }}
      >
        {/* Card Principal Imponente, Amplo e Perfeitamente Equilibrado */}
        <div
          style={{
            width: '100%',
            maxWidth: 960,
            background: 'rgba(17, 24, 39, 0.96)',
            border: '2px solid rgba(91, 108, 255, 0.5)',
            borderRadius: 44,
            padding: '52px 42px',
            boxShadow:
              '0 30px 70px rgba(0, 0, 0, 0.92), 0 0 55px rgba(91, 108, 255, 0.3)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          {/* Tag de topo */}
          <div
            style={{
              padding: '8px 26px',
              borderRadius: 9999,
              background: 'rgba(91, 108, 255, 0.22)',
              border: '1.5px solid rgba(91, 108, 255, 0.55)',
              marginBottom: 20,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#818CF8',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
              }}
            >
              Automação Comercial
            </span>
          </div>

          {/* Nome da Marca Grande */}
          <h1
            style={{
              fontFamily,
              fontSize: 76,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
              margin: '0 0 16px 0',
              textShadow:
                '0 4px 20px rgba(0,0,0,0.95), 0 0 35px rgba(91, 108, 255, 0.6)',
            }}
          >
            SuperChat IA
          </h1>

          {/* 1 frase do que o produto faz (fatos do briefing com ortografia corrigida 'Multiatendimento') */}
          <p
            style={{
              fontFamily,
              fontSize: 40,
              fontWeight: 700,
              color: '#CBD5E1',
              margin: '0 0 28px 0',
              lineHeight: 1.3,
              maxWidth: 840,
              textWrap: 'balance',
            }}
          >
            Multiatendimento e CRM com IA
          </p>

          {/* Canais centralizados */}
          <div
            style={{
              display: 'flex',
              gap: 14,
              flexWrap: 'wrap',
              justifyContent: 'center',
              marginBottom: 34,
            }}
          >
            {['WhatsApp', 'Telegram', 'Instagram'].map((canal, idx) => (
              <div
                key={idx}
                style={{
                  padding: '8px 24px',
                  borderRadius: 16,
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1.5px solid rgba(255, 255, 255, 0.18)',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#F1F5F9',
                  }}
                >
                  {canal}
                </span>
              </div>
            ))}
          </div>

          {/* Fatos oficiais de confiança */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
              width: '100%',
              maxWidth: 840,
              marginBottom: 38,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                padding: '14px 24px',
                borderRadius: 18,
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
              }}
            >
              <span style={{color: '#10B981', fontSize: 34, fontWeight: 900}}>✓</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#E2E8F0',
                }}
              >
                Centraliza conversas no mesmo painel
              </span>
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                padding: '14px 24px',
                borderRadius: 18,
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
              }}
            >
              <span style={{color: '#10B981', fontSize: 34, fontWeight: 900}}>✓</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#E2E8F0',
                }}
              >
                Atendimento IA 24h no WhatsApp
              </span>
            </div>
          </div>

          {/* Botão de CTA com Heartbeat Contínuo e Brilho Recorrente */}
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              transform: `scale(${ctaHeartbeat})`,
              transformOrigin: 'center center',
              background: 'linear-gradient(135deg, #5B6CFF 0%, #3B49DF 100%)',
              borderRadius: 28,
              padding: '24px 64px',
              boxShadow:
                '0 18px 48px rgba(91, 108, 255, 0.75), 0 0 35px rgba(91, 108, 255, 0.5)',
              border: '2px solid rgba(255, 255, 255, 0.35)',
              marginBottom: 32,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                textShadow: '0 2px 10px rgba(0,0,0,0.5)',
              }}
            >
              Chame no Direct
            </span>

            {/* Shine sweep contínuo a cada 36 frames */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: `${shineProgress}%`,
                width: 75,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)',
                transform: 'skewX(-25deg)',
              }}
            />
          </div>

          {/* Perfil Oficial (@marca) */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 34px',
              borderRadius: 9999,
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1.5px solid rgba(255, 255, 255, 0.18)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: '0.02em',
              }}
            >
              @superchatia.ia
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
