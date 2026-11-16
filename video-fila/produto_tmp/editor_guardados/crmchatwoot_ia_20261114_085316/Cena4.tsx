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

interface Cena4Props {
  fontFamily: string;
}

export const Cena4: React.FC<Cena4Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background contínuo vivo com zoom
  const bgScale = interpolate(frame, [0, 120], [1.1, 1.25], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Logo da Marca (frame 3)
  const logoSpring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Entrada da Frase de Proposta de Valor (frame 10)
  const textSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Entrada do Botão CTA (frame 18)
  const btnSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 10, stiffness: 120},
  });

  // Entrada da Conta @ (frame 26)
  const handleSpring = spring({
    frame: frame - 26,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Pulso contínuo do botão CTA (1.00 a 1.06 até o último frame)
  const btnPulse = 1.0 + Math.sin(frame / 6) * 0.035;

  // Brilho que varre o botão continuamente
  const shimmerPos = interpolate(frame % 45, [0, 45], [-150, 150]);

  // Flutuação sutil de respiração do logo
  const logoFloat = Math.sin(frame / 12) * 6;

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* Background com foto desfocada + véu escuro corporativo */}
      <AbsoluteFill style={{transform: `scale(${bgScale})`}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(25px)',
          }}
        />
        <AbsoluteFill
          style={{
            background:
              'radial-gradient(circle at 50% 50%, rgba(31,147,255,0.22) 0%, rgba(15,23,42,0.92) 65%, rgba(15,23,42,0.98) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Elementos na Safe Zone (x: 60-1020, y: 150-1580) */}
      <AbsoluteFill
        style={{
          padding: '0 60px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Bloco da Marca e Logo */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            opacity: interpolate(logoSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(logoSpring, [0, 1], [-30, 0]) + logoFloat}px)`,
          }}
        >
          {/* Ícone estilizado Chatwoot IA */}
          <div
            style={{
              width: 100,
              height: 100,
              borderRadius: 30,
              background: 'linear-gradient(135deg, #1F93FF 0%, #0284C7 100%)',
              boxShadow:
                '0 12px 35px rgba(31,147,255,0.6), 0 0 25px rgba(31,147,255,0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 52,
              marginBottom: 18,
            }}
          >
            ⚡
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 60,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: -1,
              textTransform: 'uppercase',
              textShadow: '0 6px 25px rgba(0,0,0,0.8)',
            }}
          >
            CRM Chatwoot IA
          </div>
        </div>

        {/* 1 Frase do que o produto faz */}
        <div
          style={{
            marginTop: 24,
            maxWidth: 860,
            textAlign: 'center',
            opacity: interpolate(textSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(textSpring, [0, 1], [20, 0])}px)`,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 600,
              color: '#E2E8F0',
              lineHeight: 1.35,
              textShadow: '0 4px 15px rgba(0,0,0,0.8)',
            }}
          >
            Atendimento, tickets e histórico de cada cliente centralizados em um
            só lugar.
          </div>
        </div>

        {/* Botão Principal com a MESMA ação de convite_voz ("Chame a gente no direct" -> "CHAME NO DIRECT") */}
        <div
          style={{
            marginTop: 50,
            opacity: interpolate(btnSpring, [0, 1], [0, 1]),
            transform: `scale(${interpolate(btnSpring, [0, 1], [0.85, 1]) * btnPulse})`,
          }}
        >
          <div
            style={{
              width: 780,
              height: 116,
              borderRadius: 26,
              background: 'linear-gradient(90deg, #1F93FF 0%, #0284C7 100%)',
              boxShadow:
                '0 16px 45px rgba(31, 147, 255, 0.55), 0 0 30px rgba(31, 147, 255, 0.35)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              overflow: 'hidden',
              border: '2px solid rgba(255, 255, 255, 0.4)',
            }}
          >
            {/* Shimmer sweep animation */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 80,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
                transform: `translateX(${shimmerPos}%) skewX(-25deg)`,
              }}
            />

            <span
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                textTransform: 'uppercase',
                textShadow: '0 2px 10px rgba(0,0,0,0.3)',
              }}
            >
              CHAME NO DIRECT
            </span>
          </div>
        </div>

        {/* Handle oficial @crmchatwoot.ia */}
        <div
          style={{
            marginTop: 34,
            opacity: interpolate(handleSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(handleSpring, [0, 1], [20, 0])}px)`,
          }}
        >
          <div
            style={{
              padding: '12px 32px',
              borderRadius: 30,
              background: 'rgba(15, 23, 42, 0.85)',
              border: '2px solid rgba(31, 147, 255, 0.7)',
              boxShadow: '0 8px 25px rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: '50%',
                backgroundColor: '#1F93FF',
                boxShadow: '0 0 10px #1F93FF',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 800,
                color: '#FFFFFF',
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
