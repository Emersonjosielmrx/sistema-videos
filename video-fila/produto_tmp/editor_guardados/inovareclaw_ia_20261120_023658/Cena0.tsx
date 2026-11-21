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
import {ChamferRibbon} from './ChamferRibbon';

type CenaProps = {
  fontFamily: string;
};

export const Cena0: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera: push-in contínuo do fundo
  const bgScale = interpolate(frame, [0, 156], [1.0, 1.15], {
    extrapolateRight: 'clamp',
  });
  const bgRotate = interpolate(frame, [0, 156], [0, 1.2], {
    extrapolateRight: 'clamp',
  });

  // Entrada rápida do Ribbon de topo (imediatamente no primeiro segundo)
  const ribbonSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Entrada ágil do Card 1: Chatbot comum (~frame 2 / 0.07s)
  const card1Spring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada escalonada do conector central "OU" aos 1.82s (frame 54) na virada da locução
  const vsSpring = spring({
    frame: frame - 54,
    fps,
    config: {damping: 11, stiffness: 140},
  });

  // Entrada escalonada com scale pop do Card 2 (Inovare Claw) aos 1.93s (frame 58)
  const card2Spring = spring({
    frame: frame - 58,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Micro-movimento contínuo: slow push-in nos cartões comparativos para retenção visual
  const cardsPushIn = interpolate(frame, [0, 156], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Transição de foco do Card 1: sobe sutilmente e reduz opacidade para dar destaque total ao Inovare Claw
  const card1Focus = interpolate(frame, [54, 70], [1, 0.45], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const card1OffsetY = interpolate(frame, [54, 70], [0, -15], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const card1Scale = interpolate(frame, [54, 70], [1, 0.95], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Pulso ativo e contínuo de brilho neon (roxo + verde) e leve scale heartbeat no Card 2
  const card2Glow = Math.sin(frame * 0.16) * 16 + 32;
  const card2Pulse = frame >= 58 ? 1 + Math.sin((frame - 58) * 0.15) * 0.025 : 1;

  // Saída suave da cena nos últimos 12 frames
  const sceneOpacity = interpolate(frame, [144, 156], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#0B0D13'}}>
      {/* Imagem de Fundo com zoom contínuo */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) rotate(${bgRotate}deg)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(0.65) contrast(1.1)',
          }}
        />
        {/* Overlay escuro protetor */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(124, 58, 237, 0.25) 0%, rgba(11, 13, 19, 0.85) 75%)',
          }}
        />
      </AbsoluteFill>

      {/* Grid sutil tecnológico */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
          opacity: 0.6,
          pointerEvents: 'none',
        }}
      />

      {/* Topo Informativo (y = 175) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `translateY(${interpolate(ribbonSpring, [0, 1], [-40, 0])}px)`,
          opacity: ribbonSpring,
        }}
      >
        <ChamferRibbon
          step="DÚVIDA"
          title="CHATBOT VS AGENTE AUTÔNOMO"
          fontFamily={fontFamily}
          accentColor="#7C3AED"
        />
      </div>

      {/* Centro: Comparativo Dramático e Cinético com slow push-in contínuo */}
      <div
        style={{
          position: 'absolute',
          top: 290,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 20,
          transform: `scale(${cardsPushIn})`,
          transformOrigin: 'center center',
        }}
      >
        {/* Card 1: O Chatbot Comum (Entra primeiro; gancho exclusivo dos primeiros 1.8s) */}
        <div
          style={{
            width: '100%',
            maxWidth: 960,
            background: 'rgba(15, 23, 42, 0.94)',
            borderRadius: 24,
            padding: '28px 36px',
            border: '2px solid rgba(148, 163, 184, 0.35)',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.65)',
            transform: `translateY(${interpolate(card1Spring, [0, 1], [60, 0]) + card1OffsetY}px) scale(${interpolate(card1Spring, [0, 1], [0.92, 1]) * card1Scale})`,
            opacity: interpolate(card1Spring, [0, 1], [0, 1]) * card1Focus,
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#E2E8F0',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              CHATBOT TRADICIONAL
            </div>
            <div
              style={{
                padding: '6px 18px',
                background: 'rgba(239, 68, 68, 0.35)',
                borderRadius: 12,
                border: '1.5px solid #EF4444',
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                textShadow: '0 0 10px rgba(239, 68, 68, 0.8)',
              }}
            >
              LIMITADO
            </div>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 52,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.15,
            }}
          >
            SÓ RESPONDE PERGUNTAS
          </div>

          <div
            style={{
              background: 'rgba(0, 0, 0, 0.45)',
              padding: '16px 20px',
              borderRadius: 14,
              borderLeft: '4px solid #F59E0B',
              fontFamily,
              fontSize: 34,
              fontWeight: 600,
              color: '#E2E8F0',
            }}
          >
            💬 "Aqui está um roteiro. Agora você executa."
          </div>
        </div>

        {/* Separador animado "OU" — Surge aos 1.82s (frame 54) com scale pop */}
        {frame >= 54 && (
          <div
            style={{
              transform: `scale(${vsSpring})`,
              opacity: vsSpring,
              width: 76,
              height: 76,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #7C3AED, #4F46E5)',
              boxShadow: '0 0 30px rgba(124, 58, 237, 0.9)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily,
              fontSize: 36,
              fontWeight: 900,
              color: '#FFFFFF',
              zIndex: 10,
            }}
          >
            OU
          </div>
        )}

        {/* Card 2: Inovare Claw — Surge aos 1.93s (frame 58) com scale pop e pulso neon vibrante */}
        {frame >= 58 && (
          <div
            style={{
              width: '100%',
              maxWidth: 960,
              background: 'linear-gradient(180deg, rgba(24, 18, 43, 0.98) 0%, rgba(15, 23, 42, 0.98) 100%)',
              borderRadius: 24,
              padding: '32px 36px',
              border: '2.5px solid #7C3AED',
              boxShadow: `0 20px 50px rgba(0, 0, 0, 0.8), 0 0 ${card2Glow}px rgba(124, 58, 237, 0.75), 0 0 25px rgba(16, 185, 129, 0.35)`,
              transform: `translateY(${interpolate(card2Spring, [0, 1], [60, 0])}px) scale(${interpolate(card2Spring, [0, 1], [0.92, 1]) * card2Pulse})`,
              opacity: card2Spring,
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#C4B5FD',
                  letterSpacing: 2,
                  textTransform: 'uppercase',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <span>⚡ INOVARE CLAW</span>
              </div>
              <div
                style={{
                  padding: '6px 16px',
                  background: 'rgba(16, 185, 129, 0.2)',
                  borderRadius: 12,
                  border: '1.5px solid rgba(16, 185, 129, 0.5)',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#34D399',
                }}
              >
                AUTÔNOMO
              </div>
            </div>

            <div
              style={{
                fontFamily,
                fontSize: 54,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.15,
              }}
            >
              REALMENTE FAZ O TRABALHO
            </div>

            <div
              style={{
                background: 'rgba(124, 58, 237, 0.25)',
                padding: '16px 20px',
                borderRadius: 14,
                borderLeft: '4px solid #10B981',
                fontFamily,
                fontSize: 34,
                fontWeight: 700,
                color: '#F1F5F9',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
              }}
            >
              <span style={{color: '#10B981'}}>✓</span>
              <span>Você passa a tarefa e ele executa por você</span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
