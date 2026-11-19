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

interface Cena0Props {
  fontFamily: string;
}

export const Cena0: React.FC<Cena0Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera / fundo
  const bgScale = interpolate(frame, [0, 171], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 171], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Micro-animações contínuas
  const floatY = Math.sin(frame / 14) * 5;
  const pulseScale = 1 + Math.sin(frame / 12) * 0.02;

  // Pulso contínuo e vibrante na tarja vermelha de alerta "ASSIM?" (elimina aspecto estático nos primeiros 2s)
  const assimPulse = 1.03 + Math.sin(frame * 0.35) * 0.06;

  // Entrada do Badge superior (frame 0 a 14)
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Título direto: "SEU BOT RESPONDE ASSIM?"
  const titleSpring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Entrada do Smartphone Mockup realista preenchendo a área central (frame 0 a 16)
  const phoneSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // 1. Pergunta do membro presente logo no início
  const msgUserSpring = spring({
    frame: frame + 4,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Indicador Digitando do bot ativo rapidamente entre frame 4 e frame 16
  const isTyping = frame >= 4 && frame < 16;
  const dot1 = (Math.sin(frame * 0.45) + 1) / 2;
  const dot2 = (Math.sin(frame * 0.45 + 1.2) + 1) / 2;
  const dot3 = (Math.sin(frame * 0.45 + 2.4) + 1) / 2;

  // 2. Resposta fria do Bot Genérico entra rápida aos ~0.53s (frame 16) garantindo contraste imediato
  const msgBotSpring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // 3. Membro expressa dúvida no chat aos ~2.1s (frame 64)
  const msgUser2Spring = spring({
    frame: frame - 64,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Indicador Digitando 2 entre frame 82 e frame 98
  const isTyping2 = frame >= 82 && frame < 98;

  // 4. Segunda resposta mecânica do bot genérico aos ~3.3s (frame 98)
  const msgBot2Spring = spring({
    frame: frame - 98,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Transição dinâmica de saída para Cena 1: Whip Pan lateral veloz para a esquerda (frames 158 a 171)
  const whipPanX = interpolate(frame, [158, 171], [0, -1120], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitOpacity = interpolate(frame, [164, 171], [1, 0.2], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#111827',
        fontFamily,
        opacity: exitOpacity,
        transform: `translateX(${whipPanX}px)`,
        overflow: 'hidden',
      }}
    >
      {/* Imagem de Fundo com zoom e pan contínuos */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Camada sutil de proteção e profundidade */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 35%, rgba(20, 184, 166, 0.12) 0%, rgba(17, 24, 39, 0.90) 75%)',
          }}
        />
      </AbsoluteFill>

      {/* Partículas / Orbes sutis de luz ambiente pulsando no fundo escuro */}
      <div
        style={{
          position: 'absolute',
          top: 300,
          left: 100,
          width: 480,
          height: 480,
          borderRadius: '50%',
          background: 'rgba(20, 184, 166, 0.18)',
          filter: 'blur(80px)',
          transform: `scale(${1 + Math.sin(frame / 12) * 0.14})`,
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 340,
          right: 80,
          width: 440,
          height: 440,
          borderRadius: '50%',
          background: 'rgba(13, 148, 136, 0.2)',
          filter: 'blur(85px)',
          transform: `scale(${1 - Math.sin(frame / 14) * 0.14})`,
          pointerEvents: 'none',
        }}
      />

      {/* Grid tecnológico e linhas em movimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(20, 184, 166, 0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(20, 184, 166, 0.04) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
          backgroundPosition: `0px ${frame * 0.5}px`,
          pointerEvents: 'none',
        }}
      />

      {/* TOPO INFORMATIVO (y=165 a 290) */}
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
          zIndex: 25,
        }}
      >
        {/* Badge do Gancho */}
        <div
          style={{
            transform: `scale(${badgeSpring * pulseScale})`,
            opacity: badgeSpring,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 22px',
            borderRadius: 30,
            background: 'rgba(20, 184, 166, 0.16)',
            border: '1.5px solid rgba(20, 184, 166, 0.65)',
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
            COMUNIDADES & WHATSAPP
          </span>
        </div>

        {/* Chamada Direta com Tarja Vermelha "ASSIM?" Pulsante Contínua */}
        <div
          style={{
            opacity: titleSpring,
            transform: `translateY(${(1 - titleSpring) * 18}px)`,
            fontSize: 52,
            fontWeight: 900,
            color: '#FFFFFF',
            lineHeight: 1.15,
            textShadow: '0 4px 16px rgba(0,0,0,0.85)',
            textAlign: 'center',
          }}
        >
          SEU BOT RESPONDE{' '}
          <span
            style={{
              display: 'inline-block',
              transform: `scale(${assimPulse})`,
              background: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
              color: '#FFFFFF',
              padding: '4px 20px',
              borderRadius: 16,
              boxShadow:
                '0 6px 22px rgba(239, 68, 68, 0.55), 0 0 18px rgba(239, 68, 68, 0.4)',
            }}
          >
            ASSIM?
          </span>
        </div>
      </div>

      {/* ÁREA CENTRAL (y=310 a 1380): MOCKUP REALISTA DE SMARTPHONE PREENCHENDO A TELA */}
      <div
        style={{
          position: 'absolute',
          top: 310,
          left: '50%',
          marginLeft: -460,
          width: 920,
          height: 1070,
          transform: `translateY(${floatY}px) scale(${0.96 + phoneSpring * 0.04})`,
          opacity: phoneSpring,
          background: '#0B141A',
          border: '3.5px solid rgba(20, 184, 166, 0.55)',
          borderRadius: 44,
          boxShadow:
            '0 30px 80px rgba(0, 0, 0, 0.85), 0 0 40px rgba(20, 184, 166, 0.25)',
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

        {/* Cabeçalho do Celular (WhatsApp Dark Header com Identidade de Grupo) */}
        <div
          style={{
            height: 96,
            backgroundColor: '#1F2C34',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 24px',
            borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
            zIndex: 10,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                backgroundColor: '#14B8A6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 14px rgba(20, 184, 166, 0.4)',
              }}
            >
              {/* Ícone de grupo de pessoas */}
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
                  marginTop: 2,
                }}
              >
                Membros ativos
              </div>
            </div>
          </div>
          <span
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
          </span>
        </div>

        {/* Corpo do Chat com Mensagens Sequenciais Sincronizadas */}
        <div
          style={{
            flex: 1,
            padding: '24px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            backgroundColor: '#0B141A',
            backgroundImage:
              'radial-gradient(rgba(20, 184, 166, 0.05) 1px, transparent 1px)',
            backgroundSize: '24px 24px',
            overflow: 'hidden',
          }}
        >
          {/* Mensagem 1: Membro da Comunidade (visível desde o início) */}
          <div
            style={{
              opacity: msgUserSpring,
              transform: `translateX(${(1 - msgUserSpring) * -25}px) scale(${0.96 + msgUserSpring * 0.04})`,
              alignSelf: 'flex-start',
              maxWidth: '92%',
              background: '#202C33',
              border: '1.5px solid rgba(255, 255, 255, 0.10)',
              borderRadius: '20px 20px 20px 4px',
              padding: '16px 22px',
              boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
            }}
          >
            <div
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#5EEAD4',
                marginBottom: 6,
              }}
            >
              Membro do Grupo
            </div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 600,
                color: '#FFFFFF',
                lineHeight: 1.3,
              }}
            >
              Como funciona a participação nos eventos desta semana?
            </div>
          </div>

          {/* Indicador Digitando do Bot Genérico (ativo frame 4 a 16) */}
          {isTyping && (
            <div
              style={{
                alignSelf: 'flex-end',
                backgroundColor: 'rgba(239, 68, 68, 0.22)',
                border: '1px solid rgba(239, 68, 68, 0.4)',
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
                  color: '#FCA5A5',
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
                  backgroundColor: '#EF4444',
                  transform: `scale(${0.6 + dot1 * 0.5})`,
                }}
              />
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: '#EF4444',
                  transform: `scale(${0.6 + dot2 * 0.5})`,
                }}
              />
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: '#EF4444',
                  transform: `scale(${0.6 + dot3 * 0.5})`,
                }}
              />
            </div>
          )}

          {/* Mensagem 2: Resposta fria/engessada do Bot Genérico (entra aos ~0.53s -> frame 16) */}
          {frame >= 16 && (
            <div
              style={{
                opacity: msgBotSpring,
                transform: `translateX(${(1 - msgBotSpring) * 25}px) scale(${0.96 + msgBotSpring * 0.04})`,
                alignSelf: 'flex-end',
                maxWidth: '92%',
                background: 'rgba(239, 68, 68, 0.16)',
                border: '1.5px solid rgba(239, 68, 68, 0.55)',
                borderRadius: '20px 20px 4px 20px',
                padding: '16px 22px',
                boxShadow: '0 6px 20px rgba(0,0,0,0.3)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  marginBottom: 6,
                }}
              >
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#EF4444',
                    boxShadow: '0 0 8px #EF4444',
                  }}
                />
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FCA5A5',
                    textTransform: 'uppercase',
                  }}
                >
                  Bot Padrão
                </span>
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                Olá, usuário. Consulte a descrição do grupo para mais detalhes.
              </div>
            </div>
          )}

          {/* Mensagem 3: Membro com dúvida de follow-up (entra aos ~2.1s -> frame 64) */}
          {frame >= 64 && (
            <div
              style={{
                opacity: msgUser2Spring,
                transform: `translateX(${(1 - msgUser2Spring) * -25}px) scale(${0.96 + msgUser2Spring * 0.04})`,
                alignSelf: 'flex-start',
                maxWidth: '92%',
                background: '#202C33',
                border: '1.5px solid rgba(255, 255, 255, 0.10)',
                borderRadius: '20px 20px 20px 4px',
                padding: '16px 22px',
                boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
              }}
            >
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#5EEAD4',
                  marginBottom: 6,
                }}
              >
                Membro do Grupo
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                Mas onde fica essa descrição? Alguém pode ajudar?
              </div>
            </div>
          )}

          {/* Indicador Digitando 2 */}
          {isTyping2 && (
            <div
              style={{
                alignSelf: 'flex-end',
                backgroundColor: 'rgba(239, 68, 68, 0.22)',
                border: '1px solid rgba(239, 68, 68, 0.4)',
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
                  color: '#FCA5A5',
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
                  backgroundColor: '#EF4444',
                  transform: `scale(${0.6 + dot1 * 0.5})`,
                }}
              />
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: '#EF4444',
                  transform: `scale(${0.6 + dot2 * 0.5})`,
                }}
              />
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: '#EF4444',
                  transform: `scale(${0.6 + dot3 * 0.5})`,
                }}
              />
            </div>
          )}

          {/* Mensagem 4: Segunda resposta fria e automática do bot padrão (entra aos ~3.3s -> frame 98) */}
          {frame >= 98 && (
            <div
              style={{
                opacity: msgBot2Spring,
                transform: `translateX(${(1 - msgBot2Spring) * 25}px) scale(${0.96 + msgBot2Spring * 0.04})`,
                alignSelf: 'flex-end',
                maxWidth: '92%',
                background: 'rgba(239, 68, 68, 0.16)',
                border: '1.5px solid rgba(239, 68, 68, 0.55)',
                borderRadius: '20px 20px 4px 20px',
                padding: '16px 22px',
                boxShadow: '0 6px 20px rgba(0,0,0,0.3)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  marginBottom: 6,
                }}
              >
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#EF4444',
                    boxShadow: '0 0 8px #EF4444',
                  }}
                />
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FCA5A5',
                    textTransform: 'uppercase',
                  }}
                >
                  Bot Padrão
                </span>
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  lineHeight: 1.3,
                }}
              >
                Mensagem automática. Não responda a este número.
              </div>
            </div>
          )}
        </div>

        {/* Barra inferior de entrada do WhatsApp (completa a interface do smartphone) */}
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
