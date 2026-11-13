import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera: zoom e pan contínuos no fundo (1.0 -> 1.08)
  const bgScale = interpolate(frame, [0, 242], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Rótulo Badge "COMO FUNCIONA" aos 0.15s (frame 5)
  const badgeSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Título aos 0.4s (frame 12)
  const titleSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Celular Mockup surge aos 0.35s (frame 10)
  const phoneSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 15, stiffness: 100},
  });

  // Mensagem 1 (Cliente) entra aos 0.65s (frame 20)
  const msg1Spring = spring({
    frame: frame - 20,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Indicador de "IA buscando histórico..." de 1.7s a 3.2s (frames 50 a 98)
  const showTyping = frame >= 50 && frame < 98;

  // Mensagem 2 (Empresa) entra aos 3.3s (frame 100)
  const msg2Spring = spring({
    frame: frame - 100,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Tag flutuante "Helpdesk + Atendimento" entra aos 4.3s (frame 130) na fala "unindo helpdesk e atendimento"
  const tagSpring = spring({
    frame: frame - 130,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Mensagem 3 (Cliente) entra aos 5.2s (frame 155)
  const msg3Spring = spring({
    frame: frame - 155,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Flutuação 3D sutil do celular
  const rotateY = 8 + Math.sin(frame * 0.06) * 1.8;
  const translateYPhone = Math.sin(frame * 0.08) * 4;

  // Fade out no final para transição suave
  const fadeOut = interpolate(frame, [230, 242], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', opacity: fadeOut}}>
      {/* Fundo com Imagem viva */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_2.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale})`,
            filter: 'brightness(0.7) contrast(1.08)',
          }}
        />
        {/* Gradiente lateral esquerdo: protege o rosto da atendente à direita com respiro absoluto */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(90deg, rgba(17,24,39,0.96) 0%, rgba(17,24,39,0.85) 55%, rgba(17,24,39,0.2) 100%)',
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo dentro da Safe Zone (y: 150 a 1580, x: 60 a 1020) */}
      <AbsoluteFill style={{padding: '0 60px', pointerEvents: 'none'}}>
        {/* Badge de Topo */}
        <div
          style={{
            position: 'absolute',
            top: 180,
            left: 60,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            backgroundColor: 'rgba(31, 147, 255, 0.22)',
            border: '2px solid rgba(31, 147, 255, 0.75)',
            padding: '10px 24px',
            borderRadius: 30,
            opacity: badgeSpring,
            transform: `translateY(${(1 - badgeSpring) * -20}px)`,
            backdropFilter: 'blur(8px)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#1F93FF',
              boxShadow: '0 0 12px #1F93FF',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            Como Funciona
          </span>
        </div>

        {/* Título de Impacto (largura 530px, 2 linhas sem cortar o mockup) */}
        <div
          style={{
            position: 'absolute',
            top: 255,
            left: 60,
            width: 530,
            opacity: titleSpring,
            transform: `translateY(${(1 - titleSpring) * 15}px)`,
          }}
        >
          <h2
            style={{
              fontFamily,
              fontSize: 42,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.25,
              margin: 0,
              textShadow: '0 4px 16px rgba(0,0,0,0.85)',
            }}
          >
            Solução sob medida com <span style={{color: '#1F93FF'}}>Inteligência Artificial</span>
          </h2>
        </div>

        {/* Mockup do Celular 3D na esquerda (top: 380, altura: 740px) */}
        <div
          style={{
            position: 'absolute',
            top: 380,
            left: 60,
            width: 530,
            height: 740,
            perspective: 1200,
          }}
        >
          <div
            style={{
              width: '100%',
              height: '100%',
              backgroundColor: '#0F172A',
              borderRadius: 32,
              border: '3px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 30px rgba(31, 147, 255, 0.3)',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              transform: `scale(${phoneSpring}) translateY(${translateYPhone}px) rotateY(${rotateY}deg)`,
              transformOrigin: 'left center',
            }}
          >
            {/* Top Bar do Mockup */}
            <div
              style={{
                backgroundColor: '#1E293B',
                padding: '16px 20px',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
                borderBottom: '1px solid rgba(255, 255, 255, 0.15)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 12,
                      backgroundColor: '#1F93FF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#FFFFFF',
                      fontSize: 22,
                      fontWeight: 900,
                    }}
                  >
                    ⚡
                  </div>
                  <span style={{fontFamily, fontSize: 32, fontWeight: 900, color: '#FFFFFF'}}>
                    Chatwoot IA
                  </span>
                </div>
                <div
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.12)',
                    padding: '4px 12px',
                    borderRadius: 10,
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#CBD5E1',
                  }}
                >
                  Simulação
                </div>
              </div>
              <div style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#34D399'}}>
                ● Atendimento & Tickets Ativos
              </div>
            </div>

            {/* Área de Mensagens (todas as fontes >= 32px) */}
            <div
              style={{
                flex: 1,
                padding: '18px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: 14,
                justifyContent: 'flex-start',
              }}
            >
              {/* Mensagem 1 - Cliente */}
              {frame >= 20 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '92%',
                    backgroundColor: '#334155',
                    borderRadius: '20px 20px 20px 4px',
                    padding: '14px 18px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.35)',
                    opacity: msg1Spring,
                    transform: `translateY(${(1 - msg1Spring) * 15}px)`,
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#F8FAFC',
                      lineHeight: 1.3,
                    }}
                  >
                    Preciso de ajuda com a entrega do meu pedido anterior.
                  </div>
                </div>
              )}

              {/* Indicador de Digitando / IA buscando */}
              {showTyping && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    backgroundColor: 'rgba(31, 147, 255, 0.25)',
                    border: '1.5px solid rgba(31, 147, 255, 0.6)',
                    borderRadius: '20px 20px 4px 20px',
                    padding: '12px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  <span style={{fontFamily, fontSize: 32, fontWeight: 700, color: '#60A5FA'}}>
                    IA identificando chamado...
                  </span>
                  <div
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      backgroundColor: '#1F93FF',
                      opacity: Math.sin(frame * 0.3) * 0.5 + 0.5,
                    }}
                  />
                </div>
              )}

              {/* Mensagem 2 - Empresa / IA */}
              {frame >= 100 && (
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '94%',
                    backgroundColor: '#1F93FF',
                    borderRadius: '20px 20px 4px 20px',
                    padding: '14px 18px',
                    boxShadow: '0 6px 20px rgba(31, 147, 255, 0.4)',
                    opacity: msg2Spring,
                    transform: `translateY(${(1 - msg2Spring) * 15}px)`,
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#FFFFFF',
                      lineHeight: 1.3,
                    }}
                  >
                    Localizei o chamado aberto aqui. Já estou transferindo para o responsável.
                  </div>
                </div>
              )}

              {/* Mensagem 3 - Cliente */}
              {frame >= 155 && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '92%',
                    backgroundColor: '#334155',
                    borderRadius: '20px 20px 20px 4px',
                    padding: '14px 18px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.35)',
                    opacity: msg3Spring,
                    transform: `translateY(${(1 - msg3Spring) * 15}px)`,
                  }}
                >
                  <div
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 600,
                      color: '#F8FAFC',
                      lineHeight: 1.3,
                    }}
                  >
                    Perfeito, muito obrigado pelo retorno rápido!
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tag Flutuante "Helpdesk + Atendimento" */}
        {frame >= 130 && (
          <div
            style={{
              position: 'absolute',
              top: 1140,
              left: 60,
              width: 530,
              backgroundColor: 'rgba(17, 24, 39, 0.95)',
              border: '2px solid #10B981',
              borderRadius: 20,
              padding: '16px 22px',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              boxShadow: '0 10px 25px rgba(0,0,0,0.7)',
              opacity: tagSpring,
              transform: `scale(${tagSpring})`,
              backdropFilter: 'blur(8px)',
            }}
          >
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: '50%',
                backgroundColor: '#10B981',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFFFFF',
                fontWeight: 900,
                fontSize: 24,
                flexShrink: 0,
              }}
            >
              ✓
            </div>
            <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
              Helpdesk + Atendimento juntos
            </span>
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
