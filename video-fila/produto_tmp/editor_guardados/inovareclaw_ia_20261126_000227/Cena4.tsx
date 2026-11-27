import React from 'react';
import {
  AbsoluteFill,
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

  // Movimento de câmera contínuo e expressivo (pan e zoom)
  const bgScale = interpolate(frame, [0, 120], [1.06, 1.25], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 120], [0, -35], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 120], [-15, 15], {
    extrapolateRight: 'clamp',
  });

  // Microdinâmica constante e viva
  const floatCardY = Math.sin(frame / 10) * 8;
  const pulseButton = 1.04 + Math.sin(frame / 7) * 0.05;
  const shimmerPos = -100 + ((frame * 14) % 950);

  // Anéis de pulso de energia tech se expandindo (onda de radar contínua)
  const ring1Scale = 1 + ((frame * 2.2) % 90) / 45;
  const ring1Opacity = Math.max(0, 0.45 - ((frame * 2.2) % 90) / 90);
  const ring2Scale = 1 + (((frame * 2.2) + 45) % 90) / 45;
  const ring2Opacity = Math.max(0, 0.45 - (((frame * 2.2) + 45) % 90) / 90);

  // Entrada em mola da logo e elementos
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const descSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  const ctaSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  const arrobaSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 15, stiffness: 100},
  });

  // Entrada do badge de garantia/confiança (frame 25 = ~30.2s)
  const trustSpring = spring({
    frame: frame - 25,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Posição de luz radial em movimento contínuo
  const lightX = 50 + Math.sin(frame / 14) * 18;
  const lightY = 38 + Math.cos(frame / 16) * 14;

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D13', overflow: 'hidden'}}>
      {/* Fundo de foto com zoom e pan dinâmicos */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translate(${bgTranslateX}px, ${bgTranslateY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(7px)',
        }}
      >
        <img
          src={staticFile('img_4.jpg')}
          alt="Fundo Cartão Final"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </AbsoluteFill>

      {/* Luz radial da marca em movimento orbital contínuo */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${lightX}% ${lightY}%, rgba(124, 58, 237, 0.45) 0%, rgba(11, 13, 19, 0.88) 55%, rgba(11, 13, 19, 0.98) 100%)`,
          pointerEvents: 'none',
        }}
      />

      {/* Grid tech animado com partículas flutuantes */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'radial-gradient(rgba(124, 58, 237, 0.22) 2px, transparent 2px)',
          backgroundSize: '48px 48px',
          backgroundPosition: `0px ${frame * 1.5}px`,
          opacity: 0.75,
          pointerEvents: 'none',
        }}
      />

      {/* Anéis de pulso de energia ao redor do centro */}
      <div
        style={{
          position: 'absolute',
          top: 320,
          left: '50%',
          width: 220,
          height: 220,
          marginLeft: -110,
          borderRadius: 110,
          border: '2px solid #7C3AED',
          transform: `scale(${ring1Scale})`,
          opacity: ring1Opacity,
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 320,
          left: '50%',
          width: 220,
          height: 220,
          marginLeft: -110,
          borderRadius: 110,
          border: '2px solid #A78BFA',
          transform: `scale(${ring2Scale})`,
          opacity: ring2Opacity,
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo perfeitamente distribuído na Safe Zone vertical (y 200 a 1540) */}
      <div
        style={{
          position: 'absolute',
          top: 200,
          bottom: 380, // termina em y = 1540 (respeitando y <= 1580)
          left: 70,
          right: 90,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        {/* Bloco 1: Marca e Logo (y ≈ 200 a 480) */}
        <div
          style={{
            opacity: interpolate(logoSpring, [0, 1], [0, 1]),
            transform: `scale(${interpolate(logoSpring, [0, 1], [0.85, 1])}) translateY(${interpolate(logoSpring, [0, 1], [25, 0])}px)`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
          }}
        >
          {/* Ícone Tech da Marca com Glow Pulsante */}
          <div
            style={{
              width: 116,
              height: 116,
              borderRadius: 38,
              background: 'linear-gradient(135deg, #7C3AED, #4F46E5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: `0 16px 45px rgba(124, 58, 237, ${0.55 + Math.sin(frame / 7) * 0.2})`,
              border: '2.5px solid rgba(255, 255, 255, 0.35)',
              fontSize: 58,
            }}
          >
            ⚡
          </div>

          <h1
            style={{
              margin: 0,
              fontFamily,
              fontSize: 68,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-1px',
              textTransform: 'uppercase',
              textShadow: '0 8px 30px rgba(124, 58, 237, 0.75)',
              textAlign: 'center',
            }}
          >
            Inovare Claw
          </h1>

          <div
            style={{
              background: 'rgba(124, 58, 237, 0.32)',
              border: '1.5px solid rgba(124, 58, 237, 0.7)',
              borderRadius: 999,
              padding: '8px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              boxShadow: '0 4px 16px rgba(124, 58, 237, 0.3)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#EDE9FE',
                letterSpacing: '1px',
                textTransform: 'uppercase',
              }}
            >
              Agente de IA Autônomo
            </span>
          </div>
        </div>

        {/* Bloco 2: Card institucional com fato real do briefing e shimmer contínuo */}
        <div
          style={{
            width: '100%',
            opacity: interpolate(descSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(descSpring, [0, 1], [25, 0]) + floatCardY}px)`,
            background: 'rgba(11, 13, 19, 0.95)',
            borderRadius: 32,
            border: '2px solid rgba(124, 58, 237, 0.45)',
            padding: '32px 30px',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.85), 0 0 25px rgba(124, 58, 237, 0.2)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 16,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Shimmer suave sobre o card de benefícios */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: 100,
              transform: `translateX(${shimmerPos}px) skewX(-25deg)`,
              background:
                'linear-gradient(90deg, transparent, rgba(124, 58, 237, 0.15), transparent)',
              pointerEvents: 'none',
            }}
          />

          <div
            style={{
              fontFamily,
              fontSize: 42,
              fontWeight: 800,
              color: '#FFFFFF',
              lineHeight: 1.35,
              textWrap: 'balance',
            }}
          >
            Seu agente de inteligência artificial que trabalha sozinho.
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#DDD6FE',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            ✓ Executa tarefas de verdade pelo seu negócio
          </div>
        </div>

        {/* Bloco 3: Botão de Chamada para Ação (CTA) — Grande, Pulsando e com Microanimação Contínua */}
        <div
          style={{
            width: '100%',
            opacity: interpolate(ctaSpring, [0, 1], [0, 1]),
            transform: `scale(${interpolate(ctaSpring, [0, 1], [0.85, 1]) * pulseButton})`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: 780,
              background: 'linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)',
              borderRadius: 30,
              padding: '28px 40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 18,
              boxShadow:
                '0 16px 45px rgba(124, 58, 237, 0.75), 0 0 30px rgba(124, 58, 237, 0.5)',
              border: '2.5px solid rgba(255, 255, 255, 0.4)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Shimmer light sweep contínuo até o último frame */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 120,
                transform: `translateX(${shimmerPos}px) skewX(-25deg)`,
                background:
                  'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent)',
                pointerEvents: 'none',
              }}
            />

            <span style={{fontSize: 46}}>📩</span>
            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '1px',
                textTransform: 'uppercase',
              }}
            >
              Chame no Direct
            </span>
          </div>

          {/* Badge de atendimento imediato */}
          <div
            style={{
              opacity: interpolate(trustSpring, [0, 1], [0, 1]),
              transform: `scale(${interpolate(trustSpring, [0, 1], [0.9, 1])})`,
              background: 'rgba(16, 185, 129, 0.18)',
              border: '1.5px solid rgba(16, 185, 129, 0.55)',
              borderRadius: 999,
              padding: '10px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: 6,
                background: '#10B981',
                boxShadow: '0 0 10px #10B981',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#A7F3D0',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
            >
              Atendimento Aberto no Direct
            </span>
          </div>
        </div>

        {/* Bloco 4: Perfil Oficial (@marca) na base nobre (y ≈ 1460, seguro acima de 1580) */}
        <div
          style={{
            opacity: interpolate(arrobaSpring, [0, 1], [0.85, 1]),
            transform: `translateY(${floatCardY * 0.5}px)`,
            background: 'rgba(11, 13, 19, 0.95)',
            border: '2px solid rgba(255, 255, 255, 0.22)',
            borderRadius: 999,
            padding: '14px 38px',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.7), 0 0 15px rgba(124, 58, 237, 0.2)',
          }}
        >
          <span style={{fontSize: 34}}>👉</span>
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.5px',
            }}
          >
            @inovareclaw.ia
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
