import React from 'react';
import {
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

export const Cena2Conversa: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de fundo
  const bgScale = interpolate(frame, [0, 197], [1.02, 1.09], {
    extrapolateRight: 'clamp',
  });
  const bgX = interpolate(frame, [0, 197], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Movimento 3D sutil do celular
  const phoneRotateY = interpolate(frame, [0, 197], [5, -3], {
    extrapolateRight: 'clamp',
  });
  const phoneTranslateY = interpolate(frame, [0, 197], [0, -15], {
    extrapolateRight: 'clamp',
  });

  // Entrada do celular no frame 0
  const phoneSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Top Badge: "COMO FUNCIONA"
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Balão 1 (Cliente): entra no frame 6 (~12.5s)
  const msg1Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Digitando 1: visível entre frames 30 e 46
  const typing1Visible = frame >= 30 && frame < 47;

  // Balão 2 (Empresa): entra no frame 47 (~13.9s na fala "cópia automática dos dados")
  const msg2Spring = spring({
    frame: frame - 47,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Digitando 2: visível entre frames 85 e 103
  const typing2Visible = frame >= 85 && frame < 104;

  // Balão 3 (Empresa): entra no frame 104 (~15.8s na fala "Bot Sentinela vigiando os erros")
  const msg3Spring = spring({
    frame: frame - 104,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Imagem de Fundo com Movimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateX(${bgX}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(14, 165, 233, 0.15) 0%, rgba(15, 23, 42, 0.8) 60%, rgba(15, 23, 42, 0.95) 100%)',
          }}
        />
      </div>

      {/* ================= TOPO INFORMATIVO (y: 170 a 280) ================= */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 20,
        }}
      >
        {/* Rótulo da Cena: COMO FUNCIONA */}
        <div
          style={{
            opacity: badgeSpring,
            transform: `scale(${badgeSpring})`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 999,
            background: 'rgba(15, 23, 42, 0.9)',
            border: '2px solid rgba(14, 165, 233, 0.7)',
            boxShadow: '0 4px 16px rgba(14, 165, 233, 0.3)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#0EA5E9',
              boxShadow: '0 0 10px #0EA5E9',
            }}
          />
          <span
            style={{
              color: '#38BDF8',
              fontSize: 34,
              fontWeight: 800,
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            COMO FUNCIONA
          </span>
        </div>

        <div
          style={{
            marginTop: 14,
            fontSize: 44,
            fontWeight: 900,
            color: '#FFFFFF',
            textShadow: '0 4px 14px rgba(0,0,0,0.8)',
          }}
        >
          ROTINA DE PROTEÇÃO AUTOMATIZADA
        </div>
      </div>

      {/* ================= CELULAR WHATSAPP (y: 290 a 1280) ================= */}
      <div
        style={{
          position: 'absolute',
          top: 295,
          left: 80,
          right: 80,
          height: 980,
          perspective: 1200,
          zIndex: 15,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            transform: `scale(${phoneSpring}) translateY(${phoneTranslateY}px) rotateY(${phoneRotateY}deg)`,
            borderRadius: 36,
            background: '#0B141B', // Tom oficial WhatsApp Dark
            border: '3px solid rgba(255, 255, 255, 0.15)',
            boxShadow:
              '0 30px 80px rgba(0, 0, 0, 0.8), 0 0 30px rgba(14, 165, 233, 0.2)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Header do WhatsApp */}
          <div
            style={{
              padding: '20px 24px',
              background: '#1F2C34',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              {/* Avatar com Escudo */}
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #0EA5E9, #0284C7)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 30,
                  boxShadow: '0 4px 12px rgba(14, 165, 233, 0.4)',
                }}
              >
                🛡️
              </div>
              <div>
                <div
                  style={{
                    color: '#E9EDEF',
                    fontSize: 34,
                    fontWeight: 800,
                    letterSpacing: 0.3,
                  }}
                >
                  VPS Blindada • Suporte
                </div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginTop: 2,
                  }}
                >
                  <div
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      backgroundColor: '#22C55E',
                      boxShadow: '0 0 8px #22C55E',
                    }}
                  />
                  <span
                    style={{
                      color: '#22C55E',
                      fontSize: 32,
                      fontWeight: 600,
                    }}
                  >
                    online
                  </span>
                </div>
              </div>
            </div>

            {/* Selo Obrigatório de Simulação */}
            <div
              style={{
                padding: '6px 14px',
                borderRadius: 8,
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                color: '#94A3B8',
                fontSize: 32,
                fontWeight: 700,
                letterSpacing: 0.5,
              }}
            >
              Simulação
            </div>
          </div>

          {/* Área de Mensagens */}
          <div
            style={{
              padding: '28px 24px',
              display: 'flex',
              flexDirection: 'column',
              gap: 24,
              flex: 1,
              justifyContent: 'flex-start',
            }}
          >
            {/* Mensagem 1: Cliente (direita) */}
            {frame >= 6 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '82%',
                  opacity: msg1Spring,
                  transform: `translateX(${(1 - msg1Spring) * 40}px)`,
                  padding: '18px 22px',
                  borderRadius: '24px 24px 6px 24px',
                  background: '#005C4B', // WhatsApp Dark Outgoing Green
                  boxShadow: '0 6px 16px rgba(0,0,0,0.4)',
                }}
              >
                <div
                  style={{
                    color: '#E9EDEF',
                    fontSize: 34,
                    lineHeight: 1.35,
                    fontWeight: 600,
                  }}
                >
                  Como estão as cópias e a segurança das ferramentas?
                </div>
                <div
                  style={{
                    textAlign: 'right',
                    marginTop: 8,
                    color: '#8696A0',
                    fontSize: 32,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-end',
                    gap: 6,
                  }}
                >
                  <span>14:02</span>
                  <span style={{color: '#53BDEB', fontWeight: 900}}>✓✓</span>
                </div>
              </div>
            )}

            {/* Indicador Digitando 1 */}
            {typing1Visible && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  padding: '14px 20px',
                  borderRadius: '24px 24px 24px 6px',
                  background: '#202C33',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span style={{color: '#8696A0', fontSize: 32, fontWeight: 600}}>
                  digitando
                </span>
                <span
                  style={{
                    color: '#25D366',
                    fontSize: 32,
                    fontWeight: 900,
                    letterSpacing: 2,
                  }}
                >
                  ...
                </span>
              </div>
            )}

            {/* Mensagem 2: Empresa (esquerda - na fala "cópia automática dos dados") */}
            {frame >= 47 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '84%',
                  opacity: msg2Spring,
                  transform: `translateX(${(1 - msg2Spring) * -40}px)`,
                  padding: '18px 22px',
                  borderRadius: '24px 24px 24px 6px',
                  background: '#202C33', // WhatsApp Dark Incoming
                  borderLeft: '5px solid #0EA5E9',
                  boxShadow: '0 6px 16px rgba(0,0,0,0.4)',
                }}
              >
                <div
                  style={{
                    color: '#E9EDEF',
                    fontSize: 34,
                    lineHeight: 1.35,
                    fontWeight: 600,
                  }}
                >
                  A rotina de proteção rodou perfeitamente.
                </div>
                <div
                  style={{
                    marginTop: 10,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '4px 12px',
                    borderRadius: 8,
                    background: 'rgba(16, 185, 129, 0.15)',
                    color: '#6EE7B7',
                    fontSize: 32,
                    fontWeight: 700,
                  }}
                >
                  <span>✓</span> Backup Automático OK
                </div>
                <div
                  style={{
                    textAlign: 'right',
                    marginTop: 8,
                    color: '#8696A0',
                    fontSize: 32,
                  }}
                >
                  14:02
                </div>
              </div>
            )}

            {/* Indicador Digitando 2 */}
            {typing2Visible && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  padding: '14px 20px',
                  borderRadius: '24px 24px 24px 6px',
                  background: '#202C33',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span style={{color: '#8696A0', fontSize: 32, fontWeight: 600}}>
                  digitando
                </span>
                <span
                  style={{
                    color: '#0EA5E9',
                    fontSize: 32,
                    fontWeight: 900,
                    letterSpacing: 2,
                  }}
                >
                  ...
                </span>
              </div>
            )}

            {/* Mensagem 3: Empresa (esquerda - na fala "Bot Sentinela vigiando os erros") */}
            {frame >= 104 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '84%',
                  opacity: msg3Spring,
                  transform: `translateX(${(1 - msg3Spring) * -40}px)`,
                  padding: '18px 22px',
                  borderRadius: '24px 24px 24px 6px',
                  background: '#202C33',
                  borderLeft: '5px solid #0EA5E9',
                  boxShadow: '0 6px 16px rgba(0,0,0,0.4)',
                }}
              >
                <div
                  style={{
                    color: '#E9EDEF',
                    fontSize: 34,
                    lineHeight: 1.35,
                    fontWeight: 600,
                  }}
                >
                  O Bot Sentinela segue ativo vigiando os erros.
                </div>
                <div
                  style={{
                    marginTop: 10,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '4px 12px',
                    borderRadius: 8,
                    background: 'rgba(14, 165, 233, 0.2)',
                    color: '#38BDF8',
                    fontSize: 32,
                    fontWeight: 700,
                  }}
                >
                  <span>🤖</span> Bot Sentinela Ativo
                </div>
                <div
                  style={{
                    textAlign: 'right',
                    marginTop: 8,
                    color: '#8696A0',
                    fontSize: 32,
                  }}
                >
                  14:03
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
