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

interface Cena2Props {
  fontFamily: string;
}

export const Cena2: React.FC<Cena2Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração local: ~223 frames (13.18s a 20.61s)
  // Fundo com movimento contínuo
  const bgScale = interpolate(frame, [0, 223], [1.06, 1.18], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 223], [-25, 25], {
    extrapolateRight: 'clamp',
  });

  // Movimento sutil do celular (flutuação contínua)
  const phoneFloatY = Math.sin(frame / 15) * 5;

  // Entrada do Topo
  const topSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Celular Mockup (frame 0 a 12)
  const phoneSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // CADÊNCIA ÁGIL E SEM VAZIO VISUAL:
  // Balão 1: Membro Lucas entra logo no início (frame 2)
  const b1Spring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Indicador Digitando 1: surge aos 0.2s (frame 6 a 21)
  const isTyping1 = frame >= 6 && frame < 22;

  // Balão 2: Bot responde no jargão da comunidade aos ~0.7s (frame 22)
  const b2Spring = spring({
    frame: frame - 22,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Balão 3: Membro Marina entra aos ~16.5s (frame 98 na locução "e as orientações", q08) com mola nativa
  const b3Spring = spring({
    frame: frame - 98,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Indicador Digitando 2: ativo entre frame 124 e 140
  const isTyping2 = frame >= 124 && frame < 140;

  // Balão 4: Bot responde no contexto técnico da comunidade aos ~17.9s (frame 140, na locução "conforme o contexto")
  const b4Spring = spring({
    frame: frame - 140,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Scroll vertical suave do chat para acomodar as novas mensagens em q09 sem cortar o topo
  const chatScrollY = interpolate(frame, [138, 155], [0, -36], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Status Bar do Prompt Dinâmico entra em q09 (~18.6s -> frame 162, na locução "da comunidade")
  const statusBarSpring = spring({
    frame: frame - 162,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Saída suave da cena nos últimos 10 frames
  const exitOpacity = interpolate(frame, [213, 223], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Animação dos pontinhos de digitação
  const dot1 = (Math.sin(frame * 0.45) + 1) / 2;
  const dot2 = (Math.sin(frame * 0.45 + 1.2) + 1) / 2;
  const dot3 = (Math.sin(frame * 0.45 + 2.4) + 1) / 2;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#111827',
        fontFamily,
        opacity: exitOpacity,
        overflow: 'hidden',
      }}
    >
      {/* Fundo com movimento */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translateX(${bgTranslateX}px)`,
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
        {/* Camada escura fosca */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(20, 184, 166, 0.15) 0%, rgba(17, 24, 39, 0.94) 80%)',
          }}
        />
      </AbsoluteFill>

      {/* Partículas / Orbes sutis de luz ambiente pulsando no fundo */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: 120,
          width: 460,
          height: 460,
          borderRadius: '50%',
          background: 'rgba(20, 184, 166, 0.16)',
          filter: 'blur(80px)',
          transform: `scale(${1 + Math.sin(frame / 14) * 0.12})`,
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 340,
          right: 90,
          width: 440,
          height: 440,
          borderRadius: '50%',
          background: 'rgba(13, 148, 136, 0.2)',
          filter: 'blur(85px)',
          transform: `scale(${1 - Math.sin(frame / 16) * 0.12})`,
          pointerEvents: 'none',
        }}
      />

      {/* TOPO INFORMATIVO (y=160 a 330) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          opacity: topSpring,
          transform: `translateY(${(1 - topSpring) * 20}px)`,
          zIndex: 30,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 30,
            background: 'rgba(20, 184, 166, 0.18)',
            border: '1.5px solid rgba(20, 184, 166, 0.7)',
            boxShadow: '0 0 20px rgba(20, 184, 166, 0.3)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#14B8A6',
              boxShadow: '0 0 10px #14B8A6',
            }}
          />
          <span
            style={{
              color: '#5EEAD4',
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            ETAPA 2/3 • COMO FUNCIONA
          </span>
        </div>

        <div
          style={{
            fontSize: 42,
            fontWeight: 900,
            color: '#FFFFFF',
            textAlign: 'center',
            lineHeight: 1.25,
            textShadow: '0 4px 14px rgba(0,0,0,0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
          }}
        >
          <span>PROMPT DINÂMICO:</span>
          <span
            style={{
              color: '#14B8A6',
              background: 'rgba(20, 184, 166, 0.15)',
              padding: '4px 16px',
              borderRadius: 14,
              border: '1px solid rgba(20, 184, 166, 0.4)',
              whiteSpace: 'nowrap',
            }}
          >
            TOM ADAPTÁVEL
          </span>
        </div>
      </div>

      {/* ÁREA CENTRAL (y=320 a 1380): SMARTPHONE MOCKUP COM INTERFACE REAL DE GRUPO DA COMUNIDADE */}
      <div
        style={{
          position: 'absolute',
          top: 320,
          left: '50%',
          marginLeft: -460,
          width: 920,
          height: 1060,
          transform: `translateY(${phoneFloatY}px) scale(${0.95 + phoneSpring * 0.05})`,
          background: '#0B141A',
          border: '3.5px solid rgba(20, 184, 166, 0.6)',
          borderRadius: 44,
          boxShadow:
            '0 30px 80px rgba(0,0,0,0.85), 0 0 40px rgba(20, 184, 166, 0.25)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 20,
        }}
      >
        {/* Notch / Speaker bar superior do Smartphone */}
        <div
          style={{
            height: 28,
            backgroundColor: '#070D11',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
            borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
          }}
        >
          <div
            style={{
              width: 70,
              height: 6,
              borderRadius: 3,
              backgroundColor: '#1E293B',
            }}
          />
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: '#1E293B',
            }}
          />
        </div>

        {/* Cabeçalho do Celular: Exibe o nome do grupo e identifica os membros */}
        <div
          style={{
            height: 98,
            backgroundColor: '#1F2C34',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 24px',
            borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
            zIndex: 10,
            position: 'relative',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            {/* Avatar do Grupo da Comunidade */}
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                backgroundColor: '#14B8A6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 15px rgba(20, 184, 166, 0.5)',
              }}
            >
              <svg width="30" height="30" viewBox="0 0 24 24" fill="none">
                <path
                  d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"
                  stroke="#FFFFFF"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />
                <circle
                  cx="9"
                  cy="7"
                  r="4"
                  stroke="#FFFFFF"
                  strokeWidth="2.5"
                />
                <path
                  d="M23 21v-2a4 4 0 00-3-3.87"
                  stroke="#FFFFFF"
                  strokeWidth="2.5"
                />
                <path
                  d="M16 3.13a4 4 0 010 7.75"
                  stroke="#FFFFFF"
                  strokeWidth="2.5"
                />
              </svg>
            </div>
            <div>
              <div style={{fontSize: 34, fontWeight: 800, color: '#E9EDEF'}}>
                Comunidade no WhatsApp
              </div>
              <div
                style={{
                  fontSize: 32,
                  color: '#94A3B8',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#14B8A6',
                  }}
                />
                Você, Lucas, Marina, Bot IA
              </div>
            </div>
          </div>

          {/* Selo Simulação Obrigatório */}
          <div
            style={{
              padding: '6px 16px',
              borderRadius: 12,
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: '#CBD5E1',
              fontSize: 32,
              fontWeight: 800,
              textTransform: 'uppercase',
            }}
          >
            Simulação
          </div>
        </div>

        {/* Corpo do Chat com Diálogo Orgânico do Grupo e Identificação dos Membros */}
        <div
          style={{
            flex: 1,
            padding: '18px 22px',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
            backgroundColor: '#0B141A',
            backgroundImage:
              'radial-gradient(rgba(20, 184, 166, 0.05) 1px, transparent 1px)',
            backgroundSize: '24px 24px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
              transform: `translateY(${chatScrollY}px)`,
              transition: 'transform 0.1s ease-out',
            }}
          >
            {/* Balão 1: Pergunta do membro Lucas no jargão do grupo (entra logo no frame 2) */}
            {frame >= 2 && (
              <div
                style={{
                  opacity: b1Spring,
                  transform: `translateX(${(1 - b1Spring) * -25}px)`,
                  alignSelf: 'flex-start',
                  maxWidth: '92%',
                  backgroundColor: '#202C33',
                  border: '1.5px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '18px 18px 18px 4px',
                  padding: '12px 18px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                }}
              >
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#5EEAD4',
                    marginBottom: 4,
                  }}
                >
                  Lucas (Membro)
                </div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.25,
                  }}
                >
                  E aí, turma! Onde vejo o resumo e os links da conversa de hoje?
                </div>
              </div>
            )}

            {/* Indicador Digitando 1: ativo imediatamente aos 0.2s (frame 6 a 21) */}
            {isTyping1 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  backgroundColor: 'rgba(5, 97, 98, 0.6)',
                  borderRadius: '16px 16px 4px 16px',
                  padding: '10px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#5EEAD4',
                    marginRight: 6,
                  }}
                >
                  digitando
                </span>
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#5EEAD4',
                    transform: `scale(${0.6 + dot1 * 0.5})`,
                  }}
                />
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#5EEAD4',
                    transform: `scale(${0.6 + dot2 * 0.5})`,
                  }}
                />
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#5EEAD4',
                    transform: `scale(${0.6 + dot3 * 0.5})`,
                  }}
                />
              </div>
            )}

            {/* Balão 2: Bot respondendo no jargão exato da comunidade com vocativo correto aos ~0.7s (frame 22) */}
            {frame >= 22 && (
              <div
                style={{
                  opacity: b2Spring,
                  transform: `translateX(${(1 - b2Spring) * 25}px)`,
                  alignSelf: 'flex-end',
                  maxWidth: '92%',
                  backgroundColor: '#005C4B',
                  border: '1.5px solid rgba(20, 184, 166, 0.45)',
                  borderRadius: '18px 18px 4px 18px',
                  padding: '12px 18px',
                  boxShadow: '0 6px 16px rgba(0,0,0,0.5)',
                }}
              >
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#A7F3D0',
                    marginBottom: 4,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span>Bot do Grupo</span>
                  <span
                    style={{
                      fontSize: 32,
                      background: 'rgba(255,255,255,0.2)',
                      padding: '2px 8px',
                      borderRadius: 8,
                    }}
                  >
                    IA
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.25,
                  }}
                >
                  Fala, dev! Ata tá salva e links organizados. Só colar no sprint!
                </div>
              </div>
            )}

            {/* Balão 3: Membro Marina entra aos ~16.5s (frame 98 na fala "e as orientações", q08) com mola nativa */}
            {frame >= 98 && (
              <div
                style={{
                  opacity: b3Spring,
                  transform: `translateY(${(1 - b3Spring) * 20}px) scale(${0.95 + b3Spring * 0.05})`,
                  alignSelf: 'flex-start',
                  maxWidth: '92%',
                  backgroundColor: '#202C33',
                  border: '1.5px solid rgba(255, 255, 255, 0.10)',
                  borderRadius: '18px 18px 18px 4px',
                  padding: '12px 18px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                }}
              >
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FCD34D',
                    marginBottom: 4,
                  }}
                >
                  Marina (Membro)
                </div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    lineHeight: 1.25,
                  }}
                >
                  Boa! Salvou demais, já peguei o link aqui 🙌
                </div>
              </div>
            )}

            {/* Indicador Digitando 2 (frame 124 a 140) */}
            {isTyping2 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  backgroundColor: 'rgba(5, 97, 98, 0.6)',
                  borderRadius: '16px 16px 4px 16px',
                  padding: '10px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#5EEAD4',
                    marginRight: 6,
                  }}
                >
                  digitando
                </span>
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#5EEAD4',
                    transform: `scale(${0.6 + dot1 * 0.5})`,
                  }}
                />
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#5EEAD4',
                    transform: `scale(${0.6 + dot2 * 0.5})`,
                  }}
                />
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#5EEAD4',
                    transform: `scale(${0.6 + dot3 * 0.5})`,
                  }}
                />
              </div>
            )}

            {/* Balão 4: Bot respondendo no tom orgânico (sem metalinguagem) aos ~17.9s (frame 140) */}
            {frame >= 140 && (
              <div
                style={{
                  opacity: b4Spring,
                  transform: `translateY(${(1 - b4Spring) * 20}px) scale(${0.95 + b4Spring * 0.05})`,
                  alignSelf: 'flex-end',
                  maxWidth: '92%',
                  backgroundColor: '#005C4B',
                  border: '1.5px solid rgba(20, 184, 166, 0.45)',
                  borderRadius: '18px 18px 4px 18px',
                  padding: '12px 18px',
                  boxShadow: '0 6px 16px rgba(0,0,0,0.5)',
                }}
              >
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#A7F3D0',
                    marginBottom: 4,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span>Bot do Grupo</span>
                  <span
                    style={{
                      fontSize: 32,
                      background: 'rgba(255,255,255,0.2)',
                      padding: '2px 8px',
                      borderRadius: 8,
                    }}
                  >
                    IA
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.25,
                  }}
                >
                  Fechado! Se precisar de algo da release, só chamar.
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Selo de contexto animado (entra em q09 no frame 162 sincronizado com a locução) */}
        {frame >= 162 && (
          <div
            style={{
              opacity: statusBarSpring,
              transform: `translateY(${(1 - statusBarSpring) * 15}px)`,
              backgroundColor: 'rgba(20, 184, 166, 0.18)',
              borderTop: '1.5px solid rgba(20, 184, 166, 0.45)',
              borderBottom: '1.5px solid rgba(20, 184, 166, 0.45)',
              padding: '10px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 12,
            }}
          >
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#14B8A6',
                boxShadow: '0 0 10px #14B8A6',
              }}
            />
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#5EEAD4',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              ✦ Tom ajustado à comunidade ✓
            </span>
          </div>
        )}

        {/* Barra inferior de entrada do WhatsApp */}
        <div
          style={{
            height: 76,
            backgroundColor: '#1F2C34',
            display: 'flex',
            alignItems: 'center',
            padding: '0 18px',
            gap: 12,
            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <div
            style={{
              flex: 1,
              height: 48,
              backgroundColor: '#2A3942',
              borderRadius: 24,
              display: 'flex',
              alignItems: 'center',
              padding: '0 18px',
              gap: 10,
            }}
          >
            <span style={{color: '#8696A0', fontSize: 32}}>😊</span>
            <span style={{color: '#8696A0', fontSize: 32, fontWeight: 500}}>
              Mensagem
            </span>
          </div>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              backgroundColor: '#00A884',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"
                fill="#FFFFFF"
              />
              <path
                d="M19 10v1a7 7 0 01-14 0v-1M12 18v5M8 23h8"
                stroke="#FFFFFF"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
