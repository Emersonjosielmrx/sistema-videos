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

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (> 4% variação)
  const scale = interpolate(frame, [0, 276], [1.06, 1.2], {
    extrapolateRight: 'clamp',
  });

  // Entrada do container principal
  const phoneSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Sincronização dos canais
  // Instagram: 15.514s (local frame 106)
  const isInsta = frame >= 106;
  // WhatsApp: 16.115s (local frame 124)
  const isWhats = frame >= 124;
  // Telegram: 16.860s (local frame 143)
  const isTele = frame >= 143;
  // Painel centralizado: 18.663s (local frame 200)
  const isCentralizado = frame >= 200;

  // Microanimação / pop dos selos piscando e acendendo com a voz
  const instaScale = isInsta
    ? spring({frame: frame - 106, fps, config: {damping: 10, stiffness: 180}})
    : 1.0;
  const whatsScale = isWhats
    ? spring({frame: frame - 124, fps, config: {damping: 10, stiffness: 180}})
    : 1.0;
  const teleScale = isTele
    ? spring({frame: frame - 143, fps, config: {damping: 10, stiffness: 180}})
    : 1.0;

  // Entrada das mensagens do briefing
  // Mensagem 1: entra em 1.2s (frame 36)
  const msg1Spring = spring({
    frame: frame - 36,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Mensagem 2: entra aos 3.8s (frame 114)
  const msg2Spring = spring({
    frame: frame - 114,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Digitando: de frame 155 a 195
  const isTyping = frame >= 155 && frame < 195;

  // Mensagem 3 (Empresa): entra aos 6.6s (frame 198, "painel centralizado")
  const msg3Spring = spring({
    frame: frame - 198,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Aproximação de câmera (punch-in sutil) a cada nova mensagem para quebrar o ritmo arrastado
  const punch1 = frame >= 36 ? spring({frame: frame - 36, fps, config: {damping: 12, stiffness: 180}}) * 0.02 : 0;
  const punch2 = frame >= 114 ? spring({frame: frame - 114, fps, config: {damping: 12, stiffness: 180}}) * 0.02 : 0;
  const punch3 = frame >= 198 ? spring({frame: frame - 198, fps, config: {damping: 12, stiffness: 180}}) * 0.025 : 0;
  const totalPunchZoom = punch1 + punch2 + punch3;

  // Transição de opacidade da cena
  const sceneOpacity = interpolate(
    frame,
    [0, 10, 265, 276],
    [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Microanimação de perspectiva 3D isométrica suave no celular com profundidade dinâmica
  const rotateY = interpolate(frame, [0, 276], [3.5, -3.5], {
    extrapolateRight: 'clamp',
  });
  const rotateX = interpolate(frame, [0, 276], [2.5, 1.0], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#0B0D13'}}>
      {/* Fundo com foto e iluminação volumétrica dinâmica com gradientes azuis/roxeados */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${scale + totalPunchZoom})`,
          transformOrigin: 'center center',
          filter: 'blur(20px)',
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(ellipse at 40% 30%, rgba(79,70,229,0.55) 0%, rgba(30,58,138,0.7) 45%, rgba(11,13,19,0.96) 100%)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: '20%',
            left: '10%',
            width: 700,
            height: 700,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(91,108,255,0.3) 0%, transparent 70%)',
            filter: 'blur(60px)',
            transform: `translate(${Math.sin(frame / 20) * 30}px, ${Math.cos(frame / 25) * 30}px)`,
          }}
        />
      </div>

      {/* Safe Zone: y=150 a y=1580, x=60 a x=1020 */}
      <div
        style={{
          position: 'absolute',
          top: 155,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
        }}
      >
        {/* Header com Badge e Gancho */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 20px',
              borderRadius: 24,
              background: '#5B6CFF',
              boxShadow: '0 8px 24px rgba(91, 108, 255, 0.45)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              Como Funciona
            </span>
          </div>

          <div
            style={{
              padding: '6px 16px',
              borderRadius: 16,
              background: 'rgba(17, 24, 39, 0.95)',
              border: '1.5px solid rgba(255,255,255,0.15)',
              fontFamily,
              fontSize: 32,
              fontWeight: 700,
              color: '#94A3B8',
            }}
          >
            Simulação
          </div>
        </div>

        {/* Mockup do Smartphone 9:16 de Alta Fidelidade (largura 920px, altura 1060px) com profundidade 3D */}
        <div
          style={{
            width: 920,
            height: 1060,
            borderRadius: 44,
            background: 'rgba(15, 23, 42, 0.98)',
            border: isCentralizado
              ? '3px solid #5B6CFF'
              : '2px solid rgba(255, 255, 255, 0.22)',
            boxShadow: isCentralizado
              ? '0 25px 60px rgba(91, 108, 255, 0.45)'
              : '0 25px 55px rgba(0, 0, 0, 0.85), 0 0 30px rgba(91,108,255,0.2)',
            padding: '18px 26px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            transform: `scale(${phoneSpring}) perspective(1200px) rotateY(${rotateY}deg) rotateX(${rotateX}deg)`,
            transformOrigin: 'top center',
            transition: 'border 0.3s, box-shadow 0.3s',
          }}
        >
          {/* Topo do Celular: Dynamic Island + Status */}
          <div>
            <div
              style={{
                width: 140,
                height: 24,
                borderRadius: 12,
                background: '#020617',
                margin: '0 auto 12px',
                border: '1px solid rgba(255,255,255,0.1)',
              }}
            />

            {/* Topbar do Painel SuperChat IA */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingBottom: 14,
                borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <div
                  style={{
                    width: 46,
                    height: 46,
                    borderRadius: 12,
                    background: '#5B6CFF',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 4px 12px rgba(91,108,255,0.5)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 900,
                      color: '#FFFFFF',
                    }}
                  >
                    ⚡
                  </span>
                </div>
                <div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 36,
                      fontWeight: 900,
                      color: '#FFFFFF',
                    }}
                  >
                    SuperChat IA
                  </div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#94A3B8',
                    }}
                  >
                    Painel Unificado
                  </div>
                </div>
              </div>

              {/* Chips dos Canais Integrados com microanimação pop */}
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <div
                  style={{
                    padding: '6px 14px',
                    borderRadius: 12,
                    background: isInsta ? '#E1306C' : 'rgba(255,255,255,0.08)',
                    color: '#FFFFFF',
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    boxShadow: isInsta ? '0 0 16px rgba(225,48,108,0.7)' : 'none',
                    transform: `scale(${instaScale})`,
                    transition: 'all 0.2s',
                  }}
                >
                  Insta
                </div>

                <div
                  style={{
                    padding: '6px 14px',
                    borderRadius: 12,
                    background: isWhats ? '#25D366' : 'rgba(255,255,255,0.08)',
                    color: '#FFFFFF',
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    boxShadow: isWhats ? '0 0 16px rgba(37,211,102,0.7)' : 'none',
                    transform: `scale(${whatsScale})`,
                    transition: 'all 0.2s',
                  }}
                >
                  Whats
                </div>

                <div
                  style={{
                    padding: '6px 14px',
                    borderRadius: 12,
                    background: isTele ? '#229ED9' : 'rgba(255,255,255,0.08)',
                    color: '#FFFFFF',
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    boxShadow: isTele ? '0 0 16px rgba(34,158,217,0.7)' : 'none',
                    transform: `scale(${teleScale})`,
                    transition: 'all 0.2s',
                  }}
                >
                  Tele
                </div>
              </div>
            </div>
          </div>

          {/* Área Central de Conversas (Mensagens do briefing) */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              gap: 18,
              paddingTop: 16,
              justifyContent: 'flex-start',
            }}
          >
            {/* Mensagem 1: Cliente do Instagram */}
            {frame >= 36 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '86%',
                  background: 'rgba(30, 41, 59, 0.98)',
                  border: '1.5px solid rgba(225, 48, 108, 0.45)',
                  borderRadius: '22px 22px 22px 4px',
                  padding: '18px 22px',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                  transform: `scale(${msg1Spring})`,
                  transformOrigin: 'bottom left',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 6,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#FF5483',
                    }}
                  >
                    Cliente • via Instagram
                  </span>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    lineHeight: 1.25,
                    color: '#F8FAFC',
                  }}
                >
                  Olá, vi o anúncio no Instagram e quero orçamento.
                </div>
              </div>
            )}

            {/* Mensagem 2: Cliente do WhatsApp */}
            {frame >= 114 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '86%',
                  background: 'rgba(20, 36, 30, 0.98)',
                  border: '1.5px solid rgba(37, 211, 102, 0.45)',
                  borderRadius: '22px 22px 22px 4px',
                  padding: '18px 22px',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                  transform: `scale(${msg2Spring})`,
                  transformOrigin: 'bottom left',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 6,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#25D366',
                    }}
                  >
                    Cliente • via WhatsApp
                  </span>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    lineHeight: 1.25,
                    color: '#F8FAFC',
                  }}
                >
                  Também mandei mensagem no WhatsApp.
                </div>
              </div>
            )}

            {/* Indicador de Digitando */}
            {isTyping && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '12px 20px',
                  borderRadius: 20,
                  background: 'rgba(91, 108, 255, 0.25)',
                  border: '1.5px solid #5B6CFF',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FFFFFF',
                  }}
                >
                  Digitando resposta unificada...
                </span>
                <span
                  style={{
                    color: '#5B6CFF',
                    fontSize: 32,
                  }}
                >
                  ● ● ●
                </span>
              </div>
            )}

            {/* Mensagem 3: Empresa (SuperChat IA) */}
            {frame >= 198 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '88%',
                  background: '#5B6CFF',
                  borderRadius: '22px 22px 4px 22px',
                  padding: '18px 22px',
                  boxShadow: '0 10px 30px rgba(91, 108, 255, 0.5)',
                  transform: `scale(${msg3Spring})`,
                  transformOrigin: 'bottom right',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 6,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      letterSpacing: 0.5,
                    }}
                  >
                    SuperChat IA • Centralizado
                  </span>
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 700,
                    lineHeight: 1.25,
                    color: '#FFFFFF',
                  }}
                >
                  Recebemos todos por aqui no painel centralizado.
                </div>
              </div>
            )}
          </div>

          {/* Barra inferior nativa de resposta */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '14px 20px',
              borderRadius: 22,
              background: 'rgba(255, 255, 255, 0.07)',
              border: '1.5px solid rgba(255, 255, 255, 0.12)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 600,
                color: '#94A3B8',
              }}
            >
              Responder pelo SuperChat IA...
            </span>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: '50%',
                background: '#5B6CFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFFFFF',
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
              }}
            >
              ➔
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
