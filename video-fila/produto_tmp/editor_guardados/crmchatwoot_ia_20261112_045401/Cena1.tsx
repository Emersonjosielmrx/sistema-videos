import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera: pan e scale contínuo (1.02 -> 1.08)
  const scale = interpolate(frame, [0, 218], [1.02, 1.08], {
    extrapolateRight: 'clamp',
  });
  const panX = interpolate(frame, [0, 218], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge "O PROBLEMA" aos 0.2s (frame 6)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Título principal aos 0.45s ("Sistemas prontos complicam", frame 14)
  const titleSpring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Card 1: "Sistemas engessados e genéricos" aos 0.8s (frame 24)
  const card1Spring = spring({
    frame: frame - 24,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card 2: "Telas complexas e confusas" aos 3.0s (frame 90)
  const card2Spring = spring({
    frame: frame - 90,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card 3: "Baixa adesão da equipe" aos 4.2s (frame 126)
  const card3Spring = spring({
    frame: frame - 126,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Microinteração de alerta pulsante
  const pulseAlert = Math.sin(frame * 0.15) * 0.025;

  // Saída suave nos últimos 12 frames
  const fadeOut = interpolate(frame, [206, 218], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', opacity: fadeOut}}>
      {/* Imagem de Fundo b-roll vivo com pan e zoom */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_1.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${scale}) translateX(${panX}px)`,
            filter: 'brightness(0.7) contrast(1.08)',
          }}
        />
        {/* Gradiente lateral esquerdo: protege o rosto da atendente (à direita) e dá contraste aos cards */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(90deg, rgba(17,24,39,0.95) 0%, rgba(17,24,39,0.84) 54%, rgba(17,24,39,0.22) 100%)',
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
            backgroundColor: 'rgba(239, 68, 68, 0.22)',
            border: '2px solid rgba(239, 68, 68, 0.75)',
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
              backgroundColor: '#EF4444',
              boxShadow: '0 0 12px #EF4444',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FCA5A5',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O Problema
          </span>
        </div>

        {/* Título de Impacto ancorado na lateral esquerda (largura 530px) */}
        <div
          style={{
            position: 'absolute',
            top: 260,
            left: 60,
            width: 530,
            opacity: titleSpring,
            transform: `translateY(${(1 - titleSpring) * 15}px)`,
          }}
        >
          <h2
            style={{
              fontFamily,
              fontSize: 46,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.25,
              margin: 0,
              textShadow: '0 4px 20px rgba(0,0,0,0.8)',
            }}
          >
            Sistemas prontos costumam <span style={{color: '#EF4444'}}>complicar</span> o dia a dia
          </h2>
        </div>

        {/* Pilha de Cards de Dores / Atritos (largura 530px) */}
        <div
          style={{
            position: 'absolute',
            top: 450,
            left: 60,
            width: 530,
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
          }}
        >
          {/* Card 1: Telas engessadas */}
          {frame >= 20 && (
            <div
              style={{
                backgroundColor: 'rgba(17, 24, 39, 0.94)',
                border: '2px solid rgba(239, 68, 68, 0.5)',
                borderRadius: 20,
                padding: '20px 22px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                opacity: card1Spring,
                transform: `translateX(${(1 - card1Spring) * -40}px)`,
                boxShadow: '0 10px 25px rgba(0,0,0,0.6)',
                backdropFilter: 'blur(8px)',
              }}
            >
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 14,
                  backgroundColor: 'rgba(239, 68, 68, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                  flexShrink: 0,
                }}
              >
                🔒
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                <span style={{fontFamily, fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                  Estrutura engessada
                </span>
                <span style={{fontFamily, fontSize: 32, fontWeight: 600, color: '#94A3B8'}}>
                  Fluxos genéricos sem flexibilidade
                </span>
              </div>
            </div>
          )}

          {/* Card 2: Telas difíceis */}
          {frame >= 85 && (
            <div
              style={{
                backgroundColor: 'rgba(17, 24, 39, 0.94)',
                border: '2px solid rgba(245, 158, 11, 0.5)',
                borderRadius: 20,
                padding: '20px 22px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                opacity: card2Spring,
                transform: `translateX(${(1 - card2Spring) * -40}px)`,
                boxShadow: '0 10px 25px rgba(0,0,0,0.6)',
                backdropFilter: 'blur(8px)',
              }}
            >
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 14,
                  backgroundColor: 'rgba(245, 158, 11, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                  flexShrink: 0,
                }}
              >
                📑
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                <span style={{fontFamily, fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                  Telas difíceis e confusas
                </span>
                <span style={{fontFamily, fontSize: 32, fontWeight: 600, color: '#94A3B8'}}>
                  Excesso de menus que travam
                </span>
              </div>
            </div>
          )}

          {/* Card 3: Ninguém preenche */}
          {frame >= 120 && (
            <div
              style={{
                backgroundColor: 'rgba(17, 24, 39, 0.96)',
                border: '2px solid rgba(239, 68, 68, 0.8)',
                borderRadius: 20,
                padding: '20px 22px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                opacity: card3Spring,
                transform: `scale(${card3Spring + pulseAlert})`,
                boxShadow: '0 12px 30px rgba(239, 68, 68, 0.3)',
                backdropFilter: 'blur(8px)',
              }}
            >
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 14,
                  backgroundColor: 'rgba(239, 68, 68, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                  flexShrink: 0,
                }}
              >
                ⚠️
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                <span style={{fontFamily, fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                  Ninguém na equipe preenche
                </span>
                <span style={{fontFamily, fontSize: 32, fontWeight: 600, color: '#F87171'}}>
                  Histórico de clientes perdido
                </span>
              </div>
            </div>
          )}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
