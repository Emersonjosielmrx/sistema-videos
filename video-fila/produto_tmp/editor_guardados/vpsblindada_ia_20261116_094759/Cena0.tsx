import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Cena0: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera acentuado com Ken Burns contínuo de 1.08 para 1.24 e pan vertical
  const bgScale = interpolate(frame, [0, 147], [1.08, 1.24], {
    extrapolateRight: 'clamp',
  });
  const bgPanY = interpolate(frame, [0, 147], [-10, -50], {
    extrapolateRight: 'clamp',
  });

  // Linha de varredura (scanline de alerta) que desce continuamente pela tela
  const scanlineY = ((frame * 14) % 1920);

  // Alarme pulsante vermelho no ambiente (simula luz de giro de datacenter / pane crítica)
  const alarmFlash = Math.sin(frame * 0.25) * 0.5 + 0.5; // 0 a 1

  // Entradas com spring
  const tagSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  const titleSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 11, stiffness: 160},
  });

  const caiuSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 9, stiffness: 180},
  });

  // Notificação de WhatsApp entra aos ~0.4s (frame 12) com bounce elástico acentuado
  const notifSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 9, stiffness: 150},
  });

  // Vibração tátil nos primeiros frames após a chegada do card (frames 18 a 34)
  const isVibrating = frame >= 18 && frame <= 34;
  const vibrateDecay = Math.max(0, (34 - frame) / 16);
  const vibrateX = isVibrating ? Math.sin((frame - 18) * 1.8) * 8 * vibrateDecay : 0;
  const vibrateY = isVibrating ? Math.cos((frame - 18) * 2.2) * 5 * vibrateDecay : 0;

  // Segundo elemento de tensão: alerta de telemetria / radar de queda entra aos frames 50+
  const alertBarSpring = spring({
    frame: frame - 50,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Pulso contínuo do alerta
  const alertPulse = Math.sin(frame * 0.28) * 0.08 + 1.0;
  const caiuPulse = frame >= 12 ? Math.sin((frame - 12) * 0.22) * 0.05 + 1.0 : 1.0;

  // Saída suave no final da cena para transição (frames 135 a 147)
  const exitOpacity = interpolate(frame, [135, 147], [1, 0.2], {
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
      {/* Imagem de fundo com zoom Ken Burns e pan contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgPanY}px)`,
          transformOrigin: '55% 65%',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'contrast(1.15) brightness(0.85)',
          }}
        />
      </div>

      {/* Véu escuro com iluminação dramática de alerta vermelho pulsante */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          background: `radial-gradient(circle at 50% 35%, rgba(220, 38, 38, ${
            0.18 + alarmFlash * 0.16
          }) 0%, rgba(15, 23, 42, 0.90) 65%, rgba(11, 15, 23, 0.98) 100%)`,
        }}
      />

      {/* Terminal escuro de crash com logs em código mono no fundo */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          opacity: 0.18 + alarmFlash * 0.1,
          fontFamily: 'monospace',
          fontSize: 22,
          color: '#EF4444',
          padding: 40,
          lineHeight: 1.8,
          pointerEvents: 'none',
          userSelect: 'none',
        }}
      >
        <div>[CRITICAL] CONNECTION LOST: 192.168.1.1</div>
        <div>[ERROR] BAD GATEWAY - HOST UNREACHABLE</div>
        <div>[FAIL] TIMEOUT DETECTED - 0 BYTES RECEIVED</div>
        <div>[ALERT] SERVER DOWN - UNRESPONSIVE DAEMON</div>
        <div>[STATUS] CRASH REPORT GENERATED</div>
      </div>

      {/* Linha de varredura de scanline vermelha em movimento contínuo */}
      <div
        style={{
          position: 'absolute',
          top: scanlineY,
          left: 0,
          right: 0,
          height: 6,
          background: 'linear-gradient(90deg, transparent 0%, rgba(239, 68, 68, 0.8) 50%, transparent 100%)',
          boxShadow: '0 0 18px rgba(239, 68, 68, 0.9)',
          pointerEvents: 'none',
        }}
      />

      {/* Grid cibernético de alerta no topo */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 800,
          backgroundImage:
            'linear-gradient(rgba(239, 68, 68, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(239, 68, 68, 0.08) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
          opacity: 0.7,
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo principal dentro da safe zone (x=60 a 1020, y>=170) */}
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
        {/* Badge superior de alerta com pulso contínuo (y=175) */}
        {tagSpring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 175,
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
                gap: 12,
                padding: '10px 24px',
                borderRadius: 999,
                background: 'rgba(15, 23, 42, 0.92)',
                border: '1.5px solid rgba(239, 68, 68, 0.65)',
                boxShadow: '0 8px 25px rgba(239, 68, 68, 0.35)',
                backdropFilter: 'blur(10px)',
              }}
            >
              <div
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: '50%',
                  backgroundColor: '#EF4444',
                  boxShadow: '0 0 14px #EF4444',
                  transform: `scale(${alertPulse})`,
                }}
              />
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FCA5A5',
                  textTransform: 'uppercase',
                  letterSpacing: '1.5px',
                }}
              >
                Alerta de Instabilidade
              </span>
            </div>
          </div>
        )}

        {/* Título Cinético da Pergunta (y=255) */}
        {titleSpring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 255,
              left: 0,
              right: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              transform: `scale(${Math.max(0, titleSpring)})`,
              opacity: Math.min(1, titleSpring),
            }}
          >
            <div
              style={{
                fontSize: 60,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.1,
                textTransform: 'uppercase',
                textShadow: '0 4px 20px rgba(0,0,0,0.85)',
                letterSpacing: '-0.5px',
              }}
            >
              Seu Sistema
            </div>

            {/* Palavra CAIU com explosão de mola e vermelho vivo */}
            {caiuSpring > 0.01 && (
              <div
                style={{
                  marginTop: 8,
                  transform: `scale(${Math.max(0, caiuSpring) * caiuPulse})`,
                  opacity: Math.min(1, caiuSpring),
                }}
              >
                <div
                  style={{
                    display: 'inline-block',
                    padding: '6px 34px',
                    borderRadius: 18,
                    background: 'linear-gradient(135deg, #DC2626 0%, #991B1B 100%)',
                    boxShadow: '0 0 40px rgba(220, 38, 38, 0.75)',
                    border: '2px solid rgba(254, 202, 202, 0.65)',
                  }}
                >
                  <span
                    style={{
                      fontSize: 84,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      lineHeight: 1.05,
                      textTransform: 'uppercase',
                      letterSpacing: '2px',
                    }}
                  >
                    CAIU?
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Card de Notificação de Cliente no WhatsApp com Slide-Down, Bounce e Vibração Tátil (y=490) */}
        {notifSpring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 490,
              left: 0,
              right: 0,
              transform: `translate(${vibrateX}px, ${
                interpolate(notifSpring, [0, 1], [-80, 0]) + vibrateY
              }px) scale(${Math.max(0, notifSpring)})`,
              opacity: Math.min(1, notifSpring),
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid rgba(239, 68, 68, 0.55)',
                borderRadius: 24,
                padding: '24px 28px',
                boxShadow:
                  '0 20px 45px rgba(0, 0, 0, 0.75), 0 0 30px rgba(239, 68, 68, 0.25)',
                backdropFilter: 'blur(16px)',
              }}
            >
              {/* Topo do card com ícone de mensagem e selo simulação */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 12,
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                  <div
                    style={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: '#22C55E',
                    }}
                  />
                  <span
                    style={{
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#94A3B8',
                      letterSpacing: '0.5px',
                    }}
                  >
                    WhatsApp • Cliente
                  </span>
                </div>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#64748B',
                  }}
                >
                  Simulação
                </span>
              </div>

              {/* Texto da mensagem com excelente leitura */}
              <div
                style={{
                  fontSize: 36,
                  fontWeight: 700,
                  color: '#FFFFFF',
                  lineHeight: 1.35,
                  textWrap: 'balance',
                }}
              >
                &ldquo;O sistema caiu de novo? Nossos clientes não conseguem acessar nada!&rdquo;
              </div>

              {/* Rodapé do card: sem números inventados */}
              <div
                style={{
                  marginTop: 14,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#EF4444',
                  }}
                >
                  ⚠️ Conexão Recusada • Servidor Inacessível
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 500,
                    color: '#94A3B8',
                  }}
                >
                  agora
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Segundo bloco dinâmico que entra aos frames 50+ para garantir evolução contínua da cena (> 4% movimento) */}
        {alertBarSpring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 790,
              left: 0,
              right: 0,
              transform: `scale(${Math.max(0, alertBarSpring)}) translateY(${interpolate(
                alertBarSpring,
                [0, 1],
                [30, 0]
              )}px)`,
              opacity: Math.min(1, alertBarSpring),
            }}
          >
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1.5px solid rgba(239, 68, 68, 0.4)',
                borderRadius: 18,
                padding: '14px 22px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                backdropFilter: 'blur(12px)',
                boxShadow: '0 8px 24px rgba(239, 68, 68, 0.2)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <div
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: '#EF4444',
                    boxShadow: '0 0 10px #EF4444',
                    transform: `scale(${Math.sin(frame * 0.3) * 0.15 + 1.0})`,
                  }}
                />
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FEE2E2',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}
                >
                  Falha Crítica Detectada
                </span>
              </div>
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#FCA5A5',
                }}
              >
                Sem Resposta do Host
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
