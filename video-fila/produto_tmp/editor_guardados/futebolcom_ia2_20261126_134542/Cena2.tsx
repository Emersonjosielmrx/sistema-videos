import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {fontFamily} from './fontes';

const CORES = {
  marca: '#E11D48',
  apoio: '#FACC15',
  card_fundo: 'rgba(18, 4, 8, 0.94)',
  borda_card: 'rgba(255, 255, 255, 0.16)',
};

export const Cena2: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Variação de câmera: punch-in digital de 1.14x no corte para a cena 2
  const cameraScale = interpolate(frame, [0, 8.18 * fps], [1.14, 1.19], {
    extrapolateRight: 'clamp',
  });

  const sprBadge = spring({frame, fps, config: {damping: 14, stiffness: 120}});

  // Sincronização estrita das 3 etapas com a locução:
  // "Pelo link da conversa" -> etapa 1 (0.0s a 2.6s, frames 0 a 78)
  // "ele navega pelas fotos dos pratos" -> etapa 2 (2.6s a 5.1s, frames 78 a 153)
  // "e consulta a inteligência artificial" -> etapa 3 (5.1s em diante, frames 153 a 245)
  const tRel = frame / fps;
  const etapaAtiva = tRel < 2.6 ? 1 : tRel < 5.1 ? 2 : 3;

  // Indicador deslizante (sliding pill) suave com interpolação
  const pillProgress = interpolate(
    frame,
    [0, 72, 80, 147, 155],
    [0, 0, 1, 1, 2],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Entrada do mockup de demonstração aos 2.5s (frame 75)
  const sprPhone = spring({frame: frame - 75, fps, config: {damping: 16, stiffness: 140}});

  // Animação escalonada em cascata dos pratos (stagger animation)
  const sprItem1 = spring({frame: frame - 76, fps, config: {damping: 16, stiffness: 150}});
  const sprItem2 = spring({frame: frame - 83, fps, config: {damping: 16, stiffness: 150}});
  const sprItem3 = spring({frame: frame - 90, fps, config: {damping: 16, stiffness: 150}});

  // Vídeo do apresentador reenquadrado para baixo durante a abertura (0 a 2.5s)
  // garantindo distância segura e respiro total em relação às abas superiores
  const videoOpacity = interpolate(frame, [68, 76], [1.0, 0.0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: CORES.fundo_escuro, overflow: 'hidden'}}>
      {/* Fundo limpo e sofisticado da marca para a demonstração */}
      <img
        src={staticFile('img_0.jpg')}
        alt="Fundo"
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          opacity: 0.35,
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(circle at 50% 40%, rgba(225, 29, 72, 0.35) 0%, rgba(35, 4, 10, 0.96) 80%)',
        }}
      />

      {/* Vídeo do dono reenquadrado para baixo (livre do HUD) e ocultado durante o mockup */}
      {videoOpacity > 0.001 && (
        <div
          style={{
            width: '100%',
            height: '100%',
            transform: `translateY(190px) scale(${cameraScale * 0.94})`,
            transformOrigin: '50% 10%',
            opacity: videoOpacity,
          }}
        >
          <OffthreadVideo
            src={staticFile('dono_2.mp4')}
            muted
            style={{width: '100%', height: '100%', objectFit: 'cover'}}
          />
        </div>
      )}

      {/* Vinhetas cinematográficas */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background: 'linear-gradient(to bottom, rgba(15, 3, 6, 0.94) 0%, rgba(15, 3, 6, 0.6) 65%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 520,
          background: 'linear-gradient(to top, rgba(11, 13, 19, 0.95) 0%, rgba(11, 13, 19, 0.5) 65%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top HUD (Zona y = 165 a 395, margem de 60px estritamente respeitada) */}
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
          zIndex: 40,
        }}
      >
        {/* Rótulo: COMO FUNCIONA */}
        {sprBadge > 0.01 && (
          <div
            style={{
              padding: '8px 24px',
              backgroundColor: CORES.marca,
              borderRadius: 30,
              boxShadow: '0 6px 20px rgba(225, 29, 72, 0.5)',
              transform: `scale(${sprBadge})`,
              opacity: sprBadge,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
              }}
            >
              📲 COMO FUNCIONA O CARDÁPIO
            </span>
          </div>
        )}

        {/* 3 Etapas com fundo deslizante (sliding pill) e margens seguras >= 60px */}
        <div
          style={{
            position: 'relative',
            display: 'flex',
            width: '100%',
            backgroundColor: CORES.card_fundo,
            borderRadius: 22,
            border: `1.5px solid ${CORES.borda_card}`,
            padding: 6,
            boxShadow: '0 12px 30px rgba(0,0,0,0.85)',
          }}
        >
          {/* Indicador deslizante amarelo */}
          <div
            style={{
              position: 'absolute',
              top: 6,
              bottom: 6,
              left: `calc(${pillProgress * 33.333}% + 6px)`,
              width: 'calc(33.333% - 12px)',
              backgroundColor: CORES.apoio,
              borderRadius: 16,
              boxShadow: '0 6px 20px rgba(250, 204, 21, 0.45)',
              transition: 'none',
              zIndex: 1,
            }}
          />

          {/* Etapa 1: LINK */}
          <div
            style={{
              flex: 1,
              position: 'relative',
              zIndex: 2,
              padding: '10px 4px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 2,
              transform: etapaAtiva === 1 ? 'scale(1.05)' : 'scale(1.0)',
            }}
          >
            <span style={{fontSize: 26}}>🔗</span>
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: etapaAtiva === 1 ? '#111111' : '#FFFFFF',
                lineHeight: 1.1,
              }}
            >
              1. LINK
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 26,
                fontWeight: 700,
                color: etapaAtiva === 1 ? '#222222' : '#E2E8F0',
              }}
            >
              No WhatsApp
            </div>
          </div>

          {/* Etapa 2: FOTOS */}
          <div
            style={{
              flex: 1,
              position: 'relative',
              zIndex: 2,
              padding: '10px 4px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 2,
              transform: etapaAtiva === 2 ? 'scale(1.05)' : 'scale(1.0)',
            }}
          >
            <span style={{fontSize: 26}}>📸</span>
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: etapaAtiva === 2 ? '#111111' : '#FFFFFF',
                lineHeight: 1.1,
              }}
            >
              2. FOTOS
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 26,
                fontWeight: 700,
                color: etapaAtiva === 2 ? '#222222' : '#E2E8F0',
              }}
            >
              Dos Pratos
            </div>
          </div>

          {/* Etapa 3: IA */}
          <div
            style={{
              flex: 1,
              position: 'relative',
              zIndex: 2,
              padding: '10px 4px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 2,
              transform: etapaAtiva === 3 ? 'scale(1.05)' : 'scale(1.0)',
            }}
          >
            <span style={{fontSize: 26}}>🤖</span>
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: etapaAtiva === 3 ? '#111111' : '#FFFFFF',
                lineHeight: 1.1,
              }}
            >
              3. IA
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 26,
                fontWeight: 700,
                color: etapaAtiva === 3 ? '#222222' : '#E2E8F0',
              }}
            >
              Tira Dúvidas
            </div>
          </div>
        </div>
      </div>

      {/* DEMONSTRAÇÃO VISUAL DO PRODUTO: Mockup de Smartphone animado (Show, don't tell) */}
      {sprPhone > 0.01 && (
        <div
          style={{
            position: 'absolute',
            top: 365,
            left: 60,
            right: 60,
            height: 680,
            backgroundColor: '#0F172A',
            borderRadius: 36,
            border: '2.5px solid rgba(255, 255, 255, 0.25)',
            boxShadow: '0 25px 65px rgba(0,0,0,0.9), 0 0 45px rgba(225, 29, 72, 0.3)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            transform: `translateY(${(1 - sprPhone) * 40}px) scale(${sprPhone})`,
            opacity: sprPhone,
            zIndex: 35,
          }}
        >
          {/* FASE A: Cardápio com FOTOS REAIS dos pratos (Etapa 2: frame 75 a 150) */}
          {etapaAtiva === 2 && (
            <div style={{flex: 1, display: 'flex', flexDirection: 'column'}}>
              {/* Header do Cardápio */}
              <div
                style={{
                  padding: '14px 24px',
                  backgroundColor: CORES.marca,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderBottom: '1px solid rgba(255,255,255,0.15)',
                  flexShrink: 0,
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                  <span style={{fontSize: 28}}>📸</span>
                  <span style={{fontFamily, fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                    Cardápio com Fotos Reais
                  </span>
                </div>
                <div
                  style={{
                    padding: '4px 14px',
                    backgroundColor: 'rgba(255, 255, 255, 0.2)',
                    borderRadius: 14,
                  }}
                >
                  <span style={{fontFamily, fontSize: 26, fontWeight: 700, color: '#FFFFFF'}}>
                    No Celular
                  </span>
                </div>
              </div>

              {/* Lista dos pratos com FOTOS REAIS em alta resolução e animação em cascata ajustada */}
              <div
                style={{
                  flex: 1,
                  padding: '12px 18px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: 10,
                }}
              >
                {/* Item 1: Burger com foto real */}
                <div
                  style={{
                    backgroundColor: '#1E293B',
                    borderRadius: 18,
                    border: '1.5px solid rgba(255,255,255,0.14)',
                    padding: '10px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 16,
                    transform: `translateX(${(1 - sprItem1) * 60}px)`,
                    opacity: sprItem1,
                    boxShadow: '0 6px 18px rgba(0,0,0,0.5)',
                  }}
                >
                  <img
                    src={staticFile('foto_burger.jpg')}
                    alt="Burger Artesanal"
                    style={{
                      width: 110,
                      height: 110,
                      borderRadius: 16,
                      objectFit: 'cover',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.6)',
                      border: '2px solid rgba(255, 255, 255, 0.2)',
                      flexShrink: 0,
                    }}
                  />
                  <div style={{display: 'flex', flexDirection: 'column', gap: 2, flex: 1}}>
                    <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                      <span style={{fontFamily, fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                        Burger Artesanal
                      </span>
                      <span
                        style={{
                          padding: '2px 8px',
                          backgroundColor: CORES.apoio,
                          borderRadius: 8,
                          fontFamily,
                          fontSize: 20,
                          fontWeight: 800,
                          color: '#111111',
                        }}
                      >
                        ⭐ Mais Pedido
                      </span>
                    </div>
                    <span style={{fontFamily, fontSize: 30, fontWeight: 600, color: '#CBD5E1', lineHeight: 1.2}}>
                      Pão brioche com smash duplo, queijo cheddar e molho especial
                    </span>
                  </div>
                </div>

                {/* Item 2: Batata Rústica com foto real */}
                <div
                  style={{
                    backgroundColor: '#1E293B',
                    borderRadius: 18,
                    border: '1.5px solid rgba(255,255,255,0.14)',
                    padding: '10px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 16,
                    transform: `translateX(${(1 - sprItem2) * 60}px)`,
                    opacity: sprItem2,
                    boxShadow: '0 6px 18px rgba(0,0,0,0.5)',
                  }}
                >
                  <img
                    src={staticFile('foto_batata.jpg')}
                    alt="Batata Rústica"
                    style={{
                      width: 110,
                      height: 110,
                      borderRadius: 16,
                      objectFit: 'cover',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.6)',
                      border: '2px solid rgba(255, 255, 255, 0.2)',
                      flexShrink: 0,
                    }}
                  />
                  <div style={{display: 'flex', flexDirection: 'column', gap: 2, flex: 1}}>
                    <span style={{fontFamily, fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                      Batata Rústica
                    </span>
                    <span style={{fontFamily, fontSize: 30, fontWeight: 600, color: '#CBD5E1', lineHeight: 1.2}}>
                      Batatas crocantes temperadas com páprica e alecrim especial
                    </span>
                  </div>
                </div>

                {/* Item 3: Bebidas com foto real */}
                <div
                  style={{
                    backgroundColor: '#1E293B',
                    borderRadius: 18,
                    border: '1.5px solid rgba(255,255,255,0.14)',
                    padding: '10px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 16,
                    transform: `translateX(${(1 - sprItem3) * 60}px)`,
                    opacity: sprItem3,
                    boxShadow: '0 6px 18px rgba(0,0,0,0.5)',
                  }}
                >
                  <img
                    src={staticFile('foto_bebida.jpg')}
                    alt="Bebidas & Sobremesas"
                    style={{
                      width: 110,
                      height: 110,
                      borderRadius: 16,
                      objectFit: 'cover',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.6)',
                      border: '2px solid rgba(255, 255, 255, 0.2)',
                      flexShrink: 0,
                    }}
                  />
                  <div style={{display: 'flex', flexDirection: 'column', gap: 2, flex: 1}}>
                    <span style={{fontFamily, fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                      Bebidas da Casa
                    </span>
                    <span style={{fontFamily, fontSize: 30, fontWeight: 600, color: '#CBD5E1', lineHeight: 1.2}}>
                      Sucos naturais, refrigerantes e opções refrescantes
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* FASE B: Chat do WhatsApp com IA respondendo dúvidas (Etapa 3: frame 150 em diante) */}
          {etapaAtiva === 3 && (
            <div style={{flex: 1, display: 'flex', flexDirection: 'column'}}>
              {/* Header do WhatsApp com Atendente IA */}
              <div
                style={{
                  padding: '16px 22px',
                  backgroundColor: '#075E54',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderBottom: '1px solid rgba(255,255,255,0.1)',
                }}
              >
                <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                  <div
                    style={{
                      width: 50,
                      height: 50,
                      borderRadius: 25,
                      backgroundColor: CORES.marca,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 26,
                    }}
                  >
                    🤖
                  </div>
                  <div style={{display: 'flex', flexDirection: 'column'}}>
                    <span style={{fontFamily, fontSize: 32, fontWeight: 800, color: '#FFFFFF'}}>
                      Atendimento com IA
                    </span>
                    <span style={{fontFamily, fontSize: 26, fontWeight: 600, color: '#A7F3D0'}}>
                      Online no WhatsApp
                    </span>
                  </div>
                </div>

                <div
                  style={{
                    padding: '4px 12px',
                    backgroundColor: 'rgba(0, 0, 0, 0.35)',
                    borderRadius: 12,
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                  }}
                >
                  <span style={{fontFamily, fontSize: 24, fontWeight: 700, color: '#CBD5E1'}}>
                    Simulação
                  </span>
                </div>
              </div>

              {/* Conversa com a IA tirando dúvidas na hora */}
              <div
                style={{
                  flex: 1,
                  padding: '22px 24px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 18,
                  backgroundColor: '#0B141B',
                  justifyContent: 'center',
                }}
              >
                {/* Mensagem do cliente com dúvida */}
                <div
                  style={{
                    alignSelf: 'flex-end',
                    maxWidth: '85%',
                    padding: '14px 20px',
                    backgroundColor: '#005C4B',
                    borderRadius: '20px 20px 4px 20px',
                    boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                  }}
                >
                  <div style={{fontFamily, fontSize: 34, fontWeight: 700, color: '#FFFFFF', lineHeight: 1.25}}>
                    O hambúrguer tem opção sem lactose?
                  </div>
                  <div style={{textAlign: 'right', marginTop: 4, fontFamily, fontSize: 24, color: '#8696A0'}}>
                    20:16 ✓✓
                  </div>
                </div>

                {/* Resposta instantânea da IA tirando dúvida */}
                <div
                  style={{
                    alignSelf: 'flex-start',
                    maxWidth: '88%',
                    padding: '16px 22px',
                    backgroundColor: '#1E293B',
                    borderRadius: '20px 20px 20px 4px',
                    border: `1.5px solid ${CORES.apoio}`,
                    boxShadow: '0 6px 18px rgba(0,0,0,0.5)',
                  }}
                >
                  <div style={{display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6}}>
                    <span style={{fontSize: 24}}>⚡</span>
                    <span style={{fontFamily, fontSize: 26, fontWeight: 800, color: CORES.apoio}}>
                      IA responde na hora:
                    </span>
                  </div>
                  <div style={{fontFamily, fontSize: 34, fontWeight: 700, color: '#FFFFFF', lineHeight: 1.25}}>
                    Temos sim! O Smash Artesanal pode ser preparado sem queijo e com pão especial. Quer pedir? 🍔
                  </div>
                  <div style={{textAlign: 'right', marginTop: 4, fontFamily, fontSize: 24, color: '#94A3B8'}}>
                    20:16
                  </div>
                </div>

                {/* Tag de confirmação do pedido ágil */}
                <div
                  style={{
                    alignSelf: 'center',
                    marginTop: 6,
                    padding: '10px 24px',
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    border: '1.5px solid #10B981',
                    borderRadius: 20,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  <span style={{fontSize: 24}}>✅</span>
                  <span style={{fontFamily, fontSize: 28, fontWeight: 800, color: '#A7F3D0'}}>
                    Dúvidas respondidas na hora
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </AbsoluteFill>
  );
};
