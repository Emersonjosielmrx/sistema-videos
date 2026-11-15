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

  // Movimento de câmera 3D contínuo no Mockup do Celular
  const rotY = interpolate(frame, [0, 215], [9, -3], {
    extrapolateRight: 'clamp',
  });
  const rotX = interpolate(frame, [0, 215], [4, 1], {
    extrapolateRight: 'clamp',
  });
  const phoneScale = interpolate(frame, [0, 215], [0.98, 1.04], {
    extrapolateRight: 'clamp',
  });

  // Fundo com zoom lento
  const bgScale = interpolate(frame, [0, 215], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Top header spring (frame 2)
  const headerSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Balão 1 (Cliente) entra em 12.39s (relativo à cena: ~frame 15)
  const msg1Spring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 11, stiffness: 100},
  });

  // Evento Comercial acende em 13.59s (~frame 51) "oportunidade comercial"
  const event1Spring = spring({
    frame: frame - 51,
    fps,
    config: {damping: 10, stiffness: 120},
  });

  // Digitando antes da empresa (frame 70 a 88)
  const isTyping = frame >= 68 && frame < 90;
  const dotPulse = Math.floor(frame / 6) % 3;

  // Balão 2 (Empresa) entra em 14.80s (~frame 88)
  const msg2Spring = spring({
    frame: frame - 88,
    fps,
    config: {damping: 11, stiffness: 100},
  });

  // Evento Helpdesk acende em 15.74s (~frame 115) "chamado no helpdesk"
  const event2Spring = spring({
    frame: frame - 115,
    fps,
    config: {damping: 10, stiffness: 120},
  });

  // Balão 3 (Cliente) entra em 17.0s (~frame 152)
  const msg3Spring = spring({
    frame: frame - 152,
    fps,
    config: {damping: 11, stiffness: 100},
  });

  // Status Integrado Final (~frame 175)
  const integratedSpring = spring({
    frame: frame - 175,
    fps,
    config: {damping: 10, stiffness: 110},
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* Imagem de Fundo com blur e overlay elegante */}
      <AbsoluteFill style={{transform: `scale(${bgScale})`}}>
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(10px)',
          }}
        />
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(15,23,42,0.92) 0%, rgba(15,23,42,0.85) 50%, rgba(15,23,42,0.95) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Container Principal na Safe Zone */}
      <AbsoluteFill style={{padding: '0 60px'}}>
        {/* Header Superior: Rótulo e Título da Cena */}
        <div
          style={{
            position: 'absolute',
            top: 165,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            opacity: interpolate(headerSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(headerSpring, [0, 1], [-20, 0])}px)`,
          }}
        >
          <div
            style={{
              padding: '6px 20px',
              borderRadius: 20,
              background: 'rgba(31, 147, 255, 0.2)',
              border: '1.5px solid #1F93FF',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginBottom: 8,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#60A5FA',
                textTransform: 'uppercase',
                letterSpacing: 1.5,
              }}
            >
              COMO FUNCIONA
            </span>
          </div>

          <div
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              textAlign: 'center',
              lineHeight: 1.15,
              textTransform: 'uppercase',
              textShadow: '0 4px 20px rgba(0,0,0,0.8)',
            }}
          >
            TELA INTEGRADA: CRM + HELPDESK
          </div>
        </div>

        {/* Mockup 3D do Celular WhatsApp / Chatwoot */}
        <div
          style={{
            position: 'absolute',
            top: 285,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            perspective: 1200,
          }}
        >
          <div
            style={{
              width: 860,
              height: 820,
              borderRadius: 36,
              background: '#0F172A',
              border: '3px solid rgba(31, 147, 255, 0.65)',
              boxShadow:
                '0 25px 60px rgba(0,0,0,0.8), 0 0 35px rgba(31, 147, 255, 0.25)',
              overflow: 'hidden',
              transform: `scale(${phoneScale}) rotateY(${rotY}deg) rotateX(${rotX}deg)`,
              transformStyle: 'preserve-3d',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Barra de Status do Mockup */}
            <div
              style={{
                height: 72,
                backgroundColor: '#1E293B',
                borderBottom: '2px solid rgba(255,255,255,0.08)',
                padding: '0 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #1F93FF, #0284C7)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 24,
                    color: '#FFF',
                    fontWeight: 900,
                  }}
                >
                  C
                </div>
                <div>
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    Cliente (WhatsApp)
                  </div>
                </div>
              </div>

              {/* Selo Simulação Obrigatório */}
              <div
                style={{
                  padding: '4px 14px',
                  borderRadius: 12,
                  background: 'rgba(31, 147, 255, 0.18)',
                  border: '1.5px solid #1F93FF',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#60A5FA',
                    letterSpacing: 1,
                    textTransform: 'uppercase',
                  }}
                >
                  SIMULAÇÃO
                </span>
              </div>
            </div>

            {/* Corpo da Conversa */}
            <div
              style={{
                padding: '24px 24px 12px 24px',
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
              }}
            >
              {/* Balão 1 - Cliente */}
              {frame >= 14 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: 720,
                    padding: '16px 22px',
                    borderRadius: '20px 20px 20px 4px',
                    background: '#1E293B',
                    border: '1.5px solid rgba(255,255,255,0.12)',
                    boxShadow: '0 4px 15px rgba(0,0,0,0.4)',
                    opacity: interpolate(msg1Spring, [0, 1], [0, 1]),
                    transform: `translateY(${interpolate(msg1Spring, [0, 1], [20, 0])}px)`,
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#F8FAFC',
                      lineHeight: 1.25,
                    }}
                  >
                    "Bom dia, preciso de uma proposta e também de ajuda com a fatura."
                  </div>
                </div>
              )}

              {/* Evento Automático 1: Oportunidade Comercial */}
              {frame >= 50 && (
                <div
                  style={{
                    alignSelf: 'center',
                    padding: '10px 22px',
                    borderRadius: 16,
                    background: 'rgba(16, 185, 129, 0.2)',
                    border: '2px solid #10B981',
                    boxShadow: '0 4px 20px rgba(16,185,129,0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    opacity: interpolate(event1Spring, [0, 1], [0, 1]),
                    transform: `scale(${interpolate(event1Spring, [0, 1], [0.85, 1])})`,
                  }}
                >
                  <span style={{fontSize: 30}}>💼</span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#34D399',
                      textTransform: 'uppercase',
                    }}
                  >
                    Oportunidade Comercial Criada
                  </span>
                </div>
              )}

              {/* Indicador de Digitando */}
              {isTyping && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    padding: '12px 20px',
                    borderRadius: '20px 20px 4px 20px',
                    background: 'rgba(31, 147, 255, 0.25)',
                    border: '1px solid #1F93FF',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#93C5FD',
                    }}
                  >
                    Empresa digitando
                  </span>
                  <span style={{fontSize: 28, color: '#38BDF8'}}>
                    {dotPulse === 0 ? '•' : dotPulse === 1 ? '••' : '•••'}
                  </span>
                </div>
              )}

              {/* Balão 2 - Empresa */}
              {frame >= 87 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: 720,
                    padding: '16px 22px',
                    borderRadius: '20px 20px 4px 20px',
                    background: 'linear-gradient(135deg, #1F93FF 0%, #0284C7 100%)',
                    boxShadow: '0 6px 20px rgba(31,147,255,0.4)',
                    opacity: interpolate(msg2Spring, [0, 1], [0, 1]),
                    transform: `translateY(${interpolate(msg2Spring, [0, 1], [20, 0])}px)`,
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 700,
                      color: '#FFFFFF',
                      lineHeight: 1.25,
                    }}
                  >
                    "Encaminhei seu pedido comercial e criei seu ticket de suporte aqui no painel."
                  </div>
                </div>
              )}

              {/* Evento Automático 2: Ticket Helpdesk */}
              {frame >= 114 && (
                <div
                  style={{
                    alignSelf: 'center',
                    padding: '10px 22px',
                    borderRadius: 16,
                    background: 'rgba(56, 189, 248, 0.2)',
                    border: '2px solid #38BDF8',
                    boxShadow: '0 4px 20px rgba(56,189,248,0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    opacity: interpolate(event2Spring, [0, 1], [0, 1]),
                    transform: `scale(${interpolate(event2Spring, [0, 1], [0.85, 1])})`,
                  }}
                >
                  <span style={{fontSize: 30}}>🎫</span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#38BDF8',
                      textTransform: 'uppercase',
                    }}
                  >
                    Ticket Helpdesk Aberto
                  </span>
                </div>
              )}

              {/* Balão 3 - Cliente */}
              {frame >= 151 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: 720,
                    padding: '14px 22px',
                    borderRadius: '20px 20px 20px 4px',
                    background: '#1E293B',
                    border: '1.5px solid rgba(255,255,255,0.12)',
                    opacity: interpolate(msg3Spring, [0, 1], [0, 1]),
                    transform: `translateY(${interpolate(msg3Spring, [0, 1], [20, 0])}px)`,
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#F8FAFC',
                      lineHeight: 1.25,
                    }}
                  >
                    "Perfeito, muito obrigado pelo retorno rápido."
                  </div>
                </div>
              )}
            </div>

            {/* Input Bar do Mockup WhatsApp */}
            <div
              style={{
                marginTop: 'auto',
                height: 70,
                backgroundColor: '#1E293B',
                borderTop: '1.5px solid rgba(255,255,255,0.08)',
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
                  borderRadius: 22,
                  backgroundColor: '#0F172A',
                  border: '1px solid rgba(255,255,255,0.1)',
                  padding: '0 16px',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    color: '#64748B',
                  }}
                >
                  Mensagem...
                </span>
              </div>
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: '50%',
                  backgroundColor: '#1F93FF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 22,
                  color: '#FFFFFF',
                }}
              >
                🎙️
              </div>
            </div>
          </div>
        </div>

        {/* Rodapé da Cena: Selo de Consolidação */}
        {frame >= 170 && (
          <div
            style={{
              position: 'absolute',
              top: 1180,
              left: 60,
              right: 60,
              display: 'flex',
              justifyContent: 'center',
              opacity: interpolate(integratedSpring, [0, 1], [0, 1]),
              transform: `scale(${interpolate(integratedSpring, [0, 1], [0.9, 1])})`,
            }}
          >
            <div
              style={{
                padding: '14px 28px',
                borderRadius: 20,
                background: 'rgba(15, 23, 42, 0.94)',
                border: '2px solid #1F93FF',
                boxShadow: '0 8px 30px rgba(31,147,255,0.4)',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
              }}
            >
              <span style={{fontSize: 32}}>⚡</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  letterSpacing: 1,
                  textTransform: 'uppercase',
                }}
              >
                VENDAS E SUPORTE NA MESMA TELA
              </span>
            </div>
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
