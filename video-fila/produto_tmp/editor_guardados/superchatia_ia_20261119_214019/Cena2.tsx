import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena2Props {
  fontFamily: string;
  destaque: string;
}

export const Cena2: React.FC<Cena2Props> = ({fontFamily, destaque}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom contínuo do cenário de fundo para dinamismo constante
  const sceneScale = interpolate(frame, [0, 346], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Transição de entrada suave e amortecida: slide-up + zoom-in a partir do corte + leve bloom
  const entranceSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 100},
  });
  const entranceSlideY = interpolate(entranceSpring, [0, 1], [90, 0]);
  const entranceScale = interpolate(entranceSpring, [0, 1], [0.91, 1.0]);
  const entranceBloom = interpolate(frame, [0, 6, 20], [1.35, 1.15, 1.0], {
    extrapolateRight: 'clamp',
  });

  // Slow push-in contínuo e micro-rotação 2.5D no dispositivo
  const mockPushIn = interpolate(frame, [0, 346], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });
  const mockRotY = interpolate(frame, [0, 346], [-3, -0.5]);
  const mockRotX = interpolate(frame, [0, 346], [2.5, 0.5]);

  // Entrada dos balões sincronizada com a locução
  const msg1Spring = spring({frame: frame - 15, fps, config: {damping: 14, stiffness: 140}});
  const msg2Spring = spring({frame: frame - 72, fps, config: {damping: 14, stiffness: 140}});
  const msg3Spring = spring({frame: frame - 140, fps, config: {damping: 14, stiffness: 140}});
  const msg4Spring = spring({frame: frame - 195, fps, config: {damping: 14, stiffness: 140}});
  const msg5Spring = spring({frame: frame - 255, fps, config: {damping: 14, stiffness: 140}});

  // Sincronia de canais e troca dinâmica de aba ativa:
  // Inicialmente WhatsApp é a aba ativa (msg 1 aos frames 15 a 139)
  // No frame 140 entra a mensagem 'Cliente (Instagram)' -> troca de aba com animação elástica e glow pulsante
  const isInstagramActive = frame >= 140;
  const isWhatsAppActive = frame < 140;
  const isTelegramMentioned = frame >= 120 && frame < 140;

  // Animação elástica da troca de aba no frame 140
  const igTabSpring = spring({
    frame: frame - 140,
    fps,
    config: {damping: 12, stiffness: 180},
  });
  const igTabPulse = isInstagramActive
    ? 1.0 + 0.05 * Math.sin((frame - 140) * 0.2)
    : 1.0;

  // Digitando antes da resposta da empresa
  const isTyping1 = frame >= 48 && frame < 72;
  const isTyping2 = frame >= 168 && frame < 195;

  // Feixes de luz / pulso contínuo nos elementos de convergência do terço inferior
  const beamPulse = 0.5 + 0.5 * Math.sin(frame * 0.15);
  const orbY1 = interpolate(frame, [0, 346], [240, 380]);
  const orbY2 = interpolate(frame, [0, 346], [950, 820]);

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#070A12',
        fontFamily,
        filter: `brightness(${entranceBloom})`,
      }}
    >
      {/* Fundo dinâmico com foto da marca, gradientes luminosos e malha tech em movimento */}
      <div
        style={{
          position: 'absolute',
          inset: -40,
          transform: `scale(${sceneScale})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: 0.45,
          }}
        />

        {/* Gradiente luminoso superior */}
        <div
          style={{
            position: 'absolute',
            width: 850,
            height: 850,
            borderRadius: '50%',
            background:
              'radial-gradient(circle, rgba(91, 108, 255, 0.4) 0%, rgba(91, 108, 255, 0.1) 50%, transparent 70%)',
            top: orbY1,
            left: 115,
            filter: 'blur(70px)',
          }}
        />

        {/* Gradiente luminoso inferior preenchendo o terço médio/inferior */}
        <div
          style={{
            position: 'absolute',
            width: 900,
            height: 700,
            borderRadius: '50%',
            background:
              'radial-gradient(circle, rgba(56, 189, 248, 0.25) 0%, rgba(91, 108, 255, 0.12) 50%, transparent 75%)',
            top: orbY2,
            left: 90,
            filter: 'blur(75px)',
          }}
        />

        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px)',
            backgroundSize: '70px 70px',
            opacity: 0.6,
          }}
        />
      </div>

      {/* Rótulo superior da cena 'COMO FUNCIONA' (y = 155) */}
      <div
        style={{
          position: 'absolute',
          top: 155,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `translateY(${entranceSlideY * 0.3}px) scale(${entranceScale})`,
          opacity: Math.min(1, entranceSpring),
          zIndex: 30,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 28px',
            backgroundColor: '#0F172A',
            border: '1.5px solid rgba(91, 108, 255, 0.65)',
            borderRadius: 999,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: destaque,
              boxShadow: `0 0 10px ${destaque}`,
            }}
          />
          <span
            style={{
              color: '#F8FAFC',
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>
      </div>

      {/* 1. MOLDURA DE SMARTPHONE / DISPOSITIVO MODERNO (y = 215 a 1135, altura 920px) */}
      {/* Elimina completamente o vazio inicial de q07 mantendo proporção de aplicativo SaaS real */}
      <div
        style={{
          position: 'absolute',
          top: 215,
          left: 70,
          width: 940,
          height: 920,
          transform: `perspective(1400px) translateY(${entranceSlideY}px) rotateY(${mockRotY}deg) rotateX(${mockRotX}deg) scale(${entranceScale * mockPushIn})`,
          transformOrigin: 'center 40%',
          zIndex: 20,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            backgroundColor: '#0B1120',
            borderRadius: 40,
            border: '3.5px solid rgba(255, 255, 255, 0.25)',
            boxShadow:
              '0 32px 80px rgba(0, 0, 0, 0.95), 0 0 45px rgba(91, 108, 255, 0.35)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Top Notch / Ilha dinâmica de smartphone */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              paddingTop: 10,
              backgroundColor: '#1E293B',
            }}
          >
            <div
              style={{
                width: 130,
                height: 20,
                backgroundColor: '#070A12',
                borderRadius: 10,
                border: '1px solid rgba(255,255,255,0.1)',
              }}
            />
          </div>

          {/* Header do Painel Unificado dentro do dispositivo */}
          <div
            style={{
              padding: '12px 24px 14px',
              backgroundColor: '#1E293B',
              borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 12,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 46,
                    height: 46,
                    borderRadius: 14,
                    backgroundColor: destaque,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                    fontWeight: 900,
                    fontSize: 22,
                    boxShadow: `0 0 14px ${destaque}`,
                  }}
                >
                  SC
                </div>
                <div>
                  <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 800}}>
                    SuperChat IA
                  </div>
                  <div style={{color: '#4ADE80', fontSize: 32, fontWeight: 800}}>
                    ● Painel Unificado
                  </div>
                </div>
              </div>

              {/* Selo Simulação obrigatório com tamanho legível */}
              <div
                style={{
                  padding: '8px 18px',
                  backgroundColor: 'rgba(255, 255, 255, 0.15)',
                  border: '1px solid rgba(255, 255, 255, 0.25)',
                  borderRadius: 10,
                  color: '#FFFFFF',
                  fontSize: 32,
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                Simulação
              </div>
            </div>

            {/* Abas dos canais com ANIMAÇÃO DINÂMICA DE TROCA DE ESTADO (sincronizada com Instagram no frame 140) */}
            <div style={{display: 'flex', gap: 12}}>
              {/* WhatsApp */}
              <div
                style={{
                  flex: 1,
                  padding: '10px 0',
                  textAlign: 'center',
                  borderRadius: 12,
                  fontSize: 32,
                  fontWeight: 800,
                  backgroundColor: isWhatsAppActive
                    ? 'rgba(34, 197, 94, 0.28)'
                    : 'rgba(255, 255, 255, 0.08)',
                  border: isWhatsAppActive
                    ? '2px solid #22C55E'
                    : '1.5px solid rgba(255, 255, 255, 0.22)',
                  color: isWhatsAppActive ? '#4ADE80' : '#E2E8F0',
                  boxShadow: isWhatsAppActive ? '0 0 16px rgba(34, 197, 94, 0.55)' : 'none',
                  transition: 'all 0.2s ease-out',
                }}
              >
                WhatsApp
              </div>

              {/* Telegram */}
              <div
                style={{
                  flex: 1,
                  padding: '10px 0',
                  textAlign: 'center',
                  borderRadius: 12,
                  fontSize: 32,
                  fontWeight: 800,
                  backgroundColor: isTelegramMentioned
                    ? 'rgba(56, 189, 248, 0.28)'
                    : 'rgba(255, 255, 255, 0.08)',
                  border: isTelegramMentioned
                    ? '2px solid #38BDF8'
                    : '1.5px solid rgba(255, 255, 255, 0.22)',
                  color: isTelegramMentioned ? '#38BDF8' : '#E2E8F0',
                  boxShadow: isTelegramMentioned ? '0 0 16px rgba(56, 189, 248, 0.55)' : 'none',
                  transition: 'all 0.2s ease-out',
                }}
              >
                Telegram
              </div>

              {/* Instagram: Destaque visual pulsante no surgimento da mensagem aos 17.2s (frame 140) */}
              <div
                style={{
                  flex: 1,
                  padding: '10px 0',
                  textAlign: 'center',
                  borderRadius: 12,
                  fontSize: 32,
                  fontWeight: 800,
                  backgroundColor: isInstagramActive
                    ? 'rgba(225, 48, 108, 0.35)'
                    : 'rgba(255, 255, 255, 0.08)',
                  border: isInstagramActive
                    ? '2.5px solid #E1306C'
                    : '1.5px solid rgba(255, 255, 255, 0.22)',
                  color: isInstagramActive ? '#FFA0D0' : '#E2E8F0',
                  boxShadow: isInstagramActive
                    ? '0 0 24px rgba(225, 48, 108, 0.75)'
                    : 'none',
                  transform: `scale(${igTabPulse})`,
                  transition: 'all 0.2s ease-out',
                }}
              >
                Instagram
              </div>
            </div>
          </div>

          {/* Área interna de mensagens do chat com scroll suave e todos os balões legíveis */}
          <div
            style={{
              flex: 1,
              padding: '16px 22px 16px',
              backgroundColor: '#0B1120',
              overflow: 'hidden',
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
            {/* Mensagem 1: Cliente WhatsApp */}
            {frame >= 15 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  transform: `translateY(${interpolate(msg1Spring, [0, 1], [16, 0])}px)`,
                  opacity: Math.min(1, Math.max(0, msg1Spring)),
                  backgroundColor: '#1E293B',
                  borderRadius: '18px 18px 18px 4px',
                  padding: '12px 18px',
                  border: '1.5px solid rgba(255, 255, 255, 0.16)',
                }}
              >
                <div style={{color: '#4ADE80', fontSize: 32, fontWeight: 800, marginBottom: 4}}>
                  Cliente (WhatsApp)
                </div>
                <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 600, lineHeight: 1.3}}>
                  Oi, vocês atendem aos sábados?
                </div>
              </div>
            )}

            {/* Indicador digitando 1 */}
            {isTyping1 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  backgroundColor: 'rgba(91, 108, 255, 0.28)',
                  border: '1.5px solid rgba(91, 108, 255, 0.45)',
                  borderRadius: '18px 18px 4px 18px',
                  padding: '8px 18px',
                  color: '#C7D2FE',
                  fontSize: 32,
                  fontWeight: 700,
                }}
              >
                SuperChat IA digitando...
              </div>
            )}

            {/* Mensagem 2: Empresa SuperChat IA */}
            {frame >= 72 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '86%',
                  transform: `translateY(${interpolate(msg2Spring, [0, 1], [16, 0])}px)`,
                  opacity: Math.min(1, Math.max(0, msg2Spring)),
                  backgroundColor: destaque,
                  borderRadius: '18px 18px 4px 18px',
                  padding: '12px 20px',
                  boxShadow: '0 8px 24px rgba(91, 108, 255, 0.5)',
                }}
              >
                <div style={{color: '#E0E7FF', fontSize: 32, fontWeight: 800, marginBottom: 4}}>
                  SuperChat IA
                </div>
                <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 600, lineHeight: 1.3}}>
                  Olá! Atendemos sim, com a nossa IA 24h.
                </div>
              </div>
            )}

            {/* Mensagem 3: Cliente Instagram */}
            {frame >= 140 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  transform: `translateY(${interpolate(msg3Spring, [0, 1], [16, 0])}px)`,
                  opacity: Math.min(1, Math.max(0, msg3Spring)),
                  backgroundColor: '#1E293B',
                  borderRadius: '18px 18px 18px 4px',
                  padding: '12px 18px',
                  border: '1.5px solid rgba(225, 48, 108, 0.55)',
                }}
              >
                <div style={{color: '#FFA0D0', fontSize: 32, fontWeight: 800, marginBottom: 4}}>
                  Cliente (Instagram)
                </div>
                <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 600, lineHeight: 1.3}}>
                  Chamei no Instagram ontem também.
                </div>
              </div>
            )}

            {/* Indicador digitando 2 */}
            {isTyping2 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  backgroundColor: 'rgba(91, 108, 255, 0.28)',
                  border: '1.5px solid rgba(91, 108, 255, 0.45)',
                  borderRadius: '18px 18px 4px 18px',
                  padding: '8px 18px',
                  color: '#C7D2FE',
                  fontSize: 32,
                  fontWeight: 700,
                }}
              >
                SuperChat IA digitando...
              </div>
            )}

            {/* Mensagem 4: Empresa */}
            {frame >= 195 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '88%',
                  transform: `translateY(${interpolate(msg4Spring, [0, 1], [16, 0])}px)`,
                  opacity: Math.min(1, Math.max(0, msg4Spring)),
                  backgroundColor: destaque,
                  borderRadius: '18px 18px 4px 18px',
                  padding: '12px 20px',
                  boxShadow: '0 8px 24px rgba(91, 108, 255, 0.5)',
                }}
              >
                <div style={{color: '#E0E7FF', fontSize: 32, fontWeight: 800, marginBottom: 4}}>
                  SuperChat IA
                </div>
                <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 600, lineHeight: 1.3}}>
                  Perfeito, já vejo a conversa aqui no mesmo painel.
                </div>
              </div>
            )}

            {/* Mensagem 5: Cliente */}
            {frame >= 255 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  transform: `translateY(${interpolate(msg5Spring, [0, 1], [16, 0])}px)`,
                  opacity: Math.min(1, Math.max(0, msg5Spring)),
                  backgroundColor: '#1E293B',
                  borderRadius: '18px 18px 18px 4px',
                  padding: '12px 18px',
                  border: '1.5px solid rgba(255, 255, 255, 0.16)',
                }}
              >
                <div style={{color: '#4ADE80', fontSize: 32, fontWeight: 800, marginBottom: 4}}>
                  Cliente (WhatsApp)
                </div>
                <div style={{color: '#FFFFFF', fontSize: 34, fontWeight: 600, lineHeight: 1.3}}>
                  Que bom, obrigado!
                </div>
              </div>
            )}
          </div>

          {/* Rodapé realista de input do app SaaS */}
          <div
            style={{
              padding: '12px 22px',
              backgroundColor: '#1E293B',
              borderTop: '1px solid rgba(255, 255, 255, 0.12)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={{color: '#94A3B8', fontSize: 32, fontWeight: 600}}>
              Mensagem unificada...
            </span>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 12,
                backgroundColor: destaque,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.5">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* 2. ELEMENTOS VISUAIS DE APOIO DA MARCA NO TERÇO MÉDIO/INFERIOR (y = 1160 a 1400) */}
      {/* Elimina completamente o vazio escuro (q08), ilustrando a convergência de canais para o painel com feixes sutis de luz */}
      <div
        style={{
          position: 'absolute',
          top: 1160,
          left: 70,
          right: 70,
          height: 230,
          backgroundColor: 'rgba(15, 23, 42, 0.92)',
          border: '2px solid rgba(91, 108, 255, 0.45)',
          borderRadius: 28,
          padding: '18px 24px',
          boxSizing: 'border-box',
          boxShadow: '0 16px 40px rgba(0, 0, 0, 0.85), 0 0 30px rgba(91, 108, 255, 0.25)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          transform: `translateY(${entranceSlideY * 0.5}px) scale(${entranceScale})`,
          opacity: Math.min(1, entranceSpring),
          zIndex: 25,
        }}
      >
        {/* Título de apoio oficial */}
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: '#22C55E',
                boxShadow: '0 0 8px #22C55E',
              }}
            />
            <span style={{color: '#F8FAFC', fontSize: 32, fontWeight: 800}}>
              Centralização Multicanal
            </span>
          </div>
          <span style={{color: '#94A3B8', fontSize: 32, fontWeight: 700}}>
            Tudo em um só lugar
          </span>
        </div>

        {/* Linha de canais conectados convergindo com feixes de luz para o painel */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
            position: 'relative',
          }}
        >
          {/* WhatsApp Pill */}
          <div
            style={{
              padding: '8px 18px',
              backgroundColor: 'rgba(34, 197, 94, 0.18)',
              border: '1.5px solid rgba(34, 197, 94, 0.5)',
              borderRadius: 14,
              color: '#4ADE80',
              fontSize: 32,
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>●</span> WhatsApp
          </div>

          {/* Feixe de luz 1 */}
          <div
            style={{
              flex: 1,
              height: 3,
              background: `linear-gradient(90deg, rgba(34, 197, 94, ${beamPulse}), rgba(91, 108, 255, 0.8))`,
              borderRadius: 2,
              boxShadow: `0 0 8px rgba(91, 108, 255, ${beamPulse})`,
            }}
          />

          {/* Telegram Pill */}
          <div
            style={{
              padding: '8px 18px',
              backgroundColor: 'rgba(56, 189, 248, 0.18)',
              border: '1.5px solid rgba(56, 189, 248, 0.5)',
              borderRadius: 14,
              color: '#38BDF8',
              fontSize: 32,
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>●</span> Telegram
          </div>

          {/* Feixe de luz 2 */}
          <div
            style={{
              flex: 1,
              height: 3,
              background: `linear-gradient(90deg, rgba(56, 189, 248, ${beamPulse}), rgba(225, 48, 108, 0.8))`,
              borderRadius: 2,
              boxShadow: `0 0 8px rgba(225, 48, 108, ${beamPulse})`,
            }}
          />

          {/* Instagram Pill */}
          <div
            style={{
              padding: '8px 18px',
              backgroundColor: 'rgba(225, 48, 108, 0.18)',
              border: '1.5px solid rgba(225, 48, 108, 0.5)',
              borderRadius: 14,
              color: '#FFA0D0',
              fontSize: 32,
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>●</span> Instagram
          </div>
        </div>

        {/* Resumo de valor da marca */}
        <div style={{textAlign: 'center'}}>
          <span style={{color: '#CBD5E1', fontSize: 32, fontWeight: 700}}>
            Mensagens unificadas no painel SuperChat IA
          </span>
        </div>
      </div>
    </div>
  );
};
