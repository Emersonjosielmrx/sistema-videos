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

  // Movimento de câmera contínuo no fundo (zoom 1.02 -> 1.12)
  const bgScale = interpolate(frame, [0, 258], [1.02, 1.12], {
    extrapolateRight: 'clamp',
  });

  // Movimento 3D suave do celular
  const phoneRotY = interpolate(frame, [0, 258], [-4, 3], {
    extrapolateRight: 'clamp',
  });
  const phoneScale = interpolate(frame, [0, 258], [0.98, 1.02], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Mockup do Celular (frame 8 = ~0.27s)
  const phoneEnter = spring({
    frame: frame - 8,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Timings dos passos 1-2-3 sincronizados com a fala
  const step1Active = frame >= 138;
  const step2Active = frame >= 155;
  const step3Active = frame >= 182;

  // Molas das mensagens escalonadas ao longo de toda a cena
  const msg1Spring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const msg2Spring = spring({
    frame: frame - 78,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const msg3Spring = spring({
    frame: frame - 110,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const msg4Spring = spring({
    frame: frame - 138,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const msg5Spring = spring({
    frame: frame - 170,
    fps,
    config: {damping: 14, stiffness: 120},
  });
  const msg6Spring = spring({
    frame: frame - 192,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Efeito digitando entre frames 45 e 78
  const isTyping = frame >= 45 && frame < 78;

  // Conversa sem corte de rolagem: todos os balões se acomodam perfeitamente
  const chatScrollY = 0;

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* Imagem de Fundo com zoom contínuo e véu de alto contraste */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
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
              'linear-gradient(180deg, rgba(15,23,42,0.92) 0%, rgba(15,23,42,0.85) 50%, rgba(11,13,19,0.95) 100%)',
          }}
        />
      </div>

      {/* Topo: Badges e Barra de Etapas 1-2-3 (y: 160 a 305) */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 110,
          width: 860,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
          zIndex: 60,
        }}
      >
        {/* Linha superior: Rótulo + Selo Simulação */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            width: '100%',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '6px 20px',
              borderRadius: 20,
              backgroundColor: '#0B0D13',
              border: '2px solid #FFA94D',
              boxShadow: '0 4px 16px rgba(0,0,0,0.8)',
            }}
          >
            <span
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#FFA94D',
                boxShadow: '0 0 8px #FFA94D',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFA94D',
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              COMO FUNCIONA
            </span>
          </div>

          <div
            style={{
              padding: '6px 18px',
              borderRadius: 16,
              backgroundColor: '#0B0D13',
              border: '1.5px solid rgba(255,255,255,0.18)',
              fontFamily,
              fontSize: 34,
              fontWeight: 700,
              color: '#CBD5E1',
            }}
          >
            Selo: Simulação
          </div>
        </div>

        {/* Barra de Etapas 1-2-3 acendendo uma a uma conforme a fala cita */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            gap: 10,
            width: '100%',
          }}
        >
          {/* Passo 1: AGENDA */}
          <div
            style={{
              flex: 1,
              padding: '8px 8px',
              borderRadius: 16,
              backgroundColor: step1Active ? '#FFA94D' : 'rgba(11, 13, 19, 0.95)',
              border: `2px solid ${step1Active ? '#FFA94D' : 'rgba(255,255,255,0.14)'}`,
              boxShadow: step1Active
                ? '0 6px 18px rgba(255, 169, 77, 0.45)'
                : '0 4px 12px rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transform: `scale(${step1Active ? 1.03 : 1.0})`,
              transition: 'all 0.2s ease',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: step1Active ? '#0F172A' : '#CBD5E1',
                textTransform: 'uppercase',
                whiteSpace: 'nowrap',
              }}
            >
              {step1Active ? '✓ 1. AGENDA' : '1. AGENDA'}
            </span>
          </div>

          {/* Passo 2: CONFIRMA */}
          <div
            style={{
              flex: 1,
              padding: '8px 8px',
              borderRadius: 16,
              backgroundColor: step2Active ? '#FFA94D' : 'rgba(11, 13, 19, 0.95)',
              border: `2px solid ${step2Active ? '#FFA94D' : 'rgba(255,255,255,0.14)'}`,
              boxShadow: step2Active
                ? '0 6px 18px rgba(255, 169, 77, 0.45)'
                : '0 4px 12px rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transform: `scale(${step2Active ? 1.03 : 1.0})`,
              transition: 'all 0.2s ease',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: step2Active ? '#0F172A' : '#CBD5E1',
                textTransform: 'uppercase',
                whiteSpace: 'nowrap',
              }}
            >
              {step2Active ? '✓ 2. CONFIRMA' : '2. CONFIRMA'}
            </span>
          </div>

          {/* Passo 3: REAGENDA */}
          <div
            style={{
              flex: 1,
              padding: '8px 8px',
              borderRadius: 16,
              backgroundColor: step3Active ? '#FFA94D' : 'rgba(11, 13, 19, 0.95)',
              border: `2px solid ${step3Active ? '#FFA94D' : 'rgba(255,255,255,0.14)'}`,
              boxShadow: step3Active
                ? '0 6px 18px rgba(255, 169, 77, 0.45)'
                : '0 4px 12px rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transform: `scale(${step3Active ? 1.03 : 1.0})`,
              transition: 'all 0.2s ease',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: step3Active ? '#0F172A' : '#CBD5E1',
                textTransform: 'uppercase',
                whiteSpace: 'nowrap',
              }}
            >
              {step3Active ? '✓ 3. REAGENDA' : '3. REAGENDA'}
            </span>
          </div>
        </div>
      </div>

      {/* Mockup de Celular 3D (y: 335 a 1295, largura 860px) */}
      <div
        style={{
          position: 'absolute',
          top: 335,
          left: 110,
          width: 860,
          height: 960,
          perspective: 1200,
          zIndex: 50,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            backgroundColor: '#0B0D13',
            borderRadius: 36,
            border: '2.5px solid rgba(255, 255, 255, 0.16)',
            boxShadow:
              '0 30px 70px rgba(0, 0, 0, 0.9), inset 0 0 20px rgba(255, 255, 255, 0.05)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            transform: `scale(${Math.max(0, phoneEnter) * phoneScale}) rotateY(${phoneRotY}deg)`,
            transformOrigin: 'center center',
          }}
        >
          {/* Topo do Celular / WhatsApp Header */}
          <div
            style={{
              height: 92,
              backgroundColor: '#1F2937',
              borderBottom: '1.5px solid rgba(255,255,255,0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 28px',
              zIndex: 10,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: '50%',
                  backgroundColor: '#FFA94D',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 900,
                  fontSize: 26,
                  color: '#0F172A',
                }}
              >
                IA
              </div>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Agenda IA
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#4ADE80',
                  }}
                >
                  ● Online • Atendimento 24h
                </span>
              </div>
            </div>

            <div
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 700,
                color: '#FFA94D',
                backgroundColor: 'rgba(255, 169, 77, 0.15)',
                padding: '6px 16px',
                borderRadius: 12,
              }}
            >
              WhatsApp
            </div>
          </div>

          {/* Área de Conversa com Scroll Suave */}
          <div
            style={{
              flex: 1,
              padding: '20px 24px',
              display: 'flex',
              flexDirection: 'column',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                transform: `translateY(${chatScrollY}px)`,
                display: 'flex',
                flexDirection: 'column',
                gap: 14,
                transition: 'transform 0.3s ease-out',
              }}
            >
              {/* Mensagem 1: Cliente (Frame >= 16) */}
              {frame >= 16 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '82%',
                    backgroundColor: '#005C4B',
                    padding: '14px 20px',
                    borderRadius: '20px 20px 4px 20px',
                    transform: `scale(${Math.max(0, msg1Spring)})`,
                    opacity: Math.min(1, msg1Spring),
                    boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 35,
                      fontWeight: 700,
                      color: '#FFFFFF',
                      lineHeight: 1.25,
                    }}
                  >
                    Oi! Queria marcar um horário para quinta.
                  </span>
                </div>
              )}

              {/* Indicador Digitando */}
              {isTyping && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    backgroundColor: '#1E293B',
                    padding: '10px 18px',
                    borderRadius: '20px 20px 20px 4px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    border: '1px solid rgba(255,255,255,0.1)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#FFA94D',
                    }}
                  >
                    IA digitando...
                  </span>
                </div>
              )}

              {/* Mensagem 2: Empresa / IA (Frame >= 110) */}
              {frame >= 110 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '84%',
                    backgroundColor: '#1E293B',
                    borderLeft: '5px solid #FFA94D',
                    padding: '14px 20px',
                    borderRadius: '4px 20px 20px 20px',
                    transform: `scale(${Math.max(0, msg2Spring)})`,
                    opacity: Math.min(1, msg2Spring),
                    boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 35,
                      fontWeight: 700,
                      color: '#F8FAFC',
                      lineHeight: 1.25,
                    }}
                  >
                    Olá! Tenho quinta às 15h ou às 17h. Qual prefere?
                  </span>
                </div>
              )}

              {/* Mensagem 3: Cliente (Frame >= 146) */}
              {frame >= 146 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '75%',
                    backgroundColor: '#005C4B',
                    padding: '12px 20px',
                    borderRadius: '20px 20px 4px 20px',
                    transform: `scale(${Math.max(0, msg3Spring)})`,
                    opacity: Math.min(1, msg3Spring),
                    boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 35,
                      fontWeight: 700,
                      color: '#FFFFFF',
                    }}
                  >
                    15h está ótimo.
                  </span>
                </div>
              )}

              {/* Mensagem 4: IA Confirmação (Frame >= 160) */}
              {frame >= 160 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '86%',
                    backgroundColor: '#1E293B',
                    borderLeft: '5px solid #4ADE80',
                    padding: '14px 20px',
                    borderRadius: '4px 20px 20px 20px',
                    transform: `scale(${Math.max(0, msg4Spring)})`,
                    opacity: Math.min(1, msg4Spring),
                    boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 35,
                      fontWeight: 700,
                      color: '#F8FAFC',
                      lineHeight: 1.25,
                    }}
                  >
                    ✓ Agendado para quinta, às 15h. Vou confirmar na véspera.
                  </span>
                </div>
              )}

              {/* Mensagem 5: Cliente Reagendamento (Frame >= 186) */}
              {frame >= 186 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '82%',
                    backgroundColor: '#005C4B',
                    padding: '12px 20px',
                    borderRadius: '20px 20px 4px 20px',
                    transform: `scale(${Math.max(0, msg5Spring)})`,
                    opacity: Math.min(1, msg5Spring),
                    boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 35,
                      fontWeight: 700,
                      color: '#FFFFFF',
                      lineHeight: 1.25,
                    }}
                  >
                    Preciso remarcar para sexta.
                  </span>
                </div>
              )}

              {/* Mensagem 6: IA Reagendamento Sucesso (Frame >= 198) */}
              {frame >= 198 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '86%',
                    backgroundColor: '#1E293B',
                    borderLeft: '5px solid #FFA94D',
                    padding: '14px 20px',
                    borderRadius: '4px 20px 20px 20px',
                    transform: `scale(${Math.max(0, msg6Spring)})`,
                    opacity: Math.min(1, msg6Spring),
                    boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#FFA94D',
                      lineHeight: 1.25,
                    }}
                  >
                    Sem problema! Reagendei para sexta, às 15h.
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Barra Inferior Nativa do WhatsApp */}
          <div
            style={{
              height: 72,
              backgroundColor: '#1F2937',
              borderTop: '1.5px solid rgba(255,255,255,0.08)',
              display: 'flex',
              alignItems: 'center',
              padding: '0 20px',
              gap: 12,
              zIndex: 10,
            }}
          >
            <div
              style={{
                flex: 1,
                height: 48,
                borderRadius: 24,
                backgroundColor: '#0F172A',
                border: '1px solid rgba(255,255,255,0.12)',
                display: 'flex',
                alignItems: 'center',
                padding: '0 18px',
                gap: 10,
              }}
            >
              <span style={{fontSize: 26, color: '#94A3B8'}}>😊</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  color: '#94A3B8',
                  fontWeight: 600,
                }}
              >
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
                fontSize: 24,
                color: '#FFFFFF',
              }}
            >
              🎤
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
