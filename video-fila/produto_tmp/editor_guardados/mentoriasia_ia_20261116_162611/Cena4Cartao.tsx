import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig
} from 'remotion';
import {BRIEFING} from './data';

export const Cena4Cartao: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background zoom contínuo
  const bgScale = interpolate(frame, [0, 120], [1.0, 1.14], {
    extrapolateRight: 'clamp'
  });

  // Slow zoom-in contínuo no conjunto do cartão até o final (evita cena congelada entre q14 e q15!)
  const cardZoom = interpolate(frame, [0, 120], [1.0, 1.06], {
    extrapolateRight: 'clamp'
  });

  // Entrada ágil do topo
  const logoSpring = spring({frame: frame - 1, fps, config: {damping: 14, stiffness: 130}});
  const textSpring = spring({frame: frame - 3, fps, config: {damping: 14, stiffness: 130}});

  // Pilares entram logo no início (delays 0, 3, 6) com texto 100% branco e alto contraste
  const pilares = [
    {titulo: 'Treinamento Vibe Coding', icone: '⚡', delay: 0},
    {titulo: 'Pack de Prompts Validados', icone: '🎯', delay: 3},
    {titulo: 'Consultoria de Otimização', icone: '🚀', delay: 6}
  ];

  // Antecipação do CTA: entrada no frame 4 e 8 para estar 100% na tela antes de 28.27s (f=24)
  const btnSpring = spring({frame: frame - 4, fps, config: {damping: 13, stiffness: 130}});
  const arrobaSpring = spring({frame: frame - 8, fps, config: {damping: 14, stiffness: 130}});

  const btnScale = frame < 4 ? 0 : btnSpring;
  const btnOpacity = frame < 4 ? 0 : Math.min(1, Math.max(0, btnSpring));
  const arrobaScale = frame < 8 ? 0 : arrobaSpring;
  const arrobaOpacity = frame < 8 ? 0 : Math.min(1, Math.max(0, arrobaSpring));

  // Microinteração contínua: pulso senoidal no botão (scale de 1.0 a 1.055)
  const pulse = 1.025 + Math.sin(frame / 3.5) * 0.03;

  // Shimmer luminoso diagonal contínuo em loop deslizando pelo botão
  const shimmerLeft = interpolate(frame % 28, [0, 28], [-40, 130]);

  // Brilho cíclico que percorre os 3 itens para manter a tela viva entre q14 e q15
  const activePillIndex = Math.floor((frame / 14) % 3);

  // Leve flutuação suave da marca
  const floatY = Math.sin(frame / 6) * 5;

  return (
    <AbsoluteFill style={{backgroundColor: BRIEFING.cores.fundo_escuro, overflow: 'hidden'}}>
      {/* Background Image desfocada com zoom contínuo */}
      <img
        src={staticFile('img_4.jpg')}
        alt="Fundo"
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${bgScale})`,
          filter: 'blur(14px) brightness(0.42) contrast(1.15)'
        }}
      />

      {/* Luz radial dinâmica que se move continuamente */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(circle at ${50 + Math.sin(frame / 10) * 12}% ${42 + Math.cos(frame / 12) * 10}%, rgba(37, 99, 235, 0.35) 0%, rgba(15, 23, 42, 0.90) 65%, rgba(5, 8, 16, 0.98) 100%)`,
          pointerEvents: 'none'
        }}
      />

      {/* Container Centralizado na Safe Zone com slow zoom-in contínuo (y: 150..1580, x: 60..1020) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 170,
          bottom: 170,
          transform: `scale(${cardZoom})`,
          transformOrigin: '50% 50%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 30,
          fontFamily,
          textAlign: 'center'
        }}
      >
        {/* Bloco 1: Logo e Nome da Marca (Topo) */}
        <div
          style={{
            transform: `scale(${logoSpring}) translateY(${floatY}px)`,
            opacity: logoSpring,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 14
          }}
        >
          {/* Ícone de Marca com Glow */}
          <div
            style={{
              width: 95,
              height: 95,
              borderRadius: 26,
              backgroundColor: BRIEFING.cores.marca,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 10px 36px rgba(37, 99, 235, 0.65), 0 0 24px rgba(96, 165, 250, 0.45)',
              border: '2px solid rgba(255, 255, 255, 0.35)'
            }}
          >
            <span style={{fontSize: 46, fontWeight: 900, color: '#FFFFFF'}}>IA</span>
          </div>

          {/* Nome da Marca Grande e Legível */}
          <div
            style={{
              fontSize: 46,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
              textShadow: '0 4px 20px rgba(0, 0, 0, 0.9)',
              maxWidth: 880,
              lineHeight: 1.2
            }}
          >
            TREINAMENTOS E MENTORIAS IA
          </div>
        </div>

        {/* Bloco 2: 1 Frase dos Fatos + Pilares da Oferta (Alto Contraste) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            width: '100%',
            maxWidth: 900
          }}
        >
          {/* Frase oficial dos fatos */}
          <div
            style={{
              transform: `translateY(${interpolate(textSpring, [0, 1], [24, 0])}px)`,
              opacity: textSpring,
              backgroundColor: 'rgba(15, 23, 42, 0.92)',
              padding: '18px 28px',
              borderRadius: 22,
              border: '1.5px solid rgba(59, 130, 246, 0.45)',
              boxShadow: '0 10px 32px rgba(0, 0, 0, 0.55)',
              backdropFilter: 'blur(14px)',
              width: '100%'
            }}
          >
            <div
              style={{
                fontSize: 38,
                fontWeight: 800,
                color: '#FFFFFF',
                lineHeight: 1.25
              }}
            >
              Aprenda a criar automações com IA.
            </div>
          </div>

          {/* Pilares com Alto Contraste Garantido e Microinteração Cíclica */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
              width: '100%'
            }}
          >
            {pilares.map((p, pIdx) => {
              const rawItemS = spring({
                frame: frame - p.delay,
                fps,
                config: {damping: 14, stiffness: 120}
              });
              const itemS = frame < p.delay ? 0 : rawItemS;
              const isHighlighted = activePillIndex === pIdx;
              return (
                <div
                  key={pIdx}
                  style={{
                    transform: `translateY(${interpolate(itemS, [0, 1], [24, 0])}px) scale(${isHighlighted ? 1.025 : 1})`,
                    opacity: itemS,
                    padding: '14px 24px',
                    borderRadius: 18,
                    backgroundColor: isHighlighted
                      ? 'rgba(37, 99, 235, 0.38)'
                      : 'rgba(15, 23, 42, 0.94)',
                    border: isHighlighted
                      ? '2px solid #93C5FD'
                      : '1.5px solid rgba(96, 165, 250, 0.45)',
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    boxShadow: isHighlighted
                      ? '0 8px 26px rgba(37, 99, 235, 0.5)'
                      : '0 4px 16px rgba(0, 0, 0, 0.35)'
                  }}
                >
                  <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                    <span style={{fontSize: 36}}>{p.icone}</span>
                    <span style={{color: '#FFFFFF'}}>{p.titulo}</span>
                  </div>
                  <span style={{fontSize: 32, color: isHighlighted ? '#93C5FD' : '#60A5FA', fontWeight: 900}}>
                    ✓
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Bloco 3: Botão de Ação CTA (Antecipado para o início da fala + Pulso contínuo + Shimmer) + Arroba */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            width: '100%',
            maxWidth: 860
          }}
        >
          {/* Botão de Chamada para Ação */}
          <div
            style={{
              transform: `translateY(${interpolate(btnScale, [0, 1], [24, 0])}px) scale(${btnScale * pulse})`,
              opacity: btnOpacity,
              width: '100%',
              backgroundColor: BRIEFING.cores.marca,
              borderRadius: 28,
              padding: '24px 36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              boxShadow: `0 14px 44px rgba(37, 99, 235, ${0.65 + Math.sin(frame / 3.5) * 0.25}), 0 0 28px rgba(96, 165, 250, 0.55)`,
              border: '2px solid rgba(255, 255, 255, 0.45)',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            {/* Shimmer Luminoso Correndo Continuamente */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: '32%',
                left: `${shimmerLeft}%`,
                background:
                  'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.65) 50%, transparent 100%)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none'
              }}
            />

            <span style={{fontSize: 44}}>💬</span>
            <span
              style={{
                fontSize: 46,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '1px',
                textTransform: 'uppercase'
              }}
            >
              CHAME NO DIRECT
            </span>
          </div>

          {/* Arroba Oficial */}
          <div
            style={{
              transform: `translateY(${interpolate(arrobaScale, [0, 1], [18, 0])}px)`,
              opacity: arrobaOpacity,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 28px',
              borderRadius: 20,
              backgroundColor: 'rgba(255, 255, 255, 0.12)',
              border: '1.5px solid rgba(255, 255, 255, 0.25)',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)'
            }}
          >
            <span
              style={{
                fontSize: 36,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: '0.5px'
              }}
            >
              {BRIEFING.arroba}
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
