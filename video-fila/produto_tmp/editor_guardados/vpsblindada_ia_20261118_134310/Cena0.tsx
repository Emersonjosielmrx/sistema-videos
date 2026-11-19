import React from 'react';
import {
  Img,
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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera dinâmico com corte aos 1.8s (frame 54) para impacto imediato
  const isSecondPhase = frame >= 54;

  const bgScale = interpolate(frame, [0, 54, 148], [1.05, 1.15, 1.35], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(frame, [0, 148], [0, -45], {
    extrapolateRight: 'clamp',
  });

  // Entrada ágil do Badge superior (frame 2)
  const badgeSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Entrada imediata do gancho textual nos primeiros 2s (frames 0 a 6)
  const l1Spring = spring({
    frame: frame,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const l2Spring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const l3Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Entrada do PIP com o apresentador nos primeiros 2s para impacto humano imediato
  const pipSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Corte dinâmico aos 1.8s (frame 54) para o terminal crítico
  const cutSpring = spring({
    frame: frame - 54,
    fps,
    config: {damping: 11, stiffness: 160},
  });

  // Transição para o estado de Alerta Crítico (frame 54+)
  const isAlertState = frame >= 54;
  const alertSpring = spring({
    frame: frame - 58,
    fps,
    config: {damping: 10, stiffness: 150},
  });

  // Entrada do medidor de ameaça crítica aos ~2.5s (frame 76)
  const threatMeterSpring = spring({
    frame: frame - 76,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Entrada de alerta secundário de conexão aos ~3.2s (frame 96)
  const secondaryAlertSpring = spring({
    frame: frame - 96,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Saída dinâmica da cena conectando à cena 1
  const cenaOpacity = interpolate(frame, [142, 148], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitScale = interpolate(frame, [138, 148], [1, 1.15], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitFlash = interpolate(frame, [140, 148], [0, 0.4], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Micro-animações contínuas
  const radarRotation = (frame * 5.0) % 360;
  const hudFloat = Math.sin(frame / 7) * 4;

  // Pulsação contínua de perigo no escudo e no container de alerta
  const dangerPulse = 1 + Math.sin(frame / 3) * 0.04;
  const dangerGlow = 0.65 + Math.sin(frame / 3) * 0.35;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        opacity: cenaOpacity,
        transform: `scale(${exitScale})`,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Imagem de Fundo com Movimento Forte de Câmera */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(${bgY}px)`,
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Véu Tecnológico da Marca */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(14, 165, 233, 0.18) 0%, rgba(10, 15, 28, 0.92) 75%)',
          }}
        />
      </div>

      {/* Partículas / Grade cibernética sutil em movimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.28,
          backgroundImage:
            'radial-gradient(rgba(14, 165, 233, 0.45) 1.5px, transparent 1.5px)',
          backgroundSize: '48px 48px',
          transform: `translateY(${(frame * 2.2) % 48}px)`,
        }}
      />

      {/* Topo: Badge de Categoria (y=165) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.max(0, Math.min(1, badgeSpring)),
          transform: `translateY(${(1 - Math.min(1, badgeSpring)) * -20}px)`,
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: '#151922',
            border: isAlertState
              ? '1.5px solid rgba(239, 68, 68, 0.85)'
              : '1.5px solid rgba(14, 165, 233, 0.85)',
            padding: '8px 24px',
            borderRadius: 999,
            boxShadow: isAlertState
              ? '0 4px 20px rgba(239, 68, 68, 0.4)'
              : '0 4px 20px rgba(14, 165, 233, 0.4)',
          }}
        >
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: isAlertState ? '#EF4444' : '#0EA5E9',
              boxShadow: isAlertState ? '0 0 10px #EF4444' : '0 0 10px #0EA5E9',
              transform: `scale(${1 + Math.sin(frame / 4) * 0.25})`,
            }}
          />
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: isAlertState ? '#FCA5A5' : '#7DD3FC',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            {isAlertState ? 'Alerta Crítico' : 'Alerta de Segurança'}
          </span>
        </div>
      </div>

      {/* Gancho Textual de Alto Contraste (y=230 a 440) */}
      <div
        style={{
          position: 'absolute',
          top: 230,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: 6,
          zIndex: 25,
        }}
      >
        {/* Linha 1: Branco Alto Contraste */}
        <div
          style={{
            opacity: Math.max(0, Math.min(1, l1Spring)),
            transform: `scale(${interpolate(l1Spring, [0, 1], [0.92, 1])})`,
            fontSize: 54,
            fontWeight: 900,
            color: '#FFFFFF',
            letterSpacing: 1,
            textShadow:
              '0 4px 18px rgba(0, 0, 0, 0.9), 0 0 25px rgba(255, 255, 255, 0.3)',
          }}
        >
          MEDO DE COLOCAR
        </div>

        {/* Linha 2: Destaque Ciano da Marca */}
        <div
          style={{
            opacity: Math.max(0, Math.min(1, l2Spring)),
            transform: `scale(${interpolate(l2Spring, [0, 1], [0.92, 1])})`,
            fontSize: 60,
            fontWeight: 900,
            color: '#38BDF8',
            letterSpacing: 1,
            textShadow:
              '0 4px 25px rgba(14, 165, 233, 0.7), 0 0 40px rgba(14, 165, 233, 0.4)',
          }}
        >
          SEU SISTEMA ONLINE
        </div>

        {/* Linha 3: Destaque de Risco */}
        <div
          style={{
            opacity: Math.max(0, Math.min(1, l3Spring)),
            transform: `scale(${interpolate(l3Spring, [0, 1], [0.92, 1])})`,
            fontSize: 62,
            fontWeight: 900,
            color: '#FFFFFF',
            letterSpacing: 1,
            textShadow: isAlertState
              ? `0 4px 30px rgba(239, 68, 68, 0.9), 0 0 45px rgba(239, 68, 68, 0.7)`
              : '0 4px 30px rgba(14, 165, 233, 0.8), 0 0 40px rgba(14, 165, 233, 0.5)',
          }}
        >
          E SOFRER INVASÕES?
        </div>
      </div>

      {/* Fase 1: Primeiros 1.8 segundos (frame 0 a 53) - Gancho com Presença Humana em PIP + Radar */}
      {!isSecondPhase ? (
        <div
          style={{
            position: 'absolute',
            top: 450,
            left: 60,
            right: 60,
            height: 650,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: '#0F172A',
            border: '2px solid rgba(14, 165, 233, 0.65)',
            borderRadius: 28,
            padding: '24px 24px',
            boxShadow:
              '0 25px 60px rgba(0, 0, 0, 0.8), 0 0 35px rgba(14, 165, 233, 0.25)',
            zIndex: 20,
          }}
        >
          {/* Header do Terminal com Status */}
          <div
            style={{
              width: '100%',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
              paddingBottom: 12,
            }}
          >
            <div style={{display: 'flex', gap: 10}}>
              <span style={{width: 14, height: 14, borderRadius: '50%', background: '#EF4444'}} />
              <span style={{width: 14, height: 14, borderRadius: '50%', background: '#F59E0B'}} />
              <span style={{width: 14, height: 14, borderRadius: '50%', background: '#10B981'}} />
            </div>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#38BDF8',
                letterSpacing: 1,
              }}
            >
              SCANNER EM TEMPO REAL
            </span>
          </div>

          {/* Área Central: Presença Humana do Especialista em PIP + Radar de Conexões */}
          <div
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-around',
              gap: 20,
              padding: '10px 0',
            }}
          >
            {/* PIP da Câmera do Apresentador */}
            <div
              style={{
                position: 'relative',
                width: 250,
                height: 250,
                borderRadius: 24,
                overflow: 'hidden',
                border: '2.5px solid #0EA5E9',
                boxShadow: '0 8px 30px rgba(0, 0, 0, 0.7), 0 0 20px rgba(14, 165, 233, 0.4)',
                transform: `scale(${interpolate(pipSpring, [0, 1], [0.85, 1])})`,
              }}
            >
              <OffthreadVideo
                src={staticFile('dono_1.mp4')}
                muted
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  bottom: 8,
                  left: 8,
                  right: 8,
                  background: 'rgba(15, 23, 42, 0.90)',
                  borderRadius: 8,
                  padding: '3px 8px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 6,
                }}
              >
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    backgroundColor: '#10B981',
                    boxShadow: '0 0 6px #10B981',
                  }}
                />
                <span
                  style={{
                    fontSize: 22,
                    fontWeight: 800,
                    color: '#F8FAFC',
                    letterSpacing: 0.5,
                  }}
                >
                  ESPECIALISTA
                </span>
              </div>
            </div>

            {/* Radar Circular Tecnológico */}
            <div
              style={{
                position: 'relative',
                width: 210,
                height: 210,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  borderRadius: '50%',
                  border: '2px dashed rgba(14, 165, 233, 0.45)',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  inset: 28,
                  borderRadius: '50%',
                  border: '1.5px solid rgba(14, 165, 233, 0.65)',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  width: '100%',
                  height: '100%',
                  borderRadius: '50%',
                  transform: `rotate(${radarRotation}deg)`,
                  background:
                    'conic-gradient(from 0deg, rgba(14, 165, 233, 0.5) 0deg, transparent 65deg)',
                }}
              />
              <svg
                width="70"
                height="70"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#0EA5E9"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{
                  filter: 'drop-shadow(0 0 15px rgba(14, 165, 233, 0.8))',
                }}
              >
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="M12 8v4" />
                <path d="M12 16h.01" />
              </svg>
            </div>
          </div>

          {/* Rodapé do Terminal na Fase 1 */}
          <div
            style={{
              width: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 10,
              paddingBottom: 6,
            }}
          >
            <div
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#38BDF8',
                letterSpacing: 2,
              }}
            >
              MONITORANDO CONEXÕES DE REDE...
            </div>
            <div style={{display: 'flex', gap: 12}}>
              <span
                style={{
                  background: 'rgba(14, 165, 233, 0.22)',
                  border: '1.5px solid #38BDF8',
                  borderRadius: 10,
                  padding: '6px 18px',
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#38BDF8',
                  letterSpacing: 1,
                }}
              >
                ROTAS HTTP
              </span>
              <span
                style={{
                  background: 'rgba(14, 165, 233, 0.22)',
                  border: '1.5px solid #38BDF8',
                  borderRadius: 10,
                  padding: '6px 18px',
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#38BDF8',
                  letterSpacing: 1,
                }}
              >
                CONEXÕES EXTERNAS
              </span>
            </div>
          </div>
        </div>
      ) : (
        /* Fase 2: Corte aos 1.8s (frame 54 a 148) - Terminal Crítico com Detecção de Vulnerabilidades */
        <div
          style={{
            position: 'absolute',
            top: 450,
            left: 60,
            right: 60,
            height: 650,
            opacity: Math.max(0, Math.min(1, cutSpring)),
            transform: `translateY(${hudFloat}px) scale(${interpolate(
              cutSpring,
              [0, 1],
              [0.92, 1]
            )})`,
            background: '#0F172A',
            border: `2px solid rgba(239, 68, 68, ${dangerGlow})`,
            borderRadius: 28,
            boxShadow: `0 25px 60px rgba(0, 0, 0, 0.8), 0 0 ${
              20 + dangerGlow * 20
            }px rgba(239, 68, 68, 0.45)`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '24px 28px 28px 28px',
            zIndex: 20,
          }}
        >
          {/* Barra de Status do Servidor - Vermelho Alerta */}
          <div
            style={{
              width: '100%',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
              paddingBottom: 12,
            }}
          >
            <div style={{display: 'flex', gap: 10}}>
              <span style={{width: 14, height: 14, borderRadius: '50%', background: '#EF4444'}} />
              <span style={{width: 14, height: 14, borderRadius: '50%', background: '#F59E0B'}} />
              <span style={{width: 14, height: 14, borderRadius: '50%', background: '#10B981'}} />
            </div>
            <span
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: '#FCA5A5',
                letterSpacing: 1,
              }}
            >
              VARREDURA CONCLUÍDA
            </span>
          </div>

          {/* Radar e Escudo de Alerta Crítico */}
          <div
            style={{
              position: 'relative',
              width: 180,
              height: 180,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '4px 0',
            }}
          >
            <div
              style={{
                position: 'absolute',
                inset: 0,
                borderRadius: '50%',
                border: '2px dashed rgba(239, 68, 68, 0.55)',
              }}
            />
            <div
              style={{
                position: 'absolute',
                inset: 25,
                borderRadius: '50%',
                border: '1.5px solid rgba(239, 68, 68, 0.7)',
              }}
            />
            <div
              style={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                borderRadius: '50%',
                transform: `rotate(${radarRotation}deg)`,
                background:
                  'conic-gradient(from 0deg, rgba(239, 68, 68, 0.5) 0deg, transparent 65deg)',
              }}
            />
            <div style={{transform: `scale(${dangerPulse})`}}>
              <svg
                width="84"
                height="84"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#EF4444"
                strokeWidth="2.3"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{
                  filter: 'drop-shadow(0 0 18px rgba(239, 68, 68, 0.9))',
                }}
              >
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="M12 8v4" />
                <path d="M12 16h.01" />
              </svg>
            </div>
          </div>

          {/* Alertas Críticos sem Palavra Órfã e com Respiro Inferior Adequado */}
          <div
            style={{
              width: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 10,
              paddingBottom: 4,
            }}
          >
            {/* Alerta 1: Sem quebra órfã da palavra "BLINDAGEM" */}
            <div
              style={{
                width: '100%',
                opacity: Math.max(0, Math.min(1, alertSpring)),
                transform: `scale(${
                  interpolate(alertSpring, [0, 1], [0.94, 1]) * dangerPulse
                })`,
                background: 'rgba(239, 68, 68, 0.22)',
                border: `2px solid rgba(239, 68, 68, ${dangerGlow})`,
                borderRadius: 16,
                padding: '10px 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 10,
                boxShadow: `0 0 ${16 + dangerGlow * 14}px rgba(239, 68, 68, 0.55)`,
              }}
            >
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  letterSpacing: 1,
                  textShadow: '0 0 10px #EF4444',
                  whiteSpace: 'nowrap',
                }}
              >
                ⚠️ CONEXÕES EXPOSTAS SEM BLINDAGEM
              </span>
            </div>

            {/* Alerta 2: Status Vulnerável (frame 76+) */}
            {frame >= 76 && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  background: 'rgba(15, 23, 42, 0.95)',
                  border: '1.5px solid rgba(239, 68, 68, 0.7)',
                  borderRadius: 12,
                  padding: '6px 18px',
                  opacity: Math.max(0, Math.min(1, threatMeterSpring)),
                  transform: `translateY(${
                    (1 - Math.min(1, threatMeterSpring)) * 10
                  }px)`,
                }}
              >
                <span
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#EF4444',
                    boxShadow: '0 0 8px #EF4444',
                  }}
                />
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#F87171',
                    letterSpacing: 1,
                  }}
                >
                  STATUS: VULNERÁVEL A INVASÕES
                </span>
              </div>
            )}

            {/* Alerta 3: Tráfego sem proteção adequada com margem inferior limpa (frame 96+) */}
            {frame >= 96 && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  background: 'rgba(15, 23, 42, 0.95)',
                  border: '1.5px solid rgba(239, 68, 68, 0.8)',
                  borderRadius: 12,
                  padding: '6px 18px',
                  opacity: Math.max(0, Math.min(1, secondaryAlertSpring)),
                  transform: `translateY(${
                    (1 - Math.min(1, secondaryAlertSpring)) * 10
                  }px)`,
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FCA5A5',
                    letterSpacing: 1,
                  }}
                >
                  TRÁFEGO SEM PROTEÇÃO ADEQUADA
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Flash Dinâmico de Transição conectando a Cena 0 à Cena 1 */}
      {frame >= 138 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: '#0EA5E9',
            opacity: exitFlash,
            pointerEvents: 'none',
            zIndex: 35,
          }}
        />
      )}
    </div>
  );
};

