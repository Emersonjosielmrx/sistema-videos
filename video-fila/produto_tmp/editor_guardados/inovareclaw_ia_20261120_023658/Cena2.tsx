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

export const Cena2: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com pan e zoom contínuo
  const bgScale = interpolate(frame, [0, 251], [1.0, 1.12], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 251], [-20, 20], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Ribbon (0.2s)
  const ribbonSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do celular em 3D
  const phoneSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 15, stiffness: 90},
  });

  // Levitação suave contínua do celular (microanimação contínua)
  const phoneFloat = Math.sin(frame * 0.08) * 8;
  const phoneRotateY = interpolate(frame, [0, 251], [-6, -2], {
    extrapolateRight: 'clamp',
  });

  // Push-in suave contínuo na janela do chat para eliminar composição estática
  const chatPushIn = interpolate(frame, [0, 251], [1.0, 1.07], {
    extrapolateRight: 'clamp',
  });

  // Timings das mensagens (em frames da cena)
  // Msg 1 (Cliente): entra frame 15 (~13.18s)
  const m1Spring = spring({frame: frame - 15, fps, config: {damping: 14, stiffness: 120}});

  // Digitando 1: visível frame 42 a frame 66
  const typing1Visible = frame >= 42 && frame < 66;

  // Msg 2 (Inovare Claw - Prova de Execução Tangível): entra frame 66 (~14.88s)
  const m2Spring = spring({frame: frame - 66, fps, config: {damping: 14, stiffness: 120}});

  // Msg 3 (Cliente): entra frame 122 (~16.74s)
  const m3Spring = spring({frame: frame - 122, fps, config: {damping: 14, stiffness: 120}});

  // Digitando 2: visível frame 142 a frame 158
  const typing2Visible = frame >= 142 && frame < 158;

  // Msg 4 (Inovare Claw - Confirmação de Autonomia): entra frame 158 (~17.94s)
  const m4Spring = spring({frame: frame - 158, fps, config: {damping: 14, stiffness: 120}});

  // Msg 5 (Cliente): entra frame 202 (~19.41s)
  const m5Spring = spring({frame: frame - 202, fps, config: {damping: 14, stiffness: 120}});

  // Rolagem suave e contínua do chat (scroll up) conforme novas mensagens entram,
  // garantindo transições fluidas e eliminando espaços vazios ociosos
  const scrollY = interpolate(
    frame,
    [0, 66, 85, 122, 140, 158, 178, 202, 222],
    [0, 0, -45, -45, -150, -150, -320, -320, -420],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Saída suave da cena
  const sceneOpacity = interpolate(frame, [240, 251], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#0B0D13'}}>
      {/* Fundo com pan e zoom contínuo */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translateX(${bgTranslateX}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(0.6) contrast(1.15)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 50%, rgba(124, 58, 237, 0.2) 0%, rgba(11, 13, 19, 0.9) 80%)',
          }}
        />
      </AbsoluteFill>

      {/* Topo Informativo (y = 165) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `translateY(${interpolate(ribbonSpring, [0, 1], [-30, 0])}px)`,
          opacity: ribbonSpring,
          zIndex: 30,
        }}
      >
        <ChamferRibbon
          step="02"
          title="COMO FUNCIONA"
          fontFamily={fontFamily}
          accentColor="#7C3AED"
          bgColor="#0F172A"
        />
      </div>

      {/* Mockup do Celular em Perspectiva 3D com push-in contínuo */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'center',
          transform: `perspective(1200px) rotateY(${phoneRotateY}deg) translateY(${interpolate(
            phoneSpring,
            [0, 1],
            [100, phoneFloat]
          )}px) scale(${interpolate(phoneSpring, [0, 1], [0.92, 1]) * chatPushIn})`,
          opacity: phoneSpring,
          zIndex: 10,
        }}
      >
        <div
          style={{
            width: 860,
            height: 1040,
            background: '#090D16',
            borderRadius: 44,
            border: '3px solid rgba(124, 58, 237, 0.55)',
            boxShadow:
              '0 25px 60px rgba(0, 0, 0, 0.9), 0 0 40px rgba(124, 58, 237, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {/* Header do Chat / Aplicativo */}
          <div
            style={{
              height: 120,
              background: 'rgba(15, 23, 42, 0.96)',
              borderBottom: '2px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 28px',
              zIndex: 10,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              {/* Avatar do Agente */}
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #7C3AED, #4F46E5)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 15px rgba(124, 58, 237, 0.8)',
                  fontSize: 28,
                  color: '#FFFFFF',
                }}
              >
                ⚡
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Inovare Claw
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#34D399',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <span style={{fontSize: 20}}>●</span> Agente Autônomo Ativo
                </div>
              </div>
            </div>

            {/* Selo Obrigatório de "Simulação" */}
            <div
              style={{
                padding: '6px 14px',
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: 10,
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#94A3B8',
                letterSpacing: 1,
                textTransform: 'uppercase',
              }}
            >
              Simulação
            </div>
          </div>

          {/* Área de Mensagens com scroll automático */}
          <div
            style={{
              flex: 1,
              padding: '24px 28px',
              display: 'flex',
              flexDirection: 'column',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 18,
                transform: `translateY(${scrollY}px)`,
                transition: 'transform 0.3s ease-out',
              }}
            >
              {/* Mensagem 1: Cliente — Tarefa comercial concreta e tangível */}
              {frame >= 15 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '84%',
                    background: '#1E293B',
                    color: '#FFFFFF',
                    borderRadius: '24px 24px 6px 24px',
                    padding: '16px 22px',
                    border: '1.5px solid rgba(148, 163, 184, 0.25)',
                    boxShadow: '0 6px 16px rgba(0,0,0,0.4)',
                    transform: `scale(${m1Spring}) translateY(${interpolate(
                      m1Spring,
                      [0, 1],
                      [20, 0]
                    )}px)`,
                    opacity: m1Spring,
                  }}
                >
                  <div style={{fontFamily, fontSize: 34, fontWeight: 600, lineHeight: 1.25}}>
                    Dispare o follow-up dos clientes pendentes e atualize a planilha.
                  </div>
                </div>
              )}

              {/* Digitando 1 — Alto contraste com fundo nítido e texto claro */}
              {typing1Visible && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    background: 'rgba(30, 41, 59, 0.95)',
                    borderRadius: '20px 20px 20px 6px',
                    padding: '12px 20px',
                    border: '1.5px solid rgba(167, 139, 250, 0.55)',
                    fontFamily,
                    fontSize: 32,
                    color: '#FFFFFF',
                    fontWeight: 700,
                    letterSpacing: 0.5,
                  }}
                >
                  ⚡ Inovare Claw executando tarefas...
                </div>
              )}

              {/* Mensagem 2: Inovare Claw — Comprovação Tangível de Execução */}
              {frame >= 66 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '88%',
                    background: 'linear-gradient(135deg, #6D28D9 0%, #4C1D95 100%)',
                    color: '#FFFFFF',
                    borderRadius: '24px 24px 24px 6px',
                    padding: '18px 24px',
                    border: '1.5px solid #8B5CF6',
                    boxShadow: '0 8px 24px rgba(124, 58, 237, 0.35)',
                    transform: `scale(${m2Spring}) translateY(${interpolate(
                      m2Spring,
                      [0, 1],
                      [20, 0]
                    )}px)`,
                    opacity: m2Spring,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 12,
                  }}
                >
                  <div style={{fontFamily, fontSize: 34, fontWeight: 700, lineHeight: 1.25}}>
                    Certo. Já comecei a disparar os contatos e atualizar os dados.
                  </div>

                  {/* Card de Prova de Execução Tangível com cápsula escura neutra #111827 */}
                  <div
                    style={{
                      background: '#111827',
                      borderRadius: 16,
                      padding: '14px 18px',
                      border: '1.5px solid rgba(16, 185, 129, 0.45)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 8,
                      boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
                    }}
                  >
                    <div
                      style={{
                        fontFamily,
                        fontSize: 30,
                        fontWeight: 900,
                        color: '#34D399',
                        letterSpacing: 1,
                        textTransform: 'uppercase',
                      }}
                    >
                      ⚡ Execução no Sistema
                    </div>
                    <div style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#F8FAFC'}}>
                      ✓ Follow-up enviado aos contatos
                    </div>
                    <div style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#F8FAFC'}}>
                      ✓ Planilha de clientes atualizada
                    </div>
                    <div
                      style={{
                        marginTop: 4,
                        background: 'rgba(16, 185, 129, 0.15)',
                        padding: '6px 12px',
                        borderRadius: 8,
                        alignSelf: 'flex-start',
                        fontFamily,
                        fontSize: 32,
                        fontWeight: 700,
                        color: '#34D399',
                      }}
                    >
                      ✓ O agente executa de verdade por você
                    </div>
                  </div>
                </div>
              )}

              {/* Mensagem 3: Cliente */}
              {frame >= 122 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '82%',
                    background: '#1E293B',
                    color: '#FFFFFF',
                    borderRadius: '24px 24px 6px 24px',
                    padding: '16px 22px',
                    border: '1.5px solid rgba(148, 163, 184, 0.25)',
                    boxShadow: '0 6px 16px rgba(0,0,0,0.4)',
                    transform: `scale(${m3Spring}) translateY(${interpolate(
                      m3Spring,
                      [0, 1],
                      [20, 0]
                    )}px)`,
                    opacity: m3Spring,
                  }}
                >
                  <div style={{fontFamily, fontSize: 34, fontWeight: 600, lineHeight: 1.25}}>
                    Ele faz tudo direto sem eu precisar fazer nada manual?
                  </div>
                </div>
              )}

              {/* Digitando 2 */}
              {typing2Visible && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    background: 'rgba(30, 41, 59, 0.95)',
                    borderRadius: '20px 20px 20px 6px',
                    padding: '12px 20px',
                    border: '1.5px solid rgba(167, 139, 250, 0.55)',
                    fontFamily,
                    fontSize: 32,
                    color: '#FFFFFF',
                    fontWeight: 700,
                    letterSpacing: 0.5,
                  }}
                >
                  ⚡ Confirmando status autônomo...
                </div>
              )}

              {/* Mensagem 4: Inovare Claw — Sem ficar só na conversa */}
              {frame >= 158 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '88%',
                    background: 'linear-gradient(135deg, #6D28D9 0%, #4C1D95 100%)',
                    color: '#FFFFFF',
                    borderRadius: '24px 24px 24px 6px',
                    padding: '18px 24px',
                    border: '1.5px solid #8B5CF6',
                    boxShadow: '0 8px 24px rgba(124, 58, 237, 0.35)',
                    transform: `scale(${m4Spring}) translateY(${interpolate(
                      m4Spring,
                      [0, 1],
                      [20, 0]
                    )}px)`,
                    opacity: m4Spring,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 10,
                  }}
                >
                  <div style={{fontFamily, fontSize: 34, fontWeight: 700, lineHeight: 1.25}}>
                    Exato. O Inovare Claw executa direto, sem ficar só na conversa.
                  </div>
                  <div
                    style={{
                      background: '#111827',
                      borderRadius: 14,
                      padding: '10px 16px',
                      border: '1.5px solid rgba(16, 185, 129, 0.45)',
                      alignSelf: 'flex-start',
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#34D399',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                    }}
                  >
                    <span>✓</span>
                    <span>Tarefas executadas com autonomia total</span>
                  </div>
                </div>
              )}

              {/* Mensagem 5: Cliente */}
              {frame >= 202 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '80%',
                    background: '#1E293B',
                    color: '#FFFFFF',
                    borderRadius: '24px 24px 6px 24px',
                    padding: '16px 22px',
                    border: '1.5px solid rgba(148, 163, 184, 0.2)',
                    boxShadow: '0 6px 16px rgba(0,0,0,0.4)',
                    transform: `scale(${m5Spring}) translateY(${interpolate(
                      m5Spring,
                      [0, 1],
                      [20, 0]
                    )}px)`,
                    opacity: m5Spring,
                  }}
                >
                  <div style={{fontFamily, fontSize: 34, fontWeight: 600, lineHeight: 1.25}}>
                    Perfeito, obrigado.
                  </div>
                </div>
              )}
                    opacity: m5Spring,
                  }}
                >
                  <div style={{fontFamily, fontSize: 34, fontWeight: 600, lineHeight: 1.25}}>
                    Perfeito, obrigado.
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
