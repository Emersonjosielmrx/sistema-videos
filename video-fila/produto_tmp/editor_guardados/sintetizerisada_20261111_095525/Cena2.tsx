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
  cores: {
    marca: string;
    destaque: string;
    apoio: string;
    fundo_escuro: string;
  };
};

export const Cena2: React.FC<Props> = ({fontFamily, cores}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no fundo
  const bgScale = interpolate(frame, [0, 217], [1.1, 1.22], {
    extrapolateRight: 'clamp',
  });
  const bgPanX = interpolate(frame, [0, 217], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Entrada do celular e inclinação 3D sutil
  const phoneEnter = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Movimento contínuo de flutuação do celular (respiração 3D)
  const phoneRotateY = -4 + Math.sin(frame * 0.08) * 1.5;
  const phoneRotateX = 2 + Math.cos(frame * 0.08) * 1.0;
  const phoneFloatY = Math.sin(frame * 0.1) * 8;

  // Timings das mensagens sincronizados com a fala
  // Mensagem 1: Cliente ("O cliente pede para remarcar" ~12.62s -> local frame 15)
  const animMsg1 = spring({
    frame: frame - 15,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Digitando IA (~14.25s -> local frame 64 a 78)
  const digitandoVisivel = frame >= 64 && frame < 78;
  const dotWave = (offset: number) =>
    Math.sin((frame - 64) * 0.6 + offset) * 5;

  // Mensagem 2: Empresa ("e a inteligência artificial reorganiza" -> local frame 78)
  const animMsg2 = spring({
    frame: frame - 78,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Mensagem 3: Cliente ("reorganiza o horário" -> local frame 106)
  const animMsg3 = spring({
    frame: frame - 106,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Mensagem 4: Empresa ("direto na conversa" -> local frame 143)
  const animMsg4 = spring({
    frame: frame - 143,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Selo de confirmação animado (local frame 160)
  const animConfirm = spring({
    frame: frame - 160,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: cores.fundo_escuro,
        overflow: 'hidden',
      }}
    >
      {/* Fundo com Imagem Desfocada e Pan */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateX(${bgPanX}px)`,
          filter: 'blur(10px)',
          opacity: 0.35,
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </div>

      {/* Degradê de profundidade */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 50%, rgba(15, 23, 42, 0.7) 0%, rgba(10, 15, 28, 0.98) 100%)',
        }}
      />

      {/* Cabeçalho superior: y=165 a 290 */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
          zIndex: 20,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(31, 41, 55, 0.95)',
            border: `2px solid ${cores.destaque}`,
            borderRadius: 24,
            padding: '6px 20px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            boxShadow: `0 4px 15px rgba(0,0,0,0.5), 0 0 12px rgba(255, 169, 77, 0.3)`,
            marginBottom: 10,
          }}
        >
          <span style={{fontSize: 32}}>⚡</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: cores.destaque,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>

        <div
          style={{
            fontSize: 48,
            fontWeight: 900,
            color: '#FFFFFF',
            textAlign: 'center',
            lineHeight: 1.15,
            textShadow: '0 3px 12px rgba(0,0,0,0.8)',
          }}
        >
          Reorganização no WhatsApp
        </div>
      </div>

      {/* Mockup de Smartphone 3D (largura 840px, perfeitamente equilibrado) */}
      <div
        style={{
          position: 'absolute',
          top: 330,
          left: 120,
          width: 840,
          height: 870,
          transform: `perspective(1200px) rotateY(${phoneRotateY}deg) rotateX(${phoneRotateX}deg) translateY(${phoneFloatY}px) scale(${phoneEnter})`,
          transformOrigin: 'center center',
          borderRadius: 40,
          backgroundColor: '#0B141A',
          border: '4px solid rgba(255, 255, 255, 0.2)',
          boxShadow:
            '0 25px 60px rgba(0,0,0,0.85), 0 0 30px rgba(255, 169, 77, 0.2)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 15,
          fontFamily,
        }}
      >
        {/* Topo do WhatsApp / Barra de Status */}
        <div
          style={{
            height: 90,
            backgroundColor: '#1F2C34',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                backgroundColor: cores.destaque,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
                color: cores.apoio,
                fontWeight: 900,
              }}
            >
              IA
            </div>
            <div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                }}
              >
                Agenda IA
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#22C55E',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <span>●</span> Online • 24 Horas
              </div>
            </div>
          </div>

          {/* Selo Simulação Obrigatório */}
          <div
            style={{
              backgroundColor: 'rgba(255, 169, 77, 0.2)',
              border: `1.5px solid ${cores.destaque}`,
              borderRadius: 14,
              padding: '4px 14px',
              fontSize: 32,
              fontWeight: 800,
              color: cores.destaque,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            Simulação
          </div>
        </div>

        {/* Área de Mensagens da Conversa */}
        <div
          style={{
            flex: 1,
            backgroundColor: '#0B141A',
            padding: '24px 22px',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            justifyContent: 'flex-start',
          }}
        >
          {/* Mensagem 1: Cliente (direita) */}
          {frame >= 15 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '82%',
                opacity: animMsg1,
                transform: `scale(${animMsg1}) translateY(${interpolate(animMsg1, [0, 1], [20, 0])}px)`,
                backgroundColor: '#005C4B',
                borderRadius: '20px 20px 4px 20px',
                padding: '16px 20px',
                boxShadow: '0 4px 15px rgba(0,0,0,0.4)',
              }}
            >
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                Preciso mudar meu atendimento de hoje para amanhã.
              </div>
              <div
                style={{
                  fontSize: 32,
                  color: '#8696A0',
                  textAlign: 'right',
                  marginTop: 6,
                }}
              >
                13:42 ✓✓
              </div>
            </div>
          )}

          {/* Indicador Digitando... */}
          {digitandoVisivel && (
            <div
              style={{
                alignSelf: 'flex-start',
                backgroundColor: '#202C33',
                borderRadius: '18px 18px 18px 4px',
                padding: '14px 22px',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  backgroundColor: cores.destaque,
                  transform: `translateY(${dotWave(0)}px)`,
                }}
              />
              <span
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  backgroundColor: cores.destaque,
                  transform: `translateY(${dotWave(1)}px)`,
                }}
              />
              <span
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  backgroundColor: cores.destaque,
                  transform: `translateY(${dotWave(2)}px)`,
                }}
              />
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#8696A0',
                  marginLeft: 8,
                }}
              >
                IA digitando...
              </span>
            </div>
          )}

          {/* Mensagem 2: Empresa / IA (esquerda) */}
          {frame >= 78 && (
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '85%',
                opacity: animMsg2,
                transform: `scale(${animMsg2}) translateY(${interpolate(animMsg2, [0, 1], [20, 0])}px)`,
                backgroundColor: '#202C33',
                borderLeft: `4px solid ${cores.destaque}`,
                borderRadius: '20px 20px 20px 4px',
                padding: '16px 20px',
                boxShadow: '0 4px 15px rgba(0,0,0,0.4)',
              }}
            >
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                Sem problemas! Tenho amanhã às 14h ou 16h. Qual prefere?
              </div>
              <div
                style={{
                  fontSize: 32,
                  color: '#8696A0',
                  textAlign: 'right',
                  marginTop: 6,
                }}
              >
                13:42
              </div>
            </div>
          )}

          {/* Mensagem 3: Cliente (direita) */}
          {frame >= 106 && (
            <div
              style={{
                alignSelf: 'flex-end',
                maxWidth: '75%',
                opacity: animMsg3,
                transform: `scale(${animMsg3}) translateY(${interpolate(animMsg3, [0, 1], [20, 0])}px)`,
                backgroundColor: '#005C4B',
                borderRadius: '20px 20px 4px 20px',
                padding: '14px 20px',
                boxShadow: '0 4px 15px rgba(0,0,0,0.4)',
              }}
            >
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                Pode ser às 14h.
              </div>
              <div
                style={{
                  fontSize: 32,
                  color: '#8696A0',
                  textAlign: 'right',
                  marginTop: 4,
                }}
              >
                13:43 ✓✓
              </div>
            </div>
          )}

          {/* Mensagem 4: Empresa / IA (esquerda) */}
          {frame >= 143 && (
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '85%',
                opacity: animMsg4,
                transform: `scale(${animMsg4}) translateY(${interpolate(animMsg4, [0, 1], [20, 0])}px)`,
                backgroundColor: '#202C33',
                borderLeft: '4px solid #22C55E',
                borderRadius: '20px 20px 20px 4px',
                padding: '16px 20px',
                boxShadow: '0 4px 15px rgba(0,0,0,0.4)',
              }}
            >
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                Perfeito! Horário remarcado para amanhã às 14h.
              </div>
              <div
                style={{
                  fontSize: 32,
                  color: '#8696A0',
                  textAlign: 'right',
                  marginTop: 6,
                }}
              >
                13:43
              </div>

              {/* Tag de Confirmação Instantânea */}
              {frame >= 160 && (
                <div
                  style={{
                    marginTop: 10,
                    opacity: animConfirm,
                    transform: `scale(${animConfirm})`,
                    backgroundColor: 'rgba(34, 197, 94, 0.2)',
                    border: '1.5px solid #22C55E',
                    borderRadius: 10,
                    padding: '6px 12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span style={{fontSize: 28, color: '#22C55E'}}>✓</span>
                  <span
                    style={{
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#4ADE80',
                    }}
                  >
                    Horário atualizado na grade
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
