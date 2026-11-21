import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {ChamferRibbon} from './ChamferRibbon';

type CenaProps = {
  fontFamily: string;
};

export const Cena3: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Diferenciação total da Cena 1: enquadramento mais dinâmico com close-up inicial (1.18x)
  // e corte de escala / punch-in (1.28x) na virada para "Meu agente de IA trabalha sozinho" (~frame 165)
  const isPunchIn = frame >= 165;
  const videoScale = isPunchIn
    ? interpolate(frame, [165, 246], [1.28, 1.32], {extrapolateRight: 'clamp'})
    : interpolate(frame, [0, 165], [1.16, 1.20], {extrapolateRight: 'clamp'});

  // Rebaixamento seguro de 80px/90px para garantir amplo respiro e nunca cobrir o topo da cabeça ou cabelo
  const videoTranslateY = isPunchIn ? 80 : 90;

  // Entrada do badge no topo (0.2s)
  const ribbonSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Card A (0.5s -> frame 15)
  const cardASpring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Elementos gráficos de apoio animados: surgem ao lado do apresentador para quebrar monotonia
  // Badge 1 ao falar "delego a tarefa" (~frame 25)
  const badge1Spring = spring({
    frame: frame - 25,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Badge 2 ao falar "cuidando do meu negócio" (~frame 75)
  const badge2Spring = spring({
    frame: frame - 75,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Transição fluida com slide-up e fade do Card A para Card B aos ~26.0s (frame 160 a 172)
  const cardBSwitch = interpolate(frame, [160, 172], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Saída suave no final da cena
  const sceneOpacity = interpolate(frame, [236, 246], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#0B0D13'}}>
      {/* Vídeo do Dono em Tela Cheia com close-up inicial, corte de escala e rebaixamento seguro */}
      <AbsoluteFill
        style={{
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: '50% 30%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </AbsoluteFill>

      {/* Gradiente escuro no topo para proteger leitura (sem escurecer o rosto) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 380,
          background: 'linear-gradient(180deg, rgba(11, 13, 19, 0.85) 0%, rgba(11, 13, 19, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Gradiente sutil na base para proteger karaokê */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 380,
          background: 'linear-gradient(0deg, rgba(11, 13, 19, 0.85) 0%, rgba(11, 13, 19, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo Informativo (y = 155) — Exclusivo na faixa livre superior */}
      <div
        style={{
          position: 'absolute',
          top: 155,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `translateY(${interpolate(ribbonSpring, [0, 1], [-30, 0])}px)`,
          opacity: ribbonSpring,
          zIndex: 20,
        }}
      >
        <ChamferRibbon
          step="03"
          title="O RESULTADO"
          fontFamily={fontFamily}
          accentColor="#10B981"
          bgColor="#0F172A"
        />
      </div>

      {/* Card Dinâmico no Topo (y = 205) — Amplo respiro (headroom > 20%) em relação ao apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 205,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 20,
        }}
      >
        {/* Bloco 1 (Fase A: "Delego a tarefa e sigo cuidando do meu negócio") */}
        <div
          style={{
            position: 'absolute',
            width: '100%',
            maxWidth: 960,
            background: 'rgba(15, 23, 42, 0.94)',
            borderRadius: 20,
            padding: '12px 24px',
            border: '1.5px solid rgba(16, 185, 129, 0.45)',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.75)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 4,
            transform: `translateY(${interpolate(cardASpring, [0, 1], [20, 0]) - interpolate(cardBSwitch, [0, 1], [0, 30])}px)`,
            opacity: interpolate(cardASpring, [0, 1], [0, 1]) * (1 - cardBSwitch),
            pointerEvents: 'none',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 0.5,
              textAlign: 'center',
              whiteSpace: 'nowrap',
            }}
          >
            DELEGO A TAREFA E CUIDO DO NEGÓCIO
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              color: '#34D399',
              textAlign: 'center',
            }}
          >
            ✓ Foco total no crescimento da sua empresa
          </div>
        </div>

        {/* Bloco 2 (Fase B: "Meu agente de IA trabalha sozinho") — Título em linha única e branco puro */}
        <div
          style={{
            position: 'absolute',
            width: '100%',
            maxWidth: 960,
            background: 'rgba(15, 23, 42, 0.94)',
            borderRadius: 20,
            padding: '12px 24px',
            border: '1.5px solid rgba(124, 58, 237, 0.6)',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.75)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 4,
            transform: `translateY(${interpolate(cardBSwitch, [0, 1], [30, 0])}px)`,
            opacity: cardBSwitch,
            pointerEvents: 'none',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 0.5,
              textAlign: 'center',
              whiteSpace: 'nowrap',
              textShadow: '0 4px 14px rgba(0, 0, 0, 0.8), 0 0 20px rgba(124, 58, 237, 0.5)',
            }}
          >
            MEU AGENTE DE IA TRABALHA SOZINHO
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              color: '#CBD5E1',
              textAlign: 'center',
            }}
          >
            ⚡ Autonomia real para executar o que você precisa
          </div>
        </div>
      </div>

      {/* Elementos Gráficos Flutuantes de Apoio — Diferenciação dinâmica da Cena 3 (quebra de monotonia) */}
      {/* Badge 1: Tarefa Delegada (entra aos 21.5s / frame 25) */}
      {frame >= 25 && frame < 165 && (
        <div
          style={{
            position: 'absolute',
            top: 860,
            left: 60,
            background: 'rgba(15, 23, 42, 0.94)',
            borderRadius: 20,
            padding: '14px 22px',
            border: '1.5px solid rgba(16, 185, 129, 0.55)',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.7), 0 0 20px rgba(16, 185, 129, 0.25)',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            transform: `scale(${badge1Spring}) translateY(${interpolate(badge1Spring, [0, 1], [30, 0])}px)`,
            opacity: badge1Spring,
            zIndex: 25,
          }}
        >
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: '50%',
              background: 'rgba(16, 185, 129, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 24,
              color: '#34D399',
              fontWeight: 900,
            }}
          >
            ✓
          </div>
          <div>
            <div style={{fontFamily, fontSize: 32, fontWeight: 900, color: '#34D399'}}>
              TAREFA DELEGADA
            </div>
            <div style={{fontFamily, fontSize: 32, fontWeight: 600, color: '#F1F5F9'}}>
              Agente executando sozinho
            </div>
          </div>
        </div>
      )}

      {/* Badge 2: Foco no Negócio (entra aos 23.2s / frame 75) */}
      {frame >= 75 && frame < 165 && (
        <div
          style={{
            position: 'absolute',
            top: 1010,
            right: 60,
            background: 'rgba(15, 23, 42, 0.94)',
            borderRadius: 20,
            padding: '14px 22px',
            border: '1.5px solid rgba(124, 58, 237, 0.55)',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.7), 0 0 20px rgba(124, 58, 237, 0.25)',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            transform: `scale(${badge2Spring}) translateY(${interpolate(badge2Spring, [0, 1], [30, 0])}px)`,
            opacity: badge2Spring,
            zIndex: 25,
          }}
        >
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: '50%',
              background: 'rgba(124, 58, 237, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 24,
              color: '#A78BFA',
              fontWeight: 900,
            }}
          >
            ⚡
          </div>
          <div>
            <div style={{fontFamily, fontSize: 32, fontWeight: 900, color: '#A78BFA'}}>
              FOCO NO NEGÓCIO
            </div>
            <div style={{fontFamily, fontSize: 32, fontWeight: 600, color: '#F1F5F9'}}>
              Autonomia total na rotina
            </div>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
