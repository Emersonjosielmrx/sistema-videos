import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera: push-in contínuo (1.0 -> 1.07)
  const scale = interpolate(frame, [0, 209], [1.0, 1.07], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge "O RESULTADO" aos 0.2s (frame 6)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Título principal aos 0.5s ("Sua rotina mais leve", frame 15)
  const titleSpring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Item 1: "Processos adaptados ao seu fluxo" aos 0.9s (frame 27)
  const item1Spring = spring({
    frame: frame - 27,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Item 2: "Histórico e chamados unificados" aos 2.8s (frame 84)
  const item2Spring = spring({
    frame: frame - 84,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Item 3: "Atendimento sem esforço" aos 4.3s (frame 129)
  const item3Spring = spring({
    frame: frame - 129,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Microinteração contínua de pulso sutil
  const pulse = Math.sin(frame * 0.1) * 0.02;

  // Saída suave nos últimos 12 frames
  const fadeOut = interpolate(frame, [197, 209], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', opacity: fadeOut}}>
      {/* Imagem de Fundo b-roll vivo com push-in */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_3.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${scale})`,
            filter: 'brightness(0.72) contrast(1.06)',
          }}
        />
        {/* Gradiente vertical/topo para leitura cristalina dos cards no topo e centro-alto (y: 180 a 950) */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(17,24,39,0.95) 0%, rgba(17,24,39,0.85) 45%, rgba(17,24,39,0.3) 75%, rgba(17,24,39,0.1) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo dentro da Safe Zone (y: 150 a 1580, laterais >= 60px) */}
      <AbsoluteFill style={{padding: '0 60px', pointerEvents: 'none'}}>
        {/* Rótulo Badge de Topo */}
        <div
          style={{
            position: 'absolute',
            top: 180,
            left: 60,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            backgroundColor: 'rgba(31, 147, 255, 0.2)',
            border: '2px solid rgba(31, 147, 255, 0.7)',
            padding: '10px 24px',
            borderRadius: 30,
            opacity: badgeSpring,
            transform: `translateY(${(1 - badgeSpring) * -20}px)`,
            backdropFilter: 'blur(8px)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#1F93FF',
              boxShadow: '0 0 12px #1F93FF',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O Resultado
          </span>
        </div>

        {/* Título de Impacto (y=260) */}
        <div
          style={{
            position: 'absolute',
            top: 260,
            left: 60,
            right: 60,
            opacity: titleSpring,
            transform: `translateY(${(1 - titleSpring) * 15}px)`,
          }}
        >
          <h2
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.25,
              margin: 0,
              textShadow: '0 4px 20px rgba(0,0,0,0.85)',
            }}
          >
            Sua rotina fica mais <span style={{color: '#1F93FF'}}>leve e eficiente</span>
          </h2>
        </div>

        {/* Grade de 3 Benefícios com Checkmark Animado (y: 430 a 900, deixando y > 950 com respiro absoluto do peito/cabeça da pessoa) */}
        <div
          style={{
            position: 'absolute',
            top: 430,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
          }}
        >
          {/* Item 1 */}
          {frame >= 20 && (
            <div
              style={{
                backgroundColor: 'rgba(17, 24, 39, 0.92)',
                border: '2px solid rgba(31, 147, 255, 0.5)',
                borderRadius: 22,
                padding: '20px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: 20,
                opacity: item1Spring,
                transform: `translateX(${(1 - item1Spring) * -40}px)`,
                boxShadow: '0 10px 25px rgba(0,0,0,0.6)',
                backdropFilter: 'blur(8px)',
              }}
            >
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 16,
                  backgroundColor: 'rgba(31, 147, 255, 0.25)',
                  border: '2px solid #1F93FF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontWeight: 900,
                  fontSize: 28,
                  flexShrink: 0,
                }}
              >
                ✓
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                <span style={{fontFamily, fontSize: 36, fontWeight: 800, color: '#FFFFFF'}}>
                  Processos adaptados
                </span>
                <span style={{fontFamily, fontSize: 32, fontWeight: 600, color: '#94A3B8'}}>
                  Exatamente ao jeito que você já trabalha
                </span>
              </div>
            </div>
          )}

          {/* Item 2 */}
          {frame >= 75 && (
            <div
              style={{
                backgroundColor: 'rgba(17, 24, 39, 0.92)',
                border: '2px solid rgba(16, 185, 129, 0.5)',
                borderRadius: 22,
                padding: '20px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: 20,
                opacity: item2Spring,
                transform: `translateX(${(1 - item2Spring) * -40}px)`,
                boxShadow: '0 10px 25px rgba(0,0,0,0.6)',
                backdropFilter: 'blur(8px)',
              }}
            >
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 16,
                  backgroundColor: 'rgba(16, 185, 129, 0.25)',
                  border: '2px solid #10B981',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontWeight: 900,
                  fontSize: 28,
                  flexShrink: 0,
                }}
              >
                ✓
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                <span style={{fontFamily, fontSize: 36, fontWeight: 800, color: '#FFFFFF'}}>
                  Histórico e chamados integrados
                </span>
                <span style={{fontFamily, fontSize: 32, fontWeight: 600, color: '#94A3B8'}}>
                  Cada cliente centralizado em um só lugar
                </span>
              </div>
            </div>
          )}

          {/* Item 3 */}
          {frame >= 120 && (
            <div
              style={{
                backgroundColor: 'rgba(17, 24, 39, 0.95)',
                border: '2px solid rgba(31, 147, 255, 0.75)',
                borderRadius: 22,
                padding: '20px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: 20,
                opacity: item3Spring,
                transform: `scale(${item3Spring + pulse})`,
                boxShadow: '0 12px 30px rgba(31, 147, 255, 0.3)',
                backdropFilter: 'blur(8px)',
              }}
            >
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 16,
                  backgroundColor: '#1F93FF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontWeight: 900,
                  fontSize: 28,
                  flexShrink: 0,
                }}
              >
                ✓
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                <span style={{fontFamily, fontSize: 36, fontWeight: 800, color: '#FFFFFF'}}>
                  Facilidade para a equipe
                </span>
                <span style={{fontFamily, fontSize: 32, fontWeight: 600, color: '#60A5FA'}}>
                  Adesão natural e alta produtividade
                </span>
              </div>
            </div>
          )}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
