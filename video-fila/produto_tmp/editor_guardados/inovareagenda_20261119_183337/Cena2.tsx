import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Ritmo de edição dinâmico: plano fechado focado com punch-in zoom (1.14x -> 1.18x) diferenciando da cena anterior
  const videoScale = interpolate(frame, [0, 80, 246], [1.14, 1.16, 1.18], {
    extrapolateRight: 'clamp',
  });

  // Badge topo: Como Funciona
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Fluxo de Etapas (aparece aos 14.1s -> frame 28)
  const stepsContainerSpring = spring({
    frame: frame - 28,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Ativação escalonada individual das 3 etapas perfeitamente sincronizada com a locução:
  // 1. "agenda" aos 15.735s (local frame 79) -> acende com scale pop 1.12 -> 1.0
  const step1Active = frame >= 79;
  const step1Pop = spring({
    frame: frame - 79,
    fps,
    config: {damping: 12, stiffness: 180},
  });

  // 2. "confirma" aos 16.175s (local frame 93) -> acende com scale pop 1.12 -> 1.0
  const step2Active = frame >= 93;
  const step2Pop = spring({
    frame: frame - 93,
    fps,
    config: {damping: 12, stiffness: 180},
  });

  // 3. "reagenda" aos 17.135s (local frame 121) -> acende com scale pop 1.12 -> 1.0 na fala "e reagenda"
  const step3Active = frame >= 121;
  const step3Pop = spring({
    frame: frame - 121,
    fps,
    config: {damping: 12, stiffness: 180},
  });

  // Transição coordenada e fluida: as 3 etapas saem suavemente para cima (frames 166-172)
  const stepsExitOpacity = interpolate(frame, [166, 172], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stepsExitY = interpolate(frame, [166, 172], [0, -25], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Demonstração da Prova da Ferramenta (Mockup WhatsApp com layout compacto e alto contraste)
  // Entra suavemente aos 18.8s (frame 172) na fala "direto no WhatsApp" ocupando o topo com respiro amplo
  const zapDemoSpring = spring({
    frame: frame - 172,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Balão de resposta da IA entra com spring aos ~18.8s (frame 182) na fala "sem conflito"
  const aiBubbleSpring = spring({
    frame: frame - 182,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Transição de saída suave nos últimos 8 frames
  const exitOpacity = interpolate(frame, [238, 246], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        opacity: exitOpacity,
      }}
    >
      {/* Vídeo do apresentador com punch-in focado de 15% e rebaixado para respiro visual de 200px acima da cabeça */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale}) translateY(105px)`,
          transformOrigin: '50% 45%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_2.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Degradê superior escuro garantindo contraste e foco na demonstração */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 520,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.94) 0%, rgba(15, 23, 42, 0.72) 75%, rgba(15, 23, 42, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo Seguro (y=165 a 215): Badge */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: badgeSpring,
          transform: `translateY(${(1 - badgeSpring) * -20}px)`,
          zIndex: 10,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 999,
            backgroundColor: 'rgba(15, 23, 42, 0.94)',
            border: '2px solid rgba(245, 158, 11, 0.6)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
          }}
        >
          <span style={{fontSize: 32}}>⚡</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#F59E0B',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            Como Funciona • Automação com IA
          </span>
        </div>
      </div>

      {/* Faixa das 3 Etapas Sequenciais (y=230 a 295) com acendimento escalonado e transição suave aos 172 frames */}
      {frame >= 28 && frame <= 172 && (
        <div
          style={{
            position: 'absolute',
            top: 230,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            gap: 14,
            opacity: stepsContainerSpring * stepsExitOpacity,
            transform: `translateY(${
              (1 - stepsContainerSpring) * 15 + stepsExitY
            }px)`,
            zIndex: 10,
          }}
        >
          {/* Etapa 1: Agenda (acende no frame 79 na palavra "agenda") */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '12px 10px',
              borderRadius: 18,
              backgroundColor: step1Active
                ? '#F59E0B'
                : 'rgba(30, 41, 59, 0.95)',
              border: step1Active
                ? '2px solid #FDE68A'
                : '1.5px solid rgba(255, 255, 255, 0.35)',
              boxShadow: step1Active
                ? '0 10px 28px rgba(245, 158, 11, 0.5)'
                : 'none',
              transform: step1Active
                ? `scale(${interpolate(step1Pop, [0, 1], [1.12, 1.0])})`
                : 'scale(1)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: step1Active ? '#121216' : '#FFFFFF',
                opacity: step1Active ? 1 : 0.92,
                letterSpacing: 0.5,
              }}
            >
              {step1Active ? '✓ 1. AGENDA' : '1. AGENDA'}
            </span>
          </div>

          {/* Etapa 2: Confirma (acende no frame 93 na palavra "confirma") */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '12px 10px',
              borderRadius: 18,
              backgroundColor: step2Active
                ? '#F59E0B'
                : 'rgba(30, 41, 59, 0.95)',
              border: step2Active
                ? '2px solid #FDE68A'
                : '1.5px solid rgba(255, 255, 255, 0.35)',
              boxShadow: step2Active
                ? '0 10px 28px rgba(245, 158, 11, 0.5)'
                : 'none',
              transform: step2Active
                ? `scale(${interpolate(step2Pop, [0, 1], [1.12, 1.0])})`
                : 'scale(1)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: step2Active ? '#121216' : '#FFFFFF',
                opacity: step2Active ? 1 : 0.92,
                letterSpacing: 0.5,
              }}
            >
              {step2Active ? '✓ 2. CONFIRMA' : '2. CONFIRMA'}
            </span>
          </div>

          {/* Etapa 3: Reagenda (acende no frame 121 na palavra "reagenda") */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '12px 10px',
              borderRadius: 18,
              backgroundColor: step3Active
                ? '#F59E0B'
                : 'rgba(30, 41, 59, 0.95)',
              border: step3Active
                ? '2px solid #FDE68A'
                : '1.5px solid rgba(255, 255, 255, 0.35)',
              boxShadow: step3Active
                ? '0 10px 28px rgba(245, 158, 11, 0.5)'
                : 'none',
              transform: step3Active
                ? `scale(${interpolate(step3Pop, [0, 1], [1.12, 1.0])})`
                : 'scale(1)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: step3Active ? '#121216' : '#FFFFFF',
                opacity: step3Active ? 1 : 0.92,
                letterSpacing: 0.5,
              }}
            >
              {step3Active ? '✓ 3. REAGENDA' : '3. REAGENDA'}
            </span>
          </div>
        </div>
      )}

      {/* Demonstração Prática com Protagonismo: Mockup de WhatsApp compacto e fiel (y=226 a 445) */}
      {/* Sincronizado exatamente com a fala "direto no WhatsApp" (frame 172) com amplo respiro acima da cabeça */}
      {frame >= 172 && (
        <div
          style={{
            position: 'absolute',
            top: 226,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: zapDemoSpring,
            transform: `scale(${interpolate(zapDemoSpring, [0, 1], [0.92, 1])}) translateY(${(1 - zapDemoSpring) * 15}px)`,
            zIndex: 10,
          }}
        >
          <div
            style={{
              width: 940,
              borderRadius: 20,
              backgroundColor: '#0B141A',
              border: '2px solid rgba(34, 197, 94, 0.65)',
              boxShadow:
                '0 14px 36px rgba(0, 0, 0, 0.9), 0 0 24px rgba(34, 197, 94, 0.25)',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Header oficial do WhatsApp Dark compacto */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '8px 18px',
                backgroundColor: '#1F2C34',
                borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <span style={{fontSize: 24, color: '#A0B0BA'}}>←</span>
                <div
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: '50%',
                    backgroundColor: '#00A884',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 22,
                  }}
                >
                  🤖
                </div>
                <div style={{display: 'flex', flexDirection: 'column'}}>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 30,
                      fontWeight: 800,
                      color: '#E9EDEF',
                      lineHeight: 1.1,
                    }}
                  >
                    Inovare Agenda IA
                  </span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 22,
                      fontWeight: 500,
                      color: '#00A884',
                    }}
                  >
                    Online • Reagendamento automático
                  </span>
                </div>
              </div>

              {/* Selo Simulação regulamentar */}
              <div
                style={{
                  padding: '3px 12px',
                  borderRadius: 999,
                  backgroundColor: 'rgba(245, 158, 11, 0.15)',
                  border: '1px solid rgba(245, 158, 11, 0.6)',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 24,
                    fontWeight: 800,
                    color: '#FDE68A',
                  }}
                >
                  Simulação
                </span>
              </div>
            </div>

            {/* Área de mensagens do WhatsApp demonstrando o reagendamento automático */}
            <div
              style={{
                padding: '12px 18px',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
                backgroundColor: '#0B141A',
              }}
            >
              {/* Balão 1 (Cliente): Pedido de reagendamento */}
              <div
                style={{
                  alignSelf: 'flex-start',
                  backgroundColor: '#202C33',
                  padding: '8px 16px',
                  borderRadius: '14px 14px 14px 4px',
                  boxShadow: '0 2px 6px rgba(0, 0, 0, 0.4)',
                  maxWidth: '78%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 2,
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 30,
                    fontWeight: 600,
                    color: '#E9EDEF',
                  }}
                >
                  Preciso reagendar meu horário
                </span>
                <span
                  style={{
                    alignSelf: 'flex-end',
                    fontFamily,
                    fontSize: 20,
                    fontWeight: 500,
                    color: '#8696A0',
                  }}
                >
                  14:30
                </span>
              </div>

              {/* Balão 2 (Agenda IA): Confirmação de reagendamento sem conflito */}
              {frame >= 182 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    backgroundColor: '#005C4B',
                    padding: '8px 16px',
                    borderRadius: '14px 14px 4px 14px',
                    boxShadow: '0 4px 12px rgba(0, 92, 75, 0.5)',
                    maxWidth: '85%',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2,
                    opacity: aiBubbleSpring,
                    transform: `scale(${interpolate(aiBubbleSpring, [0, 1], [0.9, 1])})`,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 30,
                      fontWeight: 800,
                      color: '#E9EDEF',
                    }}
                  >
                    ✓ Reagendado! Sem conflito de horário.
                  </span>
                  <div
                    style={{
                      alignSelf: 'flex-end',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                    }}
                  >
                    <span
                      style={{
                        fontFamily,
                        fontSize: 20,
                        fontWeight: 500,
                        color: 'rgba(233, 237, 239, 0.7)',
                      }}
                    >
                      14:30
                    </span>
                    <span
                      style={{
                        fontSize: 18,
                        color: '#53BDEB',
                        fontWeight: 900,
                      }}
                    >
                      ✓✓
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

