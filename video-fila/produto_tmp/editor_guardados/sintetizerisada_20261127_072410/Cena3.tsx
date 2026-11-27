import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {FONT_FAMILY, THEME} from './theme';

// Cena 3: ini 20.83, fim 29.80 (duração 8.97s -> 269 frames)
// Fala: "Sem conflito e sem duplo agendamento, a agenda fica organizada dia e noite, por uma fração do custo de uma recepção humana."

export const Cena3: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera no dashboard tecnológico (>= 4% de movimento)
  const bgScale = interpolate(frame, [0, 269], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 269], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Top Badge
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // FASE 1: Interface animada de Agenda / Dashboard (frames 0 a 105)
  // Substitui a lista estática de slides por visual de software inteligente preenchendo horários
  const agendaSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const slot1Spring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const slot2Spring = spring({
    frame: frame - 44,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const slot3Spring = spring({
    frame: frame - 72,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Transição suave de saída da agenda conectando com o comparativo de valor
  const phase1Opacity = interpolate(frame, [92, 106], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const phase1TranslateX = interpolate(frame, [92, 106], [0, -50], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // FASE 2: Card Hero de Ancoragem de Valor (R$ 2.500 vs R$ 199)
  // Entra com spring suave e ocupa o centro durante toda a fala sobre fração de custo (> 5.5 segundos)
  const isComparativo = frame >= 96;
  const compSpring = spring({
    frame: frame - 98,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  const pulse = Math.sin((frame - 98) * 0.22) * 0.025;

  return (
    <AbsoluteFill style={{backgroundColor: THEME.colors.darkBg, overflow: 'hidden'}}>
      {/* Background: Dashboard moderno de sistema SaaS com preenchimento de agenda inteligente */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
          background: 'linear-gradient(180deg, #070B14 0%, #0D1527 50%, #070B14 100%)',
        }}
      >
        {/* Grade tecnológica de fundo */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)',
            backgroundSize: '48px 48px',
          }}
        />

        {/* Glows de iluminação suave em degradê */}
        <div
          style={{
            position: 'absolute',
            top: '25%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 800,
            height: 500,
            background: 'radial-gradient(circle, rgba(255,169,77,0.12) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: '30%',
            left: '50%',
            transform: 'translate(-50%, 50%)',
            width: 850,
            height: 550,
            background: 'radial-gradient(circle, rgba(16,185,129,0.09) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Conteúdo na Safe Zone */}
      <div
        style={{
          position: 'absolute',
          top: THEME.safeZone.top + 15,
          left: THEME.safeZone.left,
          right: THEME.safeZone.left,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily: FONT_FAMILY,
          zIndex: 10,
        }}
      >
        {/* Top Badge */}
        {frame >= 4 && (
          <div
            style={{
              transform: `translateY(${(1 - badgeSpring) * -15}px)`,
              background: '#111827F5',
              border: `1.5px solid ${THEME.colors.primary}`,
              borderRadius: 24,
              padding: '6px 22px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
              marginBottom: 20,
            }}
          >
            <span style={{fontSize: 28}}>✨</span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: THEME.colors.primary,
                letterSpacing: 1.2,
                textTransform: 'uppercase',
              }}
            >
              O Resultado • Eficiência Total
            </span>
          </div>
        )}

        {/* FASE 1: Agenda Dinâmica Inteligente preenchendo horários automaticamente (frames 0 a 105) */}
        {frame < 106 && (
          <div
            style={{
              width: 840,
              opacity: phase1Opacity,
              transform: `translateX(${phase1TranslateX}px) scale(${agendaSpring})`,
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
            }}
          >
            {/* Cabeçalho do Card da Agenda */}
            <div
              style={{
                background: '#131B2EF5',
                border: '2px solid rgba(255,255,255,0.15)',
                borderRadius: 24,
                padding: '20px 24px',
                boxShadow: '0 12px 32px rgba(0,0,0,0.7)',
                display: 'flex',
                flexDirection: 'column',
                gap: 14,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderBottom: '1px solid rgba(255,255,255,0.1)',
                  paddingBottom: 12,
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                  <span style={{fontSize: 30}}>🗓️</span>
                  <span style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                    Agenda Inteligente IA
                  </span>
                </div>
                <div
                  style={{
                    background: '#064E3BCC',
                    border: '1.5px solid #10B981',
                    borderRadius: 12,
                    padding: '4px 14px',
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#6EE7B7',
                  }}
                >
                  Tempo Real
                </div>
              </div>

              {/* Horário 1: Zero Conflito */}
              {frame >= 16 && (
                <div
                  style={{
                    background: '#1E293BCC',
                    border: '1.5px solid #10B981',
                    borderRadius: 16,
                    padding: '14px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transform: `translateY(${(1 - slot1Spring) * 15}px)`,
                  }}
                >
                  <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                    <span style={{fontSize: 30, color: '#34D399', fontWeight: 900}}>✓</span>
                    <div>
                      <div style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                        14:00 • Mariana Costa
                      </div>
                      <div style={{fontSize: 32, color: '#94A3B8', fontWeight: 600}}>
                        Confirmado automaticamente
                      </div>
                    </div>
                  </div>
                  <div
                    style={{
                      background: '#064E3B',
                      color: '#6EE7B7',
                      padding: '4px 12px',
                      borderRadius: 8,
                      fontSize: 32,
                      fontWeight: 800,
                    }}
                  >
                    Sem Conflito
                  </div>
                </div>
              )}

              {/* Horário 2: Sem Duplo Agendamento */}
              {frame >= 44 && (
                <div
                  style={{
                    background: '#1E293BCC',
                    border: '1.5px solid #10B981',
                    borderRadius: 16,
                    padding: '14px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transform: `translateY(${(1 - slot2Spring) * 15}px)`,
                  }}
                >
                  <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                    <span style={{fontSize: 30, color: '#34D399', fontWeight: 900}}>🔒</span>
                    <div>
                      <div style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                        15:00 • Vaga Bloqueada
                      </div>
                      <div style={{fontSize: 32, color: '#94A3B8', fontWeight: 600}}>
                        Reserva exclusiva no sistema
                      </div>
                    </div>
                  </div>
                  <div
                    style={{
                      background: '#064E3B',
                      color: '#6EE7B7',
                      padding: '4px 12px',
                      borderRadius: 8,
                      fontSize: 32,
                      fontWeight: 800,
                    }}
                  >
                    1º a Escolher
                  </div>
                </div>
              )}

              {/* Horário 3: Organizada Dia e Noite 24h */}
              {frame >= 72 && (
                <div
                  style={{
                    background: '#1E293BCC',
                    border: `1.5px solid ${THEME.colors.primary}`,
                    borderRadius: 16,
                    padding: '14px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transform: `translateY(${(1 - slot3Spring) * 15}px)`,
                  }}
                >
                  <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                    <span style={{fontSize: 30}}>🌙</span>
                    <div>
                      <div style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                        Atendimento 24h
                      </div>
                      <div style={{fontSize: 32, color: THEME.colors.primary, fontWeight: 600}}>
                        Organizada dia e noite
                      </div>
                    </div>
                  </div>
                  <div
                    style={{
                      background: '#78350F',
                      color: THEME.colors.primary,
                      padding: '4px 12px',
                      borderRadius: 8,
                      fontSize: 32,
                      fontWeight: 800,
                    }}
                  >
                    24 Horas
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* FASE 2: Comparativo Hero de Ancoragem de Valor (R$ 2.500 riscado vs R$ 199) */}
        {isComparativo && (
          <div
            style={{
              width: 840,
              background: '#0B0F19FA',
              borderRadius: 28,
              border: `2.5px solid ${THEME.colors.primary}`,
              padding: '28px 24px',
              display: 'flex',
              flexDirection: 'column',
              gap: 20,
              boxShadow: '0 20px 50px rgba(0,0,0,0.95), 0 0 40px rgba(255,169,77,0.25)',
              transform: `scale(${compSpring})`,
            }}
          >
            {/* Header de Comparação */}
            <div
              style={{
                textAlign: 'center',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 12,
              }}
            >
              <span style={{fontSize: 30}}>⚡</span>
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: THEME.colors.primary,
                  textTransform: 'uppercase',
                  letterSpacing: 1.2,
                }}
              >
                Fração do Custo Tradicional
              </span>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'stretch',
                gap: 18,
              }}
            >
              {/* Opção Tradicional: Recepção Humana */}
              <div
                style={{
                  flex: 1,
                  background: '#1F2937EE',
                  borderRadius: 20,
                  padding: '22px 16px',
                  textAlign: 'center',
                  border: '1.5px solid rgba(255,255,255,0.12)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                }}
              >
                <div style={{fontSize: 34, fontWeight: 700, color: '#94A3B8'}}>
                  Recepção Humana
                </div>
                <div
                  style={{
                    fontSize: 48,
                    fontWeight: 900,
                    color: '#EF4444',
                    textDecoration: 'line-through',
                    marginTop: 10,
                  }}
                >
                  R$ 2.500
                </div>
                {/* Texto com alto contraste (#CBD5E1) corrigindo q12 */}
                <div
                  style={{
                    fontSize: 32,
                    color: '#CBD5E1',
                    marginTop: 6,
                    fontWeight: 700,
                  }}
                >
                  custo por mês
                </div>
              </div>

              {/* Solução Agenda IA */}
              <div
                style={{
                  flex: 1.2,
                  background: 'linear-gradient(145deg, #1E1B4B, #0F172A)',
                  borderRadius: 20,
                  padding: '22px 16px',
                  textAlign: 'center',
                  border: `2.5px solid ${THEME.colors.primary}`,
                  boxShadow: '0 0 30px rgba(255,169,77,0.45)',
                  transform: `scale(${1 + pulse})`,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                }}
              >
                <div
                  style={{
                    fontSize: 36,
                    fontWeight: 800,
                    color: THEME.colors.primary,
                  }}
                >
                  Agenda IA 24h
                </div>
                <div
                  style={{
                    fontSize: 50,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    marginTop: 8,
                  }}
                >
                  A partir de R$ 199
                </div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#34D399',
                    marginTop: 6,
                  }}
                >
                  Economia máxima
                </div>
              </div>
            </div>

            {/* Destaque gráfico de economia */}
            <div
              style={{
                background: '#064E3BCC',
                border: '1.5px solid #10B981',
                borderRadius: 16,
                padding: '12px 20px',
                textAlign: 'center',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 12,
              }}
            >
              <span style={{fontSize: 28}}>💰</span>
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#6EE7B7',
                  textTransform: 'uppercase',
                  letterSpacing: 0.5,
                }}
              >
                Trabalha 24h por uma fração do custo
              </span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
