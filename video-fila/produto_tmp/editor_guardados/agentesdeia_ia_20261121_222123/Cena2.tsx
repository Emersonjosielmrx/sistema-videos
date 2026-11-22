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

  // Background zoom contínuo
  const bgScale = interpolate(frame, [0, 214], [1.05, 1.2], {
    extrapolateRight: 'clamp',
  });

  // Transição de entrada suave com rotação 3D e escala
  const enterSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const enterScale = interpolate(enterSpring, [0, 1], [0.88, 1.0]);
  const enterRotateY = interpolate(enterSpring, [0, 1], [-26, -10]);
  const enterRotateX = interpolate(enterSpring, [0, 1], [8, 2]);

  // Movimento de câmera 3D contínuo e orgânico no mockup (floating idle tilt)
  const idleRotateY = Math.sin(frame / 20) * 2.5;
  const idleRotateX = Math.cos(frame / 22) * 1.5;
  const idleFloatY = Math.sin(frame / 18) * 6;

  const phoneRotateY = enterRotateY + idleRotateY;
  const phoneRotateX = enterRotateX + idleRotateX;
  const phoneScale = enterScale * interpolate(frame, [0, 214], [1.0, 1.05]);
  const phoneTranslateY = idleFloatY;

  // Badge superior aos 0.2s (frame 6)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Resposta acelerada para não deixar a tela vazia:
  // Mensagem 1 (Cliente) entra aos 0.2s (frame 6)
  const msg1Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 15, stiffness: 140},
  });

  // Indicador de "digitando..." entre frame 18 (~0.6s) e frame 38 (~1.25s)
  const typingShow = frame >= 18 && frame < 38;
  const typingSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Mensagem 2 (Empresa) entra no frame 38 (~1.25s local / 14.0s global)
  const msg2Spring = spring({
    frame: frame - 38,
    fps,
    config: {damping: 15, stiffness: 130},
  });

  // Mensagem 3 (Empresa) entra no frame 78 (~2.6s local / 15.35s global)
  const msg3Spring = spring({
    frame: frame - 78,
    fps,
    config: {damping: 15, stiffness: 130},
  });

  // Transições de corte suave
  const enterOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitOpacity = interpolate(frame, [204, 214], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0B0F19',
        opacity: Math.min(enterOpacity, exitOpacity),
      }}
    >
      {/* Background com zoom */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale})`,
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
              'radial-gradient(circle at 50% 40%, rgba(16, 185, 129, 0.15) 0%, rgba(11, 15, 25, 0.9) 65%, #0B0F19 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Fundo dinâmico com telas de automação corporativa desfocadas */}
      <AbsoluteFill
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Card de automação 1 (topo direito) */}
        <div
          style={{
            position: 'absolute',
            top: 200,
            right: -20,
            width: 440,
            padding: '16px 24px',
            borderRadius: 20,
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1.5px solid rgba(16, 185, 129, 0.35)',
            filter: 'blur(3px)',
            opacity: 0.7,
            transform: `translateY(${Math.sin(frame / 15) * 8}px) rotate(4deg)`,
          }}
        >
          <div style={{fontFamily, fontSize: 26, fontWeight: 700, color: '#34D399'}}>
            ⚡ Automação Ativa
          </div>
          <div style={{fontFamily, fontSize: 22, color: '#94A3B8', marginTop: 4}}>
            Workflow: Pesquisa + Agenda
          </div>
        </div>

        {/* Card de automação 2 (inferior esquerdo) */}
        <div
          style={{
            position: 'absolute',
            bottom: 380,
            left: -30,
            width: 460,
            padding: '16px 24px',
            borderRadius: 20,
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1.5px solid rgba(16, 185, 129, 0.35)',
            filter: 'blur(4px)',
            opacity: 0.7,
            transform: `translateY(${Math.cos(frame / 16) * 8}px) rotate(-4deg)`,
          }}
        >
          <div style={{fontFamily, fontSize: 26, fontWeight: 700, color: '#10B981'}}>
            ✓ Tarefas Concluídas
          </div>
          <div style={{fontFamily, fontSize: 22, color: '#94A3B8', marginTop: 4}}>
            Status: 100% Executado
          </div>
        </div>
      </AbsoluteFill>

      {/* Badge Superior */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 30,
          opacity: badgeSpring,
          transform: `scale(${interpolate(badgeSpring, [0, 1], [0.85, 1])})`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 24,
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1.5px solid rgba(16, 185, 129, 0.5)',
            boxShadow: '0 4px 20px rgba(16, 185, 129, 0.25)',
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: '#10B981',
              boxShadow: '0 0 10px #10B981',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#10B981',
              textTransform: 'uppercase',
              letterSpacing: 2,
            }}
          >
            Como Funciona • Delegação com IA
          </span>
        </div>
      </div>

      {/* Mockup de Celular 3D (largura 920px, altura contida em 1040px para terminar em y=1280, liberando >100px para o Karaokê) */}
      <div
        style={{
          position: 'absolute',
          top: 240,
          left: 80,
          width: 920,
          height: 1040,
          perspective: 1200,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 20,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            borderRadius: 44,
            background: '#0F172A',
            border: '3px solid rgba(16, 185, 129, 0.45)',
            boxShadow:
              '0 30px 70px rgba(0, 0, 0, 0.85), 0 0 40px rgba(16, 185, 129, 0.25)',
            transform: `rotateY(${phoneRotateY}deg) rotateX(${phoneRotateX}deg) scale(${phoneScale}) translateY(${phoneTranslateY}px)`,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Header do WhatsApp Mockup */}
          <div
            style={{
              padding: '18px 24px',
              background: '#1E293B',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              {/* Avatar do Agente */}
              <div
                style={{
                  width: 62,
                  height: 62,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 15px rgba(16, 185, 129, 0.5)',
                  fontSize: 30,
                }}
              >
                🤖
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Agente Pessoal IA
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#34D399',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: '#10B981',
                    }}
                  />
                  Online agora
                </div>
              </div>
            </div>

            {/* Selo Simulação Obrigatório */}
            <div
              style={{
                padding: '6px 16px',
                borderRadius: 14,
                background: 'rgba(255, 255, 255, 0.12)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#CBD5E1',
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              Simulação
            </div>
          </div>

          {/* Área de Mensagens do Chat com layout proporcional e sem espaços ociosos */}
          <div
            style={{
              flex: 1,
              padding: '22px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: 18,
              background: '#0B1120',
            }}
          >
            {/* Mensagem 1: Cliente (direita) */}
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '88%',
                opacity: msg1Spring,
                transform: `scale(${interpolate(msg1Spring, [0, 1], [0.85, 1])}) translateY(${interpolate(msg1Spring, [0, 1], [20, 0])}px)`,
                background: '#047857',
                borderRadius: '24px 24px 6px 24px',
                padding: '16px 22px',
                boxShadow: '0 8px 20px rgba(0, 0, 0, 0.4)',
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.32,
                }}
              >
                Pode fazer o agendamento da reunião e a pesquisa de mercado?
              </div>
              <div
                style={{
                  marginTop: 6,
                  textAlign: 'right',
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 500,
                  color: '#A7F3D0',
                }}
              >
                09:41 ✓✓
              </div>
            </div>

            {/* Balão Digitando... ativo entre 0.6s e 1.25s local */}
            {typingShow && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  opacity: typingSpring,
                  background: '#1E293B',
                  borderRadius: '24px 24px 24px 6px',
                  padding: '14px 22px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  border: '1px solid rgba(255, 255, 255, 0.08)',
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
                  Agente digitando
                </span>
                <div style={{display: 'flex', gap: 6}}>
                  {[0, 1, 2].map((i) => {
                    const dotPhase = (frame * 0.2 + i * 0.6) % (Math.PI * 2);
                    const dotY = Math.sin(dotPhase) * 4;
                    return (
                      <span
                        key={i}
                        style={{
                          width: 10,
                          height: 10,
                          borderRadius: '50%',
                          backgroundColor: '#10B981',
                          transform: `translateY(${dotY}px)`,
                        }}
                      />
                    );
                  })}
                </div>
              </div>
            )}

            {/* Mensagem 2: Empresa/IA (esquerda) entra aos 1.25s (frame 38) */}
            {frame >= 37 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '90%',
                  opacity: msg2Spring,
                  transform: `scale(${interpolate(msg2Spring, [0, 1], [0.85, 1])}) translateY(${interpolate(msg2Spring, [0, 1], [20, 0])}px)`,
                  background: '#1E293B',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  borderRadius: '24px 24px 24px 6px',
                  padding: '16px 22px',
                  boxShadow: '0 8px 20px rgba(0, 0, 0, 0.4)',
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 38,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.32,
                  }}
                >
                  Claro! Tarefas assumidas. Já estou iniciando a pesquisa e
                  organizando o agendamento.
                </div>
                <div
                  style={{
                    marginTop: 6,
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 500,
                    color: '#64748B',
                  }}
                >
                  09:42
                </div>
              </div>
            )}

            {/* Mensagem 3: Empresa/IA Concluído (esquerda) entra aos 2.6s (frame 78) */}
            {frame >= 77 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '90%',
                  opacity: msg3Spring,
                  transform: `scale(${interpolate(msg3Spring, [0, 1], [0.85, 1])}) translateY(${interpolate(msg3Spring, [0, 1], [20, 0])}px)`,
                  background: 'rgba(16, 185, 129, 0.16)',
                  border: '1.5px solid rgba(16, 185, 129, 0.6)',
                  borderRadius: '24px 24px 24px 6px',
                  padding: '16px 22px',
                  boxShadow: '0 8px 25px rgba(16, 185, 129, 0.25)',
                }}
              >
                <div
                  style={{
                    fontFamily,
                    fontSize: 38,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.32,
                  }}
                >
                  Tudo pronto por aqui. Pesquisa concluída e reunião agendada na
                  sua pauta. ✓✓
                </div>
                <div
                  style={{
                    marginTop: 6,
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#34D399',
                  }}
                >
                  09:44 • Concluído
                </div>
              </div>
            )}
          </div>

          {/* Input Bar Simulado WhatsApp no rodapé */}
          <div
            style={{
              padding: '12px 20px',
              background: '#1E293B',
              borderTop: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <div
              style={{
                flex: 1,
                padding: '10px 18px',
                borderRadius: 20,
                background: 'rgba(255, 255, 255, 0.08)',
                fontFamily,
                fontSize: 28,
                color: '#64748B',
              }}
            >
              Mensagem...
            </div>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: '50%',
                background: '#10B981',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 22,
              }}
            >
              🎙️
            </div>
          </div>
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#34D399',
                  }}
                >
                  09:44 • Concluído
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
