import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {BRIEFING} from './constants';

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera e perspectiva (>= 4%)
  const bgScale = interpolate(frame, [0, 266], [1.0, 1.07], {
    extrapolateRight: 'clamp',
  });
  const phoneRotateY = interpolate(frame, [0, 266], [-5, 2]);
  const phoneFloatY = Math.sin(frame / 14) * 6;

  // Entrada do Badge "COMO FUNCIONA"
  const badgeSpring = spring({
    frame: Math.max(0, frame - 2),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Título Superior
  const titleSpring = spring({
    frame: Math.max(0, frame - 8),
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Entrada do Celular Mockup (frame 10)
  const phoneSpring = spring({
    frame: Math.max(0, frame - 10),
    fps,
    config: {damping: 13, stiffness: 90},
  });

  // Entrada do Cardápio Interativo (frame 14)
  const menuCardSpring = spring({
    frame: Math.max(0, frame - 14),
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // 16.3s global -> frame (16.3 - 12.53)*30 = frame 113: Mensagem 1 do Cliente
  const msg1Spring = spring({
    frame: Math.max(0, frame - 110),
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // 16.9s global -> frame 131: Indicador "IA digitando..."
  const isTyping = frame >= 131 && frame < 155;

  // 17.5s global -> frame (17.5 - 12.53)*30 = frame 150: Mensagem 2 da IA
  const msg2Spring = spring({
    frame: Math.max(0, frame - 150),
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // 18.5s global -> frame (18.5 - 12.53)*30 = frame 179: Mensagem 3 do Cliente
  const msg3Spring = spring({
    frame: Math.max(0, frame - 178),
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // 19.5s global -> frame (19.5 - 12.53)*30 = frame 209: Mensagem 4 de Sucesso
  const msg4Spring = spring({
    frame: Math.max(0, frame - 208),
    fps,
    config: {damping: 11, stiffness: 130},
  });

  // Animação de pontinhos digitando
  const dot1 = Math.sin((frame - 131) * 0.4) * 4;
  const dot2 = Math.sin((frame - 131) * 0.4 + 1) * 4;
  const dot3 = Math.sin((frame - 131) * 0.4 + 2) * 4;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        background: BRIEFING.cores.fundo_escuro,
        fontFamily,
      }}
    >
      {/* Fundo com foto e gradiente com zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <img
          src={staticFile('img_2.jpg')}
          alt="Fundo"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: 0.4,
            filter: 'brightness(0.65) contrast(1.15)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(circle at 50% 30%, rgba(225, 29, 72, 0.28) 0%, rgba(49, 6, 15, 0.96) 80%)`,
          }}
        />
      </div>

      {/* Grid tecnológico sutil */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'radial-gradient(rgba(255, 255, 255, 0.08) 1.5px, transparent 1.5px)',
          backgroundSize: '40px 40px',
          opacity: 0.5,
          pointerEvents: 'none',
        }}
      />

      {/* Topo: Badge "COMO FUNCIONA" (y=175) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring,
          zIndex: 30,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 28px',
            borderRadius: 30,
            background: 'rgba(15, 23, 42, 0.94)',
            border: `2px solid ${BRIEFING.cores.apoio}`,
            boxShadow: `0 8px 24px rgba(250, 204, 21, 0.3)`,
          }}
        >
          <span style={{fontSize: 32}}>✨</span>
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            COMO FUNCIONA
          </span>
        </div>
      </div>

      {/* Título Superior (y=245 a y=310) */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `translateY(${(1 - titleSpring) * 15}px) scale(${titleSpring})`,
          opacity: titleSpring,
          zIndex: 30,
        }}
      >
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.92)',
            padding: '12px 30px',
            borderRadius: 20,
            border: '1.5px solid rgba(255, 255, 255, 0.15)',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.7)',
          }}
        >
          <span
            style={{
              fontSize: 40,
              fontWeight: 800,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
            }}
          >
            CARDÁPIO DIGITAL COM IA NO WHATSAPP
          </span>
        </div>
      </div>

      {/* CELULAR MOCKUP 3D NATIVO MOBILE 9:16 (y=330 a y=1480) */}
      <div
        style={{
          position: 'absolute',
          top: 330,
          left: 110,
          width: 860,
          height: 1140,
          perspective: 1200,
          zIndex: 20,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            transform: `scale(${phoneSpring}) translateY(${phoneFloatY}px) rotateY(${phoneRotateY}deg)`,
            transformStyle: 'preserve-3d',
            borderRadius: 44,
            background: '#0F172A',
            border: '4px solid rgba(255, 255, 255, 0.2)',
            boxShadow:
              '0 25px 60px rgba(0, 0, 0, 0.9), 0 0 40px rgba(225, 29, 72, 0.35)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Top Bar do Celular com Status e Selo Simulação */}
          <div
            style={{
              background: '#075E54', // Tom clássico de WhatsApp profissional
              padding: '18px 24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '2px solid rgba(0,0,0,0.2)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: 26,
                  background: BRIEFING.cores.marca,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                  boxShadow: '0 4px 10px rgba(0,0,0,0.4)',
                }}
              >
                🍽️
              </div>
              <div>
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    lineHeight: 1.1,
                  }}
                >
                  Cardápio Digital • IA
                </div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#86EFAC',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <span style={{fontSize: 20}}>🟢</span> Atendimento Ativo
                </div>
              </div>
            </div>

            {/* Selo Simulação (obrigatório, discreto) */}
            <div
              style={{
                padding: '6px 16px',
                borderRadius: 14,
                background: 'rgba(0, 0, 0, 0.45)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                fontSize: 32,
                fontWeight: 700,
                color: '#E2E8F0',
                letterSpacing: 0.5,
              }}
            >
              Simulação
            </div>
          </div>

          {/* Conteúdo interno do Celular */}
          <div
            style={{
              flex: 1,
              background: '#0B141A',
              padding: '20px 24px',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              overflow: 'hidden',
            }}
          >
            {/* Bloco 1: Cardápio com Fotos (ilustrando a fala: "escolhe os itens com fotos no cardápio") */}
            <div
              style={{
                transform: `scale(${menuCardSpring})`,
                opacity: menuCardSpring,
                background: 'rgba(30, 41, 59, 0.95)',
                borderRadius: 24,
                border: `2px solid ${BRIEFING.cores.marca}`,
                padding: '16px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: 18,
                boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              }}
            >
              <div
                style={{
                  width: 90,
                  height: 90,
                  borderRadius: 18,
                  background: 'linear-gradient(135deg, #F97316 0%, #E11D48 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 50,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                }}
              >
                🍔
              </div>
              <div style={{flex: 1}}>
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    marginBottom: 4,
                  }}
                >
                  X-Burger Artesanal
                </div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: BRIEFING.cores.apoio,
                  }}
                >
                  📸 Cardápio com Fotos no Celular
                </div>
              </div>
              <div
                style={{
                  padding: '10px 18px',
                  borderRadius: 16,
                  background: BRIEFING.cores.marca,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Pedir
              </div>
            </div>

            {/* Mensagem 1: Cliente pergunta se vem com cebola */}
            {frame >= 110 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  transform: `scale(${msg1Spring})`,
                  opacity: msg1Spring,
                  background: '#202C33',
                  borderRadius: '20px 20px 20px 4px',
                  padding: '14px 20px',
                  border: '1.5px solid rgba(255,255,255,0.08)',
                  boxShadow: '0 6px 18px rgba(0,0,0,0.4)',
                }}
              >
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.3,
                  }}
                >
                  Oi! Esse lanche vem com cebola?
                </div>
                <div
                  style={{
                    fontSize: 30,
                    color: '#8696A0',
                    textAlign: 'right',
                    marginTop: 4,
                  }}
                >
                  19:43
                </div>
              </div>
            )}

            {/* Indicador animado "IA digitando..." */}
            {isTyping && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  background: '#005C4B',
                  borderRadius: '20px 20px 4px 20px',
                  padding: '12px 20px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span style={{fontSize: 32, color: '#E9EDEF', fontWeight: 600}}>
                  IA digitando
                </span>
                <span style={{transform: `translateY(${dot1}px)`, fontSize: 24, color: '#86EFAC'}}>
                  ●
                </span>
                <span style={{transform: `translateY(${dot2}px)`, fontSize: 24, color: '#86EFAC'}}>
                  ●
                </span>
                <span style={{transform: `translateY(${dot3}px)`, fontSize: 24, color: '#86EFAC'}}>
                  ●
                </span>
              </div>
            )}

            {/* Mensagem 2: Resposta da IA sobre ingredientes */}
            {frame >= 150 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '86%',
                  transform: `scale(${msg2Spring})`,
                  opacity: msg2Spring,
                  background: '#005C4B',
                  borderRadius: '20px 20px 4px 20px',
                  padding: '14px 20px',
                  boxShadow: '0 6px 18px rgba(0,0,0,0.4)',
                }}
              >
                <div
                  style={{
                    fontSize: 30,
                    fontWeight: 800,
                    color: BRIEFING.cores.apoio,
                    marginBottom: 4,
                  }}
                >
                  🤖 Atendente IA
                </div>
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.3,
                  }}
                >
                  Oi! Vem com queijo, alface e tomate. A cebola é opcional, quer
                  tirar?
                </div>
                <div
                  style={{
                    fontSize: 30,
                    color: '#86EFAC',
                    textAlign: 'right',
                    marginTop: 4,
                  }}
                >
                  19:43 ✓✓
                </div>
              </div>
            )}

            {/* Mensagem 3: Cliente confirma remoção da cebola */}
            {frame >= 178 && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  maxWidth: '82%',
                  transform: `scale(${msg3Spring})`,
                  opacity: msg3Spring,
                  background: '#202C33',
                  borderRadius: '20px 20px 20px 4px',
                  padding: '14px 20px',
                  border: '1.5px solid rgba(255,255,255,0.08)',
                  boxShadow: '0 6px 18px rgba(0,0,0,0.4)',
                }}
              >
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 600,
                    color: '#E9EDEF',
                    lineHeight: 1.3,
                  }}
                >
                  Pode tirar a cebola, por favor.
                </div>
                <div
                  style={{
                    fontSize: 30,
                    color: '#8696A0',
                    textAlign: 'right',
                    marginTop: 4,
                  }}
                >
                  19:44
                </div>
              </div>
            )}

            {/* Mensagem 4: IA fecha pedido e envia organizado para a loja */}
            {frame >= 208 && (
              <div
                style={{
                  alignSelf: 'flex-end',
                  maxWidth: '88%',
                  transform: `scale(${msg4Spring})`,
                  opacity: msg4Spring,
                  background: 'linear-gradient(135deg, #005C4B 0%, #064E3B 100%)',
                  borderRadius: '20px 20px 4px 20px',
                  padding: '16px 22px',
                  border: `2px solid ${BRIEFING.cores.apoio}`,
                  boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 6,
                  }}
                >
                  <span style={{fontSize: 32}}>✅</span>
                  <span
                    style={{
                      fontSize: 32,
                      fontWeight: 800,
                      color: BRIEFING.cores.apoio,
                      textTransform: 'uppercase',
                    }}
                  >
                    Pedido Organizado
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.3,
                  }}
                >
                  Pronto! Seu pedido está completo e já foi enviado para o
                  WhatsApp da loja.
                </div>
                <div
                  style={{
                    fontSize: 30,
                    color: '#86EFAC',
                    textAlign: 'right',
                    marginTop: 6,
                  }}
                >
                  19:44 ✓✓
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
