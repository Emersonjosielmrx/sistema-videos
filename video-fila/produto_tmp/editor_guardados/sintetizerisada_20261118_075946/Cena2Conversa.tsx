import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena2Conversa: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo do estúdio e no celular
  const bgScale = interpolate(frame, [0, 172], [1.06, 1.18], {
    extrapolateRight: 'clamp',
  });
  // Slow zoom in contínuo no mockup para dar profundidade espacial
  const phoneScale = interpolate(frame, [0, 172], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });
  const phoneRotateY = interpolate(frame, [0, 172], [-6, 3], {
    extrapolateRight: 'clamp',
  });
  const phoneFloatY = Math.sin(frame / 8) * 8;

  // Entrada do container do celular
  const phoneSpring = spring({
    frame,
    fps,
    config: {damping: 15, stiffness: 120},
  });

  // Entrada das mensagens escalonadas:
  // Msg 1 (Cliente): frame 6 (~12.66s)
  const msg1Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Digitando 1: de frame 26 a frame 46
  const isTyping1 = frame >= 26 && frame < 46;

  // Msg 2 (Empresa): frame 46 (~14.0s)
  const msg2Spring = spring({
    frame: frame - 46,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Msg 3 (Cliente): frame 80 (~15.1s)
  const msg3Spring = spring({
    frame: frame - 80,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Digitando 2: de frame 94 a frame 112
  const isTyping2 = frame >= 94 && frame < 112;

  // Msg 4 (Empresa): frame 112 (~16.2s)
  const msg4Spring = spring({
    frame: frame - 112,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Ponto de virada da fala na cena:
  // "e o sistema finaliza o processo ponta a ponta" começa em ~frame 54
  const speechSwitch = interpolate(frame, [50, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Transição de saída suave no final da cena
  const exitOpacity = interpolate(frame, [155, 172], [1, 0], {
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
        fontFamily,
        opacity: exitOpacity,
      }}
    >
      {/* Fundo com o ambiente do estúdio sobreposto desfocado para contextualizar o produto */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale})`,
          transformOrigin: '50% 40%',
        }}
      >
        <Img
          src={staticFile('dono_1_freeze.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(10px)',
          }}
        />
        {/* Overlay escuro em degradê suave mantendo o tom profissional da marca */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 45%, rgba(15, 23, 42, 0.82) 0%, rgba(15, 23, 42, 0.96) 100%)',
          }}
        />
      </div>

      {/* Faixa Superior Informativa (y=195 a 380) */}
      <div
        style={{
          position: 'absolute',
          top: 195,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 24,
            background: 'rgba(31, 41, 55, 0.94)',
            border: '1.5px solid rgba(255, 169, 77, 0.7)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
          }}
        >
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#10B981',
              boxShadow: '0 0 10px #10B981',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              color: '#FFA94D',
            }}
          >
            Autonomia Total • 24 Horas
          </span>
        </div>

        {/* Título Dinâmico Sincronizado com a fala da cena */}
        <div
          style={{
            position: 'relative',
            width: '100%',
            height: 70,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          {/* Fase 1: O cliente escolhe a vaga */}
          <h2
            style={{
              position: 'absolute',
              margin: 0,
              fontSize: 42,
              fontWeight: 900,
              lineHeight: 1.25,
              color: '#FFFFFF',
              textAlign: 'center',
              textShadow: '0 4px 16px rgba(0,0,0,0.8)',
              textWrap: 'balance',
              opacity: 1 - speechSwitch,
              transform: `translateY(${speechSwitch * -12}px)`,
            }}
          >
            O cliente escolhe a vaga{' '}
            <span style={{color: '#FFA94D'}}>no WhatsApp</span>
          </h2>

          {/* Fase 2: O sistema finaliza ponta a ponta */}
          <h2
            style={{
              position: 'absolute',
              margin: 0,
              fontSize: 42,
              fontWeight: 900,
              lineHeight: 1.25,
              color: '#FFFFFF',
              textAlign: 'center',
              textShadow: '0 4px 16px rgba(0,0,0,0.8)',
              textWrap: 'balance',
              opacity: speechSwitch,
              transform: `translateY(${(1 - speechSwitch) * 12}px)`,
            }}
          >
            O sistema finaliza o processo{' '}
            <span style={{color: '#FFA94D'}}>ponta a ponta</span>
          </h2>
        </div>
      </div>

      {/* Mockup 3D de Smartphone Ampliado (largura 920px, y=390 a 1300) */}
      <div
        style={{
          position: 'absolute',
          top: 390,
          left: 80,
          width: 920,
          height: 900,
          perspective: 1200,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 10,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            borderRadius: 44,
            background: '#111B21', // Dark WhatsApp background
            border: '4px solid rgba(255, 255, 255, 0.22)',
            boxShadow:
              '0 30px 70px rgba(0, 0, 0, 0.85), 0 0 35px rgba(255, 169, 77, 0.18)',
            transform: `scale(${phoneSpring * phoneScale}) rotateY(${phoneRotateY}deg) rotateX(2deg) translateY(${phoneFloatY}px)`,
            opacity: phoneSpring,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Header do WhatsApp no Smartphone */}
          <div
            style={{
              height: 116,
              backgroundColor: '#202C33',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              padding: '0 28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexShrink: 0,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              {/* Avatar da marca */}
              <div
                style={{
                  width: 66,
                  height: 66,
                  borderRadius: '50%',
                  backgroundColor: '#FFA94D',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#1F2937',
                  boxShadow: '0 4px 12px rgba(255,169,77,0.4)',
                }}
              >
                IA
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontSize: 36,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                  }}
                >
                  Agenda IA
                </span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#25D366',
                    lineHeight: 1.2,
                  }}
                >
                  ● Online 24h
                </span>
              </div>
            </div>

            {/* Selo Simulação exigido pelo manual */}
            <div
              style={{
                padding: '8px 18px',
                borderRadius: 14,
                backgroundColor: 'rgba(255, 255, 255, 0.12)',
                border: '1px solid rgba(255, 255, 255, 0.22)',
                fontSize: 32,
                fontWeight: 700,
                color: '#E5E7EB',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              Simulação
            </div>
          </div>

          {/* Área de Mensagens (Chat Wall) */}
          <div
            style={{
              flex: 1,
              padding: '24px 28px',
              display: 'flex',
              flexDirection: 'column',
              gap: 20,
              justifyContent: 'flex-start',
              backgroundImage:
                'radial-gradient(circle at center, rgba(255,169,77,0.03) 0%, transparent 70%)',
            }}
          >
            {/* Mensagem 1 - Cliente */}
            {frame >= 6 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '84%',
                  padding: '18px 24px',
                  borderRadius: '20px 20px 20px 4px',
                  backgroundColor: '#202C33',
                  border: '1px solid rgba(255, 255, 255, 0.14)',
                  boxShadow: '0 4px 14px rgba(0,0,0,0.35)',
                  transform: `scale(${msg1Spring})`,
                  opacity: msg1Spring,
                }}
              >
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Oi, tem vaga para quinta às 15h?
                </div>
                <div
                  style={{
                    fontSize: 32,
                    color: '#D1D5DB',
                    textAlign: 'right',
                    marginTop: 4,
                  }}
                >
                  14:32
                </div>
              </div>
            )}

            {/* Indicador de Digitando 1 */}
            {isTyping1 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  padding: '12px 24px',
                  borderRadius: '20px 20px 4px 20px',
                  backgroundColor: '#005C4B',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#E2E8F0',
                  }}
                >
                  digitando
                </span>
                <span
                  style={{
                    fontSize: 34,
                    color: '#FFA94D',
                    letterSpacing: '2px',
                  }}
                >
                  •••
                </span>
              </div>
            )}

            {/* Mensagem 2 - Empresa / IA */}
            {frame >= 46 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '86%',
                  padding: '18px 24px',
                  borderRadius: '20px 20px 4px 20px',
                  backgroundColor: '#005C4B',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.35)',
                  transform: `scale(${msg2Spring})`,
                  opacity: msg2Spring,
                }}
              >
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Tenho sim! Deseja confirmar para quinta às 15h?
                </div>
                <div
                  style={{
                    fontSize: 32,
                    color: '#A7F3D0',
                    textAlign: 'right',
                    marginTop: 4,
                  }}
                >
                  14:32 ✓✓
                </div>
              </div>
            )}

            {/* Mensagem 3 - Cliente com fonte padronizada e contraste nítido em branco */}
            {frame >= 80 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '84%',
                  padding: '18px 24px',
                  borderRadius: '20px 20px 20px 4px',
                  backgroundColor: '#202C33',
                  border: '1px solid rgba(255, 255, 255, 0.14)',
                  boxShadow: '0 4px 14px rgba(0,0,0,0.35)',
                  transform: `scale(${msg3Spring})`,
                  opacity: msg3Spring,
                }}
              >
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Sim, pode marcar.
                </div>
                <div
                  style={{
                    fontSize: 32,
                    color: '#D1D5DB',
                    textAlign: 'right',
                    marginTop: 4,
                  }}
                >
                  14:33
                </div>
              </div>
            )}

            {/* Indicador de Digitando 2 */}
            {isTyping2 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  padding: '12px 24px',
                  borderRadius: '20px 20px 4px 20px',
                  backgroundColor: '#005C4B',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#E2E8F0',
                  }}
                >
                  confirmando
                </span>
                <span
                  style={{
                    fontSize: 34,
                    color: '#FFA94D',
                    letterSpacing: '2px',
                  }}
                >
                  •••
                </span>
              </div>
            )}

            {/* Mensagem 4 - Empresa / IA Finalizando */}
            {frame >= 112 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '88%',
                  padding: '18px 24px',
                  borderRadius: '20px 20px 4px 20px',
                  backgroundColor: '#005C4B',
                  border: '1.5px solid #FFA94D',
                  boxShadow: '0 6px 20px rgba(255,169,77,0.3)',
                  transform: `scale(${msg4Spring})`,
                  opacity: msg4Spring,
                }}
              >
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  ✨ Perfeito! Horário reservado com sucesso na agenda.
                </div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginTop: 6,
                  }}
                >
                  <span
                    style={{
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#FFA94D',
                    }}
                  >
                    STATUS: CONFIRMADO
                  </span>
                  <span
                    style={{
                      fontSize: 32,
                      color: '#A7F3D0',
                    }}
                  >
                    14:33 ✓✓
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
