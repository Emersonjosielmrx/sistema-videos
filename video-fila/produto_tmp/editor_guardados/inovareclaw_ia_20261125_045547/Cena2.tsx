import React from 'react';
import {interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração: ~206 frames (6.85s)
  // Transição cinematográfica de entrada (zoom-in suave + fade conectando com a cena 1)
  const sceneEntranceScale = interpolate(frame, [0, 14], [0.92, 1.0], {extrapolateRight: 'clamp'});
  const sceneEntranceOpacity = interpolate(frame, [0, 8], [0.35, 1.0], {extrapolateRight: 'clamp'});
  const sceneEntranceY = interpolate(frame, [0, 12], [30, 0], {extrapolateRight: 'clamp'});

  // Câmera com zoom constante no fundo (>= 4% de movimento)
  const bgScale = interpolate(frame, [0, 206], [1.05, 1.18], {extrapolateRight: 'clamp'});

  // Movimento 3D suave e contínuo do celular (idle dinâmico)
  const phoneRotY = interpolate(frame, [0, 100, 206], [-4, 3, -2]);
  const phoneY = interpolate(frame, [0, 100, 206], [0, -12, 0]) + Math.sin(frame * 0.08) * 4;

  // Entrada em mola do celular
  const phoneEntrance = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Badge do topo no frame 4
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Mensagem 1 (Empresa): "Emita os relatórios de fechamento da semana..."
  const m1Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Indicador de digitação 1 (IA processando): frames 48 a 72
  const showTyping1 = frame >= 48 && frame < 74;

  // Mensagem 2 (Agente): "Entendido. Acessando sistemas e compilando o fechamento."
  const m2Spring = spring({
    frame: frame - 74,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Indicador de digitação 2 (IA finalizando): frames 108 a 128
  const showTyping2 = frame >= 108 && frame < 130;

  // Mensagem 3 (Agente): "Relatórios compilados e resumo enviado no canal da diretoria. ✓"
  const m3Spring = spring({
    frame: frame - 130,
    fps,
    config: {damping: 11, stiffness: 150},
  });

  // Card inferior de status do agente (preenche a área do celular): frame 148 em diante
  const statusSpring = spring({
    frame: frame - 148,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#070A12',
        opacity: sceneEntranceOpacity,
        transform: `scale(${sceneEntranceScale}) translateY(${sceneEntranceY}px)`,
        transformOrigin: 'center center',
      }}
    >
      {/* Imagem de fundo com desfoque e movimento contínuo */}
      <img
        src={staticFile('img_2.jpg')}
        alt="Fundo"
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          objectFit: 'cover',
          filter: 'blur(14px) brightness(0.35)',
          transform: `scale(${bgScale})`,
        }}
      />

      {/* Overlay gradiente escuro com toque de marca */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 35%, rgba(15, 23, 42, 0.55) 0%, rgba(9, 13, 24, 0.90) 75%, rgba(5, 7, 14, 0.98) 100%)',
        }}
      />

      {/* Brilho radial roxo sutil */}
      <div
        style={{
          position: 'absolute',
          top: 380,
          left: 140,
          width: 800,
          height: 600,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(124, 58, 237, 0.35) 0%, transparent 70%)',
          filter: 'blur(55px)',
          pointerEvents: 'none',
        }}
      />

      {/* Badge Superior: Rótulo "02 • COMO FUNCIONA" (y=165) */}
      {frame >= 4 && (
        <div
          style={{
            position: 'absolute',
            top: 165,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            transform: `scale(${badgeSpring})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 26px',
              borderRadius: 999,
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1.5px solid #7C3AED',
              boxShadow: '0 8px 24px rgba(124, 58, 237, 0.45)',
            }}
          >
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#7C3AED',
                boxShadow: '0 0 10px #A855F7',
                transform: `scale(${1 + Math.sin(frame * 0.2) * 0.2})`,
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              02 • COMO FUNCIONA
            </span>
          </div>
        </div>
      )}

      {/* Container de Perspectiva 3D do Celular */}
      <div
        style={{
          position: 'absolute',
          top: 240,
          left: 60,
          right: 60,
          height: 980,
          perspective: 1200,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <div
          style={{
            width: 880,
            height: 940,
            borderRadius: 36,
            background: '#0F172A',
            border: '3.5px solid #334155',
            boxShadow: '0 25px 60px rgba(0, 0, 0, 0.85), 0 0 45px rgba(124, 58, 237, 0.35)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            transform: `scale(${phoneEntrance}) translateY(${phoneY}px) rotateY(${phoneRotY}deg)`,
            transformOrigin: 'center center',
          }}
        >
          {/* Cabeçalho do App / Chat */}
          <div
            style={{
              height: 105,
              background: 'linear-gradient(180deg, #1E293B 0%, #0F172A 100%)',
              borderBottom: '1.5px solid #334155',
              padding: '0 24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              {/* Avatar do Agente */}
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #7C3AED 0%, #4C1D95 100%)',
                  border: '2px solid #8B5CF6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(124, 58, 237, 0.5)',
                }}
              >
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h1v2a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-2h1a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z" />
                  <circle cx="9" cy="13" r="1" fill="#FFFFFF" />
                  <circle cx="15" cy="13" r="1" fill="#FFFFFF" />
                </svg>
              </div>

              {/* Nome e Status */}
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    lineHeight: 1.1,
                  }}
                >
                  Inovare Claw
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#10B981',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    marginTop: 2,
                  }}
                >
                  <span style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: '#10B981'}} />
                  Agente IA • Online
                </div>
              </div>
            </div>

            {/* Selo Pequeno OBRIGATÓRIO: Simulação */}
            <div
              style={{
                background: 'rgba(30, 41, 59, 0.85)',
                border: '1.5px solid rgba(255, 255, 255, 0.25)',
                borderRadius: 8,
                padding: '6px 14px',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#CBD5E1',
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                }}
              >
                Simulação
              </span>
            </div>
          </div>

          {/* Área de Mensagens da Conversa (Sem vácuo preto inferior) */}
          <div
            style={{
              flex: 1,
              padding: '22px 24px',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              justifyContent: 'flex-start',
              position: 'relative',
            }}
          >
            {/* Mensagem 1 (Gestor / Empresa): Demanda corporativa concreta */}
            {frame >= 12 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '88%',
                  transform: `scale(${m1Spring}) translateY(${interpolate(m1Spring, [0, 1], [25, 0])}px)`,
                  opacity: m1Spring,
                }}
              >
                <div
                  style={{
                    background: '#1E293B',
                    border: '1.5px solid #334155',
                    borderRadius: '20px 20px 4px 20px',
                    padding: '16px 22px',
                    boxShadow: '0 4px 14px rgba(0,0,0,0.45)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#F8FAFC',
                      lineHeight: 1.3,
                      display: 'block',
                    }}
                  >
                    Emita os relatórios de fechamento da semana e envie o resumo no canal da diretoria.
                  </span>
                </div>
              </div>
            )}

            {/* Indicador de Digitação 1 (IA pensando) */}
            {showTyping1 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  background: '#2E1065',
                  border: '1.5px solid #7C3AED',
                  borderRadius: '20px 20px 20px 4px',
                  padding: '12px 22px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#C084FC', marginRight: 4}}>
                  Agente processando
                </span>
                <div style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: '#C084FC', transform: `translateY(${Math.sin(frame * 0.45) * 4}px)`}} />
                <div style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: '#C084FC', transform: `translateY(${Math.sin(frame * 0.45 + 1) * 4}px)`}} />
                <div style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: '#C084FC', transform: `translateY(${Math.sin(frame * 0.45 + 2) * 4}px)`}} />
              </div>
            )}

            {/* Mensagem 2 (Agente): Confirmação de execução independente */}
            {frame >= 74 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '88%',
                  transform: `scale(${m2Spring}) translateY(${interpolate(m2Spring, [0, 1], [25, 0])}px)`,
                  opacity: m2Spring,
                }}
              >
                <div
                  style={{
                    background: '#2E1065',
                    border: '1.5px solid #7C3AED',
                    borderRadius: '20px 20px 20px 4px',
                    padding: '16px 22px',
                    boxShadow: '0 6px 18px rgba(124, 58, 237, 0.35)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#FFFFFF',
                      lineHeight: 1.3,
                      display: 'block',
                    }}
                  >
                    Entendido. Coletando dados dos sistemas e compilando o fechamento de forma autônoma.
                  </span>
                </div>
              </div>
            )}

            {/* Indicador de Digitação 2 (IA finalizando) */}
            {showTyping2 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  background: '#2E1065',
                  border: '1.5px solid #7C3AED',
                  borderRadius: '20px 20px 20px 4px',
                  padding: '12px 22px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#C084FC', marginRight: 4}}>
                  Concluindo envio
                </span>
                <div style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: '#C084FC', transform: `translateY(${Math.sin(frame * 0.45) * 4}px)`}} />
                <div style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: '#C084FC', transform: `translateY(${Math.sin(frame * 0.45 + 1) * 4}px)`}} />
                <div style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: '#C084FC', transform: `translateY(${Math.sin(frame * 0.45 + 2) * 4}px)`}} />
              </div>
            )}

            {/* Mensagem 3 (Agente - Conclusão) */}
            {frame >= 130 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '90%',
                  transform: `scale(${m3Spring}) translateY(${interpolate(m3Spring, [0, 1], [20, 0])}px)`,
                  opacity: m3Spring,
                }}
              >
                <div
                  style={{
                    background: 'linear-gradient(135deg, #064E3B 0%, #065F46 100%)',
                    border: '2px solid #10B981',
                    borderRadius: '20px 20px 20px 4px',
                    padding: '16px 22px',
                    boxShadow: '0 8px 24px rgba(16, 185, 129, 0.45)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                  }}
                >
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      background: '#10B981',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </div>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                      lineHeight: 1.25,
                    }}
                  >
                    Relatórios gerados e resumo enviado no canal da diretoria.
                  </span>
                </div>
              </div>
            )}

            {/* Painel Ativo de Execução Autônoma — Preenche harmonicamente a área inferior do mockup */}
            {frame >= 148 && (
              <div
                style={{
                  marginTop: 'auto',
                  transform: `scale(${statusSpring})`,
                  opacity: statusSpring,
                }}
              >
                <div
                  style={{
                    background: 'rgba(15, 23, 42, 0.88)',
                    border: '1.5px solid rgba(124, 58, 237, 0.45)',
                    borderRadius: 18,
                    padding: '12px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                    <div
                      style={{
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        backgroundColor: '#10B981',
                        boxShadow: '0 0 8px #10B981',
                        transform: `scale(${1 + Math.sin(frame * 0.3) * 0.2})`,
                      }}
                    />
                    <span style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#E2E8F0'}}>
                      Autonomia do início ao fim
                    </span>
                  </div>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 30,
                      fontWeight: 800,
                      color: '#C084FC',
                      textTransform: 'uppercase',
                    }}
                  >
                    Executado ✓
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Barra Inferior Mobile */}
          <div
            style={{
              height: 76,
              background: '#0B1120',
              borderTop: '1px solid #1E293B',
              padding: '0 20px',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <div
              style={{
                flex: 1,
                height: 44,
                background: '#1E293B',
                borderRadius: 22,
                display: 'flex',
                alignItems: 'center',
                padding: '0 18px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              <span style={{fontFamily, fontSize: 32, fontWeight: 600, color: '#64748B'}}>
                Mensagem para o agente...
              </span>
            </div>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: '50%',
                background: '#7C3AED',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(124, 58, 237, 0.5)',
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
