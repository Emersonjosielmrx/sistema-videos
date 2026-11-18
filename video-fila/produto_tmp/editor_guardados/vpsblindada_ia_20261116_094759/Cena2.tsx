import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Cena2: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no b-roll
  const videoScale = interpolate(frame, [0, 237], [1.04, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Tag do topo "COMO FUNCIONA" (y=155)
  const tagSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // SINCRONIA ESTRITA: Apenas UM card ativo por vez no topo, na hora exata em que a palavra é dita:
  // 1. "Junto com a VPS pronta": frame 14 a 67
  const card1Spring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const card1Out = interpolate(frame, [63, 67], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 2. "você recebe relatórios claros": frame 68 a 118
  const card2Spring = spring({
    frame: frame - 68,
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const card2Out = interpolate(frame, [114, 118], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 3. "e o robô Sentinela vigiando os erros por você": frame 118 a 230
  const card3Spring = spring({
    frame: frame - 118,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Painel de Gestão e Monitoramento: surge dinâmico aos frames 10+
  const panelSpring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Animações contínuas de sinais vitais (server heartbeat)
  const heartbeat = Math.sin(frame * 0.22) * 0.15 + 1.0;
  const radarPulse = Math.sin(frame * 0.28) * 0.12 + 1.0;
  const healthProgress = interpolate(frame, [68, 115], [0.3, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Onda de telemetria em tempo real
  const waveOffset = frame * 4.5;

  // Transição de saída aos frames 225 a 237
  const exitOpacity = interpolate(frame, [225, 237], [1, 0.3], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        opacity: exitOpacity,
      }}
    >
      {/* Vídeo B-roll de fundo com movimento lento */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: '40% 45%',
          filter: 'blur(3px)',
        }}
      >
        <OffthreadVideo
          src={staticFile('video_2.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu escuro da marca com iluminação técnica em azul ciano */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          background:
            'radial-gradient(circle at 50% 35%, rgba(15, 23, 42, 0.88) 0%, rgba(11, 15, 23, 0.98) 85%)',
          pointerEvents: 'none',
        }}
      />

      {/* Grid cyber com partículas / pulso dinâmico em loop */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 1200,
          backgroundImage:
            'linear-gradient(rgba(14, 165, 233, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(14, 165, 233, 0.08) 1px, transparent 1px)',
          backgroundSize: '44px 44px',
          opacity: 0.7 + Math.sin(frame * 0.12) * 0.15,
          pointerEvents: 'none',
        }}
      />

      {/* Elementos na safe zone (x=60 a 1020, y>=150) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 60,
          right: 60,
          height: '100%',
          pointerEvents: 'none',
        }}
      >
        {/* Rótulo da cena: "COMO FUNCIONA" (y=155) */}
        {tagSpring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 155,
              left: 0,
              right: 0,
              display: 'flex',
              justifyContent: 'center',
              transform: `scale(${Math.max(0, tagSpring)})`,
              opacity: Math.min(1, tagSpring),
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 24px',
                borderRadius: 999,
                background: 'rgba(15, 23, 42, 0.92)',
                border: '1.5px solid rgba(14, 165, 233, 0.65)',
                boxShadow: '0 4px 20px rgba(14, 165, 233, 0.3)',
              }}
            >
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: '#0EA5E9',
                  boxShadow: '0 0 10px #0EA5E9',
                }}
              />
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#38BDF8',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                }}
              >
                Como Funciona
              </span>
            </div>
          </div>
        )}

        {/* ÁREA SUPERIOR (y=215 a 380): APENAS UM CARD SUTIL E ANIMADO POR VEZ */}

        {/* 1. Card VPS Pronta (Frames 14 a 67) */}
        {frame < 68 && card1Spring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 215,
              left: 0,
              right: 0,
              transform: `translateY(${interpolate(card1Spring, [0, 1], [-25, 0])}px) scale(${Math.max(
                0,
                card1Spring
              )})`,
              opacity: Math.min(1, card1Spring) * card1Out,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid rgba(14, 165, 233, 0.7)',
                borderRadius: 20,
                padding: '16px 24px',
                boxShadow: '0 14px 34px rgba(0, 0, 0, 0.6), 0 0 20px rgba(14, 165, 233, 0.25)',
                backdropFilter: 'blur(14px)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                  <div
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: 12,
                      background: 'rgba(14, 165, 233, 0.25)',
                      border: '1.5px solid #0EA5E9',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                      <rect x="2" y="3" width="20" height="7" rx="2" stroke="#38BDF8" strokeWidth="2.2" />
                      <rect x="2" y="14" width="20" height="7" rx="2" stroke="#38BDF8" strokeWidth="2.2" />
                      <circle cx="6" cy="6.5" r="1.5" fill="#38BDF8" />
                      <circle cx="6" cy="17.5" r="1.5" fill="#38BDF8" />
                    </svg>
                  </div>
                  <span
                    style={{
                      fontSize: 40,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      textTransform: 'uppercase',
                      letterSpacing: '-0.3px',
                    }}
                  >
                    VPS Pronta & Configurada
                  </span>
                </div>
                <div
                  style={{
                    padding: '6px 18px',
                    borderRadius: 999,
                    background: 'rgba(16, 185, 129, 0.22)',
                    border: '1.5px solid #10B981',
                    color: '#34D399',
                    fontSize: 32,
                    fontWeight: 800,
                  }}
                >
                  ✓ Setup
                </div>
              </div>
              <div
                style={{
                  marginTop: 8,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#BAE6FD',
                  letterSpacing: '0.2px',
                }}
              >
                Docker • Portainer • Traefik • Backup
              </div>
            </div>
          </div>
        )}

        {/* 2. Card Relatórios Claros (Frames 68 a 118) */}
        {frame >= 65 && frame < 119 && card2Spring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 215,
              left: 0,
              right: 0,
              transform: `translateY(${interpolate(card2Spring, [0, 1], [-25, 0])}px) scale(${Math.max(
                0,
                card2Spring
              )})`,
              opacity: Math.min(1, card2Spring) * card2Out,
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid rgba(56, 189, 248, 0.7)',
                borderRadius: 20,
                padding: '16px 24px',
                boxShadow: '0 14px 34px rgba(0, 0, 0, 0.6), 0 0 20px rgba(56, 189, 248, 0.25)',
                backdropFilter: 'blur(14px)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                  <div
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: 12,
                      background: 'rgba(56, 189, 248, 0.25)',
                      border: '1.5px solid #38BDF8',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                      <path d="M3 3V21H21" stroke="#38BDF8" strokeWidth="2.2" strokeLinecap="round" />
                      <path d="M7 14L12 9L16 13L21 7" stroke="#34D399" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                  <span
                    style={{
                      fontSize: 40,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      textTransform: 'uppercase',
                      letterSpacing: '-0.3px',
                    }}
                  >
                    Relatórios Claros
                  </span>
                </div>
                <div
                  style={{
                    padding: '6px 18px',
                    borderRadius: 999,
                    background: 'rgba(14, 165, 233, 0.25)',
                    border: '1.5px solid #0EA5E9',
                    color: '#38BDF8',
                    fontSize: 32,
                    fontWeight: 800,
                  }}
                >
                  Visibilidade Total
                </div>
              </div>
              <div
                style={{
                  marginTop: 8,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#F1F5F9',
                  letterSpacing: '0.2px',
                }}
              >
                Diagnóstico visual da saúde da infraestrutura
              </div>
              {/* Barra de saúde animada */}
              <div
                style={{
                  marginTop: 10,
                  height: 10,
                  borderRadius: 5,
                  backgroundColor: 'rgba(255, 255, 255, 0.12)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${healthProgress * 100}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #0EA5E9, #10B981)',
                    boxShadow: '0 0 8px rgba(16, 185, 129, 0.8)',
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {/* 3. Card Robô Sentinela (Frames 118 a 237) */}
        {frame >= 115 && card3Spring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 215,
              left: 0,
              right: 0,
              transform: `translateY(${interpolate(card3Spring, [0, 1], [-25, 0])}px) scale(${Math.max(
                0,
                card3Spring
              )})`,
              opacity: Math.min(1, card3Spring),
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid rgba(16, 185, 129, 0.7)',
                borderRadius: 20,
                padding: '16px 24px',
                boxShadow: '0 14px 34px rgba(0, 0, 0, 0.6), 0 0 22px rgba(16, 185, 129, 0.3)',
                backdropFilter: 'blur(14px)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                  <div
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: 12,
                      background: 'rgba(16, 185, 129, 0.25)',
                      border: '1.5px solid #10B981',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      transform: `scale(${radarPulse})`,
                    }}
                  >
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                      <rect x="3" y="11" width="18" height="10" rx="2" stroke="#34D399" strokeWidth="2.2" />
                      <circle cx="8.5" cy="16" r="1.5" fill="#34D399" />
                      <circle cx="15.5" cy="16" r="1.5" fill="#34D399" />
                      <path d="M12 2V7M9 7H15" stroke="#34D399" strokeWidth="2.2" strokeLinecap="round" />
                    </svg>
                  </div>
                  <span
                    style={{
                      fontSize: 40,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      textTransform: 'uppercase',
                      letterSpacing: '-0.3px',
                    }}
                  >
                    Robô Sentinela
                  </span>
                </div>
                <div
                  style={{
                    padding: '6px 18px',
                    borderRadius: 999,
                    background: 'rgba(16, 185, 129, 0.25)',
                    border: '1.5px solid #10B981',
                    color: '#34D399',
                    fontSize: 32,
                    fontWeight: 800,
                  }}
                >
                  ● Vigia Ativo
                </div>
              </div>
              <div
                style={{
                  marginTop: 8,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#A7F3D0',
                  letterSpacing: '0.2px',
                }}
              >
                Vigiando os erros por você • Alertas automáticos
              </div>
            </div>
          </div>
        )}

        {/* ÁREA CENTRAL (y=400 a 1050): PAINEL REAL E DINÂMICO DE GESTÃO VPS (Traefik / Portainer) */}
        {panelSpring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 400,
              left: 0,
              right: 0,
              transform: `scale(${Math.max(0, panelSpring)}) translateY(${interpolate(
                panelSpring,
                [0, 1],
                [40, 0]
              )}px)`,
              opacity: Math.min(1, panelSpring),
            }}
          >
            <div
              style={{
                background: 'rgba(11, 15, 23, 0.95)',
                border: '1.5px solid rgba(14, 165, 233, 0.55)',
                borderRadius: 24,
                padding: '24px 26px',
                boxShadow: '0 20px 48px rgba(0, 0, 0, 0.75), 0 0 30px rgba(14, 165, 233, 0.2)',
                backdropFilter: 'blur(16px)',
              }}
            >
              {/* Barra superior de status do painel técnico */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  paddingBottom: 16,
                  borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                  <div
                    style={{
                      width: 14,
                      height: 14,
                      borderRadius: '50%',
                      backgroundColor: '#10B981',
                      boxShadow: '0 0 10px #10B981',
                      transform: `scale(${heartbeat})`,
                    }}
                  />
                  <span
                    style={{
                      fontSize: 34,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      letterSpacing: '0.5px',
                      textTransform: 'uppercase',
                    }}
                  >
                    Painel Portainer & Traefik
                  </span>
                </div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '4px 14px',
                    borderRadius: 8,
                    background: 'rgba(16, 185, 129, 0.15)',
                    border: '1px solid #10B981',
                  }}
                >
                  <div
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      backgroundColor: '#10B981',
                      boxShadow: '0 0 8px #10B981',
                      transform: `scale(${heartbeat})`,
                    }}
                  />
                  <span
                    style={{
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#34D399',
                    }}
                  >
                    Status: Saudável
                  </span>
                </div>
              </div>

              {/* Lista dinâmica de containers e serviços rodando */}
              <div
                style={{
                  marginTop: 18,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                }}
              >
                {[
                  {
                    nome: 'Docker Engine',
                    desc: 'Containers em execução',
                    status: 'Online',
                    cor: '#38BDF8',
                  },
                  {
                    nome: 'Portainer UI',
                    desc: 'Painel visual ativo',
                    status: 'Online',
                    cor: '#38BDF8',
                  },
                  {
                    nome: 'Traefik Proxy',
                    desc: 'Roteamento seguro & SSL',
                    status: 'Online',
                    cor: '#38BDF8',
                  },
                  {
                    nome: 'Bot Sentinela',
                    desc: 'Vigilância contínua',
                    status: 'Ativo',
                    cor: '#34D399',
                  },
                ].map((srv, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 18px',
                      borderRadius: 14,
                      background: 'rgba(15, 23, 42, 0.85)',
                      border: '1px solid rgba(14, 165, 233, 0.3)',
                    }}
                  >
                    <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                      <div
                        style={{
                          width: 12,
                          height: 12,
                          borderRadius: '50%',
                          backgroundColor: '#10B981',
                          boxShadow: '0 0 8px #10B981',
                          transform: `scale(${heartbeat})`,
                        }}
                      />
                      <div>
                        <div style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                          {srv.nome}
                        </div>
                        <div style={{fontSize: 32, fontWeight: 600, color: '#94A3B8'}}>
                          {srv.desc}
                        </div>
                      </div>
                    </div>
                    <div
                      style={{
                        padding: '4px 14px',
                        borderRadius: 999,
                        background: 'rgba(16, 185, 129, 0.2)',
                        border: '1px solid #10B981',
                        fontSize: 32,
                        fontWeight: 800,
                        color: '#34D399',
                      }}
                    >
                      ● {srv.status}
                    </div>
                  </div>
                ))}
              </div>

              {/* Linha animada de telemetria e estabilidade da VPS */}
              <div style={{marginTop: 18}}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: 8,
                  }}
                >
                  <span style={{fontSize: 32, fontWeight: 700, color: '#BAE6FD'}}>
                    Telemetria de Carga & Estabilidade
                  </span>
                  <span style={{fontSize: 32, fontWeight: 800, color: '#34D399'}}>
                    Operação Estável
                  </span>
                </div>
                <div
                  style={{
                    height: 52,
                    width: '100%',
                    backgroundColor: 'rgba(15, 23, 42, 0.8)',
                    borderRadius: 12,
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    border: '1px solid rgba(14, 165, 233, 0.35)',
                  }}
                >
                  <svg width="100%" height="46" viewBox="0 0 900 46" fill="none">
                    <path
                      d={`M0 24 Q 150 ${18 + Math.sin(waveOffset * 0.05) * 8}, 300 23 T 600 ${20 + Math.cos(waveOffset * 0.05) * 8} T 900 23`}
                      stroke="#0EA5E9"
                      strokeWidth="3.5"
                      fill="none"
                    />
                    <path
                      d={`M0 30 Q 200 ${26 + Math.cos(waveOffset * 0.04) * 6}, 450 28 T 900 29`}
                      stroke="#10B981"
                      strokeWidth="2.5"
                      fill="none"
                      opacity="0.85"
                    />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
