import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de fundo com zoom suave (1.0 -> 1.08)
  const bgScale = interpolate(frame, [0, 119], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Entrada dos elementos
  const cardSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const buttonSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  const handleSpring = spring({
    frame: frame - 28,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Pulso contínuo do botão CTA (movimento contínuo até o último frame)
  const buttonPulse = Math.sin(frame * 0.15) * 0.035;

  // Shimmer contínuo
  const shimmerX = interpolate(frame % 40, [0, 40], [-200, 500], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#111827'}}>
      {/* Imagem de Fundo b-roll vivo com blur elegante e véu escuro */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale})`,
            filter: 'blur(16px) brightness(0.38) contrast(1.1)',
          }}
        />
        {/* Glow dinâmico de marca */}
        <div
          style={{
            position: 'absolute',
            width: 700,
            height: 700,
            borderRadius: '50%',
            top: '40%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'radial-gradient(circle, rgba(31,147,255,0.25) 0%, transparent 70%)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(17,24,39,0.85) 0%, rgba(17,24,39,0.65) 50%, rgba(17,24,39,0.92) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo dentro da Safe Zone (y: 150 a 1580, laterais >= 60px) */}
      <AbsoluteFill
        style={{
          padding: '0 60px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: 920,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 36,
            marginTop: -40,
            opacity: cardSpring,
            transform: `scale(${cardSpring})`,
          }}
        >
          {/* Logo / Marca */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <div
              style={{
                width: 104,
                height: 104,
                borderRadius: 30,
                backgroundColor: '#1F93FF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 12px 35px rgba(31, 147, 255, 0.65)',
              }}
            >
              <span style={{fontSize: 56}}>⚡</span>
            </div>
            <h1
              style={{
                fontFamily,
                fontSize: 62,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                margin: 0,
                textTransform: 'uppercase',
                textShadow: '0 4px 20px rgba(0,0,0,0.85)',
              }}
            >
              CRM Chatwoot IA
            </h1>
          </div>

          {/* Frase de Resumo do Briefing */}
          <div style={{maxWidth: 840}}>
            <p
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 600,
                color: '#CBD5E1',
                lineHeight: 1.4,
                margin: 0,
                textWrap: 'balance',
                textShadow: '0 2px 10px rgba(0,0,0,0.8)',
              }}
            >
              Atendimento, tickets e histórico de cada cliente em um só lugar.
            </p>
          </div>

          {/* Botão de Ação CTA Pulsante com Shimmer (y entre 900 e 1450) */}
          <div
            style={{
              marginTop: 16,
              opacity: buttonSpring,
              transform: `scale(${buttonSpring + buttonPulse})`,
              position: 'relative',
              overflow: 'hidden',
              backgroundColor: '#1F93FF',
              padding: '28px 68px',
              borderRadius: 32,
              boxShadow: '0 16px 45px rgba(31, 147, 255, 0.6), 0 0 25px rgba(31, 147, 255, 0.4)',
              border: '2px solid rgba(255, 255, 255, 0.35)',
            }}
          >
            {/* Shimmer light effect */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 70,
                transform: `translateX(${shimmerX}px) skewX(-25deg)`,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                textTransform: 'uppercase',
                position: 'relative',
                zIndex: 2,
              }}
            >
              Chame no Direct
            </span>
          </div>

          {/* @handle oficial */}
          <div
            style={{
              opacity: handleSpring,
              transform: `translateY(${(1 - handleSpring) * 15}px)`,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 700,
                color: '#94A3B8',
                letterSpacing: 1,
              }}
            >
              @crmchatwoot.ia
            </span>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
