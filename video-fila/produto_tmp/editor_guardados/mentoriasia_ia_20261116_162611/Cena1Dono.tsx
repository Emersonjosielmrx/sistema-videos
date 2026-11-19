import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig
} from 'remotion';
import {BRIEFING} from './data';

export const Cena1Dono: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fala do dono:
  // 5.24s a 8.16s: "Eu não sabia qual tarefa automatizar primeiro," (Dor)
  // 8.76s a 11.86s: "até usar o mapa mental para estruturar minhas ideias." (Solução)
  // Virada suave aos ~8.6s absolutos -> frame 112 da cena
  const viradaFrame = 112;
  const isSolucao = frame >= viradaFrame;

  // Push contínuo suave (1.00 -> 1.06)
  const videoScale = interpolate(frame, [0, 235], [1.0, 1.06], {
    extrapolateRight: 'clamp'
  });

  // Entrada do bloco do topo
  const introSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120}
  });

  // Transição suave (fade out / fade in) entre Fase 1 (O Desafio) e Fase 2 (A Virada)
  const fadePhase1 = interpolate(frame, [viradaFrame - 8, viradaFrame], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });
  const fadePhase2 = interpolate(frame, [viradaFrame, viradaFrame + 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });

  // Entrada do card de fluxo integrado no terço lateral direito (safely longe do rosto/têmpora!)
  const sideCardSpring1 = spring({
    frame: frame - 16,
    fps,
    config: {damping: 14, stiffness: 110}
  });

  const sideCardSpring2 = spring({
    frame: frame - (viradaFrame + 6),
    fps,
    config: {damping: 14, stiffness: 110}
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#000000', overflow: 'hidden'}}>
      {/* 1. Vídeo do Dono em tela cheia com push contínuo */}
      <div
        style={{
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 42%'
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover'
          }}
        />
      </div>

      {/* 2. Vinheta superior suave para legibilidade sem escurecer o rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(180deg, rgba(10, 15, 30, 0.94) 0%, rgba(10, 15, 30, 0.65) 60%, rgba(10, 15, 30, 0) 100%)',
          pointerEvents: 'none'
        }}
      />

      {/* 3. Topo Informativo com Transição Suave (Crossfade entre O DESAFIO e A VIRADA) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
          zIndex: 50,
          transform: `scale(${introSpring})`,
          opacity: introSpring
        }}
      >
        {/* FASE 1: O DESAFIO (DOR) */}
        {fadePhase1 > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
              opacity: fadePhase1,
              transform: `translateY(${interpolate(fadePhase1, [0, 1], [-10, 0])}px)`
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 24px',
                borderRadius: 24,
                backgroundColor: 'rgba(239, 68, 68, 0.22)',
                border: '1.5px solid #EF4444',
                boxShadow: '0 4px 16px rgba(239, 68, 68, 0.35)',
                marginBottom: 12
              }}
            >
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: '#EF4444',
                  boxShadow: '0 0 8px #EF4444'
                }}
              />
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FECACA',
                  letterSpacing: '1px',
                  textTransform: 'uppercase'
                }}
              >
                O DESAFIO
              </span>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(15, 23, 42, 0.92)',
                borderRadius: 20,
                padding: '16px 28px',
                border: '1.5px solid rgba(239, 68, 68, 0.4)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.65)',
                backdropFilter: 'blur(12px)',
                textAlign: 'center',
                maxWidth: 900
              }}
            >
              <div
                style={{
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                  textTransform: 'uppercase'
                }}
              >
                QUAL TAREFA AUTOMATIZAR PRIMEIRO?
              </div>
            </div>
          </div>
        )}

        {/* FASE 2: A VIRADA: ESTRUTURAÇÃO (SOLUÇÃO) */}
        {fadePhase2 > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
              opacity: fadePhase2,
              transform: `translateY(${interpolate(fadePhase2, [0, 1], [10, 0])}px)`
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 24px',
                borderRadius: 24,
                backgroundColor: 'rgba(37, 99, 235, 0.28)',
                border: '1.5px solid #3B82F6',
                boxShadow: '0 4px 16px rgba(37, 99, 235, 0.45)',
                marginBottom: 12
              }}
            >
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: '#60A5FA',
                  boxShadow: '0 0 8px #60A5FA'
                }}
              />
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#93C5FD',
                  letterSpacing: '1px',
                  textTransform: 'uppercase'
                }}
              >
                A VIRADA: ESTRUTURAÇÃO
              </span>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(15, 23, 42, 0.92)',
                borderRadius: 20,
                padding: '16px 28px',
                border: '1.5px solid rgba(59, 130, 246, 0.45)',
                boxShadow: '0 8px 28px rgba(0, 0, 0, 0.65)',
                backdropFilter: 'blur(12px)',
                textAlign: 'center',
                maxWidth: 900
              }}
            >
              <div
                style={{
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                  textTransform: 'uppercase'
                }}
              >
                <span
                  style={{
                    backgroundColor: BRIEFING.cores.marca,
                    color: '#FFFFFF',
                    padding: '2px 14px',
                    borderRadius: 10,
                    marginRight: 8
                  }}
                >
                  MAPA MENTAL
                </span>
                PARA ESTRUTURAR IDEIAS
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 4. Elemento Gráfico Integrado no Terço Lateral (Substitui stickers soltos e afasta 100% do rosto) */}
      {/* Posicionado no terço lateral direito (x: 640..1020, y: 780..1100) — Rosto e têmpora 100% livres */}
      <div
        style={{
          position: 'absolute',
          right: 60,
          bottom: 560,
          width: 440,
          fontFamily,
          zIndex: 40
        }}
      >
        {!isSolucao ? (
          /* Card Integrado da Dor (Fase 1) */
          frame >= 16 && (
            <div
              style={{
                transform: `translateX(${interpolate(sideCardSpring1, [0, 1], [40, 0])}px)`,
                opacity: sideCardSpring1,
                backgroundColor: 'rgba(15, 23, 42, 0.94)',
                borderRadius: 20,
                padding: '16px 20px',
                border: '1.5px solid rgba(239, 68, 68, 0.45)',
                boxShadow: '0 12px 32px rgba(0, 0, 0, 0.75)',
                backdropFilter: 'blur(14px)',
                display: 'flex',
                flexDirection: 'column',
                gap: 10
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#EF4444'
                  }}
                />
                <span style={{fontSize: 32, fontWeight: 800, color: '#FECACA'}}>
                  DESAFIOS INICIAIS
                </span>
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 8}}>
                <div
                  style={{
                    backgroundColor: 'rgba(30, 41, 59, 0.9)',
                    padding: '8px 14px',
                    borderRadius: 12,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FFFFFF'
                  }}
                >
                  • Tarefas manuais dispersas
                </div>
                <div
                  style={{
                    backgroundColor: 'rgba(30, 41, 59, 0.9)',
                    padding: '8px 14px',
                    borderRadius: 12,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FFFFFF'
                  }}
                >
                  • Sem prioridade clara
                </div>
              </div>
            </div>
          )
        ) : (
          /* Card Integrado de Fluxo Estruturado (Fase 2 - Motion Graphics Elegante) */
          frame >= viradaFrame + 6 && (
            <div
              style={{
                transform: `translateX(${interpolate(sideCardSpring2, [0, 1], [40, 0])}px)`,
                opacity: sideCardSpring2,
                backgroundColor: 'rgba(15, 23, 42, 0.94)',
                borderRadius: 20,
                padding: '16px 20px',
                border: '2px solid rgba(59, 130, 246, 0.55)',
                boxShadow: '0 12px 36px rgba(0, 0, 0, 0.75)',
                backdropFilter: 'blur(14px)',
                display: 'flex',
                flexDirection: 'column',
                gap: 12
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                <span style={{fontSize: 32, fontWeight: 900, color: '#93C5FD'}}>
                  FLUXO ESTRUTURADO
                </span>
                <span
                  style={{
                    fontSize: 30,
                    fontWeight: 800,
                    padding: '2px 10px',
                    borderRadius: 8,
                    backgroundColor: 'rgba(16, 185, 129, 0.25)',
                    color: '#6EE7B7'
                  }}
                >
                  Clareza
                </span>
              </div>

              {/* Conector e nós de fluxo visual */}
              <div style={{display: 'flex', flexDirection: 'column', gap: 8}}>
                <div
                  style={{
                    backgroundColor: 'rgba(30, 41, 59, 0.92)',
                    padding: '10px 14px',
                    borderRadius: 12,
                    border: '1px solid rgba(96, 165, 250, 0.4)',
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10
                  }}
                >
                  <span>🧠</span>
                  <span>1. Mapear Ideias</span>
                </div>

                <div style={{display: 'flex', justifyContent: 'center'}}>
                  <span style={{fontSize: 26, color: '#60A5FA', fontWeight: 900}}>↓</span>
                </div>

                <div
                  style={{
                    backgroundColor: 'rgba(37, 99, 235, 0.35)',
                    padding: '10px 14px',
                    borderRadius: 12,
                    border: '1.5px solid #3B82F6',
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10
                  }}
                >
                  <span>🔗</span>
                  <span>2. Definir Prioridade</span>
                </div>
              </div>
            </div>
          )
        )}
      </div>
    </AbsoluteFill>
  );
};
